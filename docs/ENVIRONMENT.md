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
