from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class ToolDependency:
    name: str
    executable: str
    install_hint: str


DEFAULT_TOOLS = [
    ToolDependency("PhotoRec / TestDisk", "photorec", "Use your package manager: apt, brew, choco"),
    ToolDependency("GNU ddrescue", "ddrescue", "Use your package manager: apt, brew, choco"),
    ToolDependency("Sleuth Kit", "fls", "Install Sleuth Kit via apt, brew, choco"),
    ToolDependency("Bulk Extractor", "bulk_extractor", "Install from distro packages or project release"),
    ToolDependency("Binwalk", "binwalk", "Install via package manager or pip"),
]

PIP_PACKAGES = ["pytsk3", "python-magic", "yara-python", "construct"]


class DependencyManager:
    def detect(self) -> list[tuple[ToolDependency, bool]]:
        return [(dep, shutil.which(dep.executable) is not None) for dep in DEFAULT_TOOLS]

    def install_python_bundle(self) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "pip", "install", *PIP_PACKAGES]
        return subprocess.run(cmd, capture_output=True, text=True)

    def platform_guidance(self) -> str:
        system = platform.system().lower()
        if "linux" in system:
            return "Linux detected. Suggested: sudo apt install testdisk gddrescue sleuthkit bulk-extractor binwalk"
        if "darwin" in system:
            return "macOS detected. Suggested: brew install testdisk ddrescue sleuthkit binwalk bulk-extractor"
        if "windows" in system:
            return "Windows detected. Suggested: choco install testdisk ddrescue sleuthkit binwalk"
        return "Unknown platform. Use your OS package manager to install tools."
