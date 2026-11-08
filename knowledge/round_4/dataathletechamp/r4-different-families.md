# Round 4: significantly different strategy families (late-round sweep)

Owner request at 10:34: find strategy families that differ from the informed-flow follower. Waves of
research and parallel builds; deadlines driven by the 12:00 close.

## 1. Imitation of the hindsight-optimal ±100 policy — REJECTED (`imitate.py`, `imitate.txt`, `imitate_wide.txt`)

Folder: `experiments/round_4/dataathletechamp/20261108-r4-burst-predictor-001/`.

- **Oracle.** A DP over {−100, +100} on the 10 ms grid.
  - Gain: s × 100 × Δmid from t + 5 ms.
  - Switching cost: 200 × (spread/2 + 0.2).
  - Oracle PnL: R4 1,621,220 (1,572 flips), R3 1,158,840, R2 854,640.
  - U2's recorded engine positions, scored with the same model: R4 867,760, R3 405,740, R2 161,140.
  - U2 is on the oracle's side 61–65% of the time.
- **Model.** HistGradientBoosting on 107 live features (`feats` + `msg`) predicting the oracle side.
  - It matches the oracle better than U2 does: R4 0.70 vs 0.65, R3 0.66 vs 0.61.
- **Policy.** Hysteresis bands on p, i.e. go long only above 0.5 + h and short only below 0.5 − h.

| test (Δ vs U2, same cost model) | h 0.30 | h 0.35 | h 0.40 |
|---|---:|---:|---:|
| R4, trained on R3+R2 | +60,400 | −65,080 | −199,480 |
| R4 2nd half, trained on 1st | −5,840 | −4,040 | −14,960 |
| R4 1st half, trained on 2nd | −34,980 | −43,460 | −125,980 |
| R3, trained on R4+R2 | −78,740 | −40,060 | −132,920 |

- **Bands.** Narrower bands churn (h 0 makes 12–23k flips and loses millions).
- **Verdict.** At its best band the imitation policy only ties U2.
- **Reading.** A trigger follower and a 107-feature model trained to copy the optimal policy converge to
  the same PnL. This is strong evidence that ±100 strategies sit at the ceiling of what visible
  information predicts here; the rest of the oracle gap is unforecastable latent-price innovation.

## 2. Latent-fair-value-skewed market maker — REJECTED (`20261108-r4-mm-001/`, official engine)

- **Design.**
  - Quotes at bid = min(best bid, floor(FV − EDGE)) and ask = max(best ask, ceil(FV + EDGE)), size Q.
  - FV = 0.5 × (max new bid insert + min new ask insert) over a short window, as in the follower's `_fv`.
  - Inventory skew k; |inventory| ≤ 100.
  - Quotes are pulled for T_TOX ms after sweeps or 200 ms flow ≥ 300.

| variant | R4 | R3 | R2 | R4 1 s markout per lot |
|---|---:|---:|---:|---:|
| EDGE 0.5, Q 50 | −312,079 | −115,185 | −65,341 | −1.45 |
| EDGE 1, Q 50 | −200,022 | −85,158 | −53,552 | −2.34 |
| EDGE 2, Q 50 | −139,074 | −58,289 | −40,256 | −5.70 |
| EDGE 2, Q 50, T_TOX 2000 (least bad) | −44,623 | −37,354 | −27,435 | −22.2 |

- **Every variant loses on every tape.** The informed IOC takers make every resting quote toxic: the
  markout is −1.4 to −22 ticks against +0.6 to +2.2 of spread earned.
- **Wider quotes and longer pulls only trade less**, and each lot filled is more toxic.
- **The fair-value skew is worse than a naive touch maker** (−1.45 vs −1.01 at EDGE 0.5).
- **The family is closed for this generator.** That matches R3 (`r3-aged-maker.md`).

## 3. Literature and competition review

Pending (`experiments/round_4/dataathletechamp/20261108-r4-lit-review-001/REPORT.md`).
