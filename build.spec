# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Mitch-yt-dlp.

Builds a single-window (no console) .exe that bundles:
- The ttkbootstrap GUI
- yt-dlp and all its extractors / downloaders / post-processors
- ffmpeg.exe + ffprobe.exe (required; run setup_ffmpeg.py first)

Usage:
    pyinstaller build.spec

Output:
    dist/Mitch-yt-dlp.exe
"""

import os
from PyInstaller.utils.hooks import collect_submodules

# ---------------------------------------------------------------------------
# Collect FFmpeg binaries for bundling (required for MP3 conversion)
# ---------------------------------------------------------------------------

bundled_binaries = []
bundled_data_files = []

path_to_ffmpeg = os.path.join("bin", "ffmpeg.exe")
path_to_ffprobe = os.path.join("bin", "ffprobe.exe")

# Fail loudly instead of shipping an EXE whose "Convert to MP3" toggle is
# broken. CI (and releases) always run setup_ffmpeg.py first.
missing_binaries = [
    binary_path
    for binary_path in (path_to_ffmpeg, path_to_ffprobe)
    if not os.path.exists(binary_path)
]
if missing_binaries:
    raise SystemExit(
        "Missing FFmpeg binaries: "
        + ", ".join(missing_binaries)
        + "\nRun 'python setup_ffmpeg.py' before building."
    )

bundled_binaries.append((path_to_ffmpeg, "bin"))
bundled_binaries.append((path_to_ffprobe, "bin"))

# ---------------------------------------------------------------------------
# Application icon (bundled for window icon at runtime)
# ---------------------------------------------------------------------------
if os.path.exists("icon.ico"):
    bundled_data_files.append(("icon.ico", "."))

# ---------------------------------------------------------------------------
# yt-dlp hidden imports (dynamic modules loaded by name at runtime)
# ---------------------------------------------------------------------------

hidden_imports = [
    "yt_dlp",
    "yt_dlp.extractor",
    "yt_dlp.downloader",
    "yt_dlp.postprocessor",
]
hidden_imports += collect_submodules("yt_dlp")

# ---------------------------------------------------------------------------
# Analysis – resolve all imports and dependencies
# ---------------------------------------------------------------------------

analysis = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=bundled_binaries,
    datas=bundled_data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ---------------------------------------------------------------------------
# Package into a single executable
# ---------------------------------------------------------------------------

python_archive = PYZ(analysis.pure, analysis.zipped_data, cipher=None)

executable = EXE(
    python_archive,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="Mitch-yt-dlp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX-compressed executables are a common source of antivirus false
    # positives; the size saving is not worth the support burden.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",
)
