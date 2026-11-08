# Round 3 U7: stacking validated triggers on the refit follower

Question: can earlier, information-based triggers move the refit follower
(U6, validation 415,828) by a step rather than by a few percent?

Base: U6 `r3_alpha_follower_p1_sw3_rlin0.py` (e3102973…). It is the D1
follower (A: sweep span >= 3, or filled >= 500, or run >= 4 with filled >= 100)
plus the P1 flip gate, using a ridge refit on full R3 + R2 with intercept 0.
Candidate: `strategies/round_3/dataathletechamp/r3_follower_u7_flow_deepfv.py`
(sha256 d2a0fc9c…f897). It adds two triggers, each treated exactly like an A
event:

- `FLOW_TRIG = 600`: |signed market-taker volume over 200 ms| >= 600 lots.
  From `r3-naive-families.md`.
- `TRIG1` (300 / 0.5, gated): net taker flow >= 300 lots **and** a 200 ms mean
  of (new resting insert price − prior mid) over all visible depth >= 0.5 tick
  in the same direction. Ported from `r3-follower-deepfv.md`; the evidence
  is in `r3-oracle-gap.md`.

Runner: `experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py`.
Grids are in `20261108-r3-u6-flowtrig-001`, `20261108-r3-u6-deepfv-001`,
`20261108-r3-u7-burst-001`, `20261108-r3-u7-aflip-001` and
`20261108-r3-u7-robust-001`. Official CLI on R3: 413,588, penalty 0.

| variant on the U6 base | R3 | R3 eval/s | R2 |
|---|---:|---:|---:|
| U6 | 357,488 | 63.1 | 107,856 |
| + flow 600 | 382,252 | 68.0 | 149,502 |
| + TRIG1 300/0.5 gated | 406,906 | 74.1 | 154,315 |
| **+ both (U7)** | **413,588** | **74.6** | **167,166** |
| + both, TRIG1 300/1.0 ungated | 394,078 | 69.2 | 142,893 |

U7 neighbourhood (one change at a time; R3 / R2):

| setting | R3 | R2 |
|---|---:|---:|
| flow 400 / 800 | 390k / 409k | 157k / 157k |
| TRIG1 FV 0.35 / 0.75 | 401k / 388k | 175k / 165k |
| TRIG1 flow 200 / 400 | 415k / 377k | 166k / 154k |
| hold 4 s / 6 s | 393k / 413k | 159k / 171k |
| flip margin 0.8 / 1.2 | 387k / 380k | 166k / 140k |

Every neighbour stays well above U6 on both tapes. All runs had penalty 0.

## Rejected on top of U7

- More flow and fair-value windows (`20261108-r3-u7-flow2-001`,
  `20261108-r3-u7-flowspan-001`):
  - A second flow trigger at 100 ms/400, 500 ms/1000–1500 or
    1 s/1500–2500 adds at most +1.7k on R3 and nothing on R2.
  - TRIG1 windows of 100 ms or 400 ms (instead of 200 ms) are worse on
    both tapes.
  - Counting only multi-level sweeps toward FLOW_TRIG (300–800 lots) is
    worse on both tapes: 382–408k on R3, 146–159k on R2.
- The colleague's JumpBurst rule as a trigger (mid moves >= 2 ticks within
  100 ms at a 1-tick spread): R3 +2.4k, R2 −0.2k. Our flow and sweep triggers
  already fire on these bursts.
- Reversion overlay, motivated by the teammate tape study
  (`round3-public-tape-analysis.md`: momentum up to about 5 s, reversion over
  10 s–5 min on R3, trend on R2). Grid `20261108-r3-u7-reversion-001`.
  - Blocking same-sign entries and extensions once (mid − 60 s EMA) >= 15–35
    ticks in our favour: R3 409–413k, R2 153–166k.
  - Going flat at the same thresholds: R3 297–370k, R2 64–141k.
  - Both are worse than U7. The follower's edge sits at the 1–5 s momentum
    horizon; fighting it with the slower reversion costs more than it saves.
- A-signal thresholds on U7 (`20261108-r3-u7-athresh-001`): A_SWEEP 4 gives
  +2.9k on R3 and +1.0k on R2, which is noise-sized. A_SWEEP 2, RUN_MIN 3/5,
  BIG_FILL 400/700 and FILL_MIN 75/150 each lose on R3, R2 or both.
- Hidden-price G-class trigger (`r3-follower-trig2.md`) and exit flags
  (blocked-flat, giveback, adverse stop, opposite-flow flat;
  `r3-follower-exits.md`): none improves both tapes.
  - Standalone, JumpBurst makes R3 78,179 and R2 13,402; the owner reports
    154k on validation.
  - Its useful property is low exposure: it is flat outside 1 s bursts.
    That cannot be added to a strategy that already uses the whole ±100
    band.
- The alpha forecast as an ungated trigger (|2 s alpha| >= 2.0 / 2.5 / 3.0
  ticks on a 50 ms grid): R3 364k / 401k / 412k and R2 146k / 128k / 159k.
  All are worse than U7.

## Distribution check on synthetic tapes

Five v2 synthetic tapes from the calibrated generator
(`20261108-r3-generator-monte-carlo-001`, seeds s51–s53 base, s54
shallow-R2 placement, s55 more informed flow). They match R3 A on 1 s
volatility, short-horizon momentum and sweep drift, but have tighter
spreads. Absolute PnL levels from this generator are not credible, so use
the tapes for paired comparisons only. Script:
`20261108-r3-u7-distribution-001/` (`runner_syn.py`, `aggregate.py`).

| variant | s51 | s52 | s53 | s55 | s54 | mean | beats U7 |
|---|---:|---:|---:|---:|---:|---:|---:|
| U7 | 446,134 | 409,801 | 421,115 | 375,912 | 483,747 | 427,342 | – |
| U6-equivalent (both triggers off) | 434,096 | 403,090 | 404,050 | 371,573 | 463,269 | 415,216 | 0/5 |
| U4-equivalent (R3-only model) | 411,857 | 411,035 | 397,129 | 377,203 | 454,799 | 410,405 | 2/5 |
| TRIG1 flow 200 | 448,360 | 438,369 | 426,209 | 375,182 | 477,714 | 433,167 | 3/5 |
| flow 800 | 449,290 | 417,760 | 424,292 | 391,906 | 482,414 | 433,132 | 4/5 |
| hold 6 s / A_SWEEP 4 / TRIG1 FV 0.35 | | | | | | 425.7k / 421.4k / 425.8k | 1/5, 1/5, 2/5 |

- The trigger stack generalizes: U7 beats the U6-equivalent on all five
  synthetic tapes, on R3, on R2 and on the validation tape.
- No neighbour is clearly better. The best gain across the seven tapes is
  about 1%: TRIG1 flow 200 is +29.6k over seven tapes in total, and
  flow 800 trades an R2 loss for synthetic gains.
- U7 stays the final candidate.

## Limits

- R3 and R2 are in-sample. The TRIG1 thresholds came from the R3 oracle
  study, the flow threshold was chosen on both public tapes, and the model
  was fitted on both. The validation upload is the only out-of-sample check.
- The follower is still about ±100 almost all the time. Jump seconds on the
  validation tape (−56k to −134k for U1–U6) are not addressed.
