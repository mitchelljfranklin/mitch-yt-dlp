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
   - The yt-dlp version shown in the top-right of the window

## Feature Requests

Use the **Feature Request** template and describe:
- What problem the feature solves
- How you'd expect it to work
- Any relevant mockups or examples

## Development Setup

Python 3.14 or newer is required (the same version CI builds with).

```powershell
git clone https://github.com/mitchelljfranklin/mitch-yt-dlp
cd mitch-yt-dlp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python setup_ffmpeg.py
python src/main.py
```

`requirements-dev.txt` adds pytest and a pinned ruff on top of the runtime
dependencies, so local checks match CI exactly.

## Checks

Run these before opening a pull request (CI runs the same commands):

```powershell
ruff check src tests setup_ffmpeg.py
ruff format --check src tests setup_ffmpeg.py
pytest
python -m PyInstaller build.spec
```

`build.spec` fails if `bin/ffmpeg.exe` or `bin/ffprobe.exe` is missing, so run
`setup_ffmpeg.py` first. PyInstaller intermediates land in `build/build/`; the
finished EXE is `dist/Mitch-yt-dlp.exe`.

## Project Structure

```
mitch-yt-dlp/
├── src/
│   ├── main.py          # Entry point
│   ├── app.py           # Main window (UI layout, button handlers, polling)
│   ├── downloader.py    # yt-dlp wrapper (threaded downloads, progress)
│   ├── settings.py      # Preference persistence (%APPDATA%)
│   └── version.py       # APP_VERSION, kept in sync with release tags
├── tests/               # pytest suite (no GUI/network required)
├── bin/                 # FFmpeg binaries (populated by setup_ffmpeg.py)
├── pyproject.toml       # ruff + pytest configuration
├── requirements.txt     # Runtime dependencies
├── requirements-dev.txt # Runtime deps + pinned ruff/pytest
├── setup_ffmpeg.py      # Downloads FFmpeg Windows builds
└── build.spec           # PyInstaller packaging config
```

## Code Style

- **Human-readable names** — no single-letter variables (use `error` not `e`, `percentage` not `pct`, `options` not `opts`)
- Every function and class must have a **docstring** describing what it does
- Keep UI logic in `app.py`, download logic in `downloader.py`, and user preferences in `settings.py`
- **Threading**: all yt-dlp work happens on a background thread; UI updates happen on the main thread via `after()` polling
- Use module-level constants for colors, intervals, and status values — no magic numbers
- Imports inside `src/` are flat (`from downloader import Downloader`) because both `main.py` and `build.spec` add `src/` to the import path
- Test on Windows before submitting a PR

## Pull Requests

1. Fork the repo and create a feature branch
2. Make your changes and run the checks above
3. Test that `python -m PyInstaller build.spec` produces a working EXE
4. Open a PR with a clear description

## Releases

Releases are built by `.github/workflows/release.yml` when a `v*` tag is pushed:

1. Bump `APP_VERSION` in `src/version.py` (four-part, e.g. `1.1.0.0`)
2. Commit and push to `main`
3. `git tag v1.1.0.0 && git push origin v1.1.0.0`

The workflow refuses to publish if the tag and `APP_VERSION` disagree, then
attaches `dist/Mitch-yt-dlp.exe` to the GitHub release. CI installs with
`pip install --upgrade`, so each release bundles the newest stable yt-dlp from
PyPI; the release notes record the resolved Python, yt-dlp, and FFmpeg versions.

Published tags are immutable. The `Protect release tags` ruleset rejects moving
or deleting anything matching `v*`, and the `Protect main` ruleset rejects
force-pushes to and deletion of the default branch. If you tag the wrong commit,
delete the tag first — that also fails, so disable the ruleset temporarily in
**Settings → Rules → Rulesets**, fix the tag, and re-enable it. Avoid the
situation by checking out the intended commit before tagging.

## Questions?

Open a [discussion](https://github.com/mitchelljfranklin/mitch-yt-dlp/discussions) or email the maintainer.
