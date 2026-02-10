from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

Mode = Literal["Beginner", "Expert"]
JobStatus = Literal["Queued", "Running", "Completed", "Failed", "Canceled"]


@dataclass
class CaseRecord:
    name: str
    base_path: Path
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def metadata_path(self) -> Path:
        return self.base_path / "case.json"


@dataclass
class RecoveryJob:
    job_id: str
    case_name: str
    source: str
    profile: str
    command: str
    status: JobStatus = "Queued"
    progress: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
