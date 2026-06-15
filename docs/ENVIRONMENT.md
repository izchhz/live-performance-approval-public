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
python3 -m pip install python-docx Pillow pypdf reportlab
```

Optional packages, depending on your OCR and translation approach:

```bash
python3 -m pip install pymupdf pytesseract opencc
```

## Fonts

- Chinese government-style documents should use Songti/Song-style fonts where possible.
- Handwritten submitter labels require a local handwriting font.
- Artist signatures should use real signature images when available; otherwise use varied local handwriting/signature fonts.

## Validation

```bash
python3 skill/live-performance-approval/scripts/check_environment.py
```
