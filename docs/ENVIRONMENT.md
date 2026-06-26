# Environment

## Required System Tools

- Python 3.10+
- LibreOffice
- ffmpeg
- ffprobe
- Poppler tools are useful for PDF preview conversion (`pdfinfo`, `pdftoppm`)

On macOS with Homebrew:

```bash
brew install ffmpeg poppler
```

Install LibreOffice from the official installer or your package manager.

## Python Packages

```bash
python3 -m pip install python-docx Pillow pypdf reportlab PyYAML fonttools
```

Optional packages, depending on your OCR and translation approach:

```bash
python3 -m pip install pymupdf pytesseract opencc
```

## Local Chinese ID OCR

For local mainland Chinese ID-card OCR, install PaddlePaddle and PaddleOCR. On Apple Silicon Mac, use the official CPU package index:

```bash
python3 -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python3 -m pip install paddleocr
```

Run:

```bash
python3 skill/live-performance-approval/scripts/scan_cn_id_ocr.py \
  --project-dir <project-dir> \
  --source-dir <source-dir>
```

The first run downloads OCR models to `~/.paddlex/official_models/`; later runs use the local cache.

## Local Passport / Travel Document MRZ

For local passport and HK/Macau/Taiwan travel-document MRZ extraction:

```bash
brew install tesseract
python3 -m pip install --user PassportEye
```

Run:

```bash
python3 skill/live-performance-approval/scripts/scan_passport_mrz.py \
  --project-dir <project-dir> \
  --source-dir <source-dir>
```

Both OCR helpers can also be run through the compact context-pack helper:

```bash
python3 skill/live-performance-approval/scripts/prepare_agent_context.py \
  --project-dir <project-dir> \
  --source-dir <source-dir> \
  --extract-text \
  --scan-cn-id \
  --scan-mrz
```

## Fonts

This public package does not bundle handwriting fonts because many commercial Chinese and signature fonts cannot be redistributed on GitHub.

Recommended setup:

- Chinese official-document text: use a Songti/Song-style font available on the operator machine, such as SimSun, Songti SC, Noto Serif CJK SC, or Source Han Serif SC.
- Chinese handwritten submitter labels: install at least one licensed Chinese handwriting font locally. If a commercial font is used, keep it outside the public repository.
- Chinese artist signatures: prefer real signature images. If unavailable, install several licensed Chinese handwriting fonts and rotate them per artist; reject fonts that render as boxes, look printed, or look too uniform.
- English/foreign artist signatures: install one or more licensed signature-style Latin fonts locally, or use real signature images when available.
- Before exporting final PDFs, use `fontTools` or equivalent checks to confirm that configured handwriting/signature fonts cover every required character.
- If direct PDF embedding still renders square boxes, render verified handwriting text to a transparent image overlay in the private runtime instead of silently switching to an unapproved font.

Public-repo font policy:

- Do not commit `.ttf`, `.otf`, `.ttc`, `.woff`, or `.woff2` font files unless their license explicitly permits redistribution.
- If a team has licensed fonts, place them in a private package or a local path outside Git, then map their names in the runtime configuration.
- See `skill/live-performance-approval/assets/fonts/README.md` for the expected font categories and fallback rules.

## Validation

```bash
python3 skill/live-performance-approval/scripts/check_environment.py
```
