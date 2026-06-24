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
