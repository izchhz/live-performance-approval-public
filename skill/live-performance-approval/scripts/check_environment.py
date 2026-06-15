#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path


TOOLS = ("ffmpeg", "ffprobe")
PYTHON_MODULES = ("docx",)
OPTIONAL_PYTHON_MODULES = ("PIL", "pypdf", "reportlab")
LIBREOFFICE = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")


def main() -> None:
    missing: list[str] = []
    for tool in TOOLS:
        found = shutil.which(tool)
        print(f"{tool}: {found or 'MISSING'}")
        if not found:
            missing.append(tool)

    print(f"LibreOffice: {LIBREOFFICE if LIBREOFFICE.exists() else 'MISSING'}")
    if not LIBREOFFICE.exists():
        missing.append("LibreOffice")

    for module in PYTHON_MODULES:
        found = importlib.util.find_spec(module) is not None
        print(f"python module {module}: {'OK' if found else 'MISSING'}")
        if not found:
            missing.append(f"python:{module}")

    for module in OPTIONAL_PYTHON_MODULES:
        found = importlib.util.find_spec(module) is not None
        print(f"optional python module {module}: {'OK' if found else 'MISSING'}")

    if missing:
        raise SystemExit("缺少必需依赖：" + "、".join(missing))


if __name__ == "__main__":
    main()
