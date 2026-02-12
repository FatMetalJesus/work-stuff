from __future__ import annotations

import base64
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".iiq_mass_assigner"
CONFIG_PATH = CONFIG_DIR / "config.json"

_OBFUSCATION_SECRET = "iiq-mps-2026"


def _xor_bytes(payload: bytes) -> bytes:
    key = _OBFUSCATION_SECRET.encode("utf-8")
    return bytes(payload[i] ^ key[i % len(key)] for i in range(len(payload)))


def obfuscate(raw: str) -> str:
    scrambled = _xor_bytes(raw.encode("utf-8"))
    return base64.urlsafe_b64encode(scrambled).decode("ascii")


def deobfuscate(masked: str) -> str:
    decoded = base64.urlsafe_b64decode(masked.encode("ascii"))
    return _xor_bytes(decoded).decode("utf-8")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
