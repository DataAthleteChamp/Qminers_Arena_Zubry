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
