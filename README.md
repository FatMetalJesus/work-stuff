# IncidentIQ Mass Assigner (Windows EXE)

A desktop app built for fast IncidentIQ Chromebook operations:

- Search/select a staff member.
- Load unassigned Chromebooks.
- Multi-select and **mass assign** in one action.
- View recent timeline activity for the selected person.
- Store API key in Settings with local obfuscation.

## Quick start (dev)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=src python -m iiq_desktop
```

## Build Windows EXE

On Windows:

```bat
build_windows_exe.bat
```

Then run:

`dist\IncidentIQ-Mass-Assigner\IncidentIQ-Mass-Assigner.exe`

## Get a downloadable EXE link (GitHub Actions)

1. Push this branch to GitHub.
2. Open the **Actions** tab and run **Build Windows EXE** (or use the run triggered by push).
3. Open the workflow run and download the artifact named **IncidentIQ-Mass-Assigner-windows**.

That artifact download page is your shareable build link.

## Configuration

Open **Settings** inside the app:

- API Base URL (default: `https://muskogeeps.incidentiq.com/api/v1.0`)
- Site ID
- API Key

The API key is saved to `%USERPROFILE%\.iiq_mass_assigner\config.json` in obfuscated form.

## Notes

- Endpoints may vary by tenant configuration. If your district uses different bulk-assignment endpoints or field names, update `src/iiq_desktop/client.py`.
- This tool intentionally favors speed and minimal clicks for high-volume Chromebook assignments.
