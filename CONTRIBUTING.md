# Contributing to Mitch-yt-dlp

Thanks for your interest in contributing!

## Reporting Bugs

1. Search [existing issues](https://github.com/mitchelljfranklin/mitch-yt-dlp/issues) first
2. Use the **Bug Report** template when opening a new issue
3. Include:
   - Your Windows version
   - Steps to reproduce
   - The URL you tried to download (if shareable)
   - Any error messages shown

## Feature Requests

Use the **Feature Request** template and describe:
- What problem the feature solves
- How you'd expect it to work
- Any relevant mockups or examples

## Development Setup

```powershell
git clone https://github.com/mitchelljfranklin/mitch-yt-dlp
cd mitch-yt-dlp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Project Structure

```
mitch-yt-dlp/
├── src/
│   ├── main.py          # Entry point
│   ├── app.py            # Main window (UI layout, button handlers)
│   └── downloader.py     # yt-dlp wrapper (threaded downloads, progress)
├── bin/                  # FFmpeg binaries (populated by setup_ffmpeg.py)
├── icon.ico              # Application icon
├── setup_ffmpeg.py       # Downloads FFmpeg Windows builds
├── build.spec            # PyInstaller packaging config
└── requirements.txt
```

## Code Style

- **Human-readable names** — no single-letter variables (use `error` not `e`, `percentage` not `pct`, `options` not `opts`)
- Every function and class must have a **docstring** describing what it does
- Keep UI logic in `app.py`, download logic in `downloader.py`
- **Threading**: all yt-dlp work happens on a background thread; UI updates happen on the main thread via `after()` polling
- Use module-level constants for colors, intervals, and status values — no magic numbers
- Test on Windows before submitting a PR

## Pull Requests

1. Fork the repo and create a feature branch
2. Make your changes
3. Test that `pyinstaller build.spec` produces a working EXE
4. Open a PR with a clear description

## Questions?

Open a [discussion](https://github.com/mitchelljfranklin/mitch-yt-dlp/discussions) or email the maintainer.
