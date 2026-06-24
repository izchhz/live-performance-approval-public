#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import tempfile
import zipfile
from pathlib import Path


def clean_xml(text: str) -> str:
    replacements = {
        "dc:creator": "approval-automation",
        "cp:lastModifiedBy": "approval-automation",
    }
    for tag, value in replacements.items():
        text = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>",
            f"<{tag}>{value}</{tag}>",
            text,
            flags=re.DOTALL,
        )
    text = re.sub(r"<cp:lastPrinted>.*?</cp:lastPrinted>", "", text, flags=re.DOTALL)
    return text


def scrub(path: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temp_path, "w") as target:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == "docProps/core.xml":
                    data = clean_xml(data.decode("utf-8")).encode("utf-8")
                target.writestr(item, data)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="清理 Word 模板中的作者元数据。")
    parser.add_argument("docx", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.docx:
        scrub(path)
        print(path)


if __name__ == "__main__":
    main()
