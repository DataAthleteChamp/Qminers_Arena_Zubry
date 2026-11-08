# R3 informed follower: what limits PnL and which mechanisms do not help

Investigated 2026-11-08 (luklen123), R3 public only, with the official simulator. Base: team file
`r3_alpha_follower_p1_sw3.py` (sha256 `e4dfd2ce…`; R3 public **330,208**; validation B 411,302).
Raw work, scripts and logs: `experiments/round_3/luklen123/20261108-r3-follower-iter-001/` and
`…/20261108-r3-follower-opt-001/` (gitignored). Every number below is one public path, in-sample.

## How the follower actually earns (decision attribution of the base run)
- |position| = 100 for **98.3%** of the time. It is an always-positioned direction bet that changes sign
  on informed taker flow (signal A).
- 1,417 flips (282,587 lots): gross directional gain **+584.8k**, execution cost **−285.7k**
  (1.01 ticks/lot vs pre-trade mid). Entries, exits and resizes add about +30k.
- Cost per lot by spread at the decision: 0.63 (1 tick), 1.10 (2), 1.65 (3), 2.50 (≥ 4). Spread ≥ 2 holds 44% of
  the lots and causes 67% of the cost.
- Edge decays fast. The mid drift in the position's direction is **+0.72 ticks/s in the first second** after the
  last same-side A. At an age of 1–2 s it is −0.27 over the next 5 s, and at 2–5 s it is −0.68 over 5 s
  (46% of the time).
- 600 s block PnL ranges from 1.7k to 53.5k. It is set by market activity: corr **0.96** with the 1 s drift
  after A and 0.91 with mean |1 s move|. Execution cost is nearly constant per block.

## Mechanisms that do not help (keep them off; the code stays behind flags)
| mechanism | evidence | R3 result |
|---|---|---|
| Defer the flip IOC while the spread is wide | Every delay is worse. At spread ≥ 4: 2.70 → 4.31 ticks after 100 ms. "Wait for 1-tick spread" is no better. | rejected before coding |
| Passive unwind of stale positions (STALE_S) | Closing fills are adversely selected: markout −0.43/−0.59/−1.15 at 1/10/60 s. Flat time rises from 1.7% to 10%. | 295.8k–303.0k (−27k..−34k) |
| Close to flat on a medium-strength opposite A | Same cost, less directional gain. | 300k–305k |
| Conviction sizing (alpha-scaled size) | Edge is roughly uniform per position, so a smaller size only cuts gain. | 318k–328k |
| Fewer flips in low-edge periods | A flip beats holding by 2·gain − cost. Even the weakest block gives +32k. | rejected before coding |
| Joint HPO of 14 existing knobs (90 configs) | Flat plateau. | best 334,426 (noise) |

## Lessons
1. With the position pinned at ±100, PnL = size × sign accuracy × move − transition cost. Thresholds, timing
   and sizing no longer move it. Only a better short-horizon direction predictor (more correct sign changes,
   especially in the 1–5 s after A) can.
2. Any passive leg added to this follower is adversely selected. This is consistent with the team's
   maker probe (−660k on B) and the luklen123 ladders.
3. Execution is already as fast as it can be (5 ms). On this tape, cost is paid for immediacy, not for impatience.

## Deliberately paying the inventory penalty does not pay on R3
The breach penalty is a flat **10,000 per second** while |inventory| > 100, regardless of size. A burst of
E extra lots held for dt seconds therefore needs E × (move − round-trip cost) > 10,000 × dt, which is
**> 11.1 ticks per lot per second at E = 900**.
- Optimistic touch-to-touch research (no depth walk): the best 1 s round trips are +2.08 (sweeps ≥ 4 ticks),
  +1.89 (takers ≥ 2,000 lots) and +4.00 (both, n = 8). At ≤ 250 ms the round trips are negative.
- Official simulator, flag `BURST_*`, R3:
  - 400 lots / 250 ms on takers ≥ 2,000: **77,147** (penalty 235,061) vs 330,208 control.
  - 1,000 lots / 1 s: −575,174 (penalty 933,485).
  - Sweep-triggered bursts: −532k to −889k.
- Before the penalty, short bursts already lose 18k–405k, because 300–900 lots walk several book levels.
  Longer bursts gain at most +35k gross against ~930k of penalty.
- Keep `BURST_LOTS = 0`. The ±100 limit binds the follower, but buying around it costs far more than the
  short-horizon edge on this tape.
