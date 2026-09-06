#!/usr/bin/env python3
"""Configuration-backed applicant policy shared by domestic and foreign generation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]

def load_company_config(config_path: Path | None = None) -> tuple[dict[str, Any], Path]:
    if config_path is None:
        choices = [SKILL_DIR / "assets/config" / name for name in
                   ("company-profile.private.json", "company-profile.local.json", "company-profile.json")]
        config_path = next((path for path in choices if path.is_file()), choices[0])
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    policy = config.get("applicant_policy", {})
    key = policy.get("company_key")
    company = config.get("companies", {}).get(key, {})
    if not key or not policy.get("version") or not policy.get("effective_date"):
        raise ValueError("主体政策缺少 company_key / version / effective_date；先配置获授权主体。")
    for field in ("legal_name", "performance_license_no", "registered_address", "seal_path", "business_license_path"):
        value = str(company.get(field, "")).strip()
        if not value or any(marker in value for marker in ("{{", "}}", "待填写", "YOUR_", "<")):
            raise ValueError(f"主体配置未完成：companies.{key}.{field}")
    for branch in ("domestic", "foreign"):
        if config.get(branch, {}).get("applicant_company_key") != key:
            raise ValueError(f"{branch}.applicant_company_key 与统一主体政策冲突。")
    return config, config_path

def configured_subject(config: dict[str, Any]) -> dict[str, str]:
    key = config["applicant_policy"]["company_key"]
    company = config["companies"][key]
    return {"company_key": key, "short_name": company.get("short_name", key),
            "company": company["legal_name"], "license": company["performance_license_no"],
            "address": company["registered_address"], "seal": company["seal_path"],
            "business_license": company["business_license_path"]}

def subject_issues(manifest: dict[str, Any], config: dict[str, Any]) -> list[str]:
    actual = manifest.get("application_subject", {})
    if not isinstance(actual, dict):
        return ["旧主档 application_subject 不是对象，必须迁移后再生成。"]
    expected = configured_subject(config)
    issues = []
    for key in ("company", "license", "address", "seal", "business_license"):
        value = actual.get(key, "")
        correct = expected[key]
        # Legacy manifests used asset basenames; accept these only if the company matches.
        matches = value == correct or (key in {"seal", "business_license"} and value == Path(correct).name)
        if not matches:
            issues.append(f"application_subject.{key} 与统一主体配置不一致。")
    if actual.get("company_key") not in (None, "", expected["company_key"]):
        issues.append("application_subject.company_key 与统一主体配置不一致。")
    version = manifest.get("workflow", {}).get("applicant_policy_version")
    if version != config["applicant_policy"]["version"]:
        issues.append("主档主体政策版本过期；使用 applicant_policy.py --migrate 更新并重建受影响材料。")
    return issues

def require_current_subject(manifest: dict[str, Any], config_path: Path | None = None) -> dict[str, Any]:
    config, _ = load_company_config(config_path)
    issues = subject_issues(manifest, config)
    if issues:
        raise ValueError("停止生成：" + "；".join(issues))
    return config

def migrate_manifest(manifest: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime
    issues = subject_issues(manifest, config)
    if not issues:
        return manifest
    manifest.setdefault("migration_history", []).append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "reason": "unified_applicant_policy", "previous_subject": manifest.get("application_subject"),
        "previous_policy_version": manifest.get("workflow", {}).get("applicant_policy_version")})
    manifest["application_subject"] = configured_subject(config)
    workflow = manifest.setdefault("workflow", {})
    workflow["applicant_policy_version"] = config["applicant_policy"]["version"]
    workflow.setdefault("locked", {})["project_master"] = False
    workflow["phase_status"] = {name: "pending" for name in ("scan", "basic", "content", "video", "qa")}
    for document in manifest.get("documents", {}).values():
        document["status"] = "stale"
        document["stale_reason"] = "applicant_policy_changed"
    if workflow.get("approval_type") == "foreign" and "00" in manifest.get("documents", {}):
        manifest["documents"]["00"].update(required=bool(config["foreign"].get("generate_application_form_00", False)), status="not_required")
    manifest.setdefault("qa", {}).update({"status": "stale", "last_report": ""})
    manifest.setdefault("cache", {}).pop("generation_inputs_sha256", None)
    manifest["ready_for_upload"] = False
    return manifest

def normalize_legacy_manifest(manifest: dict[str, Any], project_dir: Path,
                              config_path: Path | None = None) -> dict[str, Any]:
    if all(isinstance(manifest.get(key), dict) for key in ("project", "workflow", "event", "people", "program")):
        return manifest
    from project_manifest import build_manifest
    normalized = build_manifest(project_dir.resolve(), manifest.get("event_name", ""),
                                manifest.get("event_time", ""), config_path=config_path)
    normalized["legacy_manifest"] = manifest
    for key in ("event", "people", "program", "sources", "documents", "venue"):
        if isinstance(manifest.get(key), dict):
            normalized[key].update(manifest[key])
    if isinstance(manifest.get("performers"), list):
        normalized["people"]["performers"] = manifest["performers"]
    if isinstance(manifest.get("staff_excluded"), list):
        normalized["people"]["staff_excluded"] = manifest["staff_excluded"]
    if isinstance(manifest.get("program"), list):
        normalized["program"]["items"] = manifest["program"]
    elif isinstance(manifest.get("program_list"), list):
        normalized["program"]["items"] = manifest["program_list"]
    approval_type = manifest.get("approval_type", "auto")
    normalized["workflow"]["approval_type"] = {"国内": "domestic", "国内报批": "domestic", "涉外": "foreign", "涉外报批": "foreign"}.get(approval_type, approval_type)
    normalized["workflow"]["applicant_policy_version"] = ""
    normalized["application_subject"] = manifest.get("application_subject", {})
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(description="校验统一报批主体，或显式迁移旧主档并使旧成品失效。")
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--migrate", action="store_true")
    args = parser.parse_args()
    from project_manifest import load_manifest, manifest_path, save_manifest, write_legacy_yaml, legacy_yaml_path
    config, _ = load_company_config(args.config)
    manifest = load_manifest(args.project_dir)
    issues = subject_issues(manifest, config)
    if issues and args.migrate:
        path = manifest_path(args.project_dir)
        # Never overwrite the original backup on repeated migration.
        backup = path.with_name("项目主档.before-applicant-policy.json")
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
        manifest = normalize_legacy_manifest(manifest, args.project_dir, args.config)
        save_manifest(migrate_manifest(manifest, config), path)
        write_legacy_yaml(manifest, legacy_yaml_path(args.project_dir))
        print("主体已迁移；原成品保留但标为 stale，须重建并复核上传交接数据。")
    elif issues:
        raise SystemExit("；".join(issues))
    else:
        print("统一报批主体校验通过。")

if __name__ == "__main__":
    main()
