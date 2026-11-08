# Round 4: TRIG2 hidden-price trigger and the U2/U3 candidates

TRIG2 is the G-insert class estimator from the R3 latent-filter study,
implemented in `strategies/round_3/dataathletechamp/r3_follower_u7_trig2.py`
(flag `TRIG2_ON`; `r3-follower-trig2.md`). Each new resting insert's class
(ticks behind its own best, by spread) maps to an implied 1 s drift through a
66-cell lookup table. The 100 ms mean of these drifts fires an A-like signal
once it has held for 20 ms. On R3 it was noise (+0.1k). On R4 it helps.
Grids: `experiments/round_4/dataathletechamp/20261108-r4-trig2-001`, `-002`,
`-003` and `20261108-r4-u2-refine-001`. All runs had penalty 0.

| variant on U7 | R4 | R3 | R2 |
|---|---:|---:|---:|
| U7 | 821,692 | 413,588 | 167,166 |
| gated 1.06 | 827,719 | 421,315 | 167,747 |
| gated 0.95 / 1.0 / 1.06 / 1.12, hold 10 s | 843,147 / **840,594** / 837,141 / 834,203 | 420,318 / **421,747** / 421,678 / 415,924 | 169,580 / **172,626** / 172,815 / 172,815 |
| ungated 0.85 / 0.9 / 0.95 / 1.0 / 1.2 | 884,462 / 880,124 / 877,204 / 869,687 / 842,726 | 402,517 / 403,474 / 415,041 / 421,438 / 420,901 | 136,524 / 139,263 / 154,447 / 155,807 / 149,239 |
| **ungated 0.95, hold 10 s (U2)** | **886,626** | 415,404 | 159,515 |
| U2 with flip margin 0.9 / 1.1 | 897,664 / 865,542 | 391,744 / 401,142 | 155,628 / 136,160 |
| U2 with TRIG2 hold 0 / 50 ms | 844,274 / 853,172 | 406,141 / 411,993 | 171,598 / 174,591 |
| U2 with TRIG2 window 50 / 200 ms | 849,355 / 851,135 | 406,816 / 415,964 | 150,817 / 174,854 |
| U2 with TRIG1 ungated | 858,712 | 321,143 | 176,581 |

- **Gated (U3, `r4_u3_trig2_gated.py`, sha256 c128a6e3…):** +2.3% on R4,
  +2.0% on R3, +3.3% on R2. It improves on all three tapes, and its
  thresholds sit on a smooth plateau.
- **Ungated (U2, `r4_u2_trig2_ungated.py`, sha256 b239d85a…):** +7.9% on R4,
  +0.4% on R3, −4.6% on R2. A bet on R4-like momentum tapes. The 0.85–1.0
  plateau is smooth on R4.
- Treat differences under about ±25k on R4 as noise. Some single-flip
  changes move R4 by that much (`r4-reversal-triggers.md`).
- Both files match the runner in the official CLI on R4 (886,626 / 840,594,
  penalty 0) and pass preflight.

## Synthetic paired check (`20261108-r4-synthetic-001`, official engine)

- **Setup:**
  - The Monte Carlo generator was recalibrated to R4 and used to make 14 tapes of 6,000 s each.
  - U7, U2 and U3 ran in the official engine. Every run had penalty 0.
  - The runner reproduced the R4 public scores exactly.
- **What the tapes match and miss:**
  - They match R4's 1 s SD, spread and momentum profile (VR10 1.8–2.7).
  - None matches R4's G placement relative to the own best, which is TRIG2's input (b3+ 45% vs 13%).
  - None matches R4's IOC behaviour (43% of IOCs do not trade vs 4% on R4).
  - So this is a stress test of a placement shift, not R4 seed variation.

Paired mean differences (wins/losses vs U7):

| family | U2−U7 | U3−U7 | U2−U3 |
|---|---:|---:|---:|
| all 14 synthetic | −206k (0/14) | −57k (1/13) | −149k (0/14) |
| SWEEP (R4-like placement, weak momentum) | −7k (0/3) | +0.2k (1/2) | −7.5k |
| R4 public | +65k | +19k | +46k |

- **U2 under stress:**
  - U2's R4 edge comes from only 75 TRIG2 flips.
  - On the momentum tapes TRIG2 fires 4–6× as often, and U2 flips 1,450–1,900 times, losing about 250k.
  - U3's gate blocks most of these flips.
- **Decision:**
  - Do not upload U2.
  - U3 is the safer TRIG2 variant, but it is not better than U7 off R4.
  - U1 (U7 byte copy, validation 1,326,712) stays the working final.
