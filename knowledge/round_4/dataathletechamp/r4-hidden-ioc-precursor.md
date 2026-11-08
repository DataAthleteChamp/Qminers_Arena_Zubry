# Round 4: hidden IOCs are a live, leading indicator of big moves

Question: is there a live signal that comes before the bursts (big, fast
moves) rather than after them?

Mechanism. Market IOCs are priced off the near-future price, and their side
looks random. When a big move is coming, IOCs on the move's side sweep the
book. IOCs on the other side have limits that don't reach the opposite touch,
so they never trade or rest: they are "hidden". The live feed never shows
them, but every insert consumes the next order ID. A gap in the IDs of newly
visible market orders (snapshot orders within the 20-tick public depth, plus
`taker_order_id` of trades) reveals them.

Scripts: `experiments/round_4/dataathletechamp/20261108-r4-burst-study-001/`
(`hidden_live_emulation.py`, `hidden_precursor.py`, `live_gap_parity.py`).
Public tapes R4, R3 and R2; descriptive statistics only, no strategy PnL yet.

## Detector

- **Exact offline emulation:** an insert is visible at its own event if it is
  a resting (G) order within 20 ticks of its own-side best, or an IOC (F)
  that trades. IDs are verified consecutive.
- **R4:** 2,276 invisible inserts (0.38/s), of which 2,211 are hidden IOCs
  and 65 deep G inserts: 97% purity. Detection delay from the hidden insert to
  the next visible insert is a median 4.1 ms (p90 16.3 ms). R3 and R2 behave
  the same (98% purity, about 4–5 ms).
- **Official-engine parity:** a lots-0 strategy running the live ID-gap logic
  on R4 finds 2,158 detections covering 2,262 missing IDs (99.4% of the
  emulation) in 28 s of CPU.

## What a detection means (mid move from detection + 5 ms; random times in brackets)

| R4 | +100 ms | +200 ms | +500 ms | +1 s |
|---|---:|---:|---:|---:|
| E\|move\| (ticks) | 1.92 (0.36) | 3.15 (0.69) | 5.50 (1.52) | 8.28 (2.70) |
| P(\|move\| >= 10) | 0.018 (0.001) | 0.033 (0.003) | 0.099 (0.017) | 0.250 (0.071) |
| P(\|move\| >= 20) | 0.014 (0.0003) | 0.019 (0.0006) | 0.036 (0.002) | 0.076 (0.009) |

Clusters sharpen it. With at least 3 detections in 300 ms (0.063/s on R4),
E|move| over 1 s is 12.56 ticks and P(>= 20 ticks) is 0.174, against 0.0085
at random times. R3 (7.29, 0.075) and R2 (6.99, 0.087) show the same pattern.

Lead: of big moves (>= 10 ticks within 500 ms, at least 2 s apart; 242 on
R4), 33% had a detection in the previous 500 ms (12% for random times) and
48% in the previous 1 s. On R3 the figures are 39% and 49%, on R2 30% and 39%.

## Direction (first evidence; not yet a live rule)

- When a huge sweep (span >= 5, or fill >= 1,000 with span >= 3) follows
  within 500 ms, it goes against the hidden IOC's unseen side 91% of the time
  (R3 93%).
- The sign of taker flow over the 200 ms before the hidden IOC matches that
  sweep's direction 90% of the time (R3 94%), for the subset followed by a
  huge sweep.
- Mid move after a hidden IOC, signed by the prior 200 ms flow: +1.51 / +2.94
  / +4.37 ticks at 0.2 / 0.5 / 1 s on R4 (R3 +1.34 / +2.23 / +2.95).

## Implications

- Within ±100, a detection can arm the follower to act on the first visible
  sweep, or to enter in the prior-flow direction. That targets the 71%
  late-entry gap (`r4-oracle-gap.md`).
- Bursts above 100 lots still need more. 900 extra lots cost 11.1 ticks per
  lot per second. Clusters of 3+ detections move 12.6 ticks in 1 s on
  average, without direction, so only a sharp direction rule plus a short
  hold could pay. Test that in the official engine before any use.

## Direction and strength at detection time (`hidden_features.py`, `hidden_gap2.py`, `hidden_strong_direction.py`)

Every feature here is live-observable at the detection time.

**All detections.** P(sign of feature = sign of the next 1 s move) and the
mean signed move in ticks, counting only events where both are non-zero:

| feature | R4 | R3 | R2 |
|---|---|---|---|
| signed taker flow, last 200 ms | 0.85 / +5.0 | 0.86 / +3.2 | 0.79 / +1.8 |
| last A-like sweep within 1 s | 0.86 / +5.1 | 0.85 / +3.6 | 0.78 / +1.2 |
| mid move, last 200 ms | 0.81 / +7.0 | 0.80 / +3.9 | 0.66 / +2.8 |
| deep-insert fair value, 200 ms | 0.81 / +3.5 | 0.81 / +2.6 | 0.75 / +1.2 |
| L1 queue imbalance | 0.67 / +2.2 | 0.68 / +1.7 | 0.63 / +0.6 |

A logistic model on these features, trained on R3 + R2 and tested untouched
on R4, is 82% accurate overall (+4.4 ticks signed at 1 s). On its most
confident half it is 92% accurate (+5.7 ticks at 1 s, +3.7 at 500 ms).

**Strength.** E|move 1 s| on R4 is 22.2 ticks when one ID gap hides 2 or more
inserts (7.7 for one), 11.0 when the spread is 2 ticks or more (6.8 at
1 tick), and 12.6 with 3+ detections in 300 ms. Medians are much smaller:
1.8–5.8 ticks for gap >= 2.

**Strong events** (gap >= 2 or 3+ detections in 300 ms; 429 on R4, 0.07/s):

| | R4 | R3 | R2 |
|---|---:|---:|---:|
| P(\|1 s move\| >= 20 ticks) | 0.177 | 0.075 | 0.101 |
| direction from last sweep within 1 s | 0.82 | 0.86 | 0.70 |
| direction from 200 ms mid move | 0.70 (+11.1 ticks at 1 s) | 0.79 (+4.7) | 0.61 (+4.2) |
| top-5 events' share of total \|move\| | 12% | 7% | 13% |

**Burst economics.** With 900 extra lots the penalty is 2.2 / 5.6 / 11.1 ticks
per lot at 0.2 / 0.5 / 1 s, plus about 3+ ticks to cross in and out, and books
are thinner exactly at these moments. On a rough touch-to-touch basis with the
flow sign, strong events are borderline on R4 (about −0.4 to +6.5 per lot at
200 ms depending on the subset) and negative on R3 and R2. The
official-engine burst test (`r4-hidden-triggers.md`) decides. The robust use
is early entry within ±100.
