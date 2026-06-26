# Security Policy

---

## Reporting a Vulnerability

If you discover a security vulnerability in Mitch-yt-dlp, please **do not** open a public GitHub issue. Instead:

1. Email the maintainer at **mitchelljfranklin** at GitHub's domain, or
2. Use GitHub's [private vulnerability reporting](https://github.com/mitchelljfranklin/mitch-yt-dlp/security/advisories/new) feature.

You can expect:

- **Acknowledgment** within 48 hours
- A **status update** within 5 business days
- A **fix or mitigation** as soon as possible, depending on severity
- **Credit** in the release notes (unless you prefer to remain anonymous)

## Scope

The security policy covers:
- The Mitch-yt-dlp application code in this repository
- The PyInstaller build configuration
- The bundled FFmpeg distribution pipeline (`setup_ffmpeg.py`)

The policy does **not** cover:
- Vulnerabilities in upstream dependencies (yt-dlp, customtkinter, FFmpeg) — those should be reported to their respective maintainers. We track upstream advisories and update dependencies promptly.
- Issues caused by misconfiguration of the user's operating system or network.

## Dependency management

| Dependency | Upstream | Pinned |
|---|---|---|
| yt-dlp | [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | `>=2024.0` |
| customtkinter | [TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | `>=5.2.0` |
| PyInstaller | [pyinstaller/pyinstaller](https://github.com/pyinstaller/pyinstaller) | `>=6.0` |
| FFmpeg | [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/) | Latest essentials build |

We monitor [Dependabot](https://docs.github.com/en/code-security/dependabot) alerts and update dependencies in a timely manner.

## Build integrity

- The **official EXE** is built via [GitHub Actions](.github/workflows/build.yml) from the source in this repository. You can verify the artifact by comparing hashes with a local build.
- The `setup_ffmpeg.py` script downloads FFmpeg **only** from gyan.dev over HTTPS. The download is ephemeral — the zip is deleted after extraction.
- We recommend verifying the integrity of the downloaded EXE against the checksum published in each [release](https://github.com/mitchelljfranklin/mitch-yt-dlp/releases).

## Supported versions

Only the latest release is actively supported. We encourage all users to update promptly.

---

*For questions that are not security-sensitive, open a [discussion](https://github.com/mitchelljfranklin/mitch-yt-dlp/discussions) or a regular [issue](https://github.com/mitchelljfranklin/mitch-yt-dlp/issues).*
