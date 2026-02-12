"""Executable entrypoint for package and frozen/script builds."""

from __future__ import annotations

import os
import sys


def _ensure_standard_streams() -> None:
    """PyInstaller --windowed may start with stdout/stderr as None.

    Some UI libraries (including dependencies of customtkinter) expect a writable
    stream object and will crash if they encounter None.
    """

    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def _resolve_run():
    # Package/module execution path (e.g. `python -m iiq_desktop`).
    try:
        from iiq_desktop.app import run

        return run
    except ImportError:
        # Script/frozen fallback (e.g. PyInstaller pointing at this file).
        from app import run

        return run


if __name__ == "__main__":
    _ensure_standard_streams()
    _resolve_run()()
