# Playground / r0

- File: `data/round0/sample.csv`; exact unchanged organizer sample, about one hour.
- Hash/source: `research/materials.json`.
- Official original: `p0-original`, 1878 PnL, 305 fills, penalty 0.
- Team baseline: `p0-zubry`, same 1878 PnL, 305 fills, penalty 0.
- Fix: clear busy state on canceled/rejected IOC, supported by regression tests.
- No observed alpha improvement on this tape; private rounds remain unseen.
- Next: verify server sandbox manually, investigate actual round data when released.
- Reviewer access: pending Write invitation; owner must confirm acceptable arrangement.
- Initial `p0-original` / `p0-zubry` records used the staging path. They remain
  unchanged; the canonical-path runs use `p0-original-r0` / `p0-zubry-r0`.
