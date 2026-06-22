# Changelog

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
