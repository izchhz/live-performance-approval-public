# Live Performance Approval Automation

中文说明：see [README.md](README.md).

Current public version: `v2026.06.22.2`. See [CHANGELOG.md](CHANGELOG.md).

This repository packages an AI-agent workflow for preparing Chinese commercial performance approval materials for live music projects.

It supports two routing branches:

- **Domestic approval**: all on-stage performers use mainland China resident ID cards.
- **Foreign/HK/Macau/Taiwan approval**: any on-stage performer uses a foreign passport or Hong Kong/Macau/Taiwan travel document.

This public repository is sanitized. It does not include real company seals, real company licenses, completed approval cases, IDs, passports, signatures, or private contact information.

## Repository Layout

```text
docs/                                  Human-facing GitHub documentation
skill/live-performance-approval/       Codex skill folder
skill/live-performance-approval/scripts
skill/live-performance-approval/references
skill/live-performance-approval/assets
```

## Quick Start

1. Install system dependencies listed in [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).
2. Copy `skill/live-performance-approval/assets/config/company-profile.example.json` to a private local config file.
3. Add your local Word templates under `skill/live-performance-approval/assets/templates/`.
4. Install or configure local fonts as described in `skill/live-performance-approval/assets/fonts/README.md`.
5. Add seal images only in a private local branch or untracked local file area.
6. Ask an agent to use `skill/live-performance-approval` to initialize a project and generate approval materials.

Example:

```bash
python3 skill/live-performance-approval/scripts/check_environment.py
python3 skill/live-performance-approval/scripts/init_project.py \
  --config skill/live-performance-approval/assets/config/company-profile.example.json \
  --project-dir ./example-project \
  --event-name "Example Band（示例乐队）2026 Tour" \
  --event-date 2026-11-13 \
  --approval-type auto \
  --subject applicant_a
```

## Safety Boundary

Do not push private data to a public Git remote. Use a separate private repository or private branch with no shared public history for real company materials.

See [docs/SANITIZATION.md](docs/SANITIZATION.md).

## v2026.06.22.2 Policy Updates

- When Hong Kong/Macau/Taiwan travel documents contain MRZ, use MRZ to extract and cross-check identity fields.
- Tested Taiwan resident mainland travel permit three-line MRZ: permit number, expiry date, and date of birth can be validated.
- Workflow optimization: lock identity data after OCR, MRZ validation, and reminder logging before generating downstream `01/02/03/04` files.

## v2026.06.22.1 Policy Updates

- Added the missing public update note for foreign passport MRZ validation: passport information should be checked against ICAO Doc 9303 TD3 MRZ fields with Modulus 10 weighting `7, 3, 1` before filling passport number, date of birth, or expiry.
- Foreign lyric headings should keep only sequence number plus song title and translation. Do not append performer rosters, band member lists, or artist lists after song titles.
- This lyric-heading change applies only to foreign/HK/Macau/Taiwan lyric materials. Domestic lyric materials are unchanged.

## v2026.06.17.1 Policy Updates

- For foreign split-bill projects, video requirements are counted per band/act: each band usually needs 1-2 videos, rather than the whole event needing only 1-2 videos.
- For foreign `02` performer certificate scan Word files, the page should contain only the certificate/passport scan image itself. Do not add an extra name label, heading, or explanatory text inside the page; keep the name in the filename only.
- For foreign `04` artist consent letters, generated signatures should follow the script of the name: Latin-script names use Latin signature fonts, Chinese names use Chinese handwriting fonts. Real signatures remain preferred when available and count-matched.
