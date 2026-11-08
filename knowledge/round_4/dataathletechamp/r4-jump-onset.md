# Round 4: latent-jump onset trigger on the U2 follower

Experiment `20261108-r4-jump-onset-001`, branch `r4-da-jump`.

**Question.** Can a live detector of latent-price jump onsets add PnL to U2 on the official engine? U2 is
`r4_u2_trig2_ungated.py`: R4 886,626 / R3 415,404 / R2 159,515, penalty 0. The detector combines
clustered order-id gaps with the visible near-touch insert imbalance. It can act in two ways: an ungated
follower flip, or a burst beyond ±100.

**Answer.** One variant passes the pre-declared rule, but only just: `both` mode (the flip plus a burst
to ±300 for 50 ms, IOC cap 5) at W20/K3/spread ≤ 1. On the official engine it scores R4 912,274
(**+25,648**), R3 407,508 (−7,896) and R2 152,088 (−7,427), with the penalty already included. The R4 gain
is at the edge of the ±25k noise band and comes from five events. All other flip and burst variants
failed the rule. Bursts larger than ±300 or held longer than 50 ms lose heavily on R3/R2.

## Mechanism (from `20261108-r4-burst-predictor-001`)

When the latent price jumps, the new G orders on the jump's far side land 21–137 ticks behind their own
best. They are invisible beyond the 20-tick feed, but each one uses an order id, so it shows up as an id
GAP. The near side cannot cross, so its new orders pile in at the touch or inside the spread. The stale
near-touch orders are then cancelled on schedule, and the book collapses onto the deep orders.

## Implementation

`strategies/round_4/dataathletechamp/r4_follower_jump.py` is `r4_follower_hidden.py` (sha256
`a94f9585…`) plus `JMP_*` module flags, all off by default.

- **Hidden sum.** The sum of order-id gap sizes from the existing HID detector, over the last `JMP_WIN_MS`.
- **Trigger.** Sum ≥ `JMP_K` at a callback that reveals a new gap, at most once per `JMP_COOLDOWN_MS`
  (1 s). The first trigger uses up the cooldown even if a filter skips it, as in the offline study.
- **`JMP_MAX_SPREAD`.** Act only if the previous snapshot's market spread is ≤ this value. 0 turns the
  filter off.
- **Direction.** The sign of the near-touch imbalance in the same window. It counts new visible market
  resting inserts no more than 1 tick behind their own best from the previous snapshot: bid +1, ask −1,
  and double weight inside the spread. It is computed in the TRIG2 scan, and 0 means skip.
- **`JMP_MODE`:**
  - `flip`: `_on_signal(t, d, gate=False)`. For `JMP_CAP_MS`, IOCs in the jump direction use limit
    touch ± `JMP_CAP`.
  - `burst`: target d·`JMP_N` for `JMP_H_MS`, using IOC at touch ± `JMP_CAP`. It builds only for the
    first `JMP_BUILD_MS` if that is > 0. It then unwinds with IOCs to the follower's target, using the
    HID_BURST code path, and pays 10,000/s while |inventory| > 100.
  - `both`: the flip plus the burst.
- **Extra flags:**
  - `JMP_BURST_K` / `JMP_BURST_IMB`: the burst needs a stronger trigger; the flip is unaffected.
  - `JMP_GAP_EXACT`: per callback, hidden = largest new id − previous max − distinct visible new ids.
  - `JMP_CONFIRM_MS` / `JMP_CONFIRM_TICKS`: end the burst early unless the mid has moved by that much.
- **Diagnostics.** A record for each trigger: hidden sum, imbalance, direction, prior spread, whether it
  acted, position and target, and the signed mid move and position at +50 and +200 ms.
- **Default check.** With the defaults (`JMP_ON = False`), every snapshot reproduces U2 exactly: 886,626 /
  415,404 / 159,515. Checked on snapshots v1, v2 and v3 and on the committed file (see below).

## Setup

- **Engine.** The official `ExchangeSimulator`, run in-process by runner `20261108-r4-runner-001`, on full
  tapes. Settings: 5 ms latency, depth 20, ±100 limit, 1000 potential cap, 10,000/s breach penalty.
- **Hashes (sha256).** Data: R4 `61c0b6d1…`, R3 `1021586b…`, R2 `88ff641e…`. `simulator.py`
  `c37b2262…`. Strategy snapshots: v1 `fd501d13…`, v2 `037883c9…`, v3 `07098d2f…`, v4 `0a5b4144…`.
- **Acceptance rule (declared before the runs, paired against U2).** R4 ≥ U2 + 25,000, R3 ≥ U2 − 10,000
  and R2 ≥ U2 − 15,000. A penalty is allowed only in the burst modes, and it is already included in PnL.
- **Caveat.** The thresholds come from descriptive statistics on these same public tapes, so the
  results are in-sample. R3 and R2 have a different configuration and serve as guards.

## Results (PnL Δ vs U2; W = window in ms, K = hidden-sum threshold, s = max spread, cap = ticks)

The "Pen R4" column is the R4 breach penalty, already included in PnL. "Acted" counts triggers that
passed the filters on R4 / R3 / R2.

| variant | mode | ΔR4 | ΔR3 | ΔR2 | pen R4 | acted R4/R3/R2 | rule |
|---|---|---:|---:|---:|---:|---|---|
| all off (every snapshot and the committed file) | – | 0 | 0 | 0 | 0 | – | = U2 |
| W30 K3 s1 cap 10 (W20, s2 and cap 3 give the same R4) | flip | +13,619 | −104 | −1,059 | 0 | 9/21/13 | no |
| W20 K3 s1 cap 10 | flip | +13,619 | −65 | −465 | 0 | 5/13/7 | no |
| W30 K3 s0 | flip | +17,686 | +9,108 | −10,878 | 0 | 21/38/26 | no |
| W30 K4 s1 | flip | +19,575 | 0 | −316 | 0 | 6/4/3 | no |
| W30 K4 s2 | flip | +19,575 | −459 | +758 | 0 | 7/7/4 | no |
| W30 K4 s0 | flip | +19,575 | −1,335 | −26,741 | 0 | 8/11/10 | no |
| W50 K4 s1 / s0 | flip | +17,871 / +21,884 | −104 / −3,966 | −801 / −27,342 | 0 | – | no |
| W30 K3 s1, exact gaps / s0 exact | flip | +13,619 / −3,603 | −104 / +9,108 | −1,305 / −11,324 | 0 | – | no |
| **W20 K3 s1, N300 H50 cap 5** | **both** | **+25,648** | **−7,896** | **−7,427** | 4,488 | 5/13/7 | **yes** |
| W20 K3 s1, N300 H50 cap 5 | burst | +5,591 | −8,032 | −7,427 | 4,488 | 5/13/7 | no |
| W30 K3 s1, N300 H50 cap 5 | burst | +1,347 | −14,095 | −11,035 | 6,642 | 9/20/13 | no |
| W20 K3 s1, N900 H200 cap 5 | both | +30,837 | −54,690 | −28,620 | 11,997 | 5/13/7 | no |
| W20 K3 s1, N900 H200 cap 5 | burst | +28,743 | −67,794 | −28,620 | 11,997 | 5/13/7 | no |
| W30 K3 s1, N900 H200 cap 5 | burst | +22,329 | −90,556 | −44,198 | 20,160 | 9/20/13 | no |
| W20 K3 s1, N600 H100 cap 10 | burst | +43,587 | −23,879 | −14,895 | 7,449 | 5/13/7 | no |
| W30 K3 s1, N300 / N600 / N1000, H100 cap 10 | burst | +16,443 / +31,716 / +16,211 | −20,684 / −34,625 / −76,426 | −16,103 / −21,899 / −34,612 | 10–12k | 9/20/13 | no |
| W30 K3 s1, N600 / N1000, H200 cap 10 | burst | +43,641 / +6,095 | −68,829 / −98,772 | −33,105 / −56,914 | 19–20k | 9/20/13 | no |
| W30 K3 s2 / s0, N600 H100 | burst | +21,357 / −39,215 | −60,613 / −92,220 | −27,806 / −34,740 | 13k / 35k | – | no |
| W30 K3 s1, N600 H100 cap 10 | both | +39,062 | −32,961 | −21,631 | 11,595 | 9/20/13 | no |
| … + confirm 20 ms / 2 ticks (H100 / H200) | both | +37,206 / +41,782 | −25,075 / −38,060 | −14,301 / −17,169 | 9k / 14k | – | no |
| W30 K3 s1, burst only if hid ≥ 4: N300 / N600, H100 | both | +10,261 / +4,537 | +3,031 / +4,372 | −3,553 / −5,034 | 4k | – | no |
| W30 K4 s1, N300 H100, build 20 ms | both | +18,764 | +737 | −3,821 | 6,051 | 6/4/3 | no |
| W30 K4 s1, N600 H100 (build 20 / 10 / none) | both | +13,541 / +13,612 / +6,845 | −387 / −378 / −6,926 | −4,850 / −4,524 / −5,913 | 6k | 6/4/3 | no |
| W30 K4 s1, N600 H200 / N1000 H200, build 20 | both | +13,609 / +13,644 | +3,774 / −2,262 | −7,869 / −9,621 | 12k | 6/4/3 | no |

**Accepted variant on R4.** The five acted onsets all moved the predicted way by +200 ms: 170.409 (−137,
U2 already short), 464.974 (−22, U2 long, flipped), 1394.122 (+108.5, already long), 2170.88 (+75.5,
short, flipped) and 2689.448 (+23, short, flipped). The burst reached the ±300 target only at 464.974 and
1394.122. On R3, 12 of 13 acted onsets moved the right way, but only 4 moved by ≥ 20 ticks. On R2, 6 of 7
moved the right way, with 2 at ≥ 29 ticks. The R3/R2 cost (about −8k each) is round-trip spread plus
penalty on small moves.

## Findings

1. **The live detector matches the offline episodes.** R4 W30/K3 gives 25 live triggers, including 170.409
   (−137 ticks), 1394.122 (+108.5) and 2170.88 (+75.5). Some offline episodes, such as 3568.43, never
   reach the sum live. `JMP_GAP_EXACT`, which counts ids hidden between two visible ids in one callback,
   did not help: s1 was unchanged and s0 fell to −3.6k on R4.
2. **Direction is reliable at spread 1, especially at K ≥ 4.** At W30/K4/s1, all 13 acted triggers across
   the three tapes moved the predicted way by +200 ms: R4 +137, +22, +132, +75.5, +31, +23; R3 +50, +7,
   +23, +6; R2 +1, +30.5, +21.
3. **U2 is usually already on the right side,** so a flip adds little. It changes position only where U2
   was wrong. On R4 that happened 3 times at K3 (+13.6k) and 4 times at K4 (+19.6k). On R3/R2 the flip is
   about 0. Without the spread filter, R2 loses about 11k.
4. **Burst fills are adversely selected.**
   - False positives (hid 3, move ≈ 1 tick, mostly R3/R2) fill the full ±N at once. Each then pays a
     round-trip spread plus 1–2k of penalty.
   - Real jumps fill only partly before the move, because the stale side vanishes. At 170.409 the
     position was only −171 of a −600 target at +50 ms.
   - The rest of a real-jump burst fills by chasing the collapsed book. The IOC unwind then crosses a
     wide post-jump spread, with fill cost around 4–6.5 ticks per burst lot against the mid at send.
   - Bursts on all K3 triggers gain +32k to +44k on R4, mostly from one hid-3 event at 1394.122 (+108
     ticks, U2 already long). They lose 24k to 169k on R3 and 15k to 66k on R2.
   - Restricting bursts to strong triggers (hidden sum ≥ 4) does worse on R4 than the flip alone.
   - A confirmation stop (unwind if the mid has not moved 2 ticks in 20 ms) cuts the R3 loss only from
     −33k to −25k.
   - Only the short burst (±300, 50 ms, cap 5) combined with the flip keeps R3/R2 inside the guards,
     at −7.9k and −7.4k.
   - Flip and burst interact. On R4 the flip alone gives +13.6k, the burst alone +5.6k, and both
     together +25.6k. In `both` mode the burst unwinds to the follower's new target, whereas a burst
     alone unwinds to U2's old, wrong-side target.

## Verdict

- **Accepted by the pre-declared rule, by a margin of only +648 on R4:**
  `strategies/round_4/dataathletechamp/r4_u5_jump.py`, sha256
  `a3e72689b0eac3a136ef641a4192150711df47f52c35573e9d92381f7aace560`. It bakes the defaults `JMP_ON`
  True, W20, K3, `JMP_MAX_SPREAD` 1, `JMP_MODE` "both", N 300, H 50 ms, cap 5.
- **Official engine.**
  - CLI on R4: PnL 912,274.16, penalty 4,487.84, matching the runner.
  - Runner on the baked file: R4 912,274 / R3 407,508 / R2 152,088. With `JMP_ON` False it gives
    886,626 / 415,404 / 159,515, which is U2 exactly.
  - Local preflight passed.
  - CPU time for the CLI on R4: 48.7 s user, against 46.5 s for U2. Both ran on a busy machine.
- **Read it as a small, uncertain edge, not a proven one.**
  - The R4 gain is at the noise threshold and rests on 3 flips plus 2 filled bursts.
  - The R3/R2 costs of about −8k each are structural: false-positive bursts pay round-trip spread
    plus penalty.
  - On the private tape (R4 configuration) the expected sign is positive only if latent jumps of
    20–140 ticks occur at a rate like the R4 public tape's, where 5 onsets were acted on.
- **Best variant without a burst:** the K4 flip at spread ≤ 2. R4 +19,575, R3 −459, R2 +758, penalty
  0. All 13 acted onsets moved the predicted way. It fails only the +25k bar.
- **The 900-lot burst inside U2 (the coordinator's probe) fails the guards.** Both mode at W20 gives
  R4 +30,837, R3 −54,690, R2 −28,620. It is baked for validation only, uncommitted, at
  `experiments/round_4/dataathletechamp/20261108-r4-jump-onset-001/baked/r4_jump_both_w20_n900_c5_h200.py`
  (sha256 `ccd16c75…`).
- **Why it probably does worse here than in the flat probe (not verified):** inside U2 the 900-lot burst
  earns +29k on R4, against +68k in the probe. The likely cause is that U2 is already on the right side
  with 100 lots, and that each burst unwinds through U2's own target.

## Reproduce (from the main repo root)

```
R=/Users/jakubpiotrowski/PycharmProjects/Qminers_Arena_Zubry
E=$R/experiments/round_4/dataathletechamp/20261108-r4-jump-onset-001
env -u VIRTUAL_ENV uv run --locked python $R/experiments/round_4/dataathletechamp/20261108-r4-runner-001/runner.py \
  --strategy <abs path>/r4_follower_jump.py --grid $E/grid6.json --tapes r4,r3,r2 --out <dir> --workers 6
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight <abs path>/r4_u5_jump.py
env -u VIRTUAL_ENV uv run --locked exchange-simulator --strategy <abs path>/r4_u5_jump.py \
  --backtest data/round4/round4_public.csv --log-dir <tmpdir> --no-logs
```

- Grids: `grid1.json` to `grid6.json`, plus `grid_off.json` and `grid_u5.json`.
- Results: `<grid>/results.jsonl`.
- Summary table: `summarize.py <results.jsonl ...> [--events VARIANT]`.

## Limitations

- **Small sample.** There are very few big jumps: 6 on R4 at K4/s1, and fewer than 10 R4 events drive any
  difference. One public tape cannot separate a +20k flip gain from noise; the team's noise band on R4 is
  ±25k.
- **In-sample thresholds.** The W/K/spread values come from the same tapes. The private tape uses the R4
  configuration, but the timing of its jumps is unknown.
- **Burst execution.** The IOC chase and unwind are crude. A passive unwind, or waiting for the post-jump
  spread to close, was not tried.
- **Unfinished grids.** Grid 2 (6 of 23 variants), grid 3 (6 of 13) and grid 4 (2 of 13) were stopped
  early to free CPU on a shared machine. Grids 1, 5 and 6 are complete. The table lists only completed
  variants. Raw results are in the experiment folder (`grid1`–`grid6/results.jsonl`, `summarize.py`).
- **Selection bias.** About 45 variants were tried, and the accepted one clears the bar by +648. Expect
  some winner's curse on the R4 margin.
