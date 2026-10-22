import os
import zipfile

import pytest

import setup_ffmpeg


def write_archive(archive_path, entries):
    """Create a zip containing *entries* (name -> bytes)."""
    with zipfile.ZipFile(archive_path, "w") as archive:
        for entry_name, content in entries.items():
            archive.writestr(entry_name, content)
    return archive_path


def test_binaries_are_present_requires_both_files(tmp_path):
    (tmp_path / "ffmpeg.exe").write_bytes(b"binary")

    assert setup_ffmpeg.binaries_are_present(tmp_path) is False

    (tmp_path / "ffprobe.exe").write_bytes(b"binary")

    assert setup_ffmpeg.binaries_are_present(tmp_path) is True


def test_binaries_are_present_rejects_empty_files(tmp_path):
    (tmp_path / "ffmpeg.exe").write_bytes(b"")
    (tmp_path / "ffprobe.exe").write_bytes(b"binary")

    assert setup_ffmpeg.binaries_are_present(tmp_path) is False


def test_extract_binaries_ignores_unrelated_files(tmp_path):
    archive_path = write_archive(
        tmp_path / "ffmpeg.zip",
        {
            "ffmpeg-7.1-essentials_build/bin/ffmpeg.exe": b"ffmpeg",
            "ffmpeg-7.1-essentials_build/bin/ffplay.exe": b"ffplay",
            "ffmpeg-7.1-essentials_build/bin/ffprobe.exe": b"ffprobe",
            "ffmpeg-7.1-essentials_build/README.txt": b"docs",
        },
    )
    output_directory = tmp_path / "bin"
    output_directory.mkdir()

    extracted_names = setup_ffmpeg.extract_binaries(archive_path, output_directory)

    assert sorted(extracted_names) == ["ffmpeg.exe", "ffprobe.exe"]
    assert sorted(entry.name for entry in output_directory.iterdir()) == [
        "ffmpeg.exe",
        "ffprobe.exe",
    ]


def test_extract_binaries_rejects_archive_without_ffprobe(tmp_path):
    archive_path = write_archive(
        tmp_path / "ffmpeg.zip",
        {"ffmpeg-7.1-essentials_build/bin/ffmpeg.exe": b"ffmpeg"},
    )
    output_directory = tmp_path / "bin"
    output_directory.mkdir()

    with pytest.raises(setup_ffmpeg.FFmpegSetupError, match="ffprobe.exe"):
        setup_ffmpeg.extract_binaries(archive_path, output_directory)


def test_extract_binaries_rejects_empty_binaries(tmp_path):
    archive_path = write_archive(
        tmp_path / "ffmpeg.zip",
        {
            "ffmpeg-7.1-essentials_build/bin/ffmpeg.exe": b"ffmpeg",
            "ffmpeg-7.1-essentials_build/bin/ffprobe.exe": b"",
        },
    )
    output_directory = tmp_path / "bin"
    output_directory.mkdir()

    with pytest.raises(setup_ffmpeg.FFmpegSetupError, match="empty files"):
        setup_ffmpeg.extract_binaries(archive_path, output_directory)


def test_extract_binaries_rejects_corrupt_archive(tmp_path):
    archive_path = tmp_path / "ffmpeg.zip"
    archive_path.write_bytes(b"definitely not a zip")
    output_directory = tmp_path / "bin"
    output_directory.mkdir()

    with pytest.raises(setup_ffmpeg.FFmpegSetupError, match="Failed to extract"):
        setup_ffmpeg.extract_binaries(archive_path, output_directory)


def test_setup_is_a_no_op_when_binaries_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_ffmpeg, "OUTPUT_DIRECTORY", str(tmp_path))
    (tmp_path / "ffmpeg.exe").write_bytes(b"ffmpeg")
    (tmp_path / "ffprobe.exe").write_bytes(b"ffprobe")

    def fail_download(destination_path):
        raise AssertionError("download should not run")

    monkeypatch.setattr(setup_ffmpeg, "download_archive", fail_download)

    assert setup_ffmpeg.setup_ffmpeg() is True


def test_setup_removes_temporary_archive_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_ffmpeg, "OUTPUT_DIRECTORY", str(tmp_path))

    def failing_download(destination_path):
        with open(destination_path, "wb") as partial_archive:
            partial_archive.write(b"partial")
        raise setup_ffmpeg.FFmpegSetupError("network down")

    monkeypatch.setattr(setup_ffmpeg, "download_archive", failing_download)

    assert setup_ffmpeg.setup_ffmpeg() is False
    assert not os.path.exists(tmp_path / setup_ffmpeg.TEMPORARY_ARCHIVE_NAME)
