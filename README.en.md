# Live Performance Approval Automation

中文说明：see [README.md](README.md).

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
