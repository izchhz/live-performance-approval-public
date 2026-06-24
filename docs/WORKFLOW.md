# Workflow

## 1. Scan Inputs

Collect:

- event name and performance time
- applicant company key
- source folder
- performer identity documents
- program list and lyrics
- video/audio files
- local templates and seals

## 2. Route Approval Type

- Domestic: every on-stage performer uses a mainland China resident ID card.
- Foreign/HK/Macau/Taiwan: any performer uses a passport or Hong Kong/Macau/Taiwan travel document.

## 3. Initialize Project

Create:

```text
00_项目主档
01_原始资料
02_生成中间文件
03_最终提交材料
04_缺失资料与提醒
```

`00_项目主档` is the source of truth after initialization.

## 4. Generate Materials

Domestic materials usually include:

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

Domestic `00` application forms and official tables must preserve the trained Word template fields, table sizing, and page geometry. Do not redraw or simplify official documents as custom layouts.

Domestic performer rosters have two layers:

- `00/01/02/03/04/08` use all actual on-stage performers.
- `05/06/07` use each song's actual participating performers. If a song uses only part of the roster, record that exception in the reminder file.

Domestic authorization fields, submitter labels, authorized signer names, verification text, and seal placement should come from private local configuration. The public package keeps placeholders and execution rules only.

Foreign/HK/Macau/Taiwan materials usually include:

```text
01 performer roster
02 performer document scans
03 venue consent
04 artist consent
program list and lyrics
video/audio files
```

Local regulations vary. Keep policy-specific requirements in configuration and references.

Foreign passport fields should be validated against ICAO Doc 9303 TD3 MRZ check digits before trusting OCR. Missing, cropped, blurred, or failed MRZ should be reported for manual review.

HK/Macau/Taiwan travel documents should also use MRZ extraction and validation when MRZ is present and supported. Tested Taiwan permit MRZ can validate permit number, expiry date, and date of birth.

Workflow optimization: lock identity data after OCR, MRZ validation, and reminder logging before generating downstream `01/02/03/04` files.

Foreign split-bill projects need media checks per band/act: each band usually needs 1-2 compressed videos, while audio should cover every final song.

Foreign performer document scans should not include extra page labels. The Word page should contain only the certificate/passport scan image itself; keep performer names in filenames and structured rosters.

Foreign lyric headings should keep only sequence number plus song title/translation. Do not append performer rosters or band member lists after the heading.

## 5. QA

Render DOCX/PDF outputs and inspect:

- page geometry
- seal placement
- document count
- ID/passport completeness
- foreign passport and HK/Macau/Taiwan MRZ validation status
- signature layout
- configured handwriting/signature fonts render without missing-glyph boxes, clipping, or overflow
- domestic total-roster and per-song performer lists are correctly separated
- translation consistency
- foreign lyric heading format
- media filenames and compression parameters
- for foreign split-bill projects, per-band video coverage
- for foreign consent letters, Latin names use Latin signature fonts and Chinese names use Chinese handwriting fonts unless real signatures are available

## 6. Deliver

Deliver only `03_最终提交材料` plus reminder files from `04_缺失资料与提醒` when relevant.
