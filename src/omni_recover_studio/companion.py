from __future__ import annotations

import argparse
import json
import mimetypes
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .case_manager import CaseManager


@dataclass
class CaseFile:
    relative_path: str
    size_bytes: int
    modified_at: str
    category: str


class CompanionIndex:
    """Case-index helper used by the mobile companion HTTP API."""

    SEARCH_FOLDERS = ("output", "reports", "imports", "evidence")

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.case_manager = CaseManager(workspace)

    def list_cases(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for case in self.case_manager.list_cases():
            rows.append(
                {
                    "name": case.name,
                    "path": str(case.base_path),
                    "created_at": case.created_at.isoformat(),
                    "updated_at": case.updated_at.isoformat(),
                }
            )
        return rows

    def list_case_files(self, case_name: str, query: str = "") -> list[CaseFile]:
        case = self.case_manager.open_case(case_name)
        needle = query.lower().strip()
        files: list[CaseFile] = []
        for folder in self.SEARCH_FOLDERS:
            root = case.base_path / folder
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(case.base_path))
                if needle and needle not in rel.lower():
                    continue
                stat = path.stat()
                files.append(
                    CaseFile(
                        relative_path=rel,
                        size_bytes=stat.st_size,
                        modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        category=folder,
                    )
                )
        files.sort(key=lambda f: (f.category, f.relative_path.lower()))
        return files

    def resolve_case_file(self, case_name: str, rel_path: str) -> Path:
        case = self.case_manager.open_case(case_name)
        candidate = (case.base_path / rel_path).resolve()
        if not str(candidate).startswith(str(case.base_path.resolve())):
            raise ValueError("Invalid path")
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError(rel_path)
        return candidate


class CompanionRequestHandler(BaseHTTPRequestHandler):
    server_version = "OmniRecoverCompanion/0.1"

    def __init__(self, *args, workspace: Path, token: str | None, **kwargs):
        self.index = CompanionIndex(workspace)
        self.workspace = workspace
        self.token = token
        self.ui_root = Path(__file__).parent / "companion_ui"
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = urllib.parse.urlparse(self.path)
            route = parsed.path
            params = urllib.parse.parse_qs(parsed.query)

            if route.startswith("/api/") and not self._authorized(params):
                self._json({"error": "Unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return

            if route == "/api/cases":
                self._json({"cases": self.index.list_cases()})
                return

            if route == "/api/case-files":
                case_name = self._required_param(params, "case")
                query = params.get("q", [""])[0]
                rows = [asdict(row) for row in self.index.list_case_files(case_name, query)]
                self._json({"files": rows, "count": len(rows)})
                return

            if route == "/api/file":
                case_name = self._required_param(params, "case")
                rel_path = self._required_param(params, "path")
                file_path = self.index.resolve_case_file(case_name, rel_path)
                self._serve_file(file_path)
                return

            if route in ("/", "/index.html"):
                self._serve_static("index.html")
                return

            if route == "/app.js":
                self._serve_static("app.js", "application/javascript")
                return

            if route == "/styles.css":
                self._serve_static("styles.css", "text/css")
                return

            self.send_error(HTTPStatus.NOT_FOUND)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _authorized(self, params: dict[str, list[str]]) -> bool:
        if not self.token:
            return True
        supplied = params.get("token", [""])[0]
        return supplied == self.token

    def _required_param(self, params: dict[str, list[str]], key: str) -> str:
        value = params.get(key, [""])[0].strip()
        if not value:
            raise ValueError(f"Missing required parameter: {key}")
        return value

    def _json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_file(self, path: Path) -> None:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'inline; filename="{path.name}"')
        self.end_headers()
        self.wfile.write(data)

    def _serve_static(self, filename: str, content_type: str | None = None) -> None:
        path = self.ui_root / filename
        if not path.exists():
            raise FileNotFoundError(filename)
        self._serve_file(path) if content_type is None else self._serve_with_type(path, content_type)

    def _serve_with_type(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_companion_server(workspace: Path, host: str = "0.0.0.0", port: int = 8787, token: str | None = None) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    handler = partial(CompanionRequestHandler, workspace=workspace, token=token)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Omni Recover Companion running at http://{host}:{port}")
    print(f"Workspace: {workspace}")
    if token:
        print("Token auth enabled; append ?token=<token> to API requests.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping companion server...")
    finally:
        server.server_close()


def companion_main() -> None:
    parser = argparse.ArgumentParser(description="Run the Omni Recover Studio mobile companion server")
    parser.add_argument("--workspace", type=Path, default=Path.home() / "OmniRecoverCases")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--token", default=None, help="Optional API token for protected API endpoints")
    args = parser.parse_args()

    run_companion_server(workspace=args.workspace, host=args.host, port=args.port, token=args.token)


if __name__ == "__main__":
    companion_main()
