# Round 4: DEEP8 deep-G-insert trigger on U2 (rejected)

Experiment `experiments/round_4/dataathletechamp/20261108-r4-deep8-001` (gitignored; grids, runner
outputs, snapshots and README with exact commands). Strategy file
`strategies/round_4/dataathletechamp/r4_follower_deep8.py` (defaults off = U2 exactly).

## Question

The bot-forensics study (`20261108-r4-bot-forensics-001` REPORT section 5, note `r4-bot-fingerprints.md`)
found that new resting market (G) inserts 8–20 ticks behind their own best ("DEEP8") precede strong moves
in the opposite direction of the order's side. The R4 1 s residual was about +5.4 ticks on both halves and
the touch-to-touch gain was +6 per lot at 1 s. Does this give U2 (`r4_u2_trig2_ungated.py`,
sha256 b239d85a…) extra PnL in the official engine?

Pre-declared acceptance, paired against U2 on the same tapes:

- R4 ≥ U2 + 25,000;
- R3 ≥ 415,404;
- R2 ≥ U2 − 10,000;
- penalty 0.

## Mechanism and flags (all default off)

- **Detection** hooks TRIG2's `k > 7` clip inside `_t2_side`. This adds no extra pass over the book.
  - The order must be a new market order (id > TRIG2's max id).
  - Its offset `k` is measured against the market best of the previous event: bid `best_bid − price`,
    ask `price − best_ask`.
  - The event counts if `DEEP8_MIN ≤ k ≤ DEEP8_MAX`. The implied direction is `d = −side`.
  - It requires `TRIG2_ON` and `DEEP8_MIN ≥ 8`; otherwise the class raises `ValueError`.
- **`DEEP8_MODE`:**
  - `"signal"` calls `_on_signal(t, d, DEEP8_GATED)`. It ranks after A / FLOW and before TRIG1 / TRIG2.
    `DEEP8_COUNT = 2` requires a second same-d event within `DEEP8_COUNT_MS` (300).
  - `"block"`: for `DEEP8_BLOCK_MS` after an event with direction d, any signal that would flip the target
    d → −d is ignored. With `DEEP8_BLOCK_ENTRY`, entries from flat to −d are ignored too.
  - `"both"` applies signal and block.
- **`TRIG2_K8`** (optional item) gives TRIG2 inserts with k ≥ 8 their own cell (`T2_K8TAB`) instead of the
  k = 7 cell.
  - The values were estimated on full R3 + R2 public only, never R4 (`k8_table.py`). The method matches
    `latent.py` `class_table`: y = side × (mid after t + 1 s − mid after t), own best taken before the
    insert, spread clipped to [1, 3], n ≥ 200.
  - At spread 1 the k ≥ 8 cell is bid −7.97 (n 1,109) and ask −6.48 (n 833). The current k = 7 cell (R3 fit
    half, k ≥ 7 merged) is −3.77 / −2.28. Exact k = 7 pooled R3 + R2 gives −2.27 / −1.94.
  - Spread 2 and 3 have n < 200, so those cells keep the existing k = 7 values.
  - Variant `k8_re7` also replaces the k = 7 cells with the exact-k = 7 pooled estimates.

## Data and code

- **Tapes:**
  - R4 `data/round4/round4_public.csv`, sha256 61c0b6d1…
  - R3 `round3_public.csv`, 1021586b…
  - R2 `round2_public.csv`, 88ff641e…
- **Simulator:** `simulator/simulator.py`, c37b2262….
- **Runner:** `20261108-r4-runner-001/runner.py`. Official engine in-process: 5 ms latency, depth 20,
  ±100 position limit, 10,000/s penalty. Full tapes.
- **Strategy:** sha256 b62fad7b… for the final file (grid 2 and timing). Grid 1 ran the earlier snapshot
  3a157d80…, which lacked the K8 code. Both reproduce U2 exactly with defaults off:
  886,626 / 415,404 / 159,515.

## Results (official engine, penalty 0 everywhere; deltas vs U2)

| variant | R4 | ΔR4 | R3 | ΔR3 | R2 | ΔR2 | R4 + blocks |
|---|---:|---:|---:|---:|---:|---:|---:|
| U2 (defaults off) | 886,626 | 0 | 415,404 | 0 | 159,515 | 0 | 10/10 |
| signal MIN 8 gated | 881,514 | −5,112 | 411,659 | −3,745 | 136,553 | −22,962 | 10/10 |
| signal MIN 8 ungated | 870,136 | −16,490 | 409,947 | −5,457 | 126,091 | −33,424 | 10/10 |
| signal MIN 10 gated | 885,774 | −852 | 415,641 | +237 | 158,231 | −1,284 | 10/10 |
| signal MIN 10 ungated | 888,581 | +1,955 | 417,461 | +2,057 | 141,539 | −17,976 | 10/10 |
| signal MIN 12 gated | 884,694 | −1,932 | 415,004 | −400 | 159,515 | 0 | 10/10 |
| signal MIN 12 ungated | 885,166 | −1,460 | 416,421 | +1,017 | 147,024 | −12,491 | 10/10 |
| signal MIN 8 ungated, COUNT 2 | 888,142 | +1,516 | 416,376 | +972 | 176,307 | +16,792 | 10/10 |
| block MIN 8, 200 ms | 883,646 | −2,980 | 412,600 | −2,804 | 157,195 | −2,320 | 10/10 |
| block MIN 8, 500 ms | 872,597 | −14,029 | 413,264 | −2,140 | 149,091 | −10,424 | 10/10 |
| block MIN 8, 1000 ms | 853,810 | −32,816 | 402,986 | −12,418 | 139,014 | −20,501 | 10/10 |
| block MIN 10, 500 ms | 858,299 | −28,327 | 412,611 | −2,793 | 154,195 | −5,320 | 10/10 |
| block MIN 8, 500 ms + entries | 872,597 | −14,029 | 413,264 | −2,140 | 149,091 | −10,424 | 10/10 |
| both MIN 8 ungated, 500 ms | 822,791 | −63,835 | 406,119 | −9,285 | 110,926 | −48,589 | 10/10 |
| both MIN 8 gated, 1000 ms | 852,585 | −34,041 | 399,170 | −16,234 | 136,799 | −22,716 | 10/10 |
| both MIN 10 ungated, 500 ms | 861,616 | −25,010 | 413,235 | −2,169 | 137,605 | −21,910 | 10/10 |
| TRIG2_K8 | 887,758 | +1,132 | 413,622 | −1,782 | 175,871 | +16,356 | 10/10 |
| TRIG2_K8 + exact-k7 cells | 883,862 | −2,764 | 415,745 | +341 | 175,827 | +16,312 | 10/10 |
| TRIG2_K8 + signal MIN 8 ungated COUNT 2 | 889,074 | +2,448 | 414,344 | −1,060 | 176,963 | +17,448 | 10/10 |

**No variant passes.** The best R4 delta is +2.4k, an order of magnitude below the +25k bar and inside
the ±25k noise band.

### DEEP8 counts on R4 (MIN 8 / 10 / 12)

- **Events:** 2,386 / 464 / 104. R3 had 1,804 / 534 / 132 and R2 320 / 51 / 10. Of the R4 MIN 8 events,
  1,129 were up.
- **Alignment with U2.** U2 already holds direction d at 96% of the events: 2,300 of the 2,386 signal fires
  at MIN 8 only extended the hold.
  - With the gate, 18 events flipped the position and 68 were ignored by the gate.
  - Without the gate, 76 flipped the position, costing −16k on R4, −5k on R3 and −33k on R2.
- **Block mode.** At MIN 8 the block ignored 25 / 174 / 514 of U2's flips at 200 / 500 / 1000 ms. PnL fell
  monotonically with the block length, so U2's flips against a fresh DEEP8 direction are profitable on
  average.
- **TRIG2_K8.** 2,404 R4 inserts used the k ≥ 8 cell. TRIG2 fires barely moved (1,893 → 1,885) because the
  k = 7 cell (−3.77 at spread 1) already exceeds the 0.95 threshold.
- U2 makes only one entry from flat per tape. It is always positioned, so DEEP8 has no "cold start" to add.

### CPU

Four R4 runs went concurrently on the same machine with the in-process runner (wall time per run, load
average 7–14):

| run | seconds |
|---|---:|
| U2 | 46.77 |
| DEEP8 file, defaults off | 46.94 (+0.4%) |
| signal MIN 8 ungated | 47.71 (+2.0%) |
| both, 500 ms | 47.24 (+1.0%) |
| TRIG2_K8 | 47.21 (+0.9%) |

All are within the +30% budget. `tools.preflight` passes on the defaults-off file.

## Verdict

**Rejected.** DEEP8 is a real, holdout-stable markout signal, but U2 already captures it. The taker flow
that accompanies these deep inserts has already put U2 on the same side 96% of the time. Where U2
disagrees, U2 is right on average:

- signal flips lose money;
- blocking U2's flips loses money.

Keep U2 (`r4_u2_trig2_ungated.py`) unchanged. Keep the flags in `r4_follower_deep8.py` for tapes where
the follower is not already positioned, for example a flatter, less momentum-driven private tape.

## Limitations

- **Public tapes only.** All PnL figures are from the public tapes, and R3 / R2 deltas are in-sample for
  U2's own fits.
- **Noise.** One R4 run per variant. A handful of flips moves R4 by ±25k, so the ±2k "best" variants are
  indistinguishable from U2.
- **R2.** The +16k on R2 for TRIG2_K8 / COUNT 2 is a few flips on the weakest tape, not evidence.
- **TRIG2_K8 data.** The k ≥ 8 cells use full R3 + R2 (not a fit half), so the R3 / R2 rows for K8 are
  in-sample.
- **Signal ordering.** DEEP8 only ranks below A / FLOW. When it fires together with TRIG1 or TRIG2
  (47 R4 events at MIN 8), those triggers are skipped for that event.
- **Untested.** Exits, sizing and the hold length were not changed. A smaller DEEP8-only position or a
  short DEEP8 hold were not tried.
