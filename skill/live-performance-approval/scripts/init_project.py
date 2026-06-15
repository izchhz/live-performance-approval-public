#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


STANDARD_FOLDERS = [
    "00_项目主档",
    "01_原始资料",
    "02_生成中间文件",
    "03_最终提交材料",
    "04_缺失资料与提醒",
]


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_event_time(event_date: str | None, event_time: str | None, default_range: str) -> str:
    if event_time:
        return event_time
    if not event_date:
        raise SystemExit("Provide --event-time or --event-date.")
    start, end = default_range.split("-", 1)
    return f"{event_date} {start} to {event_date} {end}"


def build_manifest(args, config: dict) -> dict:
    approval_type = args.approval_type
    companies = config["companies"]

    if approval_type == "foreign":
        branch = config["foreign"]
        subject_key = branch["applicant_company_key"]
        venue_key = branch["venue_company_key"]
        authority = branch["approval_authority"]
        default_range = branch.get("default_time_range", "20:00-22:00")
    else:
        branch = config["domestic"]
        subject_key = args.subject
        venue_key = args.venue or next((k for k, v in companies.items() if "venue" in v.get("roles", [])), subject_key)
        authority = branch["approval_authority"]
        default_range = branch.get("default_time_range", "20:00-22:00")

    if subject_key not in companies:
        raise SystemExit(f"Missing subject company key in config: {subject_key}")
    if venue_key not in companies:
        raise SystemExit(f"Missing venue company key in config: {venue_key}")

    subject = companies[subject_key]
    venue = companies[venue_key]
    return {
        "schema_version": 1,
        "project_folder": str(args.project_dir),
        "approval_type": approval_type,
        "approval_authority": authority,
        "application_subject_key": subject_key,
        "application_subject": subject["legal_name"],
        "application_subject_license": subject.get("performance_license_no", ""),
        "application_subject_address": subject.get("registered_address", ""),
        "venue_company_key": venue_key,
        "venue_company": venue["legal_name"],
        "venue_address": venue.get("registered_address", ""),
        "event_name": args.event_name,
        "event_time": parse_event_time(args.event_date, args.event_time, default_range),
        "performers": [],
        "staff_excluded": [],
        "program_list": [],
        "generated_date": date.today().isoformat(),
        "pending_confirmations": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a performance approval project folder and project master file.")
    parser.add_argument("--config", required=True, type=Path, help="Company profile JSON.")
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-date", help="Date only, e.g. 2026-11-13. Uses branch default time range.")
    parser.add_argument("--event-time", help="Full event time string. Overrides --event-date.")
    parser.add_argument("--approval-type", required=True, choices=["auto", "domestic", "foreign"])
    parser.add_argument("--subject", help="Company key for domestic applicant. Ignored for foreign when config fixes applicant.")
    parser.add_argument("--venue", help="Company key for venue. Optional for domestic; fixed by config for foreign.")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.approval_type == "auto":
        args.approval_type = "pending-document-scan"
        approval_type_for_manifest = "domestic"
    else:
        approval_type_for_manifest = args.approval_type
    original_approval_type = args.approval_type
    args.approval_type = approval_type_for_manifest

    args.project_dir.mkdir(parents=True, exist_ok=True)
    for folder in STANDARD_FOLDERS:
        (args.project_dir / folder).mkdir(exist_ok=True)

    manifest = build_manifest(args, config)
    manifest["approval_type_initial"] = original_approval_type

    out = args.project_dir / "00_项目主档" / "项目主档.json"
    if out.exists():
        raise SystemExit(f"Project master already exists, refusing to overwrite: {out}")
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
