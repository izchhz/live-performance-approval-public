# Agent Runbook

This runbook is written for AI agents using the skill.

## Required First Pass

1. Read `skill/live-performance-approval/SKILL.md`.
2. Read `references/shared/project-structure.md`.
3. Read `references/shared/configuration.md`.
4. Read `references/shared/routing.md`.
5. Inspect the source folder with file listing commands.
6. Create or update the project master before generating documents.

## Decision Points

- If any performer is foreign/HK/Macau/Taiwan, switch to the foreign workflow.
- If a name field asks for performers, use real on-stage performer names, not the band name.
- For domestic `00` application forms and official tables, use the trained Word templates and preserve page geometry; do not redraw, simplify, or re-layout official documents.
- For domestic `00/01/02/03/04/08`, use all actual on-stage performers. For domestic `05/06/07`, use each song's actual participating performers and log partial-participation songs in reminders.
- If a song lacks required media, remove it from all relevant output lists and re-number.
- If translation is needed, keep one translation map and reuse it everywhere.
- Domestic authorization, verification text, submitter labels, authorized signer names, and seals must come from private configuration, not hardcoded real names in the public package.
- Check configured handwriting/signature font glyph coverage before rendering; stop if output shows missing-glyph boxes, clipping, or overflow.
- For foreign split-bill projects, count video requirements per band/act; each band usually needs 1-2 videos.
- For foreign passports, validate ICAO Doc 9303 TD3 MRZ fields before trusting OCR-filled passport number, date of birth, or expiry. Report missing, cropped, blurred, or failed MRZ for manual review.
- For HK/Macau/Taiwan documents, run MRZ validation when MRZ is present and supported. Tested Taiwan permit MRZ can validate permit number, expiry date, and date of birth.
- Lock identity data after OCR, MRZ validation, and reminder logging before generating downstream `01/02/03/04` files.
- Foreign lyric headings keep only sequence number plus song title/translation. Do not append performer rosters or band member lists after the heading.
- For foreign performer certificate scan Word files, place only the certificate/passport scan image on the page; do not add an extra name label, heading, or explanatory text.
- For foreign artist consent signatures, use Latin signature fonts for Latin-script names and Chinese handwriting fonts for Chinese names unless real signatures are available and count-matched.

## Output Rules

- Final files go to `03_最终提交材料`.
- Intermediates and QA images go to `02_生成中间文件`.
- Missing-material and correction reports go to `04_缺失资料与提醒`.
- Do not delete or rewrite original user materials.

## Stop Conditions

Stop and report when:

- required local templates are missing
- a document scan is incomplete or unreadable
- ID checksum validation fails
- the `00` application form or other official template has been redrawn or visibly reflowed
- submitter labels, verification text, or authorization signatures show missing-glyph boxes, missing characters, clipping, or overflow
- passport/travel document validity cannot be read, or document MRZ is missing, cropped, blurred, or fails validation
- a foreign split-bill band/act does not meet the video material requirement
- generated PDF/DOCX visually overflows or has wrong page count
- public branch contains private data
