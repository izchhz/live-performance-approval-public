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

## 5. QA

Render DOCX/PDF outputs and inspect:

- page geometry
- seal placement
- document count
- ID/passport completeness
- signature layout
- translation consistency
- media filenames and compression parameters

## 6. Deliver

Deliver only `03_最终提交材料` plus reminder files from `04_缺失资料与提醒` when relevant.
