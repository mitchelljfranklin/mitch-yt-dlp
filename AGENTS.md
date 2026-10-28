# AGENTS.md

Windows-only desktop app: a ttkbootstrap GUI wrapping yt-dlp's Python API. Five small modules under `src/`, a headless pytest suite, and PyInstaller packaging. `requirements-dev.txt` + `pyproject.toml` + `build.spec` define the toolchain.

## Commands (PowerShell, from repo root)

```powershell
pip install -r requirements-dev.txt   # runtime deps + pinned ruff/pytest
python setup_ffmpeg.py                # required before building; needed for MP3 in dev
python src/main.py                    # run dev GUI (blocks until closed)
ruff check src tests setup_ffmpeg.py
ruff format --check src tests setup_ffmpeg.py
pytest                                # 38 tests, ~0.4 s, no GUI or network
python -m PyInstaller build.spec      # -> dist\Mitch-yt-dlp.exe
```

- CI (`.github/workflows/build.yml`) runs lint → test → build on `windows-latest` / Python 3.14; local development uses the same 3.14 line.
- Every `uses:` is pinned to a full commit SHA with a trailing `# vX.Y.Z` comment, and the repo enables **Require SHA pinning** for Actions. Using a tag or branch ref (`actions/checkout@v7`) makes the workflow fail to start; bump pins via Dependabot's `github-actions` PRs, which preserve the comment format.
- `build.spec` resolves `src/main.py`, `bin/`, and `icon.ico` relative to the **CWD** and now **fails loudly** when `bin/ffmpeg.exe`/`ffprobe.exe` is missing, so always run `setup_ffmpeg.py` and build from the repo root. Intermediates go to `build/build/` (named after the spec).
- `bin/*.exe`, `build/`, `dist/`, and all `*.exe` are gitignored; a populated `bin/` is a local prerequisite.
- Lint config is explicit in `pyproject.toml` and ruff is pinned. Ruff's defaults have changed between releases and once broke CI without a code change — change the rule list deliberately.

## Layout and wiring

- `src/main.py` — entrypoint; prepends `src/` to `sys.path`, then `from app import App`.
- `src/app.py` — `App(ttk.Window)` (theme `superhero`); UI layout, validation, `after()` polling, and all button state.
- `src/downloader.py` — yt-dlp options, progress hook, cancellation, FFmpeg discovery, engine version.
- `src/settings.py` — `%APPDATA%\Mitch-yt-dlp\settings.json` load/save; tolerant of missing/corrupt files.
- `src/version.py` — `APP_VERSION`, must match the release tag `v<APP_VERSION>`.
- Imports are flat (`from downloader import Downloader`), and there is intentionally no `src/__init__.py`. Both `main.py`'s `sys.path` hack and `pathex=["src"]` in `build.spec` depend on this.
- Every download creates a `DownloadSession` holding its **own** queue, cancel event, and `DownloadLogger`. `Downloader.progress_queue` always points at the active session, so a superseded run can never publish into the queue the UI is polling. Status constants are module-level (`STATUS_*`), not class attributes.
- `App._poll_progress_queue()` drains the queue every 120 ms while `_polling_active`; terminal statuses call `_finish_run()`, which clears that flag so the loop stops instead of polling forever. Never touch tkinter widgets from the downloader thread.
- Bundled-resource paths differ by context: `resolve_bundled_path()` uses `sys._MEIPASS` when frozen, otherwise the **CWD**, so the dev app must start from the repo root to find `bin/ffmpeg.exe`. `app.py` resolves `icon.ico` from `__file__`'s parent instead.

## Behaviour gotchas

- Cancellation is cooperative: `cancel()` sets the active session's event, checked in the yt-dlp progress hook. Stop is not instant, and Start re-enables immediately, so a new session may briefly overlap the old one (harmless now that queues/events are per-session).
- `ignoreerrors: True` keeps playlists going. Errors are captured through the custom `logger` and returned in the `STATUS_COMPLETED` payload as `errors`; the UI shows "Finished with N error(s)" plus a warning dialog (`MAX_ERRORS_IN_DIALOG` truncation). A non-zero yt-dlp return code without messages becomes a synthetic error.
- MP3 mode sets `format: "bestaudio/best"`; without it yt-dlp downloads full video that `FFmpegExtractAudio` deletes after conversion.
- "Video only" maps to yt-dlp's `noplaylist`, which only picks the single video when the URL names **both** a video and a playlist (`watch?v=…&list=…`). A playlist-only URL still expands to every entry, so `is_bare_playlist_url()` rejects that combination up front instead of silently downloading the lot. The helper is deliberately conservative and returns `False` for anything it does not recognise.
- `is_ffmpeg_available()` accepts bundled binaries *or* anything on `PATH`; `_on_start()` refuses MP3 conversion up front when neither exists.
- `Escape` stops only while polling is active; `destroy()` stops polling, cancels the download, and saves settings.
- Keep `setup_ffmpeg.py` unattended/idempotent (120 s timeout, validates extracted files, removes partial archives) — CI runs it with no interaction.

## Tests

- Tests never create a Tk window and never hit the network. Downloader tests monkeypatch `downloader.yt_dlp.YoutubeDL` with a fake context manager and read statuses from the session queue.
- `test_app_helpers.py` imports `App` only for its pure `_format_speed` / `_format_eta` statics.
- `pyproject.toml` sets `pythonpath = [".", "src"]`, so test imports work without installing a package both under `python -m pytest` and the bare CI `pytest` entry point.

## Conventions (see CONTRIBUTING.md)

- Docstring every function and class; no single-letter names (`error`, not `e`); module-level constants instead of magic numbers.
- Keep UI logic in `app.py`, download logic in `downloader.py`, preferences in `settings.py`.
- Releases: bump `APP_VERSION`, push a matching `v*` tag; `.github/workflows/release.yml` re-runs checks, installs yt-dlp with `--upgrade` (newest stable PyPI release), builds on Python 3.14, stamps the bundled Python/yt-dlp/FFmpeg versions into the release notes, and attaches the EXE to the GitHub release.
- Repo rulesets block force-pushing/deleting `main` and moving/deleting `v*` tags. Never plan a release around rewriting history or re-tagging; if a tag is wrong, disable the ruleset in **Settings → Rules → Rulesets**, fix it, and re-enable.
