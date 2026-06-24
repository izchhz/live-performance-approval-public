---
name: live-performance-approval
description: Generate and QA Chinese commercial performance approval packages for live music projects, including domestic mainland performer approvals and foreign/Hong Kong/Macau/Taiwan performer approvals. Use when Codex needs to classify approval type from performer documents, initialize a project folder, build official Word/PDF materials, normalize performer rosters, translate event/song/lyric/video names, prepare lyric/program files, compress approval media, apply configured company seals, or produce missing-material reminders.
---

# Live Performance Approval

## Load Order

1. Read `references/shared/project-structure.md`.
2. Read `references/shared/configuration.md`.
3. Classify the project with `references/shared/routing.md`.
4. For domestic projects, read `references/domestic/domestic-workflow.md`.
5. For foreign/HK/Macau/Taiwan projects, read `references/foreign/foreign-workflow.md`.
6. Before delivery, read `references/shared/qa-checklist.md`.

## Operating Contract

- Preserve user-provided official templates and page geometry. Do not redesign official files unless the user explicitly asks.
- Create or reuse the standard project folders:

```text
00_项目主档
01_原始资料
02_生成中间文件
03_最终提交材料
04_缺失资料与提醒
```

- Treat `00_项目主档/项目主档.json` or `.yaml` as the source of truth after project setup.
- Do not include non-performing staff in performer lists.
- For domestic `00` application forms and official tables, preserve the trained Word template and page geometry. Do not redraw, simplify, or replace them with hand-built layouts.
- For domestic total-roster files (`00/01/02/03/04/08`), use every actual on-stage performer. For song-specific files (`05/06/07`), use each song's actual performers and log partial-participation songs in reminders.
- Domestic authorization documents should use private-config placeholders for event name, event date, full performer roster, authorized signer, submitter, and seal. Do not hardcode real names in the public package.
- Before rendering handwriting or signature text, check that the configured font covers every required character. If the output shows missing-glyph boxes, clipping, or overflow, stop and fix the font/rendering path before delivery.
- Translate all foreign text in event names, song titles, lyrics, and media filenames, and keep translations consistent.
- For foreign passports, validate ICAO Doc 9303 TD3 MRZ fields before trusting OCR-filled passport number, date of birth, or expiry. Report missing, cropped, blurred, or failed MRZ for manual review.
- For HK/Macau/Taiwan travel documents, run MRZ validation when MRZ is present and supported; tested Taiwan permit MRZ can validate permit number, expiry date, and date of birth.
- For foreign lyric headings, keep only sequence number plus song title/translation. Do not append performer rosters, band member lists, or artist lists after the heading.
- For foreign split-bill projects, count video requirements per band/act; each band usually needs 1-2 videos.
- For foreign performer certificate scan Word files, place only the certificate/passport scan image on the page. Do not add extra text name labels, headings, or explanatory text inside the page.
- For foreign artist consent signatures, use Latin signature fonts for Latin-script names and Chinese handwriting fonts for Chinese names unless real signature images are available and count-matched.
- Do visual QA after DOCX/PDF generation. Check page count, seal placement, signatures, highlights, ID/passport completeness, and text overflow.
- This public package contains placeholders only. Each organization must add its own private templates, seals, company profile, and authorized signer documents locally.

## Useful Scripts

```bash
python3 scripts/check_environment.py
python3 scripts/init_project.py --config assets/config/company-profile.example.json --project-dir <项目目录> --event-name <演出名称> --event-date <YYYY-MM-DD> --approval-type auto --subject <company-key>
python3 scripts/validate_cn_id.py --name <姓名> --id <身份证号> --expiry <YYYY-MM-DD>
python3 scripts/compress_approval_videos.py --program-list <节目单.docx> --source-dir <视频目录>
python3 scripts/scrub_docx_metadata.py <file.docx>
```

## Privacy Rule

Never commit real seals, identity documents, passports, phone numbers, private addresses, signatures, completed approval examples, or real company license numbers to a public repository.
