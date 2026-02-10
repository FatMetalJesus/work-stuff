from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "OmniRecoverStudio"
ENTRYPOINT = "src/omni_recover_studio/main.py"
ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def clean() -> None:
    for p in (DIST, BUILD, ROOT / f"{APP_NAME}.spec"):
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()


def build_pyinstaller() -> None:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
    ]
    if platform.system().lower() == "darwin":
        args.append("--onedir")
    else:
        args.append("--onefile")
    args.append(ENTRYPOINT)
    run(args)


def build_macos_pkg() -> None:
    app_bundle = DIST / f"{APP_NAME}.app"
    pkg_out = DIST / f"{APP_NAME}.pkg"
    if not app_bundle.exists():
        return
    if shutil.which("pkgbuild") is None:
        print("pkgbuild is not available; skipping .pkg generation")
        return
    run(
        [
            "pkgbuild",
            "--component",
            str(app_bundle),
            "--install-location",
            "/Applications",
            str(pkg_out),
        ]
    )


def print_outputs() -> None:
    print("\nBuild outputs:")
    for artifact in sorted(DIST.glob("*")):
        print(f"- {artifact}")


def main() -> None:
    clean()
    build_pyinstaller()
    if platform.system().lower() == "darwin":
        build_macos_pkg()
    print_outputs()


if __name__ == "__main__":
    main()
