# Round 4: bot fingerprints — one serial generator, two scheduled add-on bots and one strong deep-insert signal

**Question.** Is R4 order flow one automated agent or several? What is each type's signature and
strategy? Do any type's live-visible actions predict the mid beyond the last 200 ms of taker flow and
mid move?

**Source.** `experiments/round_4/dataathletechamp/20261108-r4-bot-forensics-001/` (`REPORT.md`, scripts
and text outputs).
- Tapes: R4 `61c0b6d1…`, R3 `1021586b…`, R2 `88ff641e…`.
- Official null replays: R4 `46adf403…`, R3 `9c5c4f87…`, R2 `1e745b8b…`.
- Maker ids came from an official-engine null run (`maker_fills.py`).
- Descriptive only. No strategy was run.

**Windows.** Discovery is R4 0–3,000 s (R4a) plus R3. Holdout is R4 3,000–6,000 s (R4b) plus R2. The
cadences and the offset-8 cut-off were found on the full R4 tape, so R3 and R2 are the clean holdouts
for those.

**Markouts.**
- Signed mid move from t + 5 ms. "Residual" means beyond an OLS baseline on the last 200 ms of flow and
  mid move, fit on a 10 ms grid of the same window. The robust version also uses 1 s flow and mid
  move and the spread.
- CIs: 60 s block bootstrap.

## Verdict

- **One serial generator makes the base flow (about 99.7% of rows).** Two scheduled bots sit on top of
  it.
- **No batching.** Every row has a unique µs timestamp on all three tapes (0 shared-µs rows; Poisson
  rows would give about 0.04%).
- **Arrivals.** They are near-Poisson (inter-arrival CV 1.05–1.13) with no periodicity, but the intensity
  is modulated: per-second G counts have SD 27.6 against 14.0 for Poisson.
- **Side is a fair coin per event.** The 1 s bid-share SD is exactly binomial.
- **No reactive bot.** There is no fixed reaction latency after trades or BBO changes.

| type | R4 share of rows | signature | inferred strategy |
|---|---:|---|---|
| Base G quoter | 48.8% inserts + 48.8% cancels | Poisson; offset 0–7 behind own best (touch 44%, b1 30%); smooth heavy-tailed size (mode 1, median 18; larger when deeper); **lifetime pre-drawn at insert** (median 0.31 s; independent of offset and size); 13.5% of cancel rows target already fully filled orders (no-ops, invisible live) | Zero-intelligence quoting around a **latent fair price**. Placement encodes the latent price; size carries no information. |
| Deep G component (R3/R4, not R2) | ~7% of G | b2–b7, larger (size ≈ 57), longer-lived (0.5 s, heavy tail); GMM finds it on R4 but not R2 | Deep book provider, still placed around the latent price (b3–5 residual −2.0 to −2.3 at 1 s on R4) |
| Base IOC taker | 2.4% | Poisson, 9.7/s; smooth size (median 63); limit = latent near-future price ± noise. Hidden IOCs (limit short of the touch) share the size law; P(hidden) is 0.42 at spread ≥ 4 vs 0.03 at 1 | Informed taker. Reach ≥ 4 has residual +5.0 to +5.8 at 1 s (R4), +2.6 (R3). |
| **160-lot IOC TWAP (R4 only)** | 0.065% | Exactly 160 lots, exactly 500,000 µs apart, same side; 40 parents of 8–58 children (median 17 s, about 6,000 lots); 49% buys | Execution algorithm working parent orders |
| **2 ms ladder pairs (R3/R4)** | 0.26% | 2 (up to 4) same-size, same-side G orders exactly 2 ms apart; 2nd child 1–3 ticks deeper; offsets 2–7; sizes 38–49 (R4) / 23–32 (R3); 0.5 trains/s | Depth layering. **Uninformative** (1 s residual −0.32 / +0.03 / +0.09 on R4a / R4b / R3). |

## Cancellation behaviour by type (for the cancel/surge study)

- **Cancels are scheduled at insert.**
  - The lifetime law is the same on every tape (1/5/10% quantiles 20/48/75 ms).
  - Cancels ignore fills: there are 157,515 no-op cancels of filled orders.
  - There are no fleeting orders: 6 orders live < 1 ms.
- **What a cancel signal can and cannot carry.**
  - A one-sided cancel surge echoes an insert surge about 0.3 s earlier.
  - It also echoes how far the price has drifted since those orders went in.
  - It does not carry intent.
- **Cancel residuals at 1 s.**
  - At the best: +0.05 [−0.07, 0.18] on R4a, +0.04 on R4b, −0.03 on R3, +0.01 on R2. Effectively zero.
  - Cancels of orders now 6+ behind: −2.6 on R4a and −2.0 on R4b (signed against the order's side).
    This is momentum: the order was left behind by the move.
- **Scheduled bots.** TWAP children are IOCs and never cancel. Ladder children live longer (median
  0.45 s on R4, 0.62 s on R3).

## Live-visible signals (residual 1 s, 95% CI)

| signal | R4a | R4b | R3 | R2 |
|---|---|---|---|---|
| **DEEP8 episode**: new G order 8–20 behind own best, direction opposite its side; first per direction per 1 s; 0.087/s on R4 | **+5.35 [4.27, 6.26]** | **+5.47 [4.54, 6.51]** | +3.00 [2.54, 3.57] | +1.24 [−0.04, 2.52] |
| DEEP8 episode, residual at 2 s | +9.23 [7.17, 11.27] | +8.53 [6.51, 10.41] | +4.03 [3.31, 4.77] | +0.94 [−0.48, 2.53] |
| DEEP8, touch-to-touch per lot at 1 / 2 s (cross in and out) | +6.1 / +10.9 | +6.0 / +9.9 | +2.8 / +4.0 | −0.2 / −0.5 |
| G insert inside the spread (3.4/s) | +2.14 [1.54, 2.63] | +1.85 [1.34, 2.31] | +0.53 | +0.31 |
| TWAP child ≥ 2nd, rich baseline | +0.52 [−0.25, 1.28] | +0.37 [0.02, 0.76] | absent | absent |
| TWAP hold from 2nd child to first missed slot (mid move, n) | +12.3 (19) | +9.1 (26) | absent | absent |

**DEEP8 detail.**
- **A placement break.** The base placement law ends at offset 7. Inserts drop 12× from offset 7 to
  offset 8.
- **The move jumps.** The raw implied 1 s move is +3.5 at offset 7 and +12.4 at offset 8, with 95%
  direction accuracy. It is the same in both R4 halves.
- **Live timing.** The order is visible in the snapshot at the insert. Only +0.3 ticks have moved by
  t + 5 ms.
- **Book state.** The spread is 1 tick 74–79% of the time. The touch we would take has a median of
  76–97 lots.
- **Overlap.** The 200 ms flow already agrees in 91% of episodes, so a follower is often positioned
  already.
- **Split by prior flow** (`deep8_split.py`; R4 first / second half; raw mid move at 1 s, t2t =
  touch-to-touch per lot):

  | prior flow | R4 first half | R4 second half | R3 (halves) |
  |---|---|---|---|
  | 200 ms flow agrees | +8.6 (P 0.89), t2t +7.0 | +8.1 (P 0.87), t2t +6.6 | +4.5 / +4.4 |
  | 200 ms flow zero or against (n = 49 / 38) | +3.6, t2t +1.7 | +4.9, t2t +3.0 | +3.6 / +3.6 |
  | 1 s flow and 1 s mid both zero or against (n = 35 / 36) | −0.6 | +2.1 | +2.7 / +0.8 |

  DEEP8 mainly says which ongoing moves will extend. As a cold-start entry it is close to nothing.
- **TRIG2 cannot see it.** TRIG2 clips k at 7, which merges offsets ≥ 8 into the k = 7 cell. Real
  offset-7 inserts average only +3.5.
- **R2 weakness.** The effect is weak on R2 because R2 placement is touch-centric (b3+ is 3%).

**TWAP live identification.**
- A taker whose fills sum to exactly 160 lots is the TWAP 1,410 times out of 1,414.
- 90.6% of children fill completely.
- The next child's time is known to the µs.

## Official-engine tests (paired against U1/U7; do not upload without them)

1. **`DEEP8_ON`**
   - **Rule.** Track the max market order id seen. For a new market G order with distance d = best −
     price behind its own-side best and 8 ≤ d ≤ 20, call `_on_signal(sign = −side)` with A priority.
     Use a 1 s same-direction cooldown and the existing hold.
   - **Variants.** `DEEP8_MIN` 8 / 10 / 12; gated and ungated. `DEEP8_MODE` = `entry` / `extend` /
     `veto`:
     - `extend` lengthens the hold by 2 s when DEEP8 agrees with our position;
     - `veto` blocks a flip against a DEEP8 signal for 1 s.

     The split above suggests `extend` and `veto` are the likely payers.
   - **Expected sign.** + on R4 and R3, about 0 on R2.
   - **Reject** if ΔR4 < +25k (the noise band), ΔR3 < 0 or ΔR2 < −10k.
2. **`TWAP160_ON`**
   - **Rule.** Fire when a market taker's fills total exactly 160 lots and the previous such taker on
     the same side came 500 ms ± 2 ms earlier. Bias or enter in that direction. Release at the first
     missed slot (last + 510 ms).
   - **Expected sign.** + on R4 only.
   - **Sanity check.** It must not fire on R3 or R2: 0 trains there, so Δ = 0.
   - **Reject** if ΔR4 < +10k or any change on R3 or R2.
3. **`TRIG2_K8`**
   - **Rule.** Give offset ≥ 8 its own TRIG2 class instead of clipping to 7.
   - **Expected sign.** Small +.
   - **Reject** inside ±25k on R4 or < 0 on R3.
4. **Low priority.** Drop 2 ms ladder children from deep-placement features. They are only 0.5% of G
   orders and uninformative.

## Limitations

- **Public tapes only.** We do not know whether private R4 contains the TWAP or ladder agents or the
  offset-8 break. The TWAP is absent on R3 and R2.
- **Not PnL.**
  - Per-event markouts overlap.
  - They ignore the ±100 cap, queues, depth beyond L1 and existing U7 positions.
- **Thresholds and evidence status.**
  - Offset ≥ 8 and the cadences were picked from the full R4 tape.
  - R3 and R2 are the out-of-sample checks.
  - The TWAP rows rest on only 45 trains.
- **GMM.** The GaussianMixture fit degenerates on the integer offset. It is descriptive support only.
