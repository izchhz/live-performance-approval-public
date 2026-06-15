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
- If a song lacks required media, remove it from all relevant output lists and re-number.
- If translation is needed, keep one translation map and reuse it everywhere.

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
- passport/travel document validity cannot be read
- generated PDF/DOCX visually overflows or has wrong page count
- public branch contains private data
