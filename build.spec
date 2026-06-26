# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Mitch-yt-dlp.

Builds a single-window (no console) .exe that bundles:
- The customtkinter GUI
- yt-dlp and all its extractors / downloaders / post-processors
- ffmpeg.exe + ffprobe.exe (if present in bin/)

Usage:
    pyinstaller build.spec

Output:
    dist/Mitch-yt-dlp.exe
"""

import os
from PyInstaller.utils.hooks import collect_submodules

# ---------------------------------------------------------------------------
# Collect FFmpeg binaries for bundling (optional, for MP3 conversion)
# ---------------------------------------------------------------------------

bundled_binaries = []
bundled_data_files = []

path_to_ffmpeg = os.path.join("bin", "ffmpeg.exe")
path_to_ffprobe = os.path.join("bin", "ffprobe.exe")

if os.path.exists(path_to_ffmpeg):
    bundled_binaries.append((path_to_ffmpeg, "bin"))
if os.path.exists(path_to_ffprobe):
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
    upx=True,
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
