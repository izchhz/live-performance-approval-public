# Domestic Workflow

Use this workflow when all on-stage performers are mainland Chinese performers.

## Inputs

- event name and time
- applicant company key from config
- source folder
- mainland ID scans for every on-stage performer
- program list
- lyrics
- videos
- local Word templates
- local seal images

## Materials

Generate the local required set:

```text
00 application form
01 performer roster
02 ID copies
03 venue consent
04 artist consent
05 program list
06 lyrics
07 videos
08 authorization
09 business license
10 fire safety/opening permit
```

## Key Rules

- Extract real performer names from ID scans or the confirmed roster.
- Exclude crew who do not perform on stage.
- Validate mainland ID checksum and warn if expiry is within 6 months.
- Keep ID card image complete; use approximately `85.6mm x 54mm` when possible.
- Translate all foreign text in event names, song titles, lyrics, and media filenames.
- Use the final program list as the order source for lyrics and videos.
- Remove missing-video songs from program/lyrics and re-number when required by local policy.
- Apply seals according to document role, not blindly according to applicant.
