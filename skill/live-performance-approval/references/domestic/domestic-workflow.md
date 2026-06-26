# Domestic Workflow

Use this workflow when all on-stage performers are mainland Chinese performers.

## Inputs

- event name and time
- applicant company key from config
- source folder
- mainland ID scans for every on-stage performer
- program list
- lyrics
- videos
- local Word templates
- local seal images

## Materials

Generate the local required set:

```text
00 application form
01 performer roster
02 ID copies
03 venue consent
04 artist consent
05 program list
06 lyrics
07 videos
08 authorization
09 business license
10 fire safety/opening permit
```

## Key Rules

- Extract real performer names from ID scans or the confirmed roster.
- Before asking an agent to visually read ID-card images, run local OCR:

```bash
python3 scripts/scan_cn_id_ocr.py --project-dir <project-dir> --source-dir <source-dir>
```

- The OCR report is written to `02_生成中间文件/cn_id_ocr/`. Use it to review recognized names, ID numbers, checksum status, validity period, renewal warnings, and manual-review flags.
- Exclude crew who do not perform on stage.
- Preserve the trained Word templates for official files, especially `00` application forms. Do not redraw table layouts or change official wording unless the user asks.
- Use all actual on-stage performers in total-roster documents (`00/01/02/03/04/08`).
- Use each song's actual participating performers in program, lyric, and media filename materials (`05/06/07`). When a song uses only part of the roster, write it in the reminder file.
- Validate mainland ID checksum and warn if expiry is within 6 months.
- Keep ID card image complete; use approximately `85.6mm x 54mm` when possible.
- Translate all foreign text in event names, song titles, lyrics, and media filenames.
- Use the final program list as the order source for lyrics and videos.
- Remove missing-video songs from program/lyrics and re-number when required by local policy.
- Apply seals according to document role, not blindly according to applicant.
- Render submitter labels, copy-verification text, and authorization signatures with configured handwriting fonts after glyph coverage checks. Missing-glyph boxes or signature overflow are delivery blockers.
