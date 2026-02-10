# Android Companion App Specification

This document defines what the Omni Recover Studio Android companion app should do.

## Primary goal

Give users a fast mobile interface to **view and manage cases** created by the desktop recovery app, without moving heavy forensic processing onto the phone.

## Core user flows

## 1) Case browser
- View all synced/imported cases.
- Search, filter, and sort by:
  - case name
  - date updated
  - source media type
  - tags (e.g., legal, personal, business)
- Show case health summary:
  - total recovered files
  - total size
  - last recovery run status

## 2) Case detail
- Open a case and browse folders/files.
- Preview supported items:
  - images
  - text files
  - PDFs (metadata and quick preview)
- Show extracted metadata:
  - hash
  - file size
  - path
  - source tool used
  - discovered timestamp

## 3) Reports and export
- Open generated reports (timeline, file inventory, hash manifests).
- Export/share:
  - case summary PDF
  - selected report files
  - case bundle reference metadata

## 4) Remote monitoring of desktop jobs
- Pair with desktop instance.
- View active/past jobs:
  - queued/running/completed/failed
  - progress
  - live logs (tail view)
- Receive push/local notifications for job completion/failure.

## 5) Import / sync
- Import a case package (`.zip`) into phone sandbox for read-only review.
- Sync selected case artifacts from desktop/cloud storage.
- Conflict handling:
  - keep both
  - replace older
  - manual merge review

## 6) Evidence verification
- Recompute hashes (SHA-256/SHA-1/MD5 where needed) on imported files.
- Compare with stored hash values.
- Mark verification state:
  - verified
  - mismatch
  - unknown

## User modes

## Beginner mode
- Guided screens.
- Plain-language status and warnings.
- Safe defaults (read-only actions).

## Expert mode
- Advanced filters.
- Metadata-centric views.
- Log and hash detail panels.
- Optional API endpoint configuration.

## What the companion app should NOT do initially

- Raw block-device acquisition from Android hardware.
- Full forensic carving directly on phone.
- Unrestricted shell command execution.

These are desktop-first features.

## Suggested architecture

- Android client (Kotlin + Jetpack Compose).
- Optional Desktop API service (local network + token auth).
- Local mobile cache DB (Room/SQLite) for offline viewing.
- Background sync worker for case updates.

## Security model

- Pairing handshake with one-time code.
- Per-device API token.
- TLS on network links when possible.
- Read-only by default for case content.
- Audit log for sync/import/export actions.

## MVP checklist

1. Case list + case detail views.
2. Import/open case zip.
3. Report viewer and share.
4. Hash verification for selected files.
5. Desktop pairing + job status monitor.
6. Beginner/Expert toggle.

## Future extensions

- Team collaboration comments.
- Chain-of-custody timeline signing.
- OCR and semantic search across recovered docs.
- Remote trigger of predefined desktop recovery profiles.

---

## Implemented MVP (this repository)

The repository now includes an implemented mobile companion server and responsive web UI:

- Python server module: `src/omni_recover_studio/companion.py`
- Mobile UI assets: `src/omni_recover_studio/companion_ui/*`
- CLI entry point: `omni-recover-companion`

Delivered MVP capabilities:

- List available cases in a workspace.
- Browse case files across `output`, `reports`, `imports`, and `evidence`.
- Search case files by path.
- Open/download file content from a phone browser.
- Optional token gate for API endpoints.
