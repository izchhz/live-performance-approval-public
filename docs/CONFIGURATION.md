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
