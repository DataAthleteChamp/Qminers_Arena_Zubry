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

## New v2 tape and submission candidate

- `sample_v2.csv` has different multi-order microstructure; v1 flow baseline loses.
- Exact tested `strategies/zubry_v2.py`: midpoint maker, two-lot quotes,
  20-lot internal cap, inventory skew, depth overlay default-disabled.
- Actual v2 PnL **10395**, 7528 filled orders, penalty zero; reproduced exactly.
- Depth overlay scored 8992; retained but not selected.
- Freeze: `submissions/playground/cae618bb5b61/strategy.py`.
- All 16 tests pass. Human server validation/upload and Final confirmation remain.
- These are consumed public-tape comparisons, not private-round evidence.
