"""Executable entrypoint for package and frozen/script builds."""


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
    _resolve_run()()
