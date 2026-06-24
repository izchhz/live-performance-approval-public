# Changelog

## v2026.06.24.1

### Added

- Added domestic template-preservation rules for the `00` application form: agents must use trained Word templates and preserve page geometry instead of redrawing official tables.
- Added total-roster versus per-song performer rules for domestic projects: total-roster documents use all actual on-stage performers, while program, lyric, and media filenames use the actual performers for each song.
- Added stronger handwriting-font QA guidance: configured submitter, verification, and authorization-signature fonts must pass glyph coverage checks and must not render missing-glyph boxes.
- Added public sanitization checks for authorized signer names, fixed identity attachments, business-license documents, fire-permit documents, private seals, and completed private samples.

### Sanitization

- Removed project README wording that contained organization-specific branding and personal-style contact references.
- Reconfirmed that the public package remains documentation, scripts, placeholders, and example config only.

## v2026.06.22.2

### Added

- Added MRZ validation support guidance for Hong Kong/Macau/Taiwan travel documents when MRZ is present.
- Recorded a successful Taiwan resident mainland travel permit MRZ test: permit number, expiry date, and date of birth can be checked with Modulus 10 weighting `7, 3, 1`.
- Added a workflow optimization note: treat MRZ validation as part of the identity-data lock step before generating downstream files.

### Validation

- The local `validate_mrz.py` helper now supports TD3 passport MRZ and three-line mainland travel permit MRZ used by tested Taiwan permit samples.

## v2026.06.22.1

### Added

- Added the missing public changelog note for foreign passport MRZ validation: passport data should be cross-checked with ICAO Doc 9303 TD3 MRZ fields and Modulus 10 weighting `7, 3, 1` before trusting OCR for passport number, date of birth, or expiry.
- Added a foreign lyrics-title policy: lyric headings keep only sequence number plus song title and translation, and must not append performer rosters, band member lists, or artist lists.

### Scope

- The new lyrics-title policy applies only to foreign/HK/Macau/Taiwan approval lyric materials. Domestic lyric materials are unchanged.

## v2026.06.17.1

### Added

- Added a foreign split-bill media policy: each band/act in a split-bill foreign approval package should have 1-2 compressed video materials, rather than treating the whole event as needing only 1-2 videos.
- Added a foreign certificate-scan page policy: performer certificate scan Word files should contain only the certificate/passport scan image itself, with no extra text name label, heading, or explanatory text inside the page.
- Added a mixed-language artist-consent signature policy: generated signatures should use Latin signature fonts for Latin-script names and Chinese handwriting fonts for Chinese names, with real signature images preferred when available.

### Sanitization

- Reconfirmed that the public package keeps only placeholders, scripts, and documentation.
- Real company names, seals, IDs, passports, business licenses, fire permits, signatures, completed cases, and private contact details remain excluded from the public repository.
