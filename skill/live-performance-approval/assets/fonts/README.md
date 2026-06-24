# Font Requirements

This directory is intentionally documentation-only in the public package.

Do not commit font binaries to the public repository unless the font license explicitly permits redistribution. Keep licensed commercial fonts in a private package or install them on the operator machine.

## Required Font Categories

The workflow expects these font categories:

1. Official Chinese document font
   - Purpose: government-style tables, letters, and body text.
   - Recommended families: SimSun, Songti SC, Noto Serif CJK SC, Source Han Serif SC.
   - Fallback behavior: use the closest Songti/Song-style serif Chinese font available on the machine.

2. Chinese handwriting font
   - Purpose: submitter labels such as `提供人：...` and copy-verification notes.
   - Recommended behavior: use one fixed, realistic licensed handwriting font installed locally for recurring submitter and copy-verification text.
   - Quality gate: reject fonts that look printed, render missing glyph boxes, or do not support the required Chinese characters.
   - Rendering gate: run a glyph coverage check before export; if the PDF shows square boxes, switch to a verified text-to-transparent-image overlay rather than silently changing to an unapproved font.

3. Chinese artist-signature fonts
   - Purpose: generated Chinese artist signatures when real signature images are unavailable.
   - Recommended behavior: install several different licensed handwriting fonts and rotate them per artist.
   - Quality gate: signature size, baseline, and style should vary; all signatures must stay inside their intended signing area.
   - Rare characters: keep a secondary licensed handwriting/calligraphy fallback list for uncommon Chinese characters, but use it only after confirming glyph coverage and visual quality.

4. Latin signature fonts
   - Purpose: foreign artist signatures when real signature images are unavailable.
   - Recommended behavior: install licensed signature-style Latin fonts locally.
   - Quality gate: reject fonts that are too uniform, too decorative for official materials, or missing accented/foreign characters needed by the performer names.

## Private Font Packaging

For internal company use, keep actual font files in a private package such as:

```text
private-assets/fonts/
  chinese-handwriting/
  chinese-signature/
  latin-signature/
```

Then configure the runtime to load font family names or local paths from a private config file, for example:

```json
{
  "fonts": {
    "official_chinese": ["SimSun", "Songti SC", "Noto Serif CJK SC"],
    "submitter_handwriting": ["Your Licensed Chinese Handwriting Font"],
    "chinese_signature": ["Signature Font A", "Signature Font B"],
    "latin_signature": ["Latin Signature Font A", "Latin Signature Font B"]
  }
}
```

## Public Repository Rule

The public `.gitignore` excludes common font binary extensions:

- `.ttf`
- `.otf`
- `.ttc`
- `.woff`
- `.woff2`

If a truly open font must be included later, add a `LICENSE` file beside it and document the source URL and redistribution terms in this README.
