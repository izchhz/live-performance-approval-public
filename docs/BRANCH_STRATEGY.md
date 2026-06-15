# Branch Strategy

Use separate histories for private and public material.

Recommended local layout:

```text
live-performance-approval-private   branch: private-local
live-performance-approval-public    branch: public-github
```

The public repository must not be created by deleting private files from a private branch. Git keeps deleted files in history.

## Publishing Public GitHub

1. Work only inside `live-performance-approval-public`.
2. Run the sensitive scans in `docs/SANITIZATION.md`.
3. Review all binary files manually.
4. Push only the `public-github` branch or rename it to `main` in a clean public remote.

## Private Local

Keep real templates, seals, company configuration, and completed cases in a private repository or encrypted storage.
