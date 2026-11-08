# Round 3 validation (server tape B) feedback log

Validation B is a separate ~12,000 s server tape; uploads return only a result
JSON and a 1 s wealth curve (no market tape). Final = latest successful upload.
Exports are kept locally under
`experiments/round_3/dataathletechamp/20261108-r3-validation-feedback-001/`.

| Upload | File (sha256 prefix) | Public R3 A | Validation B | Notes |
|---|---|---:|---:|---|
| U1 | `r3_informed_follower.py` (1d3f2506) | 270,035 | **272,176** | penalty 0; 874,968 lots; 17/20 positive 600 s blocks; max drawdown -79.5k; last block -61.6k |
| U2 (probe) | `round_2/.../final_maker_seed_from_r1.py` (c1f19466) | -422,816 | **-659,826** | heavy R1 maker; 3/20 positive blocks |

Interpretation:
- The follower earned ~23/s on B versus ~45/s on A: same traded volume
  per second, half the edge per trade. B's informed flow is weaker or
  mean-reverts sooner than A's.
- Heavy passive quoting is toxic on B (-55/s vs -70/s on A), so B is not a
  calm R1-like tape; passive legs must stay small and gated.
- Field context (owner-relayed dashboard chart, 01:49): median best
  validation PnL ~503k, inter-quartile ~180k-800k, 27 teams; owner hears of
  teams near 1.5M.

Next candidate: U3 `r3_combined_regime.py` (111fc83e): follower in high
informed-flow states, FV-gated Q20 maker otherwise; public R3 269,288,
R2 63,328, R1 40,363.
