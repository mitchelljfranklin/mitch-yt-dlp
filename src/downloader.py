"""
Thin wrapper around yt-dlp's Python API.

Runs downloads in a background thread and reports progress via a
thread-safe queue so the GUI can poll it without blocking.

Also handles cancellation, MP3 post-processing, and locating the
bundled FFmpeg binary when packaged with PyInstaller.
"""

import os
import sys
import queue
import threading

import yt_dlp
import yt_dlp.utils


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def resolve_bundled_path(relative_path):
    """
    Return the absolute path to a bundled resource.

    When running as a PyInstaller one-file EXE, ``sys._MEIPASS`` points
    to the temporary extraction directory.  In development mode the path
    is resolved relative to the current working directory.
    """
    if getattr(sys, "_MEIPASS", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------


class Downloader:
    """
    Manages a yt-dlp download on a background thread.

    Reports progress through a :class:`queue.Queue` that the UI polls on
    the main thread to avoid tkinter thread-safety issues.
    """

    # Status values written to the progress queue
    STATUS_DOWNLOADING = "downloading"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_ERROR = "error"

    def __init__(self):
        self.progress_queue = queue.Queue()
        self._cancel_event = threading.Event()
        self._download_thread = None

    # -- Progress hook (called by yt-dlp from its download thread) ----------

    def _on_progress(self, progress_data):
        """
        Progress hook invoked by yt-dlp during a download.

        Pushes a status dict onto the thread-safe queue so the UI can
        consume it on the main thread.  Raises ``DownloadCancelled`` if
        the user has requested cancellation.
        """
        if self._cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Cancelled by user")

        status = progress_data.get("status")

        if status == "downloading":
            total_bytes = progress_data.get("total_bytes") or progress_data.get(
                "total_bytes_estimate", 0
            )
            downloaded_bytes = progress_data.get("downloaded_bytes", 0)
            percent_done = (
                (downloaded_bytes / total_bytes * 100) if total_bytes else 0
            )

            self.progress_queue.put(
                {
                    "status": self.STATUS_DOWNLOADING,
                    "percent": percent_done,
                    "speed": progress_data.get("speed"),
                    "eta": progress_data.get("eta"),
                    "filename": os.path.basename(progress_data.get("filename", "")),
                }
            )
        elif status == "finished":
            self.progress_queue.put(
                {"status": self.STATUS_PROCESSING, "percent": 100}
            )

    # -- Public API ---------------------------------------------------------

    def download(self, url, output_directory, convert_to_mp3=False):
        """
        Start downloading *url* into *output_directory* on a background thread.

        If *convert_to_mp3* is ``True``, the downloaded media will be
        post-processed into an MP3 audio file (requires FFmpeg).
        """

        def _download_task():
            try:
                options = {
                    "outtmpl": os.path.join(
                        output_directory, "%(title)s.%(ext)s"
                    ),
                    "progress_hooks": [self._on_progress],
                    "quiet": True,
                    "no_warnings": True,
                    "ignoreerrors": False,
                    "noplaylist": False,
                    "extract_flat": False,
                }

                # Point yt-dlp to the bundled FFmpeg binary if available
                ffmpeg_executable = resolve_bundled_path(
                    os.path.join("bin", "ffmpeg.exe")
                )
                if os.path.exists(ffmpeg_executable):
                    options["ffmpeg_location"] = ffmpeg_executable

                if convert_to_mp3:
                    options["postprocessors"] = [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ]

                with yt_dlp.YoutubeDL(options) as youtube_downloader:
                    youtube_downloader.download([url])

                self.progress_queue.put(
                    {"status": self.STATUS_COMPLETED, "percent": 100}
                )
            except yt_dlp.utils.DownloadCancelled:
                self.progress_queue.put({"status": self.STATUS_CANCELLED})
            except Exception as error:
                self.progress_queue.put(
                    {"status": self.STATUS_ERROR, "error": str(error)}
                )

        # Reset state before starting a new download
        self._cancel_event.clear()
        self.progress_queue = queue.Queue()
        self._download_thread = threading.Thread(target=_download_task, daemon=True)
        self._download_thread.start()

    def cancel(self):
        """
        Request cancellation of the active download.

        The progress hook will notice the cancel event on its next
        invocation and abort the yt-dlp download loop gracefully.
        """
        self._cancel_event.set()
