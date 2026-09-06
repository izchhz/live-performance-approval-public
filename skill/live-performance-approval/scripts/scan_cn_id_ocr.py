#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from validate_cn_id import add_months, parse_date, validate_id


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp", ".pdf"}
CANDIDATE_KEYWORDS = ("身份证", "居民身份证", "证件", "id", "identity")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value).strip()


def normalize_date_text(value: str) -> str:
    value = value.strip()
    value = value.replace("．", ".").replace("。", ".").replace("/", ".").replace("-", ".")
    match = re.search(r"(\d{4})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})", value)
    if not match:
        return ""
    year, month, day = match.groups()
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return ""


def load_ocr():
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as exc:
        raise SystemExit("缺少 PaddleOCR。请先安装：python3 -m pip install paddlepaddle paddleocr") from exc

    try:
        return PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            lang="ch",
        )
    except TypeError:
        return PaddleOCR(use_angle_cls=True, lang="ch")


def read_ocr_lines(ocr: Any, path: Path) -> list[dict[str, Any]]:
    try:
        pages = ocr.predict(str(path))
        lines: list[dict[str, Any]] = []
        for page in pages:
            rec_texts = list(page.get("rec_texts", []))
            rec_scores = list(page.get("rec_scores", []))
            rec_boxes = list(page.get("rec_boxes", []))
            for index, text in enumerate(rec_texts):
                box = rec_boxes[index] if index < len(rec_boxes) else None
                lines.append(
                    {
                        "text": str(text),
                        "score": float(rec_scores[index]) if index < len(rec_scores) else None,
                        "box": box.tolist() if hasattr(box, "tolist") else box,
                    }
                )
        return lines
    except AttributeError:
        pass

    raw = ocr.ocr(str(path), cls=True)
    lines = []
    for page in raw or []:
        for item in page or []:
            try:
                lines.append({"text": str(item[1][0]), "score": float(item[1][1]), "box": item[0]})
            except Exception:
                continue
    return lines


def clean_id_number(value: str) -> str:
    value = normalize_text(value).upper()
    value = value.replace("O", "0").replace("I", "1")
    match = re.search(r"\d{17}[\dX]", value)
    return match.group(0) if match else ""


def extract_after_label(text: str, label: str) -> str:
    if label not in text:
        return ""
    return text.split(label, 1)[1].strip(" :：,，")


def parse_name(texts: list[str]) -> str:
    for text in texts:
        value = normalize_text(text)
        if "姓名" in value:
            name = extract_after_label(value, "姓名")
            name = re.sub(r"[^一-龥·•A-Za-z]", "", name)
            if name:
                return name.replace("•", "·")
    return ""


def parse_sex_ethnicity(texts: list[str]) -> tuple[str, str]:
    sex = ""
    ethnicity = ""
    for text in texts:
        value = normalize_text(text)
        if "性别" in value:
            after = extract_after_label(value, "性别")
            sex_match = re.search(r"[男女]", after)
            if sex_match:
                sex = sex_match.group(0)
        if "民族" in value:
            after = extract_after_label(value, "民族")
            ethnicity = re.sub(r"[^一-龥]", "", after)
            ethnicity = ethnicity[:4]
    return sex, ethnicity


def parse_birth(texts: list[str], id_number: str) -> str:
    for text in texts:
        value = normalize_text(text)
        if "出生" in value:
            parsed = normalize_date_text(extract_after_label(value, "出生"))
            if parsed:
                return parsed
    if re.fullmatch(r"\d{17}[\dX]", id_number):
        try:
            return datetime.strptime(id_number[6:14], "%Y%m%d").date().isoformat()
        except ValueError:
            return ""
    return ""


def parse_address(texts: list[str]) -> str:
    parts: list[str] = []
    in_address = False
    for text in texts:
        value = normalize_text(text)
        if "住址" in value:
            in_address = True
            candidate = extract_after_label(value, "住址")
            if candidate:
                parts.append(candidate)
            continue
        if "公民身份号码" in value or clean_id_number(value):
            break
        if in_address:
            parts.append(value)
    return "".join(parts)


def parse_issuing_authority(texts: list[str]) -> str:
    for text in texts:
        value = normalize_text(text)
        if "签发机关" in value:
            authority = extract_after_label(value, "签发机关")
            return authority
    return ""


def parse_valid_period(texts: list[str]) -> tuple[str, str, str]:
    joined = " ".join(texts)
    normalized = joined.replace("—", "-").replace("－", "-").replace("至", "-")
    if "有效期限" not in normalized and "有效期" not in normalized:
        return "", "", ""
    dates = re.findall(r"\d{4}[./．。-]\d{1,2}[./．。-]\d{1,2}", normalized)
    start = normalize_date_text(dates[0]) if dates else ""
    end = normalize_date_text(dates[1]) if len(dates) > 1 else ""
    if "长期" in normalized:
        end = "长期"
    display = ""
    if start and end:
        display = f"{start}-{end}"
    return start, end, display


def classify_side(texts: list[str]) -> str:
    joined = "".join(normalize_text(text) for text in texts)
    has_front = "公民身份号码" in joined or "姓名" in joined or bool(clean_id_number(joined))
    has_back = "签发机关" in joined or "有效期限" in joined or "有效期" in joined
    if has_front and has_back:
        return "front_and_back"
    if has_front:
        return "front"
    if has_back:
        return "back"
    return "unknown"


def parse_cn_id(lines: list[dict[str, Any]], today: date) -> dict[str, Any]:
    texts = [line["text"] for line in lines if line.get("text")]
    normalized_texts = [normalize_text(text) for text in texts]
    joined = "".join(normalized_texts)
    id_number = clean_id_number(joined)
    validation = validate_id(id_number) if id_number else validate_id("")
    name = parse_name(normalized_texts)
    sex, ethnicity = parse_sex_ethnicity(normalized_texts)
    birth = parse_birth(normalized_texts, id_number)
    address = parse_address(normalized_texts)
    issuing_authority = parse_issuing_authority(normalized_texts)
    valid_from, valid_to, valid_period = parse_valid_period(normalized_texts)
    side = classify_side(normalized_texts)

    renewal_warning = False
    expiry_for_check = ""
    if valid_to and valid_to != "长期":
        try:
            expiry = parse_date(valid_to)
            expiry_for_check = expiry.isoformat()
            renewal_warning = expiry < add_months(today, 6)
        except ValueError:
            pass

    missing_fields = []
    if side in {"front", "front_and_back"}:
        if not name:
            missing_fields.append("姓名")
        if not id_number:
            missing_fields.append("身份证号")
        if id_number and not validation["valid"]:
            missing_fields.append("身份证号校验失败")
    elif side == "back":
        if not issuing_authority:
            missing_fields.append("签发机关")
        if not valid_period:
            missing_fields.append("有效期限")
    else:
        missing_fields.append("证件正反面类型未识别")

    return {
        "side": side,
        "name": name,
        "sex": sex,
        "ethnicity": ethnicity,
        "birth_date": birth,
        "address": address,
        "id_number": id_number,
        "id_validation": validation,
        "issuing_authority": issuing_authority,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "valid_period": valid_period,
        "expiry_for_check": expiry_for_check,
        "renewal_warning": renewal_warning,
        "missing_fields": missing_fields,
        "needs_manual_review": bool(missing_fields),
        "ocr_texts": texts,
        "ocr_lines": lines,
    }


def candidate_files(paths: list[Path], all_images: bool) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            found.append(path)
        elif path.is_dir():
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
            deduped.append(file)
            seen.add(resolved)
    return deduped


def compact_for_report(item: dict[str, Any]) -> str:
    parsed = item["parsed"]
    side = parsed.get("side")
    if side == "back":
        identity_line = f"  - authority: `{parsed.get('issuing_authority') or '待复核'}`"
    else:
        identity_line = f"  - id_valid: `{parsed.get('id_validation', {}).get('valid')}`"
    parts = [
        f"- source: `{Path(item['source_file']).name}`",
        f"  - status: `{item['status']}`",
        f"  - side: `{side}`",
        f"  - name: `{parsed.get('name') or '待复核'}`",
        identity_line,
        f"  - expiry: `{parsed.get('valid_to') or '未识别'}`",
    ]
    if parsed.get("renewal_warning"):
        parts.append(f"  - warning: `{parsed.get('name') or '该人员'}的身份证需要换新。`")
    if parsed.get("missing_fields"):
        parts.append(f"  - missing: {', '.join(parsed['missing_fields'])}")
    return "\n".join(parts)


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# Chinese ID OCR Report", ""]
    lines.append(f"- generated_at: `{datetime.now().isoformat(timespec='seconds')}`")
    lines.append(f"- total: {len(results)}")
    lines.append(f"- ok: {sum(1 for item in results if item['status'] == 'ok')}")
    lines.append(f"- needs_manual_review: {sum(1 for item in results if item['needs_manual_review'])}")
    lines.append("")
    for item in results:
        lines.append(compact_for_report(item))
        lines.append("")
    return "\n".join(lines)


def default_output_dir(project_dir: Path | None, output_dir: Path | None) -> Path:
    if output_dir:
        return output_dir
    if project_dir:
        return project_dir / "02_生成中间文件" / "cn_id_ocr"
    return Path.cwd() / "cn_id_ocr"


def main() -> None:
    parser = argparse.ArgumentParser(description="本地使用 PaddleOCR 识别中国居民身份证，输出结构化 JSON。")
    parser.add_argument("paths", nargs="*", type=Path, help="身份证图片/PDF 或资料目录。")
    parser.add_argument("--project-dir", type=Path, help="项目目录；默认输出到 02_生成中间文件/cn_id_ocr。")
    parser.add_argument("--source-dir", action="append", default=[], type=Path, help="资料目录，可重复。")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--all-images", action="store_true", help="目录扫描时处理全部图片/PDF，而不只处理身份证关键词文件。")
    parser.add_argument("--today", help="用于有效期不足 6 个月判断，默认今天。")
    args = parser.parse_args()

    today = parse_date(args.today) if args.today else date.today()
    output_dir = default_output_dir(args.project_dir, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = candidate_files([*args.paths, *args.source_dir], args.all_images)
    if not files:
        raise SystemExit("没有找到可扫描的身份证图片或 PDF。可使用 --all-images 或直接传入文件路径。")

    ocr = load_ocr()
    results: list[dict[str, Any]] = []
    for file in files:
        try:
            lines = read_ocr_lines(ocr, file)
            parsed = parse_cn_id(lines, today)
            results.append(
                {
                    "source_file": str(file),
                    "scanned_at": datetime.now().isoformat(timespec="seconds"),
                    "engine": "PaddleOCR",
                    "status": "needs_manual_review" if parsed["needs_manual_review"] else "ok",
                    "needs_manual_review": parsed["needs_manual_review"],
                    "parsed": parsed,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "source_file": str(file),
                    "scanned_at": datetime.now().isoformat(timespec="seconds"),
                    "engine": "PaddleOCR",
                    "status": "needs_manual_review",
                    "needs_manual_review": True,
                    "error": f"{exc.__class__.__name__}: {exc}",
                    "parsed": {"missing_fields": ["OCR失败"], "ocr_texts": [], "ocr_lines": []},
                }
            )

    from project_manifest import source_fingerprint
    for item in results:
        source = Path(item["source_file"]) if item.get("source_file") else None
        if source and source.is_file():
            item["source_fingerprint"] = source_fingerprint(source)
    json_path = output_dir / "cn_id_ocr_results.json"
    md_path = output_dir / "cn_id_ocr_report.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(results), encoding="utf-8")
    print(md_path)
    print(json_path)

    failed = sum(1 for item in results if item["needs_manual_review"])
    if failed:
        print(f"needs_manual_review={failed}")


if __name__ == "__main__":
    main()
