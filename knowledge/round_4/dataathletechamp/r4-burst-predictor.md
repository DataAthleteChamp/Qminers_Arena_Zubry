# Round 4: a model on the recent trade/quote window predicts volatility, not bursts

Experiment: `experiments/round_4/dataathletechamp/20261108-r4-burst-predictor-001/`
(`build_features.py`, `predict.py`, `quiet_check.py`, `build_msg_features.py`, `msg_direction.py`;
outputs in the matching `.txt` files and `log_*.txt`).

## Question

The owner asked whether a prediction model on the recent stream of trades can detect huge orders and
big moves before they happen. The test is whether that is good enough for bursts above 100 lots,
which make about 4M with foresight. A follow-up question: do one-sided cancellations or changes in
request volume carry extra information?

## Setup

- **Decision grid:** every 10 ms on R4, R3 and R2 public (597k rows per tape; the first 30 s are
  warm-up). Labels start at t+5 ms, our order latency.
- **Features:** 63 live-visible, causal features from the trailing window, grouped as follows.

  | Group | Features |
  |---|---|
  | trades | signed and gross flow over 50 ms – 5 s |
  | takers | taker count; A-sweeps (span ≥ 3 or fill ≥ 500); last sweep sign and age; last taker fill |
  | book | spread; top sizes and imbalance; mid moves over 50 ms – 30 s; realized mid activity over 1–30 s |
  | inserts | visible G inserts (within 20 ticks): near-touch counts per side, spread-improving inserts, mean placement vs mid |
  | cancels | visible cancels near the touch per side |
  | hidden IOCs | order-id gaps: counts, gap size, age |

  A further 44 message features cover:
  - per-side insert and cancel counts and near-touch volumes over 100 ms – 10 s;
  - net near-touch liquidity change (inserted − cancelled − consumed);
  - message-rate surges (100 ms vs 1 s, 1 s vs 10 s);
  - cancel/insert ratios.
- **Models:**
  - HistGradientBoosting with fixed parameters (200 trees, 31 leaves, min leaf 500); nothing is tuned
    on test rows.
  - Ridge and HGB regressors for direction.
- **Out-of-sample splits:**
  - XR: train R3+R2, test R4.
  - R4T: two-fold, R4 first half vs second half.
  - LOTO: train two tapes, test the third.
  - CIs come from a 60 s block bootstrap.
- **Burst economics:**
  - Debounced episodes: enter at the touch at t+5 ms and exit at the opposite touch after H.
  - Each episode pays the flat 10,000/s penalty spread over 900 extra lots (2.22 / 5.56 / 11.1 ticks
    per lot at 200 ms / 500 ms / 1 s).
  - No depth walk is included, so results are optimistic.

## Results

### 1. Big moves are predictable, mostly from the volatility state

AUC, with precision at the top 0.1% of rows in brackets. "vol" = realized mid activity, spread and
time since the last mid change only.

| test | target (base rate) | all features | vol only | all − vol (95% CI) |
|---|---|---:|---:|---:|
| XR → R4 | \|500 ms move\| ≥ 10 (1.74%) | 0.869 (0.41) | 0.861 (0.17) | +0.008 [−0.000, +0.019] |
| XR → R4 | \|1 s move\| ≥ 20 (0.93%) | 0.890 (0.76) | 0.871 (0.47) | +0.022 [+0.001, +0.045] |
| XR → R4 | huge sweep within 200 ms (0.78%) | 0.871 (0.10) | 0.862 (0.06) | +0.011 [−0.003, +0.021] |
| R4T, two folds | \|500 ms move\| ≥ 10 | 0.908 / 0.904 | 0.865 / 0.860 | +0.044 / +0.043 (both CIs > 0) |
| LOTO → R3 / R2 | \|500 ms move\| ≥ 10 | 0.907 / 0.944 | 0.882 / 0.932 | +0.024 / +0.010 (both CIs > 0) |

- **Feature groups (XR, permutation):**
  - Book state carries almost everything (AUC drop 0.115).
  - Visible inserts drop it by 0.026.
  - Sweeps, cancels, flow and hidden IOCs each drop it by ≤ 0.006.
- **Hidden-IOC features add nothing beyond volatility:** vol+hidden − vol = +0.000 / +0.009 / +0.006
  AUC (XR / R4T / LOTO R3). The precursor statistics in `r4-hidden-ioc-precursor.md` are mostly a
  volatility-regime effect.
- **The "foresight" in quiet states is a wide-spread artifact:**
  - 98% of the model's top 0.1% rows have a spread ≥ 2 ticks, where one quote refill jumps the mid.
  - In quiet states with a 1-tick spread (41% of rows, 3.4% of big moves), precision is only 4.6%
    at the top 1% of rows and 15% at the top 0.1%.
- **Huge sweeps cannot be timed:** at most 10% precision even at the top 0.1%.

### 2. Bursts on model alerts lose; only foresight pays

R4 test (XR); burst PnL is for 900 extra lots at touch prices.

| H | oracle (true timing and side) | true timing, model side | model alerts P ≥ 0.15 / 0.3 / 0.4 / 0.5 |
|---|---:|---:|---:|
| 200 ms | +2.75M | +0.62M [+0.02, +1.19] | −554k / −6k / +113k (28 eps) / +11k (11 eps) |
| 500 ms | +2.33M | −0.34M | −1.30M / −25k / +180k (48 eps) / −99k |
| 1 s | +1.73M | −2.45M | all negative |

- On the R4 temporal halves and on R3/R2 the model alerts lose at almost every threshold. Most 95% CIs
  are below zero.
- The few positive buckets are small (7–48 episodes) and not monotonic in the threshold.
- The touch held 900 lots in only 0–8% of alert episodes, so a real depth walk adds further cost.
- **Official engine** (`r4-hidden-triggers.md`): bursts on hidden-IOC strong events lose even before
  the penalty.

So the 2–3M "foresight" profit needs near-perfect timing and direction. The visible data supports
neither.

### 3. One-sided cancels, request surges and quote placement

| feature | R4 | R3 | R2 | reading |
|---|---:|---:|---:|---|
| near-touch insert count imbalance, bid − ask over 200 ms (`sG_200`) | +0.127 | +0.059 | +0.047 | quote placement leads |
| visible insert count imbalance over 1 s (`i_imb_1000`) | +0.120 | +0.044 | +0.026 | leads |
| near-touch insert volume imbalance over 200 ms | +0.099 | +0.035 | +0.006 | weak off R4 |
| cancel count imbalance, ask − bid over 1 s | −0.027 | −0.020 | +0.014 | cancels follow |
| near-touch cancel volume imbalance over 1 s | −0.003 | −0.005 | +0.004 | cancels follow |
| net near-touch liquidity imbalance over 1 s | +0.024 | −0.021 | −0.008 | nothing |

The figures are correlations with the 1 s move after removing a linear fit on flow, mid moves, top
imbalance and placement.

- **Cancellations on one side carry no information beyond flow and the mid move.** Raw correlations are
  +0.10–0.29, because cancels react to the move that has already happened.
- **Out-of-sample direction:** message features raise the correlation with the clipped 1 s move by
  +0.012 to +0.028 over a strong baseline (0.49–0.56). All CIs are above zero (XR, both R4T folds).
  - Most of this comes from insert placement.
  - Beyond the older insert features (`sG`, `impr`) the gain is ≤ 0.007.
  - U7's P1 gate already holds spread-improving insert intensities (`ib50`, `ia200`, ...) and
    extreme-insert FV, but not the near-touch insert-count imbalance.
- **Request-rate surges add nothing to big-move timing:** AUC +(−0.0009) [−0.007, +0.005].
- Almost every visible G order is cancelled: about 195 inserts/s vs 195 cancels/s on R4. The market
  is mostly re-quoting.

## Conclusions

- No burst rule from this model is worth testing in the engine. Volatility clustering and wide-spread
  states are already where the follower holds ±100.
- The only live signal that leads price is **where new quotes are placed**, the same mechanism as
  TRIG1/TRIG2.
  - It is strongest on R4 public and weaker on R3/R2.
  - It supports TRIG2 being real on R4-generator tapes.
  - The synthetic stress test penalised U2 only because those tapes place quotes far deeper than R4
    does (`r4-trig2-candidates.md`).
- **Possible engine test:** add the near-touch insert-count imbalance to the P1 gate (same pooled
  R3+R2 ridge fit). The expected gain is small.
- Keep the feature builder and predictor as research tools. There is no strategy change.
