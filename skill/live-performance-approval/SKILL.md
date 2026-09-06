---
name: live-performance-approval
description: Prepare and verify Chinese commercial performance approval materials, route domestic or foreign/Hong Kong/Macau/Taiwan projects from performer evidence, and hand verified files to a separate portal-upload skill.
---

# Live Performance Approval

Use the configured applicant for both domestic and foreign projects. Applicant policy does not determine the approval branch, venue operator, actual venue, or document-specific seals.

## Start with the requested outcome

- For a new project, read [configuration](references/shared/configuration.md) and [routing](references/shared/routing.md), then initialize its master file. `auto` is unresolved until performer evidence establishes a branch; do not treat it as domestic.
- For a resumed project or a targeted correction, read its master file and current evidence first. Use [execution and recovery](references/shared/execution-contract.md) to check the applicant policy and stale inputs. Open only the workflow and document references affected by the request.
- For domestic materials, read the [domestic workflow](references/domestic/domestic-workflow.md). For foreign or mixed performer projects, read the [foreign workflow](references/foreign/foreign-workflow.md). Preserve these branches' different lyrics, media, handwriting, certificates, and templates.
- For delivery, use the [QA checklist](references/shared/qa-checklist.md). For webpage filling or uploads, use the separately installed `performance-approval-upload` skill and its current branch template; material QA alone never establishes portal readiness.

## Working rules

1. Keep source evidence and unresolved conflicts in the [project master](references/shared/project-structure.md). Do not infer nationality, consent, a missing ID field, or final program changes from filenames or an old example.
2. Use local OCR/MRZ, hashes, document parsers, and media tools where they help. Reuse unchanged verified results; inspect original scans when extraction is missing, ambiguous, or fails validation. OCR success is not proof of identity or consent.
3. Preserve official Word templates and page geometry. Export matching Word/PDF versions, then inspect the relevant rendered pages; successful conversion does not prove layout or correct seals.
4. A changed applicant, program, source file, template, or seal invalidates dependent outputs. Mark old outputs stale and regenerate only affected materials. Keep originals and unresolved reminders available.
5. Use already authorized actions without repeated confirmation. Ask only for consequential missing facts or authority; continue independent work. Missing media is a reported gap until an applicable user instruction authorizes removing a song.
6. This public package contains generic scripts and placeholders. Real configuration, templates, seals, certificates, identity materials, handwriting fonts and signed examples belong in a private local installation. Missing private assets are a setup gap, not permission to invent them.

## Commands

```bash
python3 scripts/check_environment.py
python3 scripts/init_project.py --config assets/config/company-profile.local.json --project-dir <project-dir> --event-name <event-name> --event-date <YYYY-MM-DD> --approval-type auto
python3 scripts/applicant_policy.py --config assets/config/company-profile.local.json --project-dir <project-dir>
python3 scripts/prepare_agent_context.py --project-dir <project-dir> --source-dir <source-dir> --extract-text
```

Add `--scan-cn-id` or `--scan-mrz` only for relevant unverified identity inputs. The public package is a workflow foundation; production materials require locally supplied and verified templates and generator integration.
