# Omni Recover Studio

Omni Recover Studio is a cross-platform desktop GUI application for advanced media and file recovery workflows.

## Core capabilities

- Beginner and Expert operating modes.
- Device ingestion support for image files, HDD/SSD/NVMe block devices, and removable USB media.
- Case-centric workflow with:
  - Create/open cases.
  - Import/export case packages (`.zip`).
  - Live case browser that auto-refreshes from the case folder.
- Recovery pipeline presets for quick scans and deep forensic-style scans.
- Queue-based jobs with progress tracking and live logs.
- Integrated dependency center for one-click installation of optional recovery tooling.
- Built-in plugin-safe command generation for:
  - Carving tools.
  - Filesystem analyzers.
  - Hashing and timeline extraction.
- Evidence index (SQLite) for discovered artifacts and metadata.

## Quick start

```bash
python -m omni_recover_studio.main
```

Or install editable:

```bash
pip install -e .
omni-recover-studio
```

## Downloading a desktop app build (`.exe`, `.app`, `.pkg`)

### Option A: Download prebuilt installers from GitHub Actions artifacts

1. Push a tag like `v0.1.0`.
2. Open **Actions → Build Desktop Installers**.
3. Download the artifact for your platform:
   - **Windows:** includes `.exe`
   - **macOS:** includes `.app` and `.pkg`
   - **Linux:** includes native executable binary

The workflow file is in `.github/workflows/build-installers.yml`.

### Option B: Build locally

```bash
pip install pyinstaller
python scripts/build_release.py
```

Artifacts are generated in `dist/`:

- Windows: `OmniRecoverStudio.exe`
- macOS: `OmniRecoverStudio.app` and (when `pkgbuild` is available) `OmniRecoverStudio.pkg`
- Linux: `OmniRecoverStudio` executable

## Optional external tools

The app can orchestrate optional external tools when they are installed:

- `testdisk` / `photorec`
- `sleuthkit` (`fls`, `icat`, `mmls`)
- `bulk_extractor`
- `ddrescue`
- `binwalk`

Use **Dependency Center → Install Missing** for guided one-click setup.

## Safety notes

- Use read-only mode for source media whenever possible.
- Prefer making an image first and running analysis against the image.
- This project focuses on workflow orchestration and indexing; recovery output quality depends on the underlying tools and media state.


## Android support

Yes, Android support is possible, but it adds complexity because this project is currently a desktop Tkinter app with desktop-native recovery tool dependencies.

- Best near-term path: an **Android companion app** for case browsing, reports, import/export, and remote monitoring.
- Keep heavy media recovery (raw disk workflows) on desktop.
- Optional advanced rooted Android mode can be added later for power users.

See the full plan in `docs/ANDROID_SUPPORT.md`.


## What the Android companion app would do

The companion app is designed for **mobile case management and visibility**, not heavy recovery execution.

- Browse/open synced or imported cases.
- Inspect recovered files, metadata, and reports.
- Verify hashes for integrity checks.
- Monitor desktop recovery jobs with status/progress/logs.
- Import/export case packages for portable review.
- Operate in Beginner and Expert modes.

Detailed scope: `docs/COMPANION_APP_SPEC.md`.

## Mobile companion app (implemented)

A lightweight mobile-friendly companion is now included. It runs on your desktop and lets your phone browse case files over your local network.

Start it with:

```bash
omni-recover-companion --workspace ~/OmniRecoverCases --host 0.0.0.0 --port 8787
```

Then on your phone browser, open:

- `http://<your-desktop-ip>:8787`

Features currently available:

- Case list with timestamps.
- Per-case file browsing (`output`, `reports`, `imports`, `evidence`).
- Search by relative file path.
- Open/download recovered files from phone.
- Optional API token protection (`--token <value>`).
