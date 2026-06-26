<h1 align="center">Mitch-yt-dlp</h1>

<p align="center">
  <strong>A modern Windows GUI for <a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a></strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-0085FC?style=flat-square&logo=windows" alt="Platform" />
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/ui-customtkinter-008cff?style=flat-square" alt="UI" />
</p>

---

## Features

- **Simple, clean interface** — paste a URL, pick a folder, hit Start
- **Playlist support** — download entire playlists with one click
- **MP3 conversion** — toggle to extract audio as MP3 (FFmpeg bundled)
- **Real-time progress** — speed, ETA, and percentage while downloading
- **Stop & Cancel** — full control over in-progress downloads
- **Standalone `.exe`** — no Python installation needed, everything bundled

## Quick Start

### Option 1: Download the EXE (recommended)

Grab the latest `Mitch-yt-dlp.exe` from [Releases](https://github.com/mitchelljfranklin/mitch-yt-dlp/releases) — no setup required.

### Option 2: Run from source

```powershell
git clone https://github.com/mitchelljfranklin/mitch-yt-dlp
cd mitch-yt-dlp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Building from source

```powershell
# Install dependencies
pip install -r requirements.txt

# Download FFmpeg Windows binaries (required for MP3 conversion)
python setup_ffmpeg.py

# Build standalone EXE
pyinstaller build.spec
# Output: dist\Mitch-yt-dlp.exe
```

## How it works

Mitch-yt-dlp imports [yt-dlp](https://github.com/yt-dlp/yt-dlp) as a Python library rather than shelling out to a CLI process. This gives finer control over progress reporting and cancellation.

| Component | Technology |
|---|---|
| UI Framework | [customtkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Download Engine | [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Python API) |
| Audio Encoding | [FFmpeg](https://ffmpeg.org/) (bundled in EXE) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

```
┌──────────────────────────────────────┐
│              Mitch-yt-dlp            │
├──────────────────────────────────────┤
│  ┌── Download ────────────────────┐  │
│  │  [ Choose Output Folder  ][🔍] │  │
│  │  [ Playlist or URL           ] │  │
│  │  Convert to MP3         [⚪——] │  │
│  └────────────────────────────────┘  │
│  [⏹ Stop] [✕ Cancel]      [▶ Start] │
│  ████████████░░░░░░░░  80%          │
└──────────────────────────────────────┘
```

## Requirements

- **Windows 10/11** (64-bit)
- **For source installs**: Python 3.11+

  No other dependencies — yt-dlp and FFmpeg are bundled into the EXE.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs, requesting features, and submitting PRs.

## Privacy & Security

- [PRIVACY.md](PRIVACY.md) — what data the app does (and does not) collect
- [SECURITY.md](SECURITY.md) — how to report vulnerabilities

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ using <a href="https://github.com/TomSchimansky/CustomTkinter">customtkinter</a> and <a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a>
</p>
