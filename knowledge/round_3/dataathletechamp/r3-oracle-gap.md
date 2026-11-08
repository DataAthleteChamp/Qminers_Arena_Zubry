# Round 3: where perfect foresight beats the incumbent

Question: why does U4 (`r3_alpha_follower_p1_sw3.py`, R3 public 330,208,
validation 411,302) trail a ±100 perfect-foresight trader, and which part of
the gap can live features capture?

Source: `experiments/round_3/dataathletechamp/20261108-r3-w6-oracle-gap-001/`
(`REPORT.md`; reproduction commands listed there). Tapes: R3 public
(sha256 1021586b…) and R2 public (88ff641e…), 6,000 s each. Oracle: dynamic
programme over {−100, 0, +100} with 10 ms decisions, crossing at the touch
5 ms later. Incumbent paths come from the official engine. This is a
descriptive grid study; it is not an engine result for any new rule.

## Gap

| | R3 | R2 |
|---|---:|---:|
| oracle net at touch | 1,238,000 (206/s) | 920,500 (153/s) |
| incumbent engine PnL | 330,208 | 109,317 |
| mid-to-mid gap | 867,938 | 738,380 |

- 97% of the gap is time spent holding the opposite sign.
- **Late entry**, 57% of the gap (54% on R2): the oracle switches about 0.3 s
  before us, costing about 2.7 ticks × 200 lots per episode.
- **Counter-swings during our 5 s hold**, 36%: 0.75–0.9 s, about 4.5 ticks
  each.
- A large part of the gap is V-shaped turns: the prior 1 s move runs against
  the oracle's new direction and every live signal still points the old way.
  Fade and reversal triggers lose 13k–443k on both tapes, so treat this part
  as uncapturable.
- Our execution costs 0.98 ticks/lot against the oracle's 0.60. We cross
  right after sweeps, when the spread averages 1.58 ticks, and waiting for a
  1-tick spread does not recover the difference.

## Live information that leads the move

- New resting inserts near the touch carry almost nothing: within ±2.5 ticks
  of the mid, the correlation with the next 0.5 s move is −0.015 (R3) and
  +0.055 (R2). All visible inserts within ±20 ticks give 0.227 / 0.145.
  The live fair value in U4 (`FV_DEPTH = 2`) was therefore measuring the
  wrong orders.
- Trigger: net market-taker volume over 200 ms ≥ 300 lots **and** a 200 ms
  mean of (new insert price − prior mid) ≥ 1.0 tick in the same direction.
  It fired 1,826 times on R3 and 946 on R2.

| | R3 | R2 |
|---|---:|---:|
| signed mid move at 2 s (ticks) | +2.75 | +1.89 |
| executable, touch to touch, at 2 s (ticks per unit) | +1.32 | +0.28 |
| tape halves (move at 2 s) | +2.88 / +2.62 | +1.94 / +1.86 |
| oracle agreement | 0.91 | 0.89 |

- The thresholds were chosen on R3; R2 is the replication. The official-engine
  test is `r3-follower-deepfv.md` (branch `r3-da-deepfv`).

## Rejected as triggers

- Momentum-only triggers (recent move, sweep ≥ 2) lose 30k–104k.
- Imbalance-only triggers lose 218k–912k.
- Fade triggers lose 13k–443k.
