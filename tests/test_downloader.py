import os
import queue
import time

import pytest
import yt_dlp

import downloader


def wait_for_status(progress_queue, expected_status, timeout=5.0):
    """Collect queue messages until *expected_status* arrives."""
    messages = []
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            messages.append(progress_queue.get(timeout=0.05))
        except queue.Empty:
            continue
        if messages[-1].get("status") == expected_status:
            return messages

    raise AssertionError(f"never received {expected_status}: {messages}")


def make_fake_youtube_dl(
    progress_events=(), return_code=0, error=None, logger_errors=()
):
    """Build a yt-dlp stand-in and a holder for its options/URLs."""
    holder = {}

    class FakeYoutubeDL:
        def __init__(self, options):
            self.options = options
            holder["options"] = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def download(self, urls):
            holder["urls"] = urls
            for logger_error in logger_errors:
                self.options["logger"].error(logger_error)
            for progress_data in progress_events:
                self.options["progress_hooks"][0](progress_data)
            if error is not None:
                raise error
            return return_code

    return FakeYoutubeDL, holder


def test_build_progress_message_downloading():
    message = downloader.build_progress_message(
        {
            "status": "downloading",
            "downloaded_bytes": 50,
            "total_bytes": 200,
            "filename": r"C:\output\video.webm",
            "speed": 1024,
            "eta": 42,
            "info_dict": {"playlist_index": 2, "playlist_count": 5},
        }
    )

    assert message == {
        "status": downloader.STATUS_DOWNLOADING,
        "percent": 25.0,
        "speed": 1024,
        "eta": 42,
        "filename": "video.webm",
        "playlist_index": 2,
        "playlist_count": 5,
    }


def test_build_progress_message_falls_back_to_estimated_size():
    message = downloader.build_progress_message(
        {
            "status": "downloading",
            "downloaded_bytes": 25,
            "total_bytes_estimate": 100,
        }
    )

    assert message["percent"] == 25.0


def test_build_progress_message_without_size_reports_zero_percent():
    message = downloader.build_progress_message(
        {"status": "downloading", "downloaded_bytes": 25}
    )

    assert message["percent"] == 0


def test_build_progress_message_finished():
    message = downloader.build_progress_message({"status": "finished"})

    assert message == {
        "status": downloader.STATUS_PROCESSING,
        "percent": downloader.COMPLETE_PERCENT,
    }


def test_build_progress_message_ignores_other_statuses():
    assert downloader.build_progress_message({"status": "starting"}) is None


def test_clean_error_message_strips_colour_and_prefix():
    message = downloader.clean_error_message(
        "\x1b[0;31mERROR:\x1b[0m Video unavailable"
    )

    assert message == "Video unavailable"


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/playlist?list=PL123",
        "https://www.youtube.com/playlist?list=PL123&index=4",
        "https://example.com/gallery?playlist_id=42",
    ],
)
def test_is_bare_playlist_url_detects_playlists_without_a_video(url):
    assert downloader.is_bare_playlist_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc123&list=PL123",
        "https://youtu.be/abc123?list=PL123",
        "https://www.youtube.com/watch?v=abc123",
        "https://example.com/video",
        "https://soundcloud.com/artist/sets/album",
    ],
)
def test_is_bare_playlist_url_ignores_videos_and_unknown_urls(url):
    assert downloader.is_bare_playlist_url(url) is False


def test_download_reports_progress_and_completion(tmp_path, monkeypatch):
    fake_youtube_dl, holder = make_fake_youtube_dl(
        [
            {
                "status": "downloading",
                "downloaded_bytes": 50,
                "total_bytes": 200,
                "filename": "video.webm",
            },
            {"status": "finished"},
        ]
    )
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake_youtube_dl)
    instance = downloader.Downloader()

    instance.download("https://example.com/video", str(tmp_path))

    messages = wait_for_status(instance.progress_queue, downloader.STATUS_COMPLETED)

    assert [message["status"] for message in messages] == [
        downloader.STATUS_DOWNLOADING,
        downloader.STATUS_PROCESSING,
        downloader.STATUS_COMPLETED,
    ]
    assert messages[-1]["errors"] == []
    assert holder["urls"] == ["https://example.com/video"]


def test_download_reports_partial_failures(tmp_path, monkeypatch):
    fake_youtube_dl, _holder = make_fake_youtube_dl(
        return_code=1,
        logger_errors=["ERROR: Video unavailable", "ERROR: Postprocessing failed"],
    )
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake_youtube_dl)
    instance = downloader.Downloader()

    instance.download("https://example.com/playlist", str(tmp_path))

    completed = wait_for_status(instance.progress_queue, downloader.STATUS_COMPLETED)[
        -1
    ]

    assert completed["errors"] == [
        "Video unavailable",
        "Postprocessing failed",
    ]


def test_download_reports_return_code_without_messages(tmp_path, monkeypatch):
    fake_youtube_dl, _holder = make_fake_youtube_dl(return_code=2)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake_youtube_dl)
    instance = downloader.Downloader()

    instance.download("https://example.com/video", str(tmp_path))

    completed = wait_for_status(instance.progress_queue, downloader.STATUS_COMPLETED)[
        -1
    ]

    assert completed["errors"] == ["yt-dlp exited with code 2"]


def test_download_reports_unexpected_errors(tmp_path, monkeypatch):
    fake_youtube_dl, _holder = make_fake_youtube_dl(error=RuntimeError("boom"))
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake_youtube_dl)
    instance = downloader.Downloader()

    instance.download("https://example.com/video", str(tmp_path))

    error_message = wait_for_status(instance.progress_queue, downloader.STATUS_ERROR)[
        -1
    ]

    assert error_message["error"] == "boom"


def test_cancelled_session_raises_download_cancelled():
    session = downloader.DownloadSession()
    session.cancel_event.set()

    with pytest.raises(yt_dlp.utils.DownloadCancelled):
        downloader.Downloader()._on_progress(
            session, {"status": "downloading", "downloaded_bytes": 1}
        )


def test_progress_and_cancellation_are_scoped_to_the_active_session():
    stale_session = downloader.DownloadSession()
    active_session = downloader.DownloadSession()
    instance = downloader.Downloader()
    instance._active_session = active_session
    instance.progress_queue = active_session.progress_queue

    instance._on_progress(
        stale_session,
        {"status": "downloading", "downloaded_bytes": 1, "total_bytes": 2},
    )

    assert stale_session.progress_queue.qsize() == 1
    assert active_session.progress_queue.empty()

    instance.cancel()

    assert active_session.cancel_event.is_set()
    assert not stale_session.cancel_event.is_set()


def test_build_options_uses_audio_only_format_for_mp3(monkeypatch, tmp_path):
    monkeypatch.setattr(
        downloader, "find_ffmpeg_location", lambda: str(tmp_path / "bin")
    )
    session = downloader.DownloadSession()

    options = downloader.Downloader()._build_options(
        session, str(tmp_path), convert_to_mp3=True
    )

    assert options["format"] == downloader.AUDIO_ONLY_FORMAT
    assert options["ffmpeg_location"] == str(tmp_path / "bin")
    assert options["postprocessors"] == [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": downloader.MP3_PREFERRED_QUALITY,
        }
    ]
    assert options["outtmpl"] == os.path.join(str(tmp_path), "%(title)s.%(ext)s")


def test_build_options_keeps_full_video_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader, "find_ffmpeg_location", lambda: None)
    session = downloader.DownloadSession()

    options = downloader.Downloader()._build_options(
        session, str(tmp_path), convert_to_mp3=False
    )

    assert "format" not in options
    assert "postprocessors" not in options
    assert "ffmpeg_location" not in options


def test_build_options_expands_playlists_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader, "find_ffmpeg_location", lambda: None)
    session = downloader.DownloadSession()

    options = downloader.Downloader()._build_options(
        session, str(tmp_path), convert_to_mp3=False, video_only=False
    )

    assert options["noplaylist"] is False


def test_build_options_ignores_playlist_for_video_only(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader, "find_ffmpeg_location", lambda: None)
    session = downloader.DownloadSession()

    options = downloader.Downloader()._build_options(
        session, str(tmp_path), convert_to_mp3=False, video_only=True
    )

    assert options["noplaylist"] is True


def test_download_passes_video_only_to_yt_dlp(tmp_path, monkeypatch):
    fake_youtube_dl, holder = make_fake_youtube_dl()
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake_youtube_dl)
    instance = downloader.Downloader()

    instance.download(
        "https://www.youtube.com/watch?v=abc123&list=PL123",
        str(tmp_path),
        video_only=True,
    )

    wait_for_status(instance.progress_queue, downloader.STATUS_COMPLETED)

    assert holder["options"]["noplaylist"] is True


def test_find_ffmpeg_location_requires_both_binaries(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    binary_directory = tmp_path / "bin"
    binary_directory.mkdir()
    (binary_directory / "ffmpeg.exe").write_bytes(b"ffmpeg")

    assert downloader.find_ffmpeg_location() is None

    (binary_directory / "ffprobe.exe").write_bytes(b"ffprobe")

    assert downloader.find_ffmpeg_location() == str(binary_directory)


def test_resolve_bundled_path_prefers_pyinstaller_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert downloader.resolve_bundled_path("bin") == os.path.join(str(tmp_path), "bin")


def test_is_ffmpeg_available_falls_back_to_path(monkeypatch):
    monkeypatch.setattr(downloader, "find_ffmpeg_location", lambda: None)
    monkeypatch.setattr(downloader.shutil, "which", lambda name: None)

    assert downloader.is_ffmpeg_available() is False

    monkeypatch.setattr(
        downloader.shutil, "which", lambda name: r"C:\ffmpeg\ffmpeg.exe"
    )

    assert downloader.is_ffmpeg_available() is True
