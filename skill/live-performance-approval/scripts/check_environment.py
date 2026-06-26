#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path


TOOLS = ("ffmpeg", "ffprobe")
RECOMMENDED_TOOLS = ("tesseract",)
PYTHON_MODULES = ("docx",)
OPTIONAL_PYTHON_MODULES = ("PIL", "pypdf", "reportlab", "fontTools")
RECOMMENDED_PYTHON_MODULES = ("passporteye", "pytesseract", "skimage", "scipy", "paddleocr", "paddle")
LIBREOFFICE = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
SKILL_DIR = Path(__file__).resolve().parents[1]
REQUIRED_SCRIPTS = (
    "scripts/check_environment.py",
    "scripts/compress_approval_videos.py",
    "scripts/create_authorization_template.py",
    "scripts/init_project.py",
    "scripts/prepare_agent_context.py",
    "scripts/project_manifest.py",
    "scripts/scan_cn_id_ocr.py",
    "scripts/scan_passport_mrz.py",
    "scripts/scrub_docx_metadata.py",
    "scripts/validate_cn_id.py",
)


def main() -> None:
    missing: list[str] = []
    for tool in TOOLS:
        found = shutil.which(tool)
        print(f"{tool}: {found or 'MISSING'}")
        if not found:
            missing.append(tool)

    for tool in RECOMMENDED_TOOLS:
        found = shutil.which(tool)
        print(f"recommended tool {tool}: {found or 'MISSING'}")

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

    for module in RECOMMENDED_PYTHON_MODULES:
        found = importlib.util.find_spec(module) is not None
        print(f"recommended python module {module}: {'OK' if found else 'MISSING'}")

    for script in REQUIRED_SCRIPTS:
        found = (SKILL_DIR / script).exists()
        print(f"script {script}: {'OK' if found else 'MISSING'}")
        if not found:
            missing.append(script)

    if missing:
        raise SystemExit("缺少必需依赖：" + "、".join(missing))


if __name__ == "__main__":
    main()
