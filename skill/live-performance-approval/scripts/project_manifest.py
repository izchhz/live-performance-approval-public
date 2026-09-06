#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2026-09-05"

from applicant_policy import load_company_config, configured_subject

PROJECT_DIRS = (
    "00_项目主档",
    "01_原始资料",
    "02_生成中间文件",
    "02_生成中间文件/cache",
    "02_生成中间文件/rendered_pages",
    "03_最终提交材料",
    "03_最终提交材料/报批视频已压缩",
    "04_缺失资料与提醒",
)

DOCUMENTS: dict[str, dict[str, Any]] = {
    "00": {"name": "营业性演出申请登记表", "phase": "basic", "required": True},
    "01": {"name": "演员身份材料（演员名单）", "phase": "basic", "required": True},
    "02": {"name": "艺人身份证扫描件", "phase": "basic", "required": True},
    "03": {"name": "场地同意函", "phase": "basic", "required": True},
    "04": {"name": "艺人同意函", "phase": "basic", "required": True},
    "05": {"name": "节目单", "phase": "content", "required": True},
    "06": {"name": "演出曲目歌词", "phase": "content", "required": True},
    "07": {"name": "视频文件", "phase": "video", "required": True},
    "08": {"name": "授权委托书及身份证明", "phase": "basic", "required": True},
    "09": {"name": "报批公司营业执照", "phase": "basic", "required": True},
    "10": {"name": "消防开业许可证", "phase": "basic", "required": True},
    "11": {"name": "翻译资质证明", "phase": "content", "required": False, "condition": "domestic_final_lyrics_foreign_ratio_gte_0.25"},
}

PHASES = ("scan", "basic", "content", "video", "qa")


def today_iso() -> str:
    return date.today().isoformat()


def ensure_project_dirs(project_dir: Path) -> None:
    for folder in PROJECT_DIRS:
        (project_dir / folder).mkdir(parents=True, exist_ok=True)


def manifest_path(project_dir: Path) -> Path:
    return project_dir / "00_项目主档" / "项目主档.json"


def legacy_yaml_path(project_dir: Path) -> Path:
    return project_dir / "00_项目主档" / "项目主档.yaml"


def load_manifest(path_or_project: Path) -> dict[str, Any]:
    path = path_or_project
    if path.is_dir():
        path = manifest_path(path)
    if not path.exists():
        raise FileNotFoundError(f"项目主档不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(manifest: dict[str, Any], path_or_project: Path) -> Path:
    path = path_or_project
    if path.is_dir():
        path = manifest_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_manifest(project_dir: Path, event_name: str, event_time: str, subject: str | None = None,
                   *, config_path: Path | None = None, approval_type: str = "auto") -> dict[str, Any]:
    config, resolved_config = load_company_config(config_path)
    info = configured_subject(config)
    if subject and subject not in {info["company_key"], info["short_name"], info["company"]}:
        raise ValueError("所选主体不符合统一主体政策；国内与涉外必须使用配置中的同一主体。")
    branch = approval_type if approval_type in {"domestic", "foreign"} else "domestic"
    venue_key = config[branch].get("venue_company_key", config["applicant_policy"]["company_key"])
    venue = config["companies"][venue_key]
    documents = {
        seq: {
            **meta,
            "status": "pending",
            "outputs": [],
            "source_hashes": [],
            "last_generated_at": "",
        }
        for seq, meta in DOCUMENTS.items()
    }
    if approval_type == "foreign":
        documents["00"]["required"] = bool(config["foreign"].get("generate_application_form_00", False))
        documents["00"]["status"] = "not_required" if not documents["00"]["required"] else "pending"
    return {
        "schema_version": SCHEMA_VERSION,
        "project": {
            "folder": str(project_dir),
            "created_date": today_iso(),
            "generated_date": today_iso(),
            "final_dir": str(project_dir / "03_最终提交材料"),
            "cache_dir": str(project_dir / "02_生成中间文件" / "cache"),
        },
        "workflow": {
            "approval_type": approval_type,
            "approval_authority": config[branch]["approval_authority"] if approval_type != "auto" else "",
            "applicant_policy_version": config["applicant_policy"]["version"],
            "config_source": str(resolved_config),
            "phase_status": {phase: "pending" for phase in PHASES},
            "locked": {
                "project_master": False,
                "program_list": False,
            },
        },
        "application_subject": info,
        "event": {
            "name": event_name,
            "name_with_translation": event_name,
            "time_raw": event_time,
            "time_for_forms": event_time,
        },
        "venue": {
            "company": venue["legal_name"],
            "address": venue["registered_address"],
        },
        "people": {
            "performers": [],
            "staff_excluded": [],
            "id_warnings": [],
        },
        "program": {
            "items": [],
            "translations": {},
            "sensitive_edits": [],
        },
        "sources": {
            "identity_files": [],
            "program_files": [],
            "lyric_files": [],
            "video_files": [],
            "other_files": [],
        },
        "documents": documents,
        "cache": {
            "enabled": True,
            "source_hashes": {},
            "video_cache_file": str(project_dir / "03_最终提交材料" / "报批视频已压缩" / "压缩缓存.json"),
        },
        "qa": {
            "last_report": "",
            "required_checks": [
                "00-10 输出完整",
                "模板高亮已清除",
                "公章完整在 A4 范围内",
                "身份证完整清晰",
                "签名无方框、无溢出",
                "外文翻译一致",
                "视频输出位置和参数正确",
            ],
        },
        "ready_for_upload": False,
        "field_sources": {},
        "pending_confirmations": [],
    }


def quote_yaml(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_legacy_yaml(manifest: dict[str, Any], path: Path) -> None:
    subject = manifest["application_subject"]
    event = manifest["event"]
    venue = manifest["venue"]
    project = manifest["project"]
    workflow = manifest["workflow"]
    lines = [
        f"project_folder: {quote_yaml(project['folder'])}",
        f"approval_type: {quote_yaml(workflow['approval_type'])}",
        f"approval_authority: {quote_yaml(workflow['approval_authority'])}",
        f"application_subject: {quote_yaml(subject['company'])}",
        f"application_subject_license: {quote_yaml(subject['license'])}",
        f"application_subject_address: {quote_yaml(subject['address'])}",
        f"event_name: {quote_yaml(event['name'])}",
        f"event_time: {quote_yaml(event['time_raw'])}",
        f"venue_company: {quote_yaml(venue['company'])}",
        f"venue_address: {quote_yaml(venue['address'])}",
        "performers: []",
        "staff_excluded: []",
        "program_list: []",
        f"generated_date: {quote_yaml(project['generated_date'])}",
        "pending_confirmations:",
    ]
    lines.extend(f"  - {quote_yaml(item)}" for item in manifest["pending_confirmations"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "name": path.name,
        "sha256": file_sha256(path),
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "mtime_ns": stat.st_mtime_ns,
        "suffix": path.suffix.lower(),
    }


def source_fingerprint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    record = {
        "path": str(path.resolve()),
        "name": path.name,
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "mtime_ns": stat.st_mtime_ns,
        "suffix": path.suffix.lower(),
    }

    # Text/identity sources need content hashes; large media uses a cheap inventory key.
    if path.suffix.lower() not in {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm", ".mp3", ".wav"}:
        record["sha256"] = file_sha256(path)
    return record


def outputs_for(final_dir: Path, seq: str) -> list[Path]:
    if seq == "07":
        return sorted((final_dir / "报批视频已压缩").glob("*.mp4"))
    candidates = []
    for path in final_dir.glob(f"{seq}*"):
        candidates.extend(path.rglob("*") if path.is_dir() else [path])
    if seq == "01":
        candidates.extend(final_dir.glob("演员名单上传版*"))
    return sorted({path for path in candidates if path.is_file() and path.suffix.lower() in {".docx", ".pdf"}})


def generation_inputs_sha256(manifest: dict[str, Any], config: dict[str, Any]) -> str:
    root = Path(__file__).resolve().parents[1]
    dependencies = {}
    for folder in ("assets/templates", "assets/foreign-templates", "assets/seals", "assets/fixed-documents", "references", "scripts"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                dependencies[str(path.relative_to(root))] = file_sha256(path)
    data = {key: manifest.get(key) for key in ("event", "people", "program", "venue", "application_subject", "sources")}
    data["approval_type"] = manifest.get("workflow", {}).get("approval_type")
    data.update(config=config, dependencies=dependencies)
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def refresh_generation_inputs(manifest: dict[str, Any], config: dict[str, Any]) -> bool:
    current = generation_inputs_sha256(manifest, config)
    cache = manifest.setdefault("cache", {})
    previous = cache.get("generation_inputs_sha256")
    changed = previous != current
    if changed:
        for document in manifest.get("documents", {}).values():
            if document.get("status") not in {"pending", "missing"}:
                document.update(status="stale", stale_reason="generation_inputs_changed")
        manifest.setdefault("qa", {})["status"] = "stale"
        manifest["ready_for_upload"] = False
    cache["generation_inputs_sha256"] = current
    return changed
