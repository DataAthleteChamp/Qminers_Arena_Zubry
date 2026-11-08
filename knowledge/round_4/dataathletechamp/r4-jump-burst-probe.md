# Round 4: jump-onset bursts in the official engine (probe)

Experiment: `experiments/round_4/dataathletechamp/20261108-r4-burst-predictor-001/`.
- Scripts: `jump_anatomy.py`, `jump_microscope.py`, `jump_onset.py`, `jump_onset2.py`, `jump_episodes.py`,
  `export_onsets.py`, `burst_probe.py`.
- Engine grids: `grid_burst_<tape>.json`, `run_burst_<tape>.log`.

## Mechanism (raw tapes)

Big moves in this market are repricings of a latent fair price, not sweeps.

- **Far side goes deep.** When the latent price jumps, the far side's new resting orders are placed
  more than 20 ticks behind their own best (for a down-jump, those are bids). They are invisible live,
  but each one consumes an order id, which shows as an id gap. Several gaps arrive within about 25 ms.
- **Near side piles at the touch.** The near side's new orders cannot cross, so they pile at the touch
  or inside the spread.
- **The book collapses without trades.** Stale near-touch orders are cancelled on their pre-drawn
  schedule, and the book collapses onto the deep orders with few trades.
  - Example, R4 at 170.386 s: down 137 ticks within 45 ms.
- **Followers see nothing until it is over.** The follower's sweep and flow triggers fire only after
  the repricing (`jump_microscope_r4.txt`). R4's worst U2 seconds are these jumps taken on the wrong
  side (`r4-u2-trade-anatomy.md`).

## Live detector

- **Inputs, at every visible insert (one callback):**
  - hidden inserts revealed in the last W ms (sum of id gaps);
  - the spread before the insert;
  - the visible near-touch insert imbalance over W: G orders at most 1 tick behind their own-side
    best, bid +1 and ask −1, counted double if inside the spread.
- **Trigger:** at least K hidden inserts in W, spread ≤ S, imbalance ≠ 0. The first trigger per 1 s
  counts. Direction = sign of the imbalance.
- **Results:** move measured from trigger + 5 ms.

| tape | W/K/S | onsets | signed move 20 / 50 / 200 ms | direction accuracy at 200 ms |
|---|---|---:|---|---:|
| R4 | 20/3/1 | 7 | +49.7 / +75.9 / +77.5 | 1.00 |
| R4 | 30/3/1 | 11 | +32.0 / +48.7 / +51.4 | 1.00 |
| R3 | 20/3/1 | 17 | +2.5 / +10.3 / +11.4 | 1.00 |
| R2 | 20/3/1 | 8 | +7.9 / +10.0 / +11.4 | 1.00 |

- **Without the spread filter** (W 30, K 3), onsets driven by deep orders average |200 ms move| 47
  ticks. Clusters of hidden IOCs, which occur at wide spreads, average 3.9.
- The only wrong-way case was at spread 102.

## Burst probe (official engine, bursts only, flat otherwise)

- **What the probe does:**
  - It enters at the onset callback with an IOC of N lots at the touch ± cap.
  - It holds for H, then exits to flat with an IOC at the touch ± 20.
  - Onset times are exported from the live detector above.
- **Results:** PnL includes the 10,000/s penalty above 100 lots.

| variant | R4 | R3 | R2 |
|---|---:|---:|---:|
| 100 lots, hold 200 ms, W 20 / W 30 | +24,143 / +25,150 | +6,172 / +5,179 | −57 / +846 |
| 300 lots, cap 5, hold 50 ms, W 20 | +37,939 | −8,039 | −4,211 |
| 300 lots, cap 5, hold 200 ms, W 20 | +45,437 | −18,496 | −8,758 |
| **900 lots, cap 5, hold 200 ms, W 20** | **+67,794** | −35,157 | −12,760 |
| 900 lots, cap 5, hold 200 ms, W 30 | +60,096 | −71,745 | −21,392 |
| any hold of 500 ms | worse everywhere | | |

- **Liquidity is the limit.** A 900-lot IOC fills only about 150 lots per onset at W 20, and about 370
  at W 30. The book is collapsing.
- **Bursts above 100 lots pay only where jumps are big.**
  - R4 onsets move 50–80 ticks; R3 and R2 onsets move 8–13.
  - R3 and R2 come from other round configurations. Private R4 comes from the R4 generator, as public
    R4 and validation do, so the validation tape is the arbiter.
- **The 100-lot version** (realign to the jump at onset, no penalty) is positive on all three tapes.

## Rejected companion fixes (official engine; U2 copy with flags, ΔPnL vs U2)

- **Post-jump flip freeze:** ignore flip signals for 0.5–2 s after the mid moves 10–25+ ticks within
  200 ms.
  - R4: −9k to −26k.
  - R3: −1k to −6k.
  - R2: +19k to +31k.
  - Rejected.
- **Minimum hold and spread-wait:** see `r4-u2-trade-anatomy.md`.

## Integrated in U2 and tuned (official engine, Δ vs U2)

- **The builder's file.** The builder's integrated file
  (`r4_follower_jump.py`, `r4_u5_jump.py`; `r4-jump-onset.md`) shows that most of the standalone burst
  value overlaps with what U2 already earns. The gain comes from the flip on wrong-side jumps plus a
  small burst.

| variant (all flip + burst 300 lots / 50 ms, cap 5 unless noted) | R4 | R3 | R2 |
|---|---:|---:|---:|
| W20 K3 S≤1 (U5) | +25,648 | −7,896 | −7,427 |
| **W20 K4 S≤2 (U6)** | **+33,912** | **+700** | **−822** |
| W30 K4 S≤2 | +34,383 | −4,315 | −2,257 |
| W40 K4 S≤2 | +33,738 | −6,325 | −2,682 |
| W30 K4 S≤3 | +34,383 | −7,790 | −2,257 |
| W30 K4 S≤2, burst 500 / 100 ms | +49,773 | −12,568 | −7,284 |
| W30 K4 S≤2, burst 900 | +8,989 | −30,983 | −16,375 |
| W20 K3 S≤1, burst 900 / 200 ms | +30,837 | −54,690 | −28,620 |

- **TWAP overlay rejected.** Following the 160-lot TWAP's trains on top of U5 lost 1.8k to 9.4k on R4,
  however it was done: push on every child, push only at the start, or veto opposite signals
  (`20261108-r4-twap-001`). The trains' drift is weaker than the follower's own signals.

## Next

An integrated U2 + onset flip/burst strategy is being built on branch `r4-da-jump` (`r4-jump-onset.md`).
If it reproduces the probe, upload it as a validation probe and decide the final from the paired
validation difference.
