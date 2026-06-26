#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DOCUMENTS: dict[str, dict[str, Any]] = {
    "00": {"name": "application form", "phase": "basic", "required": True},
    "01": {"name": "performer roster", "phase": "basic", "required": True},
    "02": {"name": "performer identity scans", "phase": "basic", "required": True},
    "03": {"name": "venue consent", "phase": "basic", "required": True},
    "04": {"name": "artist consent", "phase": "basic", "required": True},
    "05": {"name": "program list", "phase": "content", "required": True},
    "06": {"name": "lyrics", "phase": "content", "required": True},
    "07": {"name": "media files", "phase": "video", "required": True},
    "08": {"name": "authorization", "phase": "basic", "required": True},
    "09": {"name": "business license", "phase": "basic", "required": True},
    "10": {"name": "fire safety / opening permit", "phase": "basic", "required": True},
}


def manifest_path(project_dir: Path) -> Path:
    return project_dir / "00_项目主档" / "项目主档.json"


def load_manifest(path_or_project: Path) -> dict[str, Any]:
    path = path_or_project
    if path.is_dir():
        path = manifest_path(path)
    if not path.exists():
        raise FileNotFoundError(f"Project manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(manifest: dict[str, Any], path_or_project: Path) -> Path:
    path = path_or_project
    if path.is_dir():
        path = manifest_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
