# Project Structure

Every approval run must use the same folder layout so different agents can resume work without reconstructing context.

```text
<project>/
├── 00_项目主档
├── 01_原始资料
├── 02_生成中间文件
├── 03_最终提交材料
└── 04_缺失资料与提醒
```

## Folder Rules

- `00_项目主档`: canonical project data, performer roster, translations, stage decisions, and generation parameters.
- `01_原始资料`: source files or source indexes. Do not overwrite the user's only copy.
- `02_生成中间文件`: scripts, render previews, temporary conversions, debug images, PDF QA pages, and caches.
- `03_最终提交材料`: only submission-ready files.
- `04_缺失资料与提醒`: missing material reports, media mismatch logs, excluded staff, ID/passport warnings, and content edits.

Domestic final files usually include `00` through `10`. Foreign final files may omit the `00` application form depending on local policy and configuration.
