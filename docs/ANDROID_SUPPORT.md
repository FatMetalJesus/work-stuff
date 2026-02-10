# Android Support Plan

Short answer: **yes, Android is possible**, but a direct port of the current Tkinter desktop app is not practical.

## Why it is complicated

The current app uses:

- `tkinter` desktop widgets
- desktop-style filesystem/device assumptions
- external native forensic binaries (`photorec`, `ddrescue`, `sleuthkit`, etc.)

On Android, those assumptions break because:

- Tkinter does not provide a production Android UI runtime.
- Android sandboxing restricts block-device access.
- Many forensic binaries are not packaged/signed for Android app stores.
- Root access is required for low-level raw device workflows.

## Recommended approach

## 1) Keep desktop app for heavy recovery
Use desktop (Windows/macOS/Linux) for raw media recovery and advanced carving.

## 2) Add an Android companion app
Build a companion app focused on:

- case browsing
- report viewing
- importing/exporting case bundles
- hash verification
- cloud sync / remote job monitoring

This gives Android support without losing forensic power.

## 3) Optional advanced Android mode (power users)
For rooted/off-store workflows:

- run limited command pipelines against image files
- clearly warn that results depend on rooted environment and tool availability

## Viable technical options

### Option A (fastest): Web UI companion
- Expose case data as a local API from desktop.
- Use a mobile-first web app (PWA/Capacitor).
- Easiest distribution and lowest maintenance.

### Option B: Native Android client
- Build with Kotlin/Jetpack Compose.
- Best UX and Play Store alignment.
- Higher development effort.

### Option C: Python-based mobile runtime (not recommended as primary)
- Kivy/BeeWare can work for prototypes.
- Harder long-term support for forensic/native integrations.

## Scope recommendation

For this project, implement Android in phases:

1. **Phase 1**: Android companion for case/report access.
2. **Phase 2**: Remote desktop job control and notifications.
3. **Phase 3**: Optional rooted-device power features.

This keeps the core recovery engine stable and still gives real Android availability.
