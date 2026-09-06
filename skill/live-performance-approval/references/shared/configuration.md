# Configuration

Load company, venue, submitter, seal, and authority data from a local config file:

```text
assets/config/company-profile.example.json
```

For real use, copy it to a private untracked file, for example:

```text
assets/config/company-profile.local.json
```

Do not hardcode company names, addresses, license numbers, or seal paths inside generation scripts when a config value exists.

## Required Keys

- `default_submitter.name`
- `companies.<key>.legal_name`
- `companies.<key>.performance_license_no`
- `companies.<key>.registered_address`
- `companies.<key>.seal_path`
- `domestic.approval_authority`
- `foreign.approval_authority`
- `foreign.applicant_company_key`
- `foreign.venue_company_key`

## Public Repository Rule

Do not commit real company names, license numbers, addresses, seals, identity documents, signatures, completed examples, or private contact information.

## Unified applicant policy

Configure `applicant_policy.company_key`, `version`, and `effective_date`. Both `domestic.applicant_company_key` and `foreign.applicant_company_key` must select that same company. Add its `business_license_path` alongside its legal name, license, address and seal. Venue company keys remain independent. Placeholder profiles intentionally fail real initialization; fill an ignored local profile first. Never keep a second applicant active only because an old example used it.
