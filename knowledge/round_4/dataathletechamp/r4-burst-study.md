# Round 4: bursts above 100 lots after huge orders do not pay

Question: the owner notes that on R4 public, aggressive ±1,000-lot positions
around huge market orders exceed 4M with foresight, despite the penalty.
Can we capture that by detecting the huge orders live?

Penalty arithmetic: the penalty is a flat 10,000 PnL per second while
|inventory| > 100, independent of size. With 900 extra lots it is
11.1 ticks per extra lot per second (2.2 at 200 ms, 5.6 at 500 ms). Crossing
in and out with 900 lots adds the spread plus depth walking.

## Event study after detection
Script: `experiments/round_4/dataathletechamp/20261108-r4-burst-study-001/huge_taker_study.py`.
We act 5 ms after the huge taker trades, buy at the touch and exit at the
opposite touch. Depth walking is ignored, so the figures are optimistic.
Net ticks per lot:

| R4 event | n | 200 ms | 500 ms | 1 s |
|---|---:|---:|---:|---:|
| fill >= 1,000 lots | 810 | −0.11 | +0.79 | +1.63 |
| fill >= 2,000 | 114 | −0.04 | +1.11 | +2.35 |
| span >= 5 ticks | 161 | +1.12 | +2.55 | +4.53 |
| fill >= 1,000 & span >= 3 | 134 | +1.54 | +3.40 | +5.73 |
| span >= 10 | 7 | +7.43 | +9.14 | +10.43 |
| penalty per extra lot (900 extra) | | 2.22 | 5.56 | 11.11 |

Every frequent event class stays below the penalty at every horizon, before
any depth cost. R3 and R2 are weaker still. Only 10+-tick sweeps clear it, and
there are 7 of those per 6,000 s.

## Official engine: jump rider (naive file, `FAMILY "jump"`)
Grid: `experiments/round_4/dataathletechamp/20261108-r4-jump-rider-001/`.

| variant | R4 PnL | penalty |
|---|---:|---:|
| 20-tick move in 1 s, 1,000 lots, hold 0.5 s | −902,611 | 1,131,183 |
| 10-tick move in 0.5 s, 1,000 lots, hold 0.2 s | −2,293,141 | 1,881,060 |
| 6-tick move in 0.3 s, 300 lots, hold 0.2 s | −2,635,470 | 2,734,154 |

## Conclusion
Above-limit bursts need foresight of the huge order before it trades. The
best live leading information we have (deep-insert fair value, the G-insert
class estimator, taker flow) predicts 1 s moves with correlation of about
0.2–0.3. Expected moves after those triggers are 2–5 ticks at 1 s, far below
11 ticks per extra lot per second. Keep ±100 as a hard cap unless a
predictor with near-perfect timing of huge orders is found.
