# R4 market diagnosis vs R3/R2: what to trade (experiment 20261108-r4-w1-diag-001)

**Question.** What changed in Round 4 public, and which U7 changes does it support? Descriptive
event studies only. No strategy was run here, and every number below needs a paired official-simulator test.

**Data and code.**
- R4 public `data/round4/round4_public.csv`, sha256 `61c0b6d1…8a56`, 6,000 s.
- Official null replays (engine `6dba6395…`):
  - R4 replay `46adf403…` from `20261108-r4-diagnostics-001`;
  - R3 replay `9c5c4f87…` (data `1021586b…`) and R2 replay `1e745b8b…` (data `88ff641e…`) from
    `20261108-r3-deep-diagnostics-001`.
- Scripts (gitignored), in `experiments/round_4/dataathletechamp/20261108-r4-w1-diag-001/`:
  - `diag.py` (`18e78d8e…`);
  - `extra.py` (`61c1c541…`).
- Command: `env -u VIRTUAL_ENV uv run --locked python <exp>/diag.py round4|round3|round2`, and the same for `extra.py`.
- Outputs are in `diag-<round>.txt` and `extra-<round>.txt`. The `*-v1-t0-mid-contaminated.txt` files are the
  failed first pass: an empty-book mid at t=0 faked a 5,000-tick jump, which only affected the whole-tape VR and block 0.

**Conventions.**
- Units are ticks and seconds.
- Entry is at the touch at event + 5 ms.
- "net" = signed (mid at H − entry touch). It includes the entry half-spread but not the exit cost.
- Events overlap and the ±100 cap is ignored, so these are per-event edges, not PnL.
- A (U7 definition) fires on any of: run ≥ 4 & filled ≥ 100; span ≥ 3; filled ≥ 500.

## 1. Generator: the same event mix, but price impact persists much longer

| | R4 | R3 | R2 |
|---|---|---|---|
| inserts/s (IOC/s), IOC share | 204.8 (9.74), 4.8 % | 205.8 (9.38), 4.6 % | 187.2 (8.90), 4.8 % |
| trades/s, lots/s, taker orders/s | 34.9, 1285, 9.37 | 34.0, 1194, 8.83 | 32.9, 1167, 8.56 |
| sweep share span ≥ 1 / ≥ 3 | 19.4 % / 1.24 % | 17.1 % / 0.82 % | 14.0 % / 0.56 % |
| no-trade (hidden) IOC/s | 0.37 | 0.55 | 0.35 |
| P(\|1 s move\| ≥ 10) with/without a hidden IOC in the prior 200 ms | 0.23 / 0.062 | 0.10 / 0.022 | 0.094 / 0.016 |

IOC limit buckets: signed mid move at 1 s / 5 s from the pre-IOC mid. The limit is measured relative to the opposite touch.

| bucket | R4 | R3 |
|---|---|---|
| < 0 (no trade) | −4.38 / −7.55 | −3.02 / −3.55 |
| [2,4) | +2.81 / +5.01 | +1.87 / +1.97 |
| ≥ 4 | +7.17 / +14.15 | +3.54 / +3.03 |

In R4 the move keeps growing after 1 s. In R3 it does not.

## 2. Price process: 1–5 s momentum, 10–30 s reversal; jumps continue

| statistic | R4 | R3 | R2 |
|---|---|---|---|
| ACF of 1 s returns, lag 1 / 2 / 3 | +0.29 / +0.15 / +0.10 | +0.11 / +0.02 / −0.02 | +0.03 / −0.07 / 0.00 |
| ACF lag 1 of 5 s / 10 s / 30 s returns | +0.13 / −0.09 / −0.21 | 0.00 / −0.07 / −0.10 | 0.01 / +0.08 / −0.03 |
| time-series momentum E[sign(past L)·future H]: L5H5, L10H10, L30H30 | +1.34, −1.09, −4.00 | −0.33, −0.96, −1.37 | |
| 1 s jumps ≥ 10 / ≥ 20 / ≥ 50 ticks | 420 / 56 / 10 | 176 / 20 / 6 | 109 / 22 / 5 |
| move after a ≥ 10-tick second, +5 s / +30 s (signed) | **+16.1** / +1.8 | +0.5 / −4.3 | −0.6 / +0.6 |

Per-600 s block, R4:
- VR10 is 1.31–2.64 in all 9 blocks. The ≤ 10 s momentum is stable.
- VR60 is 0.73–2.41, ACF of 10 s returns is −0.37 to +0.15, and block drift is −228 to +258. Beyond about 10 s there is no stable trend.

## 3. Maker economics: a touch maker loses at every size

Lots-weighted markout per lot at 0.5 / 1 / 2 / 10 s.

| touch fills | R4 | R3 |
|---|---|---|
| all | −0.66 / −1.01 / −1.31 / −1.16 | −0.46 / −0.62 / −0.76 / −0.37 |
| aggressor < 10 lots | −0.01 / −0.32 / −0.60 / −0.17 | +0.35 / +0.21 / +0.01 / +0.27 |
| aggressor 200–999 lots | −0.79 / −1.09 / −1.32 / −1.25 | −0.57 / −0.74 / −0.83 / −0.39 |
| queue-behind proxy (fills from sweeping orders) | −2.31 / −3.14 / −4.15 / −3.90 | −1.80 / −2.18 / −2.54 / −1.47 |
| maker side with / against the prior 30 s trend, at 10 s | −2.97 / **+0.51** | −1.93 / +1.06 |

Positive maker value exists only as a ≥ 10 s mean-reversion inventory bet against the 30 s trend. There is no
positive spread capture. The +122k from the aged maker therefore needs a paired explanation.

## 4. Taker event studies (R4 public, with R3 for comparison)

Net at 0.5 / 1 / 2 / 5 / 10 / 30 s.

| event (R4 rate/s) | R4 net | R3 net |
|---|---|---|
| A, U7 definition (1.17) | +1.42 +2.44 +3.63 **+4.89** +4.13 +1.15 | +0.78 +1.14 +1.36 +0.91 +0.20 −0.32 |
| span = 1 (1.44) | +0.38 +1.08 +1.98 +2.99 +2.32 +0.56 | −0.26 −0.07 0.00 −0.33 −0.65 −0.85 |
| span = 2 (0.24) | +2.08 +3.98 +6.64 +9.48 +6.84 −1.04 | +0.84 +1.24 +1.25 +0.73 −0.41 −0.73 |
| span ≥ 3 (0.11) | +3.45 +5.78 +9.43 +14.28 +12.85 +5.15 | +1.86 +2.73 +3.49 +3.02 +0.95 −1.79 |
| at-touch, < 50 lots (3.84) | 0.00 +0.33 +0.69 +1.07 +0.73 −0.24 | −0.36 −0.24 −0.19 −0.20 −0.26 −0.26 |
| 200 ms flow ≥ 600, onset (0.43) | +1.10 +1.78 +2.56 +3.21 +2.47 +1.43 | +0.82 +1.15 +1.48 +1.19 +0.88 +0.56 |
| deep-insert FV ≥ 0.5 & flow ≥ 200, onset (0.66) | +0.81 +1.45 +2.15 +2.91 +2.16 +0.99 | +0.44 +0.62 +0.80 +0.57 +0.41 +0.09 |
| deep-insert FV ≥ 1.0 & flow ≥ 200, onset (0.34) | +1.67 +2.80 +4.16 +5.86 +4.75 +1.88 | +0.93 +1.21 +1.61 +1.33 +1.06 +0.60 |

A hold curve, net at 2 / 3 / 4 / 5 / 6 / 8 / 10 / 15 / 20 / 30 s.

| A events | R4 | R3 | R2 |
|---|---|---|---|
| all | 3.63 4.36 4.67 4.89 **4.98** 4.59 4.13 3.15 2.11 1.15 | peak 1.36 at 2 s | 0.29 … 0.74 at 15 s |
| agree with prior 30 s trend (0.64/s) | 3.62 **4.12** 4.10 4.05 3.82 2.92 2.00 −0.20 −2.30 −3.49 | 1.15 … −1.66 | 0.28 … **+2.52** |
| against prior 30 s trend (0.51/s) | 3.71 4.74 5.48 6.08 6.57 6.77 6.85 7.39 **7.78** 7.17 | 1.62 … 1.72 at 10 s, 1.51 at 20 s | 0.32 … **−1.54** |

Stability:
- At 20 s, against-trend beats agree-trend in 8/9 R4 blocks and 7/9 R3 blocks.
- R2 has the opposite sign. R2 was a long-horizon trending tape (VR at 600 s = 2.35).

Continuation after a fixed point in the trade:

| condition | R4 | R3 | R2 |
|---|---|---|---|
| A with move ≤ −5 at 2 s, n = 516: further move 2→5 s / 2→7 s | **−7.08 / −8.27** | −1.63 / −0.77 | +1.05 / +0.29 |
| A with move ≥ +10 at 2 s: further move 2→5 s | +9.28 | | |
| A with move ≥ +15 at 5 s, n = 1,422: further move over +2 / +5 / +10 / +25 s | +3.53 / +2.67 / −3.65 / **−12.39** | −0.80 / −3.36 / −6.18 / −8.66 | |
| A with move ≤ −3 at 5 s: further move over the next 2 s | −3.32 | +0.04 | |

Incremental events not already A (net at 5 s):

| event | R4 | R3 | R2 |
|---|---|---|---|
| span = 2 & not A | 0.11/s, **+6.84** | −0.68 | −1.05 |
| span = 1 & not A | 1.05/s, +2.61 | −0.62 | −0.78 |

## 5. Perfect-foresight ceilings

The ceiling is ±100 lots, crossing at L1 at decision + 5 ms.

| decision step | R4 | R3 | R2 |
|---|---|---|---|
| 10 ms | 1,686,300 | 1,238,000 | 920,500 |
| 1 s | 1,432,200 | 959,300 | 667,100 |
| 5 s | 1,067,600 | 592,000 | 415,500 |

U7 makes 821,692 on R4 public, which is 49 % of the 10 ms ceiling and 57 % of the 1 s ceiling. On R3 it made 413,588, or 33 % of the 10 ms ceiling.

## Ranked U7 changes for R4

These are hypotheses to test with paired official-simulator runs on R4 and the R3 guard tape.

1. **Early stop.** If the mid has moved ≤ −5 ticks against an A position within 2 s, exit by IOC. At the deadline,
   use an IOC instead of the 1 s passive join when the trade is losing (≤ −3).
   - Evidence: R4 −7.08/−8.27 further loss (n = 516) and −3.32 at the deadline; R3 −1.63; R2 +1.05, a small cost.
2. **Trend-aware hold.**
   - A against the prior 30 s trend: hold 10–20 s (R4 net 6.08 at 5 s → 6.85 at 10 s → 7.78 at 20 s; 8/9 blocks).
   - A agreeing with the trend: hold ≤ 5 s with no same-side extension (4.05 at 5 s vs 2.00 at 10 s and −3.49 at 30 s).
     A 3 s cut is not stable across the halves.
   - Regime risk: R2 reverses both. Prefer a live gate on the sign of the rolling ACF of 10–30 s returns (R4 −0.09/−0.21).
3. **Profit-take cap on extensions.** Once the open gain is ≥ 15 ticks, let the trade run about 2–5 s more, then
   exit and do not re-extend.
   - Evidence: R4 +3.53 at +2 s but −12.39 at +25 s; R3 −8.66 at +25 s.
   - This overlaps with item 2 because both are the 10–30 s reversal.
4. **Sweep threshold SW 3 → 2.** This is R4-specific: span-2 events that are not already A make +6.84 at 5 s (0.11/s)
   in R4, but −0.68 in R3 and −1.05 in R2.
   - Span 1 (+2.61, 1.05/s) is a bigger but riskier bet.
5. **Keep the base hold at 5 s.** The R4 curve is flat over 4–8 s (4.67–4.98).
6. **Do not add a touch maker leg.** R4 touch markout is −1.01 per lot at 1 s and negative even for < 10-lot aggressors.
   - The aged maker (+122k standalone) must be tested paired with U7.

**Chronological halves check.** Each tape was split into its first and last 3,000 s. Script `halves.py`; outputs in
`halves-<round>.txt`. Values are first half / second half.

| item | R4 | R3 |
|---|---|---|
| stop: further move 2→5 s after ≤ −5 at 2 s | −7.96 / −6.20 | −1.98 / −1.38 |
| winner ≥ 15 at 5 s: further move 5→30 s | −16.96 / −7.53 | −5.36 / −11.67 |
| agree-trend net at 3 / 5 / 10 s, first half | 3.51 / 3.24 / 0.30 | |
| agree-trend net at 3 / 5 / 10 s, second half | 4.71 / 4.85 / 3.66 | |
| against-trend net at 5 / 20 s | 7.55 / 8.94 and 4.51 / 6.54 | flat |
| span = 2 & not A, net at 5 s | +7.80 / +5.91 | −1.55 / −0.06 |

What the halves show:
- In R4, items 1, 3 and 4 and the against-trend extension hold in both halves.
- The 3 s cut for agree-trend A events is not supported in the second half. The finding is "do not extend beyond
  5 s", not "cut at 3 s".

**Limitations.**
- Public tape only. Whether the private R4 tape shares R4-public parameters is unknown.
- The event-level edges overlap, ignore the position cap, queue position and exit cost, and are not PnL.
- The thresholds (−5, 15 ticks, 30 s) were chosen once on the full tape. Stability was checked only with the 600 s
  blocks and the halves above, not with a fit/evaluation split.
