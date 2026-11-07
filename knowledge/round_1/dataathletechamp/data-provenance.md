# Round 1 data provenance

The user supplied `data/round1/round1.csv` and confirmed the download complete.
This checkpoint records storage and integrity only: no Round 1 market analysis,
model fitting or strategy evaluation has been performed.

## Shared data

- Working CSV: `data/round1/round1.csv`, 161,219,988 bytes.
- Git archive: `data/round1/round1.csv.gz`, 36,594,963 bytes.
- Checksums for both files: `data/round1/round1.sha256`.
- The CSV exceeds GitHub's 100 MiB regular-file limit. It remains unchanged
  locally and is ignored; the lossless compressed copy is shared in the private repo.
- Compression used Python gzip, level 6, empty embedded filename and `mtime=0`.
  The decompressed archive's SHA-256 was verified against the original CSV.

CSV SHA-256:
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`

Archive SHA-256:
`ba5468336f850e42c3834b093d78b41adb6fdf867e5cf0cde6d4c5da2eca1acd`

These identify the received local bytes. No organizer-provided reference
checksum was supplied, so they do not independently authenticate the download.

## Restore on another machine

Only decompress when the working CSV is absent; do not overwrite an existing
raw input.

```bash
uv run --locked python -m gzip -d data/round1/round1.csv.gz
uv run --locked python -c "from pathlib import Path; from tools.common import sha256; print(sha256(Path('data/round1/round1.csv')))"
```

The printed CSV fingerprint must match the checksum above before research begins.
