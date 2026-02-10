from __future__ import annotations

import shlex
import uuid
from pathlib import Path

from .models import RecoveryJob


RECOVERY_PROFILES: dict[str, list[str]] = {
    "Quick Recover": [
        "photorec /log /d {out} {source}",
    ],
    "Deep Carving": [
        "ddrescue -f -n {source} {out}/disk_image.dd {out}/ddrescue.log",
        "photorec /log /d {out}/carved {out}/disk_image.dd",
        "bulk_extractor -o {out}/bulk {out}/disk_image.dd",
    ],
    "Filesystem Triage": [
        "mmls {source}",
        "fls -r {source}",
        "binwalk -e {source}",
    ],
}


class RecoveryEngine:
    def build_job(self, case_name: str, source: str, profile: str, output_root: Path) -> RecoveryJob:
        if profile not in RECOVERY_PROFILES:
            raise ValueError(f"Unknown profile: {profile}")

        source_escaped = shlex.quote(source)
        output_root.mkdir(parents=True, exist_ok=True)
        commands = [
            cmd.format(source=source_escaped, out=shlex.quote(str(output_root)))
            for cmd in RECOVERY_PROFILES[profile]
        ]
        command = " && ".join(commands)
        return RecoveryJob(
            job_id=str(uuid.uuid4())[:8],
            case_name=case_name,
            source=source,
            profile=profile,
            command=command,
        )
