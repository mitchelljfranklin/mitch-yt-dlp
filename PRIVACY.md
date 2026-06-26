# Privacy Policy

*Last updated: June 2026*

Mitch-yt-dlp is a **local desktop application** — it runs entirely on your machine. Your privacy is a core design principle.

---

## What Mitch-yt-dlp does NOT do

- **No telemetry** — the app does not send usage data, analytics, crash reports, or any diagnostic information back to the developer or any third party.
- **No data collection** — nothing you type into the UI (URLs, folder paths, settings) is ever logged to disk beyond what your operating system may cache for its own purposes.
- **No network requests of its own** — the app itself never connects to the internet. All outbound requests are made exclusively by [yt-dlp](https://github.com/yt-dlp/yt-dlp) to the video platforms you explicitly choose to download from.
- **No third-party trackers or ads** — the application contains no advertising, tracking pixels, or embedded analytics.

## What does happen

### Network activity by yt-dlp

When you start a download, yt-dlp makes HTTP/HTTPS requests to:

- The video platform you provided (YouTube, Vimeo, etc.) to fetch metadata and media streams.
- GitHub (on first run) to check for yt-dlp updates (configurable in yt-dlp settings).

These requests are the same ones yt-dlp would make from the command line. Mitch-yt-dlp does **not** intercept, log, or redirect them.

### Files written to disk

- Downloaded media is saved to the **output folder you chose**.
- yt-dlp may cache extracted information in its standard cache directory (`%APPDATA%/yt-dlp/`). This is a feature of yt-dlp itself, not something Mitch-yt-dlp adds.
- No logs are persisted by the GUI — status messages are ephemeral and disappear when you close the app.

### FFmpeg bundling

The standalone EXE includes [FFmpeg](https://ffmpeg.org/) binaries obtained from the trusted [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) Windows builds. FFmpeg runs locally on your machine during audio conversion and does not communicate over the network.

## Your control

- You can **audit the source code** — the entire application is open-source (MIT). See [src/](../src/).
- You can **build from source** instead of using the pre-built EXE if you prefer, using `pyinstaller build.spec`.
- You can **block the app in your firewall** — the download functionality will still work, as yt-dlp only needs outbound HTTPS to the video platforms.

## Questions?

Open a [discussion](https://github.com/mitchelljfranklin/mitch-yt-dlp/discussions) or a [GitHub issue](https://github.com/mitchelljfranklin/mitch-yt-dlp/issues).
