"""
Download FFmpeg Windows binaries for bundling with Mitch-yt-dlp.

FFmpeg is required for the "Convert to MP3" post-processing feature.
This script fetches the latest essentials build from gyan.dev and
extracts ffmpeg.exe and ffprobe.exe into the ``bin/`` directory.

Usage:
    python setup_ffmpeg.py
"""

import os
import sys
import shutil
import zipfile
import urllib.request

FFMPEG_DOWNLOAD_URL = (
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
)

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "bin")


def setup_ffmpeg():
    """Download and extract ffmpeg.exe and ffprobe.exe into bin/."""
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    ffmpeg_destination = os.path.join(OUTPUT_DIRECTORY, "ffmpeg.exe")
    ffprobe_destination = os.path.join(OUTPUT_DIRECTORY, "ffprobe.exe")

    # Skip if binaries already exist
    if os.path.exists(ffmpeg_destination) and os.path.exists(ffprobe_destination):
        print("FFmpeg binaries already present in bin/")
        return

    temporary_zip_path = os.path.join(OUTPUT_DIRECTORY, "ffmpeg-download.zip")

    print(f"Downloading FFmpeg from {FFMPEG_DOWNLOAD_URL} ...")
    try:
        urllib.request.urlretrieve(FFMPEG_DOWNLOAD_URL, temporary_zip_path)
    except Exception as download_error:
        print(f"Failed to download FFmpeg: {download_error}")
        print(
            "Please download ffmpeg.exe and ffprobe.exe manually "
            "and place them in the bin/ directory."
        )
        sys.exit(1)

    print("Extracting ffmpeg.exe and ffprobe.exe ...")
    try:
        with zipfile.ZipFile(temporary_zip_path, "r") as zip_archive:
            for entry_name in zip_archive.namelist():
                file_name = os.path.basename(entry_name)
                if file_name in ("ffmpeg.exe", "ffprobe.exe"):
                    destination_path = os.path.join(OUTPUT_DIRECTORY, file_name)
                    with zip_archive.open(entry_name) as source, open(
                        destination_path, "wb"
                    ) as destination:
                        shutil.copyfileobj(source, destination)
                    print(f"  Extracted {file_name}")
    finally:
        os.remove(temporary_zip_path)

    print("FFmpeg setup complete.")
    print(f"Binaries placed in {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    setup_ffmpeg()
