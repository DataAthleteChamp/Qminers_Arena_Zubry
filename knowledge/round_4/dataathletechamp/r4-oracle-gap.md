# Round 4: where perfect foresight beats U7

Source: `experiments/round_4/dataathletechamp/20261108-r4-w2-oracle-gap-001/`
(`REPORT.md`, `run_variant.py`, `variants.log`). Every rule result below is
an official-engine run. U7 reproduces 821,692 on R4 and 413,588 on R3.

Oracle (±100, 10 ms decisions, crossing at the touch): 1,686,300 on R4
(281/s; 1,577 switches; never flat). The mid-price gap to U7 is 709,552,
and U7 trades 1,931 times.

| Gap component | n | Gap | Share | Median duration |
|---|---:|---:|---:|---:|
| **Late entry** (oracle flips first) | 993 | 501,515 | **71%** | 0.16 s |
| Counter-swing during our hold | 149 | 128,926 | 18% | 0.69 s |
| False flip (we flip, then revert) | 308 | 50,550 | 7% | 1.16 s |
| Early flip (we lead, oracle follows) | 278 | 22,450 | 3% | 0.26 s |
| Flat time | – | 4,900 | 0.7% | – |

- U7 does not exit too early on R4: it is flat 0.1% of the time and exits
  to flat only 16 times. Leaving or flipping away from 5–30 s oracle trends
  costs about 61k (9% of the gap).
- 69% of our flips agree with the oracle. The best flips are against a
  ≥25-tick 30 s trend; R4's 10 s trends end in sharp V-turns.
- Execution: 0.98 ticks/lot for us vs 0.62 for the oracle. We cross at an
  average spread of 1.62 vs 1.25.

Rules tested (ΔPnL vs U7, R4 / R3):

| Rule | R4 | R3 |
|---|---:|---:|
| HOLD_S 10 (20 identical) | +9.4k (mostly the first half) | +0.4k |
| no flip while the 30 s trend agrees (≥25 / ≥10 ticks) | −425k / −543k | −139k (≥25) |
| no flip while the 10 s trend agrees (≥10) | −359k | −220k |
| no chasing after a ≥25-tick 30 s trend | −321k | −71k |
| skip the gate for signals against the trend | −11k to −22k | −6k to −11k |
| wait up to 0.2–0.5 s for a 1-tick spread before flipping | −11k to −12k | −11k to −12k |
| take profit after a big favourable move (grid estimate) | −240k to −597k | −31k to −234k |

Conclusion: reject trend-based no-flip, no-chasing, take-profit,
gate-bypass and spread-wait rules. The next lever is faster reversal
detection on thin, wide books, where the late-entry gap starts; it is being
tested in `r4-reversal-triggers.md`.
