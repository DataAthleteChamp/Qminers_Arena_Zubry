# Round 3 strategy research, wave 1: engines, disproofs and experiment backlog

Question: which mechanisms on R3 public A can survive 5 ms latency, FIFO
queues, the +/-100 cap and crossing costs, and how large are they?
Data: `data/round3/round3_public.csv`, SHA256
`1021586b92a3d9dfdb70096e6b0af34d460813b139f1f51f56b73871cb5a2d15`.
Fit t < 2400 s, evaluation t >= 2400 s; R2 A and R1 used as regime stress.
All numbers below are causal **screens** (numpy or order-level queue replays
that reproduce the official engine's 204,124 null trades), not official
strategy PnL. Detailed scripts/notes live in uncommitted experiment folders
`experiments/round_3/dataathletechamp/20261108-r3-*-001/`.

## Engine facts that change design (official `simulator/simulator.py`)

- Send/cancel/modify apply 5 ms later, just before the first market event at
  or after that time (lines ~776, 826, 860, 879, 942); same-time actions apply
  in send order (938).
- Modify that shrinks keeps queue priority (1104, 223-238); cancel+replace
  loses it. A non-shrinking modify is rejected; unknown ids are ignored.
- Every R3 market taker is an IOC (52,961); market G inserts never cross.
  Market takers trade with our resting orders at our price, even inside the
  spread. When we consume a resting market order, later tape takers trade
  deeper or are dropped; its later tape delete is a no-op (931, 202-204).
- Penalty accrues only with time spent at |I| > 100 (1273-1296), flat 10,000/s
  regardless of excess; the reject check counts resting but not in-flight
  orders (1261-1271). Liquidation uses resting market orders (1334-1356).
- CPU: ~150-180 us per event for a 12,000 s tape within the 900 s budget.

## Engines that screen positive on R3 A

| Engine | Trigger and action | Screen result (fit / eval) | R2 / R1 | Status |
|---|---|---|---|---|
| E1 informed follow | Signal A = (4th+ same-direction IOC in a run and filled >=100) or 2+ levels taken or filled >=500; take +/-100 5 ms later, extend on same-sign signal, flip on opposite | 2 s hold +38.7 / +54.7 PnL/s; 5 s +43.7 / +58.9; 600 s blocks 9/10 positive, t 4.8 | +2.5/+4.7 (2 s), +11.9/+17.1 (5 s) / negative | Best engine; 17-23% of screen fills assumed at best without enough size |
| E2 stale-side snipe | One side jumps >=k ticks in one update; IOC the unchanged opposite side (still there 5 ms later ~98%); cross out after ~1 s | k=2: +1.07 / +0.81 ticks per lot (n 987/1,824); k=3: +1.77 / +1.66 (n 282/523); ~0.47 events/s | not yet | Clip at +/-20 ticks; needs exit price guard |
| E3 contrarian passive entry | Rest 25 lots at touch against heavy 5 s taker flow (<= -1,688 lots), hold ~30 s | +2.72 / +2.63 ticks per lot at 30 s; +34.5 / +33.6 PnL/s uncapped | R2 opposite sign at 60 s | Inventory cap limits to ~7-9 PnL/s |
| E5 follow large taker (owner screen) | Cross 5 ms after taker >=1000 lots, or 200-1000 lots sweeping >=2 levels; cross out after 2 s | +1.24 / +1.86 and +1.84 / +1.18 ticks per lot | ~0 or negative | Subsumed by E1 |

Informed flow is defined by hidden IOC limit depth: orders priced 2+ ticks
through the book drift +1.4 (2 ticks) to +2.4 (3+) at 1 s; 1 tick through
+0.5; at-the-touch IOCs ~0. Their share grew R1 1.2% -> R2 16.6% -> R3 25.9%,
and 2+ level sweeps per hour 21 -> 568 -> 905: the regime knob is informed-flow
intensity, which makes an online intensity gate (E1-H3) the key transfer guard.

## Disproved or parked on R3 A (keep behind default-off flags)

- Conditional passive quoting at 1 s: no observable state makes a fresh
  back-of-queue order non-toxic. Touch fills -0.73 / -0.83 at 1 s; fills that
  empty the level -1.53 / -1.61, fills that leave it standing +0.12 / +0.08.
- Quoting one tick behind: worse (-1.24 / -1.31). Pennying when spread >= 2:
  -1.30 / -1.16 at 1 s. Short queues worse than long ones.
- Generic momentum taking after 2-sigma moves: cost-dominated; taker cost at
  trigger times is 1.7-3.5 ticks per lot. Shuffle test confirms sub-second
  momentum is real without costs (+26.6/s vs 0 +/- 2) but not capturable.
- Slow OU-style fades: EMA-deviation half-lives match random-walk mechanics;
  best fade (+12/s) came from 5 trades. Passive tau=30 fade +7.0 / +3.9/s.
- Identity fingerprints: order IDs sequential, no sub-second periodicity,
  exact sizes do not carry from fit to eval, partial IOCs reverse.
- Following every taker: about -440/s (control).

## Gap to the 2-3M target

2-3M on a 12,000 s tape needs ~170-250 PnL/s. The frictionless 100-lot
sign oracle on A is 199/s at 1 s. Current best realistic engine is ~40-60/s
on A (~0.5-0.7M per 12,000 s if B/C look like R3, far less if like R2).
Closing the gap needs cheaper execution (passive exits), more independent
triggers (E2, aggressive add-ons) and a maker that only accepts benign fills.

## Predeclared experiment backlog (official simulator, R3 A, then R2 stress)

Each uses a standalone file with default-off flags, an unchanged flag-off
baseline, fit/eval split at 2400 s from `pnl.csv`, zero penalty required.

1. `INFORMED_FOLLOW_ENABLED`, `INFORMED_FOLLOW_HOLD_S` in {2,5},
   `INFORMED_FOLLOW_LOTS`=100: reject if A < 100k, eval segment <= 0 or any penalty.
2. `INFORMED_GATE_WINDOW_S`, `INFORMED_GATE_MIN_SWEEPS_PER_H`: reject if R2
   still loses at 2 s hold or R3 keeps < 80% of ungated PnL.
3. `STALE_JUMP_K` in {2,3}, `STALE_HOLD_S`=1, `STALE_EXIT_GUARD_TICKS`:
   reject if PnL <= 0 in either window or eval < +0.3 ticks per round trip.
4. `CONTRA_FLOW5_ENTRY`, `FLOW5_CUT`=1688, `HOLD_S`=30: reject if eval <= 0,
   30 s markout < +1.0 or any penalty.
5. `INFORMED_QUOTE_GUARD_S`, `MOVE_PULL_ENABLE`: guard/pull a maker's quotes on
   signal A or after >2-sigma 2 s moves; reject if paired gain <= 0 overall or
   after 2400 s, or fewer than 50 fills removed.
6. `CANCEL_ON_THIN_LEVEL` / `MIN_LEVEL_QTY`, `WIDE_SPREAD_PAUSE`: maker
   hygiene; reject if 1 s fill markout improves < 0.3 or PnL does not rise.
7. Guard test `MOMO_TAKER_ENABLE`: expected loss; reject the cost model if
   realised taker cost < 1.5 ticks per lot.
8. Negative controls kept: `PENNY_WHEN_SPREAD_GE`=2 expected to lower PnL.

Wave 2-3 research (participants/generator, language-specific literature,
industry/academic HFT, poker/betting/chess analogies, exits, combined
capacity, aggressive add-ons, big-queue tactics) is in progress.
