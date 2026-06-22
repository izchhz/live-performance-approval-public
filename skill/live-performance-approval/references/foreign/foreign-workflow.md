# Foreign / HK / Macau / Taiwan Workflow

Use this workflow when any on-stage performer is foreign, Hong Kong, Macau, or Taiwan.

## Inputs

- event name and time
- source folder
- passports or Hong Kong/Macau/Taiwan travel documents
- performer roster
- program list and lyrics
- audio files for every song
- 1-2 videos for a single act, or 1-2 videos per band/act in a split-bill project, unless local policy requires more
- local foreign roster and consent templates

## Performer Documents

Use the document region/nationality:

- foreign passport: country name in Chinese, document type `护照`
- Taiwan: `中国台湾`, document type `台湾居民往来内地通行证`
- Hong Kong: `中国香港`, document type `港澳居民来往内地通行证`
- Macau: `中国澳门`, document type `港澳居民来往内地通行证`

## Passport MRZ Validation

- For foreign passports, read the two MRZ lines from the passport data page before trusting OCR-filled passport fields.
- Validate ICAO Doc 9303 TD3 check digits with Modulus 10 weighting `7, 3, 1`.
- Check passport number, date of birth, date of expiry, optional/personal number where present, and the composite check digit.
- If MRZ is missing, cropped, blurred, or fails validation, do not silently trust OCR. Add the passport to the reminder list for manual review.

## HK / Macau / Taiwan MRZ Validation

- If Hong Kong, Macau, or Taiwan travel documents include MRZ, use MRZ to extract and cross-check identity fields before locking the performer roster.
- Tested Taiwan resident mainland travel permit three-line MRZ supports validation of permit number, expiry date, and date of birth.
- Use the same MRZ Modulus 10 weighting `7, 3, 1` for supported checked fields.
- If MRZ is incomplete, blurred, cropped, unrecognized, or fails validation, add a reminder and manually review the original document image.

## Passport Scan Layout

- Output foreign performer certificate scans as Word files unless the local private workflow says otherwise.
- Put only the certificate/passport scan image itself on the Word page.
- Do not add an extra text name label, heading, or explanatory text inside the page. Keep the performer name in the filename only.
- Passport single page: fit near `125mm x 88mm` when possible.
- Passport double-page spread: fit near `125mm x 176mm` when possible.
- Preserve full content first; do not crop edges, MRZ, photo, validity, signature, or visa areas.

## Artist Consent Signatures

- Prefer real signature images when they are available and count-matched to the performer roster.
- When generating signatures from fonts, use Latin signature fonts for Latin-script names.
- Use Chinese handwriting fonts for Chinese names.
- Do not render all performer names with one uniform font, size, or baseline if the result looks artificial.

## Lyrics and Program

- Create one total program/lyrics Word file.
- Create one Word file per song.
- Foreign lyric headings should contain only sequence number plus song title and translation, for example `01 Song Title（中文译名）`.
- Do not append performer rosters, band member lists, or artist lists after lyric headings.
- If two-column original/translation alignment is unreliable, use single-column layout: original line, then Chinese translation in full-width parentheses.

## Media

- Audio must cover every final song.
- Video usually covers 1-2 songs for a single act.
- For split-bill projects, every band/act should have 1-2 videos represented.
- Output filenames must match the final program list.
- If audio is missing, remove the song from program/lyrics and re-number, then report it.
