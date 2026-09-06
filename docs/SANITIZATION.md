# Sanitization Policy

This public repository must not contain:

- real company names, addresses, license numbers, or tax/business registration files
- real company seals or seal scans
- real identity cards, passports, travel permits, or visas
- phone numbers, private addresses, personal names of submitters, authorized signers, or legal representatives
- real signatures
- fixed identity-proof attachments, completed authorization letters, business licenses, fire permits, or similar private attachment files
- completed approval cases
- private lyrics, media, contracts, invoices, or government feedback
- Git history containing any of the above

## Recommended Workflow

Use two repositories or two unrelated histories:

- private repository/branch: real company data and seals
- public repository/branch: placeholders and examples only

Do not create a public branch by committing private files first and deleting them later. Deleted files remain in Git history.

## Pre-Push Scan

Before pushing public code:

```bash
rg -n "REAL_COMPANY|身份证|护照|公章|营业执照|消防|法定代表|授权人|经办人|手机号|330101|浙演经|杭州" .
find . -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.pdf" -o -name "*.docx" \) -print
```

Review every binary file manually before publishing.

## 自动发布检查（2026-09-05）

在仓库外保存私有值 JSON 列表，执行：

```bash
python3 scripts/verify_public_package.py . --denylist /private/path/denylist.json --history --history-exceptions docs/public-history-exceptions.json
```

扫描当前文件、符号链接、非白名单资产、Unicode 转义值及可达 Git blobs。历史豁免只对应已审阅的特定不可变 blob、路径和类别；不适用于当前文件，也不豁免密钥。不要把私有 denylist 或包含真实业务内容的测试输出提交到公开仓库。公私版本保持独立历史。
