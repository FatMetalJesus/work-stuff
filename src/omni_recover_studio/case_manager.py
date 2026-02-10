from __future__ import annotations

import json
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import CaseRecord


class CaseManager:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def create_case(self, name: str) -> CaseRecord:
        safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_", " ")).strip()
        if not safe_name:
            raise ValueError("Case name cannot be empty")
        case_path = self.workspace / safe_name
        case_path.mkdir(parents=True, exist_ok=True)

        for directory in ("evidence", "output", "logs", "reports", "imports"):
            (case_path / directory).mkdir(exist_ok=True)

        record = CaseRecord(name=safe_name, base_path=case_path)
        self._write_metadata(record)
        self._init_index(record)
        return record

    def list_cases(self) -> list[CaseRecord]:
        cases: list[CaseRecord] = []
        for child in self.workspace.iterdir():
            if child.is_dir() and (child / "case.json").exists():
                payload = json.loads((child / "case.json").read_text(encoding="utf-8"))
                cases.append(
                    CaseRecord(
                        name=payload["name"],
                        base_path=child,
                        created_at=datetime.fromisoformat(payload["created_at"]),
                        updated_at=datetime.fromisoformat(payload["updated_at"]),
                    )
                )
        return sorted(cases, key=lambda c: c.updated_at, reverse=True)

    def open_case(self, name: str) -> CaseRecord:
        case_path = self.workspace / name
        metadata = case_path / "case.json"
        if not metadata.exists():
            raise FileNotFoundError(f"Case not found: {name}")
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        return CaseRecord(
            name=payload["name"],
            base_path=case_path,
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
        )

    def import_case_archive(self, archive: Path) -> CaseRecord:
        if archive.suffix.lower() != ".zip":
            raise ValueError("Only .zip case imports are supported")
        with zipfile.ZipFile(archive, "r") as zf:
            roots = {Path(name).parts[0] for name in zf.namelist() if name.strip()}
            if len(roots) != 1:
                raise ValueError("Archive must contain a single case root directory")
            root_name = next(iter(roots))
            destination = self.workspace / root_name
            zf.extractall(self.workspace)
        record = self.open_case(root_name)
        self.touch_case(record)
        return self.open_case(root_name)

    def export_case_archive(self, record: CaseRecord, destination_zip: Path) -> Path:
        destination_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in record.base_path.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(record.base_path.parent))
        return destination_zip

    def touch_case(self, record: CaseRecord) -> None:
        record.updated_at = datetime.utcnow()
        self._write_metadata(record)

    def upsert_evidence(self, record: CaseRecord, rows: Iterable[tuple[str, str, int, str]]) -> None:
        db_path = record.base_path / "evidence_index.sqlite3"
        conn = sqlite3.connect(db_path)
        try:
            conn.executemany(
                """
                INSERT INTO recovered_items(path, category, size_bytes, source_tool, discovered_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                rows,
            )
            conn.commit()
        finally:
            conn.close()

    def _init_index(self, record: CaseRecord) -> None:
        db_path = record.base_path / "evidence_index.sqlite3"
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recovered_items(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    category TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    source_tool TEXT NOT NULL,
                    discovered_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _write_metadata(self, record: CaseRecord) -> None:
        payload = {
            "name": record.name,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }
        record.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
