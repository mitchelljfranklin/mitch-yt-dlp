"""
Thin wrapper around yt-dlp's Python API.

Runs downloads in a background thread and reports progress via a
thread-safe queue so the GUI can poll it without blocking.

Also handles cancellation, MP3 post-processing, and locating the
bundled FFmpeg binary when packaged with PyInstaller.
"""

import functools
import os
import queue
import re
import shutil
import sys
import threading
from urllib.parse import parse_qs, urlparse

import yt_dlp

# Status values written to the progress queue
STATUS_DOWNLOADING = "downloading"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
STATUS_ERROR = "error"

# Engine version, shown in the UI so stale bundled extractors are visible
YT_DLP_VERSION = yt_dlp.version.__version__

# yt-dlp option values
FFMPEG_BUNDLE_DIRECTORY = "bin"
MP3_PREFERRED_QUALITY = "192"
AUDIO_ONLY_FORMAT = "bestaudio/best"
COMPLETE_PERCENT = 100

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
ERROR_MESSAGE_PREFIX = "ERROR:"

# Query parameters that mark a URL as referring to a playlist, and the ones
# that carry the single video to prefer when both are present.
PLAYLIST_QUERY_PARAMETERS = ("list", "playlist", "playlist_id")
VIDEO_QUERY_PARAMETERS = ("v",)
# Hosts that put the video id in the path, so a ``list`` parameter alone does
# not mean the link is a playlist.
VIDEO_PATH_HOSTS = ("youtu.be", "www.youtu.be")


# ---------------------------------------------------------------------------
# Helpers
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


def find_ffmpeg_location():
    """
    Return the directory holding the bundled FFmpeg binaries, or ``None``.

    Both ``ffmpeg.exe`` and ``ffprobe.exe`` must be present, otherwise
    yt-dlp is left to discover a system-wide FFmpeg installation.
    """
    ffmpeg_directory = resolve_bundled_path(FFMPEG_BUNDLE_DIRECTORY)
    ffmpeg_executable = os.path.join(ffmpeg_directory, "ffmpeg.exe")
    ffprobe_executable = os.path.join(ffmpeg_directory, "ffprobe.exe")
    if os.path.exists(ffmpeg_executable) and os.path.exists(ffprobe_executable):
        return ffmpeg_directory
    return None


def is_ffmpeg_available():
    """Return ``True`` when FFmpeg is bundled or available on ``PATH``."""
    return find_ffmpeg_location() is not None or shutil.which("ffmpeg") is not None


def clean_error_message(message):
    """Strip ANSI colour codes and the ``ERROR:`` prefix from a yt-dlp message."""
    cleaned_message = ANSI_ESCAPE_PATTERN.sub("", message).strip()
    if cleaned_message.startswith(ERROR_MESSAGE_PREFIX):
        cleaned_message = cleaned_message[len(ERROR_MESSAGE_PREFIX) :].strip()
    return cleaned_message


def is_bare_playlist_url(url):
    """
    Return ``True`` when *url* points at a playlist without a chosen video.

    yt-dlp's ``noplaylist`` option only picks the single video when the URL
    carries both a video and a playlist (``watch?v=…&list=…``).  A playlist
    link with no video in it cannot honour "video only", so the UI warns
    instead of silently downloading every entry.  The check is deliberately
    conservative: anything it does not recognise is left to yt-dlp.
    """
    parsed_url = urlparse(url)
    query_parameters = parse_qs(parsed_url.query)

    if not any(name in query_parameters for name in PLAYLIST_QUERY_PARAMETERS):
        return False
    if any(name in query_parameters for name in VIDEO_QUERY_PARAMETERS):
        return False
    if (
        parsed_url.netloc.lower() in VIDEO_PATH_HOSTS
        and parsed_url.path.strip("/") != ""
    ):
        return False

    return True


def build_progress_message(progress_data):
    """
    Convert a yt-dlp progress dict into a queue message for the UI.

    Returns ``None`` for progress statuses the UI does not need to see.
    """
    progress_status = progress_data.get("status")

    if progress_status == "downloading":
        total_bytes = progress_data.get("total_bytes") or progress_data.get(
            "total_bytes_estimate", 0
        )
        downloaded_bytes = progress_data.get("downloaded_bytes", 0)
        percent_done = (
            (downloaded_bytes / total_bytes * COMPLETE_PERCENT) if total_bytes else 0
        )
        info = progress_data.get("info_dict") or {}

        return {
            "status": STATUS_DOWNLOADING,
            "percent": percent_done,
            "speed": progress_data.get("speed"),
            "eta": progress_data.get("eta"),
            "filename": os.path.basename(progress_data.get("filename", "")),
            "playlist_index": info.get("playlist_index"),
            "playlist_count": info.get("playlist_count"),
        }

    if progress_status == "finished":
        return {"status": STATUS_PROCESSING, "percent": COMPLETE_PERCENT}

    return None


class DownloadLogger:
    """
    Minimal yt-dlp logger that records error messages for the UI.

    yt-dlp writes errors through ``logger.error`` whenever a logger is
    configured, so this keeps diagnostics available even though the GUI
    has no console (and ``ignoreerrors`` keeps playlists going).
    """

    def __init__(self):
        self.error_messages = []

    def debug(self, message):
        """Ignore debug output."""

    def info(self, message):
        """Ignore informational output."""

    def warning(self, message):
        """Ignore warnings; only errors are surfaced after a download."""

    def error(self, message):
        """Record an error message for the completion summary."""
        self.error_messages.append(clean_error_message(str(message)))


class DownloadSession:
    """
    State belonging to a single download run.

    Keeping the queue and cancel event per session means a superseded
    download can never publish into the queue the UI is currently polling.
    """

    def __init__(self):
        self.progress_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.logger = DownloadLogger()


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------


class Downloader:
    """
    Manages a yt-dlp download on a background thread.

    Reports progress through a :class:`queue.Queue` that the UI polls on
    the main thread to avoid tkinter thread-safety issues.
    """

    def __init__(self):
        self.progress_queue = queue.Queue()
        self._active_session = None
        self._download_thread = None

    # -- Progress hook (called by yt-dlp from its download thread) ----------

    def _on_progress(self, session, progress_data):
        """
        Progress hook invoked by yt-dlp during a download.

        Pushes a status dict onto the session's thread-safe queue so the
        UI can consume it on the main thread.  Raises
        ``DownloadCancelled`` if the user has requested cancellation.
        """
        if session.cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Cancelled by user")

        progress_message = build_progress_message(progress_data)
        if progress_message is not None:
            session.progress_queue.put(progress_message)

    # -- Public API ---------------------------------------------------------

    def download(self, url, output_directory, convert_to_mp3=False, video_only=False):
        """
        Start downloading *url* into *output_directory* on a background thread.

        If *convert_to_mp3* is ``True``, the downloaded media will be
        post-processed into an MP3 audio file (requires FFmpeg).  If
        *video_only* is ``True``, a URL that points at both a video and a
        playlist downloads just that video.
        """
        session = DownloadSession()
        self._active_session = session
        self.progress_queue = session.progress_queue

        self._download_thread = threading.Thread(
            target=self._download_task,
            args=(session, url, output_directory, convert_to_mp3, video_only),
            daemon=True,
        )
        self._download_thread.start()

    def cancel(self):
        """
        Request cancellation of the active download.

        The progress hook will notice the cancel event on its next
        invocation and abort the yt-dlp download loop gracefully.
        """
        if self._active_session is not None:
            self._active_session.cancel_event.set()

    # -- Internals ----------------------------------------------------------

    def _download_task(
        self, session, url, output_directory, convert_to_mp3, video_only
    ):
        """Run one download to completion, reporting the final status."""
        try:
            options = self._build_options(
                session, output_directory, convert_to_mp3, video_only
            )
            with yt_dlp.YoutubeDL(options) as youtube_downloader:
                return_code = youtube_downloader.download([url])

            error_messages = list(session.logger.error_messages)
            if return_code != 0 and not error_messages:
                error_messages.append(f"yt-dlp exited with code {return_code}")

            session.progress_queue.put(
                {
                    "status": STATUS_COMPLETED,
                    "percent": COMPLETE_PERCENT,
                    "errors": error_messages,
                }
            )
        except yt_dlp.utils.DownloadCancelled:
            session.progress_queue.put({"status": STATUS_CANCELLED})
        except Exception as error:
            # Any yt-dlp failure (including extractor bugs) must reach the UI
            # instead of killing the worker thread silently.
            error_message = str(error) or type(error).__name__
            session.progress_queue.put({"status": STATUS_ERROR, "error": error_message})

    def _build_options(
        self, session, output_directory, convert_to_mp3, video_only=False
    ):
        """Return the yt-dlp options dict for one download run."""
        options = {
            "outtmpl": os.path.join(output_directory, "%(title)s.%(ext)s"),
            "progress_hooks": [functools.partial(self._on_progress, session)],
            "logger": session.logger,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            # Only meaningful when the URL names both a video and a playlist;
            # a playlist-only URL still expands to every entry.
            "noplaylist": video_only,
            "extract_flat": False,
        }

        if convert_to_mp3:
            # Downloading audio only avoids fetching video that is deleted
            # immediately after the MP3 conversion.
            options["format"] = AUDIO_ONLY_FORMAT
            options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": MP3_PREFERRED_QUALITY,
                }
            ]

        ffmpeg_location = find_ffmpeg_location()
        if ffmpeg_location is not None:
            options["ffmpeg_location"] = ffmpeg_location

        return options
