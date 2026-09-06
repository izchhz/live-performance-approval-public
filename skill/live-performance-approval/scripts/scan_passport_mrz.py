#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp", ".pdf"}
CANDIDATE_KEYWORDS = (
    "passport",
    "护照",
    "证件",
    "通行证",
    "港澳",
    "台湾",
    "visa",
    "permit",
    "id",
)

REGION_ALIASES = {
    "台湾": ("中国台湾", "台湾居民往来内地通行证"),
    "臺灣": ("中国台湾", "台湾居民往来内地通行证"),
    "taiwan": ("中国台湾", "台湾居民往来内地通行证"),
    "twn": ("中国台湾", "台湾居民往来内地通行证"),
    "香港": ("中国香港", "港澳居民来往内地通行证"),
    "hongkong": ("中国香港", "港澳居民来往内地通行证"),
    "hong_kong": ("中国香港", "港澳居民来往内地通行证"),
    "hkg": ("中国香港", "港澳居民来往内地通行证"),
    "澳门": ("中国澳门", "港澳居民来往内地通行证"),
    "澳門": ("中国澳门", "港澳居民来往内地通行证"),
    "macau": ("中国澳门", "港澳居民来往内地通行证"),
    "macao": ("中国澳门", "港澳居民来往内地通行证"),
    "mac": ("中国澳门", "港澳居民来往内地通行证"),
}

COUNTRY_ZH = {
    "BLR": "白俄罗斯",
    "CHN": "中国",
    "HKG": "中国香港",
    "MAC": "中国澳门",
    "TWN": "中国台湾",
    "USA": "美国",
    "GBR": "英国",
    "CAN": "加拿大",
    "AUS": "澳大利亚",
    "NZL": "新西兰",
    "JPN": "日本",
    "KOR": "韩国",
    "FRA": "法国",
    "DEU": "德国",
    "ITA": "意大利",
    "ESP": "西班牙",
    "PRT": "葡萄牙",
    "NLD": "荷兰",
    "BEL": "比利时",
    "CHE": "瑞士",
    "AUT": "奥地利",
    "SWE": "瑞典",
    "NOR": "挪威",
    "DNK": "丹麦",
    "FIN": "芬兰",
    "RUS": "俄罗斯",
    "UKR": "乌克兰",
    "POL": "波兰",
    "CZE": "捷克",
    "SVK": "斯洛伐克",
    "HUN": "匈牙利",
    "ROU": "罗马尼亚",
    "MEX": "墨西哥",
    "BRA": "巴西",
    "ARG": "阿根廷",
    "CHL": "智利",
    "SGP": "新加坡",
    "MYS": "马来西亚",
    "THA": "泰国",
    "IDN": "印度尼西亚",
    "PHL": "菲律宾",
    "VNM": "越南",
    "IND": "印度",
}

WEIGHTS = (7, 3, 1)


def clean_number(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("<", "").strip()


def date_yyMMdd(value: str | None) -> str:
    if not value or len(value) != 6 or not value.isdigit():
        return value or ""
    yy = int(value[:2])
    # Passport/permit expiry dates in current approval work are modern future dates.
    century = 2000 if yy < 50 else 1900
    return f"{century + yy:04d}-{value[2:4]}-{value[4:6]}"


def normalize_lines(lines: list[str]) -> list[str]:
    normalized = []
    for line in lines:
        line = line.strip().upper().replace(" ", "")
        if line:
            normalized.append(line)
    return normalized


def char_value(char: str) -> int:
    if char == "<":
        return 0
    if char.isdigit():
        return int(char)
    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10
    raise ValueError(f"Unsupported MRZ character: {char!r}")


def check_digit(value: str) -> str:
    total = sum(char_value(char) * WEIGHTS[index % 3] for index, char in enumerate(value))
    return str(total % 10)


def valid_digit(value: str, digit: str) -> bool:
    return digit.isdigit() and check_digit(value) == digit


def parse_name_line(line: str) -> tuple[str, str]:
    parts = [part for part in line.strip("<").split("<<") if part]
    surname = parts[0].replace("<", " ") if parts else ""
    names = " ".join(part.replace("<", " ") for part in parts[1:]).strip()
    return surname, names


def parse_china_mainland_travel_permit(lines: list[str]) -> dict[str, Any] | None:
    """Parse CT/CR/CF MRZ lines used by Taiwan/HK/Macau mainland travel permits."""
    normalized = normalize_lines(lines)
    if len(normalized) < 2:
        return None
    line1 = normalized[0]
    document_code = line1[:2]
    if document_code not in {"CT", "CR", "CF"} or len(line1) < 30:
        return None

    number_field = line1[2:11]
    if document_code == "CT":
        number = line1[2:10]
        region_zh = "中国台湾"
        document_type_zh = "台湾居民往来内地通行证"
    else:
        number = clean_number(number_field)
        first_char = number[:1].upper()
        if first_char == "H":
            region_zh = "中国香港"
        elif first_char == "M":
            region_zh = "中国澳门"
        else:
            region_zh = ""
        document_type_zh = "港澳居民来往内地通行证"
        if document_code == "CF":
            document_type_zh = "港澳居民来往内地通行证（非中国籍）"

    number_check = line1[11]
    issue_count = line1[12:14]
    issue_check = line1[14]
    expiration = line1[15:21]
    expiration_check = line1[21]
    sex = line1[22]
    birth = line1[23:29]
    birth_check = line1[29]
    valid_number = valid_digit(number_field, number_check)
    valid_issue_count = valid_digit(issue_count, issue_check)
    valid_expiration = valid_digit(expiration, expiration_check)
    valid_birth = valid_digit(birth, birth_check)
    surname, names = parse_name_line(normalized[2] if len(normalized) >= 3 else normalized[1])

    return {
        "mrz_type": document_code,
        "document_code": document_code,
        "valid_score": 100 if valid_number and valid_expiration and valid_birth else 0,
        "type": document_code,
        "country": "CHN",
        "number": number,
        "date_of_birth": birth,
        "expiration_date": expiration,
        "nationality": "CHN",
        "sex": sex,
        "surname": surname,
        "names": names,
        "personal_number": "",
        "issue_count": issue_count,
        "valid_number": valid_number,
        "valid_issue_count": valid_issue_count,
        "valid_date_of_birth": valid_birth,
        "valid_expiration_date": valid_expiration,
        "valid_composite": True,
        "valid_personal_number": None,
        "raw_lines": normalized,
        "method": "china_mainland_travel_permit_custom",
        "region_zh_for_approval": region_zh,
        "document_type_zh_for_approval": document_type_zh,
    }


def mrz_from_lines(lines: list[str]) -> dict[str, Any]:
    from passporteye.mrz.text import MRZ  # type: ignore

    normalized = normalize_lines(lines)
    custom = parse_china_mainland_travel_permit(normalized)
    if custom:
        return custom
    mrz = MRZ(normalized)
    data = dict(mrz.to_dict())
    data["raw_lines"] = normalized
    return data


def read_mrz_file(path: Path, extra_cmdline_params: str) -> dict[str, Any] | None:
    from passporteye import read_mrz  # type: ignore

    mrz = read_mrz(str(path), save_roi=False, extra_cmdline_params=extra_cmdline_params)
    if mrz is None:
        return None
    data = dict(mrz.to_dict())
    raw_text = data.get("raw_text", "")
    if raw_text:
        data["raw_lines"] = normalize_lines(raw_text.splitlines())
        custom = parse_china_mainland_travel_permit(data["raw_lines"])
        if custom:
            return custom
    return data


def is_valid_mrz(data: dict[str, Any] | None) -> bool:
    if not data or not data.get("mrz_type"):
        return False
    core = [
        bool(data.get("valid_number")),
        bool(data.get("valid_date_of_birth")),
        bool(data.get("valid_expiration_date")),
    ]
    if "valid_composite" in data:
        core.append(bool(data.get("valid_composite")))
    return all(core)


def infer_region_from_path(path: Path | None) -> tuple[str, str]:
    if not path:
        return "", ""
    name = path.name.lower().replace(" ", "_").replace("-", "_")
    for token, value in REGION_ALIASES.items():
        if token in name:
            return value
    return "", ""


def infer_region_from_mrz(data: dict[str, Any] | None) -> tuple[str, str]:
    if not data:
        return "", ""
    nationality = str(data.get("nationality") or "").upper()
    country = str(data.get("country") or "").upper()
    for token in (nationality, country):
        if token == "TWN":
            return "中国台湾", "台湾居民往来内地通行证"
        if token == "HKG":
            return "中国香港", "港澳居民来往内地通行证"
        if token in {"MAC", "MO"}:
            return "中国澳门", "港澳居民来往内地通行证"
    raw_lines = data.get("raw_lines") or []
    first_line = str(raw_lines[0]) if raw_lines else ""
    # Common observed Taiwan permit MRZ samples begin with CT followed by the permit number.
    if first_line.startswith("CT"):
        return "中国台湾", "台湾居民往来内地通行证"
    if first_line.startswith(("CR", "CF")):
        number = first_line[2:11]
        if number.startswith("H"):
            return "中国香港", "港澳居民来往内地通行证"
        if number.startswith("M"):
            return "中国澳门", "港澳居民来往内地通行证"
    return "", ""


def infer_document_type(data: dict[str, Any] | None, region_zh: str, document_type: str) -> str:
    if region_zh == "中国台湾":
        return "台湾居民往来内地通行证"
    if region_zh in {"中国香港", "中国澳门"}:
        return "港澳居民来往内地通行证"
    if document_type.startswith("P"):
        return "护照"
    mrz_type = (data or {}).get("mrz_type")
    if mrz_type == "TD3":
        return "护照"
    if mrz_type in {"MRVA", "MRVB"}:
        return "签证"
    if mrz_type in {"TD1", "TD2"}:
        return "证件类型待确认"
    return ""


def compact_result(path: Path | None, data: dict[str, Any] | None, error: str = "") -> dict[str, Any]:
    valid = is_valid_mrz(data)
    nationality = (data or {}).get("nationality") or (data or {}).get("country") or ""
    country = (data or {}).get("country") or ""
    custom_region = (data or {}).get("region_zh_for_approval") or ""
    custom_document_type = (data or {}).get("document_type_zh_for_approval") or ""
    region_zh, region_doc_type = custom_region, custom_document_type
    if not region_zh:
        region_zh, region_doc_type = infer_region_from_path(path)
    if not region_zh:
        region_zh, region_doc_type = infer_region_from_mrz(data)
    document_type = (data or {}).get("type") or ""
    document_type_zh = custom_document_type or region_doc_type or infer_document_type(data, region_zh, document_type)
    country_zh = region_zh or COUNTRY_ZH.get(nationality) or COUNTRY_ZH.get(country) or ""
    region_needs_review = bool(valid and document_type_zh == "证件类型待确认")
    result: dict[str, Any] = {
        "source_file": str(path) if path else "",
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "engine": "PassportEye/Tesseract",
        "status": "ok" if valid and not region_needs_review else "needs_manual_review",
        "needs_manual_review": (not valid) or region_needs_review,
        "error": error,
        "mrz_type": (data or {}).get("mrz_type"),
        "valid_score": (data or {}).get("valid_score"),
        "document_type": document_type,
        "document_type_zh_for_approval": document_type_zh,
        "country": country,
        "nationality": nationality,
        "country_zh": country_zh,
        "region_zh_for_approval": region_zh or country_zh,
        "region_needs_review": region_needs_review,
        "number": clean_number((data or {}).get("number")),
        "date_of_birth": date_yyMMdd((data or {}).get("date_of_birth")),
        "expiration_date": date_yyMMdd((data or {}).get("expiration_date")),
        "sex": (data or {}).get("sex") or "",
        "surname": (data or {}).get("surname") or "",
        "names": (data or {}).get("names") or "",
        "personal_number": clean_number((data or {}).get("personal_number")),
        "valid_number": bool((data or {}).get("valid_number")),
        "valid_date_of_birth": bool((data or {}).get("valid_date_of_birth")),
        "valid_expiration_date": bool((data or {}).get("valid_expiration_date")),
        "valid_composite": bool((data or {}).get("valid_composite")) if "valid_composite" in (data or {}) else None,
        "valid_personal_number": bool((data or {}).get("valid_personal_number"))
        if "valid_personal_number" in (data or {})
        else None,
        "raw_lines": (data or {}).get("raw_lines") or [],
        "raw": data or {},
    }
    if not valid and not error:
        result["error"] = "MRZ missing, unrecognized, or failed check digits."
    if region_needs_review and not result["error"]:
        result["error"] = "MRZ valid, but region/document type needs manual confirmation."
    return result


def candidate_files(paths: list[Path], all_images: bool) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix.lower() in IMAGE_SUFFIXES:
                found.append(path)
            continue
        if path.is_dir():
            for file in sorted(path.rglob("*")):
                if not file.is_file() or file.suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                lower_name = file.name.lower()
                if all_images or any(keyword in lower_name for keyword in CANDIDATE_KEYWORDS):
                    found.append(file)
    deduped: list[Path] = []
    seen: set[Path] = set()
    for file in found:
        resolved = file.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(file)
    return deduped


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# Passport MRZ Scan Report", ""]
    lines.append(f"- generated_at: `{datetime.now().isoformat(timespec='seconds')}`")
    lines.append(f"- total: {len(results)}")
    lines.append(f"- ok: {sum(1 for item in results if item['status'] == 'ok')}")
    lines.append(f"- needs_manual_review: {sum(1 for item in results if item['needs_manual_review'])}")
    lines.append("")
    for item in results:
        lines.append(f"## {Path(item['source_file']).name if item['source_file'] else 'MRZ lines'}")
        lines.append(f"- status: `{item['status']}`")
        lines.append(f"- type: `{item.get('mrz_type')}`")
        lines.append(f"- number: `{item.get('number')}`")
        lines.append(f"- nationality: `{item.get('nationality')}` / {item.get('country_zh') or '待确认'}")
        lines.append(
            f"- approval: {item.get('region_zh_for_approval') or '待确认'} / "
            f"{item.get('document_type_zh_for_approval') or '待确认'}"
        )
        lines.append(f"- birth: `{item.get('date_of_birth')}`")
        lines.append(f"- expiry: `{item.get('expiration_date')}`")
        lines.append(f"- name: `{item.get('surname')}` / `{item.get('names')}`")
        if item.get("error"):
            lines.append(f"- error: {item['error']}")
        raw_lines = item.get("raw_lines") or []
        if raw_lines:
            lines.append("- raw_lines:")
            lines.extend(f"  - `{line}`" for line in raw_lines)
        lines.append("")
    return "\n".join(lines)


def default_output_dir(project_dir: Path | None, output_dir: Path | None) -> Path:
    if output_dir:
        return output_dir
    if project_dir:
        return project_dir / "02_生成中间文件" / "passport_mrz"
    return Path.cwd() / "passport_mrz"


def main() -> None:
    parser = argparse.ArgumentParser(description="本地扫描护照/港澳台证件 MRZ，输出结构化 JSON，减少云端视觉识别。")
    parser.add_argument("paths", nargs="*", type=Path, help="证件图片/PDF 或资料目录。")
    parser.add_argument("--project-dir", type=Path, help="项目目录；默认输出到 02_生成中间文件/passport_mrz。")
    parser.add_argument("--source-dir", action="append", default=[], type=Path, help="资料目录，可重复。")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--all-images", action="store_true", help="目录扫描时处理全部图片/PDF，而不只处理护照/证件关键词文件。")
    parser.add_argument("--tesseract-params", default="", help="传给 Tesseract 的额外参数。")
    parser.add_argument("--mrz-lines", nargs="+", help="直接校验给定 MRZ 行，不做 OCR。")
    args = parser.parse_args()

    if shutil.which("tesseract") is None and not args.mrz_lines:
        raise SystemExit("缺少 tesseract。请先执行：brew install tesseract")

    output_dir = default_output_dir(args.project_dir, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    if args.mrz_lines:
        try:
            results.append(compact_result(None, mrz_from_lines(args.mrz_lines)))
        except Exception as exc:
            results.append(compact_result(None, None, f"{exc.__class__.__name__}: {exc}"))

    paths = [*args.paths, *args.source_dir]
    for path in candidate_files(paths, args.all_images):
        try:
            data = read_mrz_file(path, args.tesseract_params)
            results.append(compact_result(path, data))
        except Exception as exc:
            results.append(compact_result(path, None, f"{exc.__class__.__name__}: {exc}"))

    if not results:
        raise SystemExit("没有找到可扫描的护照/证件图片或 PDF。可使用 --all-images 或直接传入文件路径。")

    from project_manifest import source_fingerprint
    for item in results:
        source = Path(item["source_file"]) if item.get("source_file") else None
        if source and source.is_file():
            item["source_fingerprint"] = source_fingerprint(source)
    json_path = output_dir / "passport_mrz_results.json"
    md_path = output_dir / "passport_mrz_report.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(results), encoding="utf-8")
    print(md_path)
    print(json_path)

    failed = sum(1 for item in results if item["needs_manual_review"])
    if failed:
        print(f"needs_manual_review={failed}")


if __name__ == "__main__":
    main()
