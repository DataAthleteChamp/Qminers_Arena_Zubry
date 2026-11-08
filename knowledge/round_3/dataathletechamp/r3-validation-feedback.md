# Round 3 validation (server tape B) feedback log

Validation B is a separate ~12,000 s server tape; uploads return only a result
JSON and a 1 s wealth curve (no market tape). Final = latest successful upload.
Exports are kept locally under
`experiments/round_3/dataathletechamp/20261108-r3-validation-feedback-001/`.

| Upload | File (sha256 prefix) | Public R3 A | Validation B | Notes |
|---|---|---:|---:|---|
| U1 | `r3_informed_follower.py` (1d3f2506) | 270,035 | **272,176** | penalty 0; 874,968 lots; 17/20 positive 600 s blocks; max drawdown -79.5k; last block -61.6k |
| U2 (probe) | `round_2/.../final_maker_seed_from_r1.py` (c1f19466) | -422,816 | **-659,826** | heavy R1 maker; 3/20 positive blocks |
| U3 | `r3_combined_regime.py` (111fc83e) | 269,288 | **258,688** | regime gate + Q20 maker; switched the follower off in profitable B stretches |
| U4 | `r3_alpha_follower_p1_sw3.py` (e4dfd2ce) | 330,208 | **411,302** | P1 ridge flip gate + 3-tick sweep trigger; R2 109,317; ordinary seconds +467.2k (38.9/s), 26 jump seconds -55.9k |
| U5 (optional probe) | `r3_aged_maker_best.py` (24fc7515) | 35,027 | not reported | aged maker alone; tests passive quoting on B |
| U6 | `r3_alpha_follower_p1_sw3_rlin0.py` (e3102973) | 357,488 | **415,828** | alpha ridge refit on full R3 + R2, intercept 0; ordinary seconds +509.3k (42.4/s), 27 jump seconds -93.4k; better than U4 in 12 of 20 blocks |
| U7 | `r3_follower_u7_flow_deepfv.py` (d2a0fc9c) | 413,588 | **538,844** | U6 + 600-lot/200 ms flow trigger + deep-insert FV flow trigger; ordinary seconds +610.7k (50.9/s), 30 jump seconds -71.8k; better than U6 in 17 of 20 blocks (owner export folder `results_jumps_maciej`; class AlphaFollower) |
| U8 (not uploaded) | `r3_follower_u8.py` (0075a2bf) | 415,883 | – | U7 with TRIG1 flow 200, 6 s hold, 8 s flow hold; +1.2% over seven tapes |

**Final (private C, 12,000 s):** U7 was the last upload. It scored
**+589,202, rank 34 of 53**, against 538,844 on B (C/B = 1.09). The
private leaderboard top was 1,458,005, 10th 929,224, the median (27th) 724,745
and the last −2,192. See `round3-retrospective.md`.

Interpretation:
- The follower earned ~23/s on B versus ~45/s on A at the same traded
  volume per second. Splitting B's 1 s wealth curve by |ΔPnL| shows why:
  ordinary seconds earned **+406.5k (33.9/s)**, while the 29 seconds with
  |ΔPnL| >= 3,000 lost **-134.3k** (10 positive). Seconds 11,525-11,526 alone
  lost -70.7k (moves of ~270 and ~440 ticks against a 100-lot position).
  Same split on public tapes: R3 A D1 ordinary 46.1/s, jump seconds -6.7k
  (9 s); R2 D1 ordinary 7.5/s, jump seconds -19.1k (12 s). Pooled, 31 of 50
  jump seconds went against the follower (z ~ 1.7, weak). B's per-second
  |ΔPnL| quantiles match A's (q50 100, q90 400, q99 ~1,250) but its kurtosis
  is 1,988 vs 206: B has far larger rare jumps, not a higher ordinary
  volatility. Inferring B's ordinary volatility from wealth CSV is only
  valid here because the follower holds about ±100 nearly all the time.
- Heavy passive quoting is toxic on B (-55/s vs -70/s on A), so B is not a
  calm R1-like tape; passive legs must stay small and gated.
- Field context (owner-relayed dashboard chart, 01:49): median best
  validation PnL ~503k, inter-quartile ~180k-800k, 27 teams; owner hears of
  teams near 1.5M. By ~03:10 the owner reported a median of ~906k, and
  ~1.3M later.
- **Correction after the round:** we suggested these were best-of-uploads on
  one heavy-tailed tape or fits to B's wealth curve. The private leaderboard
  disproved it: 33 teams beat our +589,202 on the unseen tape C, and the top
  team made 1.46M. Treat field scores as evidence of a real edge.

Scripts for the decomposition:
`experiments/round_3/dataathletechamp/20261108-r3-ioc-limit-structure-001/`
(`validation_pnl_stats.py`, `validation_jump_seconds.py`,
`jump_second_decomposition.py`), run with `python3` from the repository root.
