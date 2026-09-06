# Live Performance Approval · Sanitized Public Package

Version: `v2026.09.06.1` · [中文](README.md) · [Changelog](CHANGELOG.md)

Two Codex skills cover preparation and portal handoff for domestic and foreign/Hong Kong/Macau/Taiwan performance approvals. This repository contains generic workflows, reusable scripts and placeholder configuration. Supply and verify your own private templates, company credentials, seals, certificates and fonts before production use.

Both branches now use one configured applicant. Routing, venue roles and branch-specific material requirements remain separate. The update adds concise task routing, applicant-policy validation/migration, stale-output handling, and staged portal validation tied to the current session, account, draft and material digest.

Install both directories under `skill/` into your local Codex skills directory. Copy the material skill's example profile to an ignored `company-profile.local.json`, complete it, and configure the upload skill's local applicant policy as explained in its handoff reference. Placeholder values intentionally fail production initialization.

`--approval-type auto` remains unresolved until performer evidence determines the branch. Existing project migration preserves originals and marks affected outputs stale; signed or sealed documents may require reissue. Materials passing QA are still subject to a separate live-portal check.

Public release checks use a text-file allowlist, a private denylist kept outside this repository, and reachable Git-blob auditing. A documented exact historical-blob exception covers previously published branding that has already been removed; it never exempts current files or credentials. No private binary assets are included.
