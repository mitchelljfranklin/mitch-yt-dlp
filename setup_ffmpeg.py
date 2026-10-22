"""
Download FFmpeg Windows binaries for bundling with Mitch-yt-dlp.

FFmpeg is required for the "Convert to MP3" post-processing feature.
This script fetches the latest essentials build from gyan.dev and
extracts ffmpeg.exe and ffprobe.exe into the ``bin/`` directory.

Usage:
    python setup_ffmpeg.py

Exits with a non-zero status when the binaries cannot be fetched, so CI
fails loudly instead of producing an EXE without MP3 support.
"""

import os
import shutil
import sys
import urllib.error
import urllib.request
import zipfile

FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
DOWNLOAD_TIMEOUT_SECONDS = 120
REQUIRED_BINARIES = ("ffmpeg.exe", "ffprobe.exe")
TEMPORARY_ARCHIVE_NAME = "ffmpeg-download.zip"

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "bin")


class FFmpegSetupError(RuntimeError):
    """Raised when the FFmpeg archive cannot be downloaded or extracted."""


def binaries_are_present(output_directory=None):
    """Return ``True`` when both required binaries exist and are non-empty."""
    resolved_directory = output_directory or OUTPUT_DIRECTORY
    for binary_name in REQUIRED_BINARIES:
        binary_path = os.path.join(resolved_directory, binary_name)
        try:
            if os.path.getsize(binary_path) <= 0:
                return False
        except OSError:
            return False
    return True


def remove_if_present(path):
    """Delete *path* when it exists, ignoring a missing file."""
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def download_archive(destination_path):
    """
    Download the FFmpeg release archive to *destination_path*.

    Uses an explicit timeout so an unresponsive mirror cannot hang CI.
    """
    request = urllib.request.Request(
        FFMPEG_DOWNLOAD_URL, headers={"User-Agent": "Mitch-yt-dlp"}
    )
    try:
        with urllib.request.urlopen(
            request, timeout=DOWNLOAD_TIMEOUT_SECONDS
        ) as response:
            with open(destination_path, "wb") as archive_file:
                shutil.copyfileobj(response, archive_file)
    except (urllib.error.URLError, OSError, TimeoutError) as download_error:
        raise FFmpegSetupError(
            f"Failed to download FFmpeg: {download_error}"
        ) from download_error


def extract_binaries(archive_path, output_directory):
    """
    Extract ``ffmpeg.exe`` and ``ffprobe.exe`` from the downloaded archive.

    Raises :class:`FFmpegSetupError` when either binary is missing or empty,
    which happens with truncated or partially written archives.
    """
    extracted_names = []

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            for entry_name in archive.namelist():
                file_name = os.path.basename(entry_name)
                if file_name not in REQUIRED_BINARIES:
                    continue

                destination_path = os.path.join(output_directory, file_name)
                with (
                    archive.open(entry_name) as source,
                    open(destination_path, "wb") as destination,
                ):
                    shutil.copyfileobj(source, destination)
                extracted_names.append(file_name)
    except (zipfile.BadZipFile, OSError) as extraction_error:
        raise FFmpegSetupError(
            f"Failed to extract FFmpeg: {extraction_error}"
        ) from extraction_error

    missing_names = [
        binary_name
        for binary_name in REQUIRED_BINARIES
        if binary_name not in extracted_names
    ]
    if missing_names or not binaries_are_present(output_directory):
        missing_summary = ", ".join(missing_names) or "empty files"
        raise FFmpegSetupError(
            f"Archive did not contain usable FFmpeg binaries: {missing_summary}"
        )

    return extracted_names


def setup_ffmpeg():
    """
    Download and extract the FFmpeg binaries into ``bin/``.

    Returns ``True`` on success and ``False`` when the download or
    extraction failed.  Safe to run repeatedly: existing binaries are kept.
    """
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    temporary_zip_path = os.path.join(OUTPUT_DIRECTORY, TEMPORARY_ARCHIVE_NAME)
    remove_if_present(temporary_zip_path)

    if binaries_are_present():
        print("FFmpeg binaries already present in bin/")
        return True

    print(f"Downloading FFmpeg from {FFMPEG_DOWNLOAD_URL} ...")
    try:
        download_archive(temporary_zip_path)
        print("Extracting ffmpeg.exe and ffprobe.exe ...")
        for extracted_name in extract_binaries(temporary_zip_path, OUTPUT_DIRECTORY):
            print(f"  Extracted {extracted_name}")
    except FFmpegSetupError as setup_error:
        print(setup_error)
        print(
            "Please download ffmpeg.exe and ffprobe.exe manually "
            "and place them in the bin/ directory."
        )
        return False
    finally:
        remove_if_present(temporary_zip_path)

    print("FFmpeg setup complete.")
    print(f"Binaries placed in {OUTPUT_DIRECTORY}")
    return True


def main():
    """Run the setup and exit non-zero when it fails."""
    if not setup_ffmpeg():
        sys.exit(1)


if __name__ == "__main__":
    main()
