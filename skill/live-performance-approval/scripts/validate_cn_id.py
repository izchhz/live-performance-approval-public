#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime


WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
CHECK_CODES = "10X98765432"


def parse_date(value: str) -> date:
    normalized = value.strip().replace(".", "-").replace("/", "-")
    return datetime.strptime(normalized, "%Y-%m-%d").date()


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def validate_id(id_number: str) -> dict[str, object]:
    value = id_number.strip().upper()
    shape_ok = bool(re.fullmatch(r"\d{17}[\dX]", value))
    expected = ""
    checksum_ok = False
    birth_date = ""
    birth_date_ok = False
    if shape_ok:
        expected = CHECK_CODES[sum(int(char) * weight for char, weight in zip(value[:17], WEIGHTS)) % 11]
        checksum_ok = value[-1] == expected
        try:
            birth_date = datetime.strptime(value[6:14], "%Y%m%d").date().isoformat()
            birth_date_ok = True
        except ValueError:
            birth_date = value[6:14]
    return {
        "id_number": value,
        "shape_ok": shape_ok,
        "expected_checksum": expected,
        "actual_checksum": value[-1:] if value else "",
        "checksum_ok": checksum_ok,
        "birth_date": birth_date,
        "birth_date_ok": birth_date_ok,
        "valid": shape_ok and checksum_ok and birth_date_ok,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="校验中国居民身份证号码和证件有效期。")
    parser.add_argument("--name", default="")
    parser.add_argument("--id", required=True, dest="id_number")
    parser.add_argument("--expiry", help="身份证有效期截止日，例如 2035-09-15。长期证件可省略。")
    parser.add_argument("--today", help="用于复核的当前日期，默认今天，例如 2026-06-03。")
    args = parser.parse_args()

    result = validate_id(args.id_number)
    today = parse_date(args.today) if args.today else date.today()
    result["name"] = args.name
    result["today"] = today.isoformat()
    result["renewal_warning"] = False
    if args.expiry:
        expiry = parse_date(args.expiry)
        result["expiry"] = expiry.isoformat()
        result["renewal_warning"] = expiry < add_months(today, 6)
    else:
        result["expiry"] = "长期或未提供"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(2)
    if result["renewal_warning"]:
        print(f"{args.name or '该人员'}的身份证需要换新。")


if __name__ == "__main__":
    main()
