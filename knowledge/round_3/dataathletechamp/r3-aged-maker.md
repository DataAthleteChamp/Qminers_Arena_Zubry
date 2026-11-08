# R3 aged-queue maker: pre-position, keep-aged, size-by-age and passive unwind (wave 2)

Owner dataathletechamp · branch `r3-da-maker` · experiment `20261108-r3-w2-aged-maker-001`
(outputs are gitignored and live under `experiments/round_3/dataathletechamp/` in the worktree) · 2026-11-08, 02:16–02:50 CET.
**All PnL figures are official-engine PnL on public or older tapes. Private B/C performance is UNKNOWN.**
Nothing was uploaded. The strategy file passed local `tools.preflight` only; the server sandbox has not checked it.

## Question
Fills of maker orders that are at least 300 ms old, or that have at least 300 lots queued behind them, earn
+0.14 to +0.37 ticks/lot (1 s markout) on every tape. Fills of young orders lose. Can an "aged queue" maker
collect the good fills at scale? The target is at least 20 PnL/s on R3. For comparison, our taker engines
make about 45/s.

Baseline: the FV-gated touch maker **M1_q20_fv05** from `20261108-r3-gated-maker-official-001`, which
breaks even on R3.

## Provenance
| item | value |
|---|---|
| R3 public | `data/round3/round3_public.csv` sha256 `1021586b92a3d9dfdb70096e6b0af34d460813b139f1f51f56b73871cb5a2d15` (6,000 s; fit = first 2,400 s, eval = the remaining 3,600 s) |
| R2 public | `data/round2/round2_public.csv` sha256 `88ff641e962540c66fa1cc4a3547585d31838d0929340150690cabb4f3cfb9f4` (6,000 s; split at 2,400 s) |
| R1 | `data/round1/round1.csv` sha256 `362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940` (12,000 s; split at 4,800 s) |
| engine (unchanged) | `simulator.py` `c37b2262…e0d4c4`, `models.py` `d66d6155…`, `strategy.py` `464830f4…`. Config: 5 ms accept delay, depth 20, max position 100, penalty 10,000/s |
| runner | shared `20261108-r3-wave-runner-001/runner.py` sha256 `079727719583626a27aca7666128ef8ee8831806bb202fc010f2eba11b3302a9`, in-process official `ExchangeSimulator` |
| strategy v1 | sha256 `32ebd18ef353cca867e2818264ba6af5cb23af98c0c3121002030b5771a1ebfd`, used for the A1 screen, the A2 screen and the M1/A2 runs on R2 and R1 |
| strategy v2 (committed) | `strategies/round_3/dataathletechamp/r3_aged_maker.py` sha256 `3be6adc6c8d2a8820fb900ba1743e2f88f1473e7fe82f993ceb50ac3e316b5ab`. It equals v1 plus two default-off flags (A2b). Identity reruns reproduced v1 exactly: M1 on R3 −3,348, A2 at Q10 on R3 +13,482 and on R2 +25,928 |
| repo HEAD at start | `2b50061c` (worktree) |

Commands are run from the MAIN checkout. `$W` is the worktree and `$E` is the experiment directory.
```
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy <file> --grid $E/grids/<grid>.json --tapes <tapes> --out $E/<out> --workers 3
# grids:
#   screen1.json (r3; v1)
#   oos_a2.json (r2,r1; v1)
#   screen2_a2.json (r3,r2; v1)
#   screen3_a2b.json (r3,r2; v2)
#   screen4_cd.json (r3,r2; v2)
#   oos_r1_q10.json / oos_r1_cd.json (r1; v2)
#   final_identity.json (r3; committed file)
#   robust5_best.json (r3,r2; committed file)
#   oos_r1_robust.json (r1; committed file)
env -u VIRTUAL_ENV uv run --locked python $E/summarize.py $E/<out>/results.jsonl   # markdown table
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight $W/strategies/round_3/dataathletechamp/r3_aged_maker.py   # passed
```

## Definitions (module constants; defaults = M1)
- **FV.** Take the maximum price of new bid limit inserts and the minimum price of new ask limit inserts over
  the last 50 ms. An insert is new when its numeric order id exceeds every id seen before. FV is the midpoint of
  those two prices minus the market mid, and is 0 when either side had no new insert. Side s (+1 bid, −1 ask)
  is **opposed** when −s·FV ≥ the cut-off.
- **M1 (all flags off).**
  - One LIMIT of Q = 20 at the market touch on each side.
  - When the touch moves away from our price, we cancel and re-send after the cancel is confirmed.
  - The order is cancelled or blocked while −s·FV ≥ `FV_CANCEL` = 0.5.
  - Exposure is capped: inv + live buys ≤ 80 and inv − live sells ≥ −80, counting resting and in-flight
    orders. A breach raises an error. Penalty was 0 and maximum exposure was 80 in every run.
- **A1 `PRE_TICKS`=k.**
  - Rest `Q_PRE` lots at touch−1 … touch−k on bids, mirrored on asks.
  - Cancel when −s·FV ≥ `PRE_FV_CANCEL`, on an A-sweep when `A_GUARD` is on, or when the order is more than
    `MAX_DIST` ticks behind the touch.
  - A touch order whose touch moved away by ≤ k ticks is kept as a pre order instead of being re-priced.
  - `TOUCH_JOIN=false` disables touch orders entirely, leaving a pure pre-position maker.
- **A2 `KEEP_AGED`.** An order is *strong* when it is ≥ `AGE_KEEP_US` (300 ms) past its ACCEPTED event and has
  ≥ `QB_MIN` (300) market lots behind it at its price. Queue position comes from the public snapshot.
  - A strong order is cancelled for FV only when −s·FV ≥ `FV_STRONG` (1.5).
  - When the touch moves away from a strong order, the order is kept ("demoted") while it is ≤ `MAX_DIST` (2)
    ticks behind, and a new touch order is placed.
  - `JOIN_AGREE` sends new touch orders only when s·FV > 0. `YOUNG_CXL` also cancels young touch orders while
    s·FV ≤ 0.
- **A2b.**
  - `TOUCH_AGE_MIN_US`: join the touch only after the market touch price of that side has been unchanged for
    at least this long.
  - `FILL_COOLDOWN_US`: no new touch order on a side within this time of our last fill on that side.
- **A3.** `Q_TOUCH` sets the size of new (young) touch orders, while pre orders keep `Q_PRE`. Modify can only
  shrink an order, so an order that ages cannot be grown back to full size.
- **A4 `UNWIND`.**
  - The side that reduces inventory sends max(size, min(|inv|, 60)) lots and is exempt from `JOIN_AGREE` and
    `YOUNG_CXL`.
  - If |inv| ≥ 80 for 5 s, an IOC reduces inventory to 40 at the opposite touch ∓ 2 ticks.
- **Diagnostics.** `diagnostics()` returns 1 s markouts of our fills, in ticks per lot against the market mid
  at fill + 1 s, including the half-spread. They are split by order age since ACCEPTED, by role (main touch
  order or kept/pre order), by queue behind at the last snapshot and by FV state. The strategy ledger matches
  the official lots and inventory.

## Results (official engine; per-second values are fit/eval; acceptance rule: R3 eval > −2.9/s **and** R2 total ≥ +9,436)
| variant (overrides) | R3 PnL | R3 fit/eval /s | R3 lots | R3 mo1s fit/eval | R2 PnL (fit/eval /s) | R1 PnL (fit/eval /s) | verdict |
|---|---|---|---|---|---|---|---|
| **M1_base** (defaults) | −3,348 | +2.9/−2.9 | 213,105 | −0.09/−0.21 | +9,436 (+5.5/−1.1) | +72,447 (+5.5/+6.4) | baseline reproduced exactly |
| A1_p1_c05 (PRE 1, cut 0.5, dist 1) | −39,687 | −1.7/−9.9 | 240,576 | −0.14/−0.22 | – | – | reject |
| A1_p1_c10 (PRE 1, cut 1.0) | −61,490 | −3.6/−14.7 | 300,184 | −0.13/−0.22 | – | – | reject |
| A1_p2_c10 (PRE 2, cut 1.0) | −84,184 | −6.3/−19.2 | 300,772 | −0.20/−0.32 | – | – | reject |
| A1_p1_c10_notouch (pre only) | −43,355 | −4.1/−9.3 | 101,284 | −0.56/−0.59 | – | – | reject |
| A12_p1 (+KEEP_AGED, JOIN_AGREE) | −55,499 | −4.3/−12.5 | 238,308 | −0.16/−0.30 | – | – | reject |
| A123_p1_qt5 (+Q_TOUCH 5) | −26,050 | −1.0/−6.6 | 121,200 | −0.28/−0.42 | – | – | reject |
| A1234_p1_qt5 (+UNWIND) | −77,029 | −9.7/−14.9 | 249,189 | −0.16/−0.32 | – | – | reject |
| A2_only (KEEP_AGED, dist 2, strong 1.5, Q20) | +4,402 | +3.4/−1.0 | 248,542 | −0.03/−0.14 | +15,592 (+8.1/−1.1) | +123,284 (+9.5/+10.8) | pass |
| A2_s10 (strong 1.0) | +1,035 | +3.0/−1.7 | 241,346 | −0.04/−0.16 | +9,961 (+6.9/−1.8) | – | pass, weak |
| A2_d1 (dist 1) | +8,518 | +3.4/+0.1 | 246,544 | −0.04/−0.15 | +17,298 (+8.2/−0.7) | – | pass |
| A2_d3 (dist 3) | +2,519 | +3.8/−1.8 | 249,070 | −0.03/−0.14 | +15,085 (+8.1/−1.2) | – | pass, weak |
| A2_qb100 (QB_MIN 100) | −6,761 | +2.2/−3.3 | 255,494 | −0.03/−0.14 | +18,182 (+7.7/−0.1) | – | reject (R3) |
| A2_agree (+JOIN_AGREE) | −7,883 | +3.1/−4.3 | 147,588 | +0.06/−0.08 | −2,200 (+3.5/−3.0) | – | reject |
| A2_q40 | −42,046 | −3.7/−9.2 | 425,141 | −0.09/−0.19 | +7,404 (+7.3/−2.8) | – | reject |
| A2_q10 | +13,482 | +3.6/+1.4 | 135,189 | −0.01/−0.10 | +25,928 (+6.1/+3.2) | +64,380 (+5.2/+5.5) | pass |
| A2q5 | +24,311 | +6.1/+2.7 | 70,974 | −0.01/−0.07 | +6,301 (+2.7/−0.1) | – | reject (R2) |
| A2q10_d1 | +14,761 | +3.7/+1.6 | 133,771 | −0.02/−0.10 | +25,481 (+5.8/+3.2) | – | pass |
| A2q10_unw (+UNWIND) | −5,368 | −0.0/−1.5 | 180,412 | +0.00/−0.09 | +6,528 (+5.0/−1.5) | – | reject |
| A2q10_cd100 (FILL_COOLDOWN 100 ms) | +20,199 | +5.9/+1.7 | 119,774 | +0.04/−0.04 | +27,944 (+6.2/+3.6) | +60,914 (+5.1/+5.0) | pass |
| A2q10_cd200 | +19,754 | +5.5/+1.8 | 108,622 | +0.02/−0.01 | +31,176 (+9.0/+2.7) | +55,286 (+4.4/+4.7) | pass |
| A2q10_cd500 | +18,785 | +5.4/+1.6 | 85,706 | +0.05/+0.00 | +28,038 (+8.6/+2.0) | – | pass |
| **A2q20_cd100** (KEEP_AGED, dist 2, strong 1.5, Q20, cooldown 100 ms) | **+28,749** | **+6.1/+4.0** | 223,864 | +0.02/−0.08 | **+24,884 (+8.9/+1.0)** | **+114,383 (+9.0/+9.9)** | **best passing** |
| A2q10_ta50 (TOUCH_AGE 50 ms) | +8,664 | +6.2/−1.8 | 99,468 | −0.08/−0.17 | +5,743 (+4.0/−1.1) | – | reject |
| A2q10_ta200 | +50,129 | +11.5/+6.3 | 60,290 | −0.03/−0.14 | −6,027 (+2.6/−3.4) | – | reject (R2) |
| A2q10_cd100_ta100 | +37,764 | +9.3/+4.3 | 77,783 | −0.09/−0.16 | +6,387 (+5.9/−2.2) | – | reject (R2) |
| A2q10_cd100_ta200 | +50,201 | +11.0/+6.6 | 57,480 | −0.03/−0.14 | −6,962 (+4.6/−5.0) | – | reject (R2) |
| A2q20_cd100_ta200 | +42,204 | +9.3/+5.5 | 108,756 | −0.07/−0.20 | −9,186 (+5.4/−6.2) | – | reject (R2) |

All runs had penalty 0 and maximum exposure including pending of 80.

### Neighbourhood of the best arm (robustness check; committed file; added after the first commit)
| variant (change vs A2q20_cd100) | R3 PnL (fit/eval /s) | R2 PnL (fit/eval /s) | R1 PnL (fit/eval /s) |
|---|---|---|---|
| A2q20_cd100 (reference) | +28,749 (+6.1/+4.0) | +24,884 (+8.9/+1.0) | +114,383 (+9.0/+9.9) |
| **age150** (`AGE_KEEP_US` 150 ms) | **+35,027 (+6.8/+5.2)** | **+29,705 (+8.5/+2.6)** | **+134,661 (+10.4/+11.7)** |
| age600 | +25,264 (+6.1/+2.9) | +16,929 (+6.1/+0.7) | – |
| s20 (`FV_STRONG` 2.0) | +28,259 (+6.1/+3.8) | +26,687 (+9.8/+0.9) | – |
| d1 (`MAX_DIST` 1) | +33,459 (+6.1/+5.2) | +26,973 (+9.4/+1.3) | +112,419 (+8.7/+9.8) |
| Q15 | +27,546 (+6.7/+3.2) | +28,940 (+7.2/+3.2) | – |

The neighbourhood is a plateau: every arm earns +25k to +35k on R3 and +17k to +30k on R2. A shorter age
threshold helps and a longer one hurts, which fits the fill-age split (fills of orders 100–300 ms old are about
break-even, fills of orders ≥ 300 ms old are positive). age150 is better on all three tapes, but it was picked
after the neighbourhood scan.

**Positive 600 s blocks on R3.**

| variant | positive blocks |
|---|---|
| M1 | 5/10 |
| A2_only | 7/10 |
| A2q10_cd100 | 9/10 |
| A2q20_cd100 | 9/10 |

**Worst R3 600 s block.**

| variant | worst block |
|---|---|
| M1 | −11.5k |
| A2q20_cd100 | −5.4k |

The committed file reproduces M1 at −3,348 and A2q20_cd100 at +28,749 on R3 (`final_identity_r3`).

### Fill anatomy (R3, share of fill lots with 1 s markout in ticks/lot)
| variant | age < 100 ms | 100–300 ms | 0.3–1 s | ≥ 1 s | kept/pre role | queue behind ≥ 300 / 0 | FV agree / neutral / oppose |
|---|---|---|---|---|---|---|---|
| M1_base | 0.48 (−0.41) | 0.31 (−0.07) | 0.19 (+0.25) | 0.01 (+0.67) | – | 0.43 (+0.19) / 0.19 (−1.38) | 0.45 (+0.20) / 0.53 (−0.42) / 0.02 (−1.50) |
| A1_p1_c10_notouch | 0.21 (−0.46) | 0.22 (−1.55) | 0.35 (−0.46) | 0.22 (+0.11) | 1.00 (−0.58) | 0.57 (−0.22) / 0.13 (−2.35) | 0.24 (+0.05) / 0.48 (−0.82) / 0.29 (−0.71) |
| A2_only | 0.41 (−0.40) | 0.26 (−0.06) | 0.24 (+0.24) | 0.08 (+0.30) | 0.06 (+0.25) | 0.51 (+0.20) / 0.17 (−1.36) | 0.41 (+0.23) / 0.54 (−0.30) / 0.06 (−0.52) |
| A2q20_cd100 | 0.40 (−0.27) | 0.26 (−0.05) | 0.25 (+0.23) | 0.09 (+0.32) | 0.07 (+0.28) | 0.53 (+0.20) / 0.15 (−1.10) | 0.41 (+0.27) / 0.54 (−0.24) / 0.06 (−0.36) |
| A2q10_ta200 | 0.25 (−0.65) | 0.21 (−0.21) | 0.38 (+0.18) | 0.15 (+0.30) | 0.11 (+0.26) | – | – |

## Findings
1. **A1 pre-positioning is rejected, and decisively so.**
   - Orders resting 1–2 ticks behind the touch lose −0.47 to −0.82 ticks/lot at 1 s on R3. Every A1 arm loses
     between −26k and −84k.
   - The pure pre-position maker loses −43k even though 57% of its lots fill with at least 300 lots behind them.
     Those well-queued fills average −0.22, against +0.19 for touch orders with the same queue state in M1.
   - Mechanism: a level behind the touch only becomes fillable after the price has moved toward it, through a
     sweep of the touch or a cascade of cancels. A fill there is therefore conditional on adverse momentum, and
     queue position no longer protects the order. With a 5 ms latency, the FV cancel catches only part of it:
     29% of fills land in an FV-opposed state.
   - Whatever "aging" the order gains while it sits behind the touch does not carry over to the good fills.
2. **A2 keep-aged is the mechanism that works.** Two parts:
   - A strong order (≥ 300 ms old and ≥ 300 lots behind) tolerates FV opposition up to 1.5.
   - When the touch moves away from it, it rests 1–2 ticks behind instead of being re-priced.

   Effect: R3 −3.3k → +4.4k (eval −2.9 → −1.0/s), R2 +9.4k → +15.6k, R1 +72k → +123k. About 2,300 demotions
   happen per 6,000 s on R3. Kept and demoted fills earn +0.25 to +0.32 on R3 (+0.32 to +0.41 on R2, +0.56 on
   R1). The oppose share rises from 2% to 6%, but those aged oppose fills lose only −0.36 to −0.52, against
   −1.5 for young ones.
   The demoted orders are not the same as A1 pre orders. They were already at the head of a long queue
   *before* the touch moved, so price has to come back through 300+ lots of queue to reach them.
3. **A 100–200 ms fill cooldown adds to A2** (no re-join on a side right after our fill on that side; sweeps
   cluster).
   - Q20: R3 +4.4k → +28.7k, eval −1.0 → +4.0/s; R2 +15.6k → +24.9k; R1 +123k → +114k.
   - Q10: R3 +13.5k → +20.2k; R2 +25.9k → +27.9k; R1 +64.4k → +60.9k.
   - The cooldown cuts the < 100 ms fill loss (−0.40 → −0.27) and time at cap (0.105 → 0.090).
4. **Q.** Q40 is bad on R3 (−42k). Q5 is good on R3 but fails R2. Q10 and Q20 are both acceptable, and Q20 is
   about twice as good on R1. Size is capped at about Q20 by adverse selection, not by the inventory cap.
5. **The touch-age gate is an R3-only effect, so it is rejected.**
   - `TOUCH_AGE_MIN_US=200 ms` lifts R3 to +50k (fit +11.0 to +11.5, eval +6.3 to +6.6/s), but loses on R2
     (−6.0k to −9.2k) in every arm.
   - Its 1 s markout is *negative* (−0.14 eval), so the R3 gain is inventory drift beyond 1 s, not better fills.
     This is the same pattern as the rejected JOIN_MIN=300 arm in the official gated-maker experiment.
   - The flag stays default-off for possible private-tape regime use. It is not part of the recommendation.
6. **A4 unwind is negative again.** It brings time at cap to 0.001 but turns A2q10 from +13.5k to −5.4k on R3
   and from +25.9k to +6.5k on R2. Agree-only joining (A2_agree) and QB_MIN = 100 are also rejected. A3
   (small young touch orders) helps only inside the losing A1 family.

## Verdict
- **Best configuration** (post-hoc pick among about 35 arms by R3 fit/eval, then checked on R2 and R1):
  **A2q20_cd100** = `{"KEEP_AGED": true, "MAX_DIST": 2, "FV_STRONG": 1.5, "Q": 20, "FILL_COOLDOWN_US": 100000}`.

  | tape | PnL | fit/s | eval/s |
  |---|---|---|---|
  | R3 | +28,749 (4.8/s overall) | +6.1 | +4.0 |
  | R2 | +24,884 | +8.9 | +1.0 |
  | R1 | +114,383 | +9.0 | +9.9 |

  It passes the acceptance rule: R3 eval rises from −2.9 to +4.0/s, and R2 is +24.9k against +9.4k. The
  more conservative alternative is A2q10_cd100 (R3 +20.2k, R2 +27.9k, R1 +60.9k).

  Its plateau neighbour **A2q20_cd100_age150** (`AGE_KEEP_US=150000`) is better on all three tapes but was
  selected after the neighbourhood scan:

  | tape | PnL | fit/s | eval/s |
  |---|---|---|---|
  | R3 | +35,027 (5.8/s overall) | +6.8 | +5.2 |
  | R2 | +29,705 | +8.5 | +2.6 |
  | R1 | +134,661 | +10.4 | +11.7 |
- **Passive income does not reach ≥ 20 PnL/s on R3 with this family.**
  - The best passing arm makes 4.8/s on R3 (5.8/s for the age150 neighbour). That is about 4× below the target
    and about 8–9× below the taker engines.
  - Even the R2-failing touch-age arms reach only 8.4/s.
  - Its fills average −0.08 to +0.02 ticks/lot at 1 s, on about 37 lots/s. Aged good fills (≥ 300 ms) are only
    about 34% of volume, and scaling Q destroys the edge. On R3 the PnL is mostly inventory drift after the
    first second: the 1 s markouts sum to −8.5k and the residual is +37.3k (decomposition below).

**PnL = Σ (1 s markout × lots) + residual** (the residual is inventory drift after 1 s plus the liquidation mark):

| tape | arm | PnL | Σ 1 s markout | residual |
|---|---|---|---|---|
| R3 | M1_base | −3,348 | −35,332 | +31,984 |
| R3 | A2q10_cd100 | +20,199 | −837 | +21,036 |
| R3 | A2q20_cd100 | +28,749 | −8,548 | +37,297 |
| R3 | A2q10_ta200 | +50,129 | −5,559 | +55,688 |
| R2 | M1_base | +9,436 | −14,538 | +23,974 |
| R2 | A2q10_cd100 | +27,944 | +6,742 | +21,202 |
| R2 | A2q20_cd100 | +24,884 | +7,763 | +17,121 |
| R2 | A2q10_ta200 | −6,027 | +1,304 | −7,331 |
| R1 | M1_base | +72,447 | +76,652 | −4,205 |
| R1 | A2q20_cd100 | +114,383 | +112,894 | +1,489 |

The gain of A2 plus the cooldown over M1 is a *fill-quality* gain, consistent on all three tapes: R3 +27k, R2
+22k and R1 +36k of 1 s markout. The touch-age gain on R3 sits almost entirely in the residual, which turns
negative on R2. That is why it is rejected.
- **Reusable outcome.** The keep-aged rule and the fill cooldown fix the M1 maker's young-fill bleed and make it
  a small positive engine on all three tapes. It is a candidate passive leg next to a taker engine, but not a
  replacement for one.

## Limitations
- Public tapes only. R3 eval is 3,600 s of one tape, and there are no paired-delta SEs. The best arm was chosen
  after about 35 R3 arms, so its R3 numbers are selection-biased. R2 and R1 were run for only a subset.
- The age is measured from the ACCEPTED event, and queue behind from the last public snapshot within 20
  ticks. Modify can only shrink, so true "size by age", meaning growing an aged order, is impossible. A3 was
  tested only as a smaller size for new touch orders.
- `TOUCH_AGE_MIN_US` measures how long the market touch *price* has held, not the age of the orders at the level.
- The pre-order FV cut-off grid was coarse (0.5 and 1.0). A pre-order variant that requires ≥ 300 lots behind
  *before* the order becomes the touch was not tested.
- Runtime was 27–49 s per R3/R2 run and 56–65 s per R1 run, with 2–3 processes on a laptop. These are not
  server timings.
