import os
import sys
import zipfile
import urllib.request
import shutil

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(SCRIPT_DIR, "bin")


def setup_ffmpeg():
    os.makedirs(BIN_DIR, exist_ok=True)

    ffmpeg_path = os.path.join(BIN_DIR, "ffmpeg.exe")
    ffprobe_path = os.path.join(BIN_DIR, "ffprobe.exe")

    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        print("FFmpeg binaries already present in bin/")
        return

    zip_path = os.path.join(BIN_DIR, "ffmpeg-temp.zip")

    print(f"Downloading FFmpeg from {FFMPEG_URL}...")
    try:
        urllib.request.urlretrieve(FFMPEG_URL, zip_path)
    except Exception as e:
        print(f"Failed to download FFmpeg: {e}")
        print("Please download ffmpeg.exe and ffprobe.exe manually into bin/")
        sys.exit(1)

    print("Extracting ffmpeg.exe and ffprobe.exe...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                basename = os.path.basename(member)
                if basename in ("ffmpeg.exe", "ffprobe.exe"):
                    with zf.open(member) as src, open(
                        os.path.join(BIN_DIR, basename), "wb"
                    ) as dst:
                        shutil.copyfileobj(src, dst)
                    print(f"  Extracted {basename}")
    finally:
        os.remove(zip_path)

    print("FFmpeg setup complete.")


if __name__ == "__main__":
    setup_ffmpeg()
