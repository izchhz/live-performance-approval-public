#!/usr/bin/env python3
from __future__ import annotations
import argparse
from datetime import date
from pathlib import Path
from project_manifest import build_manifest, ensure_project_dirs, legacy_yaml_path, manifest_path, save_manifest, write_legacy_yaml

def main() -> None:
    parser = argparse.ArgumentParser(description="初始化国内或涉外报批项目；申请主体由统一配置确定。")
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--event-name", required=True)
    event = parser.add_mutually_exclusive_group(required=True)
    event.add_argument("--event-time", help="完整演出日期和时间。")
    event.add_argument("--event-date", help="YYYY-MM-DD；时间段使用分支配置默认值。")
    parser.add_argument("--approval-type", choices=("auto", "domestic", "foreign"), default="auto")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--subject", help="兼容旧调用；只能与统一配置主体匹配，无需传入。")
    parser.add_argument("--force", action="store_true", help="覆盖主档并先保存备份；不改已有成品。")
    args = parser.parse_args()
    project_dir = args.project_dir.resolve()
    event_time = args.event_time
    if args.event_date:
        from applicant_policy import load_company_config
        date.fromisoformat(args.event_date)
        config, _ = load_company_config(args.config)
        event_time = args.event_date + " " + config[args.approval_type if args.approval_type != "auto" else "domestic"]["default_time_range"]
    manifest = build_manifest(project_dir, args.event_name, event_time, args.subject, config_path=args.config, approval_type=args.approval_type)
    path = manifest_path(project_dir)
    if path.exists():
        if not args.force:
            raise SystemExit(f"项目主档已存在，未覆盖：{path}；续做直接读取，主体升级使用 applicant_policy.py --migrate。")
        backup = path.with_name("项目主档.before-init.json")
        if backup.exists():
            raise SystemExit("已存在初始化备份，为避免覆盖请使用新目录或先人工归档。")
        backup.write_bytes(path.read_bytes())
    ensure_project_dirs(project_dir)
    save_manifest(manifest, path)
    write_legacy_yaml(manifest, legacy_yaml_path(project_dir))
    print(path)

if __name__ == "__main__":
    main()
