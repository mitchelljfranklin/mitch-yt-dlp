import os
import sys
import queue
import threading
import yt_dlp
import yt_dlp.utils


def resource_path(relative_path):
    if getattr(sys, "_MEIPASS", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)


class Downloader:
    def __init__(self):
        self.progress_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self._thread = None

    def _progress_hook(self, d):
        if self.cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Cancelled by user")

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0
            self.progress_queue.put(
                {
                    "percent": percent,
                    "speed": d.get("speed"),
                    "eta": d.get("eta"),
                    "status": "downloading",
                    "filename": os.path.basename(d.get("filename", "")),
                }
            )
        elif d["status"] == "finished":
            self.progress_queue.put({"percent": 100, "status": "processing"})

    def download(self, url, output_path, to_mp3=False):
        def _run():
            try:
                opts = {
                    "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
                    "progress_hooks": [self._progress_hook],
                    "quiet": True,
                    "no_warnings": True,
                    "ignoreerrors": False,
                    "noplaylist": False,
                    "extract_flat": False,
                }

                ffmpeg_path = resource_path(os.path.join("bin", "ffmpeg.exe"))
                if os.path.exists(ffmpeg_path):
                    opts["ffmpeg_location"] = ffmpeg_path

                if to_mp3:
                    opts["postprocessors"] = [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ]

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                self.progress_queue.put({"percent": 100, "status": "completed"})
            except yt_dlp.utils.DownloadCancelled:
                self.progress_queue.put({"status": "cancelled"})
            except Exception as e:
                self.progress_queue.put({"status": "error", "error": str(e)})

        self.cancel_event.clear()
        self.progress_queue = queue.Queue()
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def cancel(self):
        self.cancel_event.set()
