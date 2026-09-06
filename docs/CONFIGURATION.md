# Configuration

The public config is a placeholder:

```text
skill/live-performance-approval/assets/config/company-profile.example.json
```

For real work:

1. Copy it to a local private file.
2. Fill company names, license numbers, addresses, seal paths, authorities, and default submitter.
3. Keep that local file ignored by Git.

Example:

```bash
cp skill/live-performance-approval/assets/config/company-profile.example.json \
   skill/live-performance-approval/assets/config/company-profile.local.json
```

Then run:

```bash
python3 skill/live-performance-approval/scripts/init_project.py \
  --config skill/live-performance-approval/assets/config/company-profile.local.json \
  --project-dir ./my-project \
  --event-name "Example（示例）" \
  --event-date 2026-11-13 \
  --approval-type auto \
  --subject applicant_a
```

## 2026-09-05：统一主体配置

`applicant_policy.company_key` 指定国内和涉外共同使用的主体。配置 `version`、`effective_date`，并令两个分支的 `applicant_company_key` 与之相同。主体还需 `business_license_path`；场地方由 `venue_company_key` 独立指定。先填本地私有配置，示例占位配置不会通过正式初始化。上传 skill 的主体配置必须与此全称一致。
