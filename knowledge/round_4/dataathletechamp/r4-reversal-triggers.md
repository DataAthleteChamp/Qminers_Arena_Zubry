# R4 faster reversal triggers on U7: all rejected (`20261108-r4-w5-reversal-001`)

Public-tape research only; public PnL is not private PnL. Outputs live (uncommitted) in
`experiments/round_4/dataathletechamp/20261108-r4-w5-reversal-001/` of the main clone.

## Question and mechanism

The R4 oracle-gap study (`20261108-r4-w2-oracle-gap-001`) attributes 71% of U7's gap to perfect foresight to
late entry at reversals (median 0.16 s behind the oracle), starting on thin, wide books. Hypothesis: earlier,
weaker reversal evidence on thin / wide books, used as an extra A event (same-sign = hold extension, opposite =
flip through the unchanged P1 alpha gate, FLIP_MARGIN 1.0), recovers part of that lag.

Strategy `strategies/round_4/dataathletechamp/r4_follower_reversal.py` = U7 plus flags, **all off by default**
(sha256 `3a0c9c5d9952f4c11cdd84c09caf04457aac1b6a669d234645e318656e8f92a4`). Triggers are evaluated only for market
taker orders that are not already A trade triggers and only when no A / FLOW_TRIG signal fired in the event.
"Pre-event" = the previous public snapshot. Model features are unchanged.

- `DA_DEPTH` (DEPTH_ADAPTIVE): sweep span >= `DA_SPAN` counts as A if pre-event market depth on the consumed side
  over 3 price levels from the touch is < D lots, or the pre-event spread is >= `DA_SPREAD` (2; 0 = depth only).
- `TF_DEPTH` (THIN_FLIP): in position, an opposite taker order that empties our exit-side best level whose
  pre-event market L1 size was < D lots.
- `FS_MOVE` (FIRST_SWEEP): after a >= `FS_MOVE`-tick mid move against the position within 0.3 s (rolling extreme
  to now), any opposite sweep of span >= 1 for the next 0.3 s.
- `REV_MARGIN` > 0: stricter alpha-gate margin for these flips only.

## Setup

Official `simulator/simulator.py` `c37b2262186f977d`, in-process runner
`20261108-r4-runner-001/runner.py` `27806eed8f3aec4f` (±100, 1000 potential, 10,000/s, 5 ms, depth 20), 3 workers.
Tapes (full, no slicing): R4 `round4_public.csv` `61c0b6d149e5e508`, R3 `1021586b92a3d9df`, R2 `88ff641e962540c6`.
Base U7 `r4_u1_follower_u7_baseline.py` `d2a0fc9c3b81fc2d`. Frozen run snapshots: `snap_w5a_…` `596e6addd565bbac`
(wave 1), `snap_w5b_…` `d6f57658499c17aa` (wave 2; adds `REV_MARGIN`). The committed file differs from `snap_w5b`
only in docstring / comment wrapping (AST-identical code). Flags-off reproduces U7 exactly on all three
tapes in both waves (R4 821,692 / R3 413,588 / R2 167,166, 1,934 fills on R4). All thresholds were set from the
brief, not fitted; every tape is evaluation. ACCEPT rule (set before running): R4 > 829,909 (U7 + 1%) and
R3 + R2 >= 563,331 (−3%).

## Results (official engine, full tapes; Δ vs U7; trig / flips / ignored = R4 trigger fires, direct flips, gate-blocked)

| variant | R4 | ΔR4 | ΔR3 | ΔR2 | Δ(R3+R2) | trig / flips / ign (R4) | verdict |
|---|---:|---:|---:|---:|---:|---|---|
| DA D200 span 2 | 813,830 | −7,862 | −5,637 | −5,496 | −1.9% | 190 / 26 / 33 | reject |
| DA D400 span 2 | 814,659 | −7,033 | −7,810 | −9,386 | −3.0% | 289 / 41 / 46 | reject |
| DA D200 span 1 | 797,317 | −24,375 | −41,587 | −55,556 | −16.7% | 1,913 / 241 / 631 | reject |
| DA D400 span 1 | 790,874 | −30,818 | −44,578 | −59,794 | −18.0% | 2,443 / 265 / 726 | reject |
| DA D200 span 2, depth clause only | 817,042 | −4,650 | −3,018 | −3,966 | −1.2% | 108 / 5 / 15 | reject |
| DA D200 span 2, REV_MARGIN 2 | 820,400 | −1,292 | −1,225 | +679 | −0.1% | 189 / 8 / 51 | reject (no-op) |
| TF D200 | 746,973 | −74,719 | −89,224 | −111,957 | −34.6% | 3,198 / 729 / 2,469 | reject |
| TF D400 | 744,820 | −76,872 | −121,668 | −114,520 | −40.7% | 3,424 / 775 / 2,649 | reject |
| TF D200, REV_MARGIN 2 | 805,269 | −16,423 | −30,548 | −2,359 | −5.7% | 3,128 / 139 / 2,989 | reject |
| TF D200, REV_MARGIN 3 | 796,850 | −24,842 | +5,022 | +6,984 | +2.1% | 3,120 / 12 / 3,108 | reject |
| FS 3 ticks | 820,764 | −928 | −9,478 | −16,576 | −4.5% | 135 / 51 / 84 | reject |
| FS 5 ticks | 821,279 | −413 | −3,166 | +2,304 | −0.2% | 30 / 5 / 25 | reject (no-op) |
| FS 3 ticks, REV_MARGIN 2 | 822,552 | +860 | +645 | −807 | −0.0% | 141 / 18 / 123 | reject (no-op) |
| best pair: DA D200 s2 + FS 3 | 811,774 | −9,918 | −11,585 | −14,302 | −4.5% | 320 / 77 / 113 | reject |
| reference: `A_SWEEP` 3 → 2 (unconditional) | 816,097 | −5,595 | −13,889 | −14,863 | −5.0% | — | reject |

## Findings

1. **No variant passes; nothing is adopted.** The committed file keeps every flag off and is U7 behaviour
   (official CLI on R4: 821,692, 1,934 fills, penalty 0; local preflight passed).
2. Earlier, weaker reversal evidence loses after crossing cost, and the loss grows with how often it fires:
   ΔPnL per direct triggered flip (cascades included) is about −100 to −300 (TF D200: −74.7k / 729 on R4; DA D200
   span 1: −24.4k / 241; DA D200 span 2: −7.9k / 26). U7 flips cost about 1.1 ticks per lot against the send mid
   (`fill_stats` ioc_flip: R4 1.10, R3 1.10, R2 1.01), so a 200-lot flip needs > 1.1 ticks of follow-through,
   which thin-book 1–2 tick sweeps, level depletions and first opposite sweeps do not deliver on average.
3. A stricter gate (REV_MARGIN 2) turns DA and FS into near no-ops (|Δ| ≤ 1.3k per tape), so there is no
   gate setting between "harmful" and "inactive" on these tapes.
4. Path-dependence noise is large: TF with REV_MARGIN 3 made only 12 direct flips on R4 yet moved R4 by −24.8k
   (and R3 / R2 by +5k / +7k). Treat paired deltas below about ±25k from small trigger changes as noise.
5. Together with the w2 trend-rule results, the 0.16 s V-turn lag does not look recoverable from public
   sweep / depth / mid-move evidence at U7's IOC execution cost. Do not retry these trigger shapes; remaining ideas
   need new information (not lower thresholds on existing signals) or cheaper execution.

## Reproduce (main clone root, ≤ 3 workers)

```
R="env -u VIRTUAL_ENV uv run --locked python"; E=$PWD/experiments/round_4/dataathletechamp/20261108-r4-w5-reversal-001
$R experiments/round_4/dataathletechamp/20261108-r4-runner-001/runner.py --strategy $E/snap_w5a_r4_follower_reversal.py \
  --grid $E/grid_single.json --tapes r4,r3,r2 --out $E/out_single --workers 3
$R experiments/round_4/dataathletechamp/20261108-r4-runner-001/runner.py --strategy $E/snap_w5b_r4_follower_reversal.py \
  --grid $E/grid_wave2.json --tapes r4,r3,r2 --out $E/out_wave2 --workers 3
$R $E/summarize.py
$R -m simulator.main --strategy strategies/round_4/dataathletechamp/r4_follower_reversal.py \
  --backtest data/round4/round4_public.csv --log-dir $E/cli_r4_final --no-logs   # 821,692, 1,934 fills
```

## Limitations

Single public tapes per round; R4 was also the diagnosis tape, so R4 is not independent of the hypothesis.
"Within 3 ticks" was implemented as 3 price levels (touch, +1, +2) and spread / depth are read from the pre-event
snapshot; the other readings (4 levels, post-event book) were not run. FIRST_SWEEP uses the rolling 0.3 s mid
extreme, not the oracle's switch time. Server validation is still needed for any upload.
