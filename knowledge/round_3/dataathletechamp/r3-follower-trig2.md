# R3 follower TRIG2: hidden-price G-insert trigger (negative). Experiment 20261108-r3-w8-trig2-001

Owner: dataathletechamp, branch `r3-da-trig2`. Budget: 25 min (04:27–04:55 CET).

## Question
U7 (`r3_follower_u7_flow_deepfv.py`, sha256 d2a0fc9c…) uses information-based triggers. Does it gain from one
more trigger built on the generator study's hidden-price estimator `G_meanz_100`
(`20261108-r3-w6-latent-filter-001/REPORT.md` §1, §4)?

## Mechanism (flag `TRIG2_ON`, default False = U7 exactly)
`strategies/round_3/dataathletechamp/r3_follower_u7_trig2.py`:
- Each new resting market insert (id > max seen id, same single-row scan shortcut as TRIG1) gets
  z = side × `T2_ITAB[(side==bid)*33 + (k+3)*3 + (min(spread,3)-1)]`.
  - k = ticks behind its own best in the previous event's market book, clipped to [−3, 7].
  - The 66 cells are embedded from `final_model.json["itab"]`, fit on the R3 fit half.
- G_meanz = mean z over `TRIG2_WIN_MS` = 100.
- If |G_meanz| >= `TRIG2_THR` holds with the same sign for >= `TRIG2_HOLD_MS` = 20 (checked at events), it calls
  `_on_signal(t, sign, TRIG2_GATED)` once per run. A, FLOW and TRIG1 events take priority.

## Data, engine, commands
- Tapes: R3 public sha256 `1021586b92a3d9df…`; R2 public `88ff641e962540c6…`.
- Engine: official `ExchangeSimulator`, run in-process by `20261108-r3-wave-runner-001/runner.py`
  (5 ms, depth 20, ±100), 3 workers or fewer.
- The grid ran on a snapshot of the committed file (sha256 7c31aa76…41bf, identical).
- `grid.json` / `grid2.json` and `out*/results.jsonl` are in the gitignored experiment folder.

```bash
W=experiments/round_3/dataathletechamp/worktrees/trig2; E=$W/experiments/round_3/dataathletechamp/20261108-r3-w8-trig2-001
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy $E/strategy.py --grid $E/grid.json --tapes r3,r2 --out $E/out --workers 3
```

## Results (public PnL, penalty 0 everywhere; base = U7 = 413,588 / 167,166)
| variant | THR | gated | R3 | Δ R3 | R2 | Δ R2 | R3 fires (ext/flip/ignored) |
|---|---|---|---|---|---|---|---|
| base | – | – | 413,588 | 0 | 167,166 | 0 | – |
| t15_g | 1.5 | yes | 413,701 | +113 | 167,383 | +217 | 442 (439/1/2) |
| t20_g | 2.0 | yes | 413,588 | 0 | 167,166 | 0 | 101 (101/0/0) |
| t25_g | 2.5 | yes | 413,588 | 0 | 167,166 | 0 | 12 (12/0/0) |
| t15_u | 1.5 | no | 414,419 | +831 | 166,338 | −828 | 442 (439/3/0) |
| t20_u | 2.0 | no | 413,588 | 0 | 167,166 | 0 | 101 |
| t25_u | 2.5 | no | 413,588 | 0 | 167,166 | 0 | 12 |
| t08_u | 0.8 | no | 405,527 | −8,061 | 135,282 | −31,884 | follow-up |
| t08_g | 0.8 | yes | 410,881 | −2,707 | 141,398 | −25,768 | follow-up |
| t11_u | 1.06 | no | 420,688 | +7,100 | 154,613 | −12,553 | follow-up |

Notes on the results:
- **Fires are rare and almost all are hold extensions.** On R3 the scan found 1.18 M inserts. At THR 1.5 there
  are 0.07 fires/s, and 439 of the 442 land when U7 is already on that side. This matches the overlap study:
  the latent re-discovers the incumbent's direction 85–89% of the time.
- **Scale caveat.** The study's executable thresholds 1.5–2.5 apply to the RED_h1.0 *prediction*, which is
  0.368 + 1.884·G_meanz_100 + …. They do not apply to raw G_meanz. Raw THR 1.5–2.5 is about 2× stricter than the
  study's rule. The follow-up rows use THR 0.8 / 1.06, which are roughly the prediction thresholds 1.5 / 2.0
  divided by 1.884.

## Verdict: REJECT (flag stays False)
- Acceptance needed R3 > 413,588 **and** R2 > 167,166.
  - t15_g passes nominally, by +113 / +217. That is 0.03% / 0.13%, from 1 flip on each tape.
  - Neither neighbour (2.0, or 0.8 in the follow-up) keeps >= 0.5 of that gain, so t15_g fails the stability rule.
  - Ungated 1.5 trades R3 +831 against R2 −828.
  - The scale-corrected 0.8 loses heavily: ungated R3 −8.1k / R2 −31.9k, gated R3 −2.7k / R2 −25.8k.
  - Ungated 1.06 gains on R3 (+7.1k) but loses on R2 (−12.6k). That looks like an R3-fitted table overfitting R3.
- The information is already priced in U7's position, as the overlap study predicted. Extra flips from it lose
  on R2.
- **Official CLI** on the committed default (`TRIG2_ON = False`): R3 public `pnl=413588.00`, penalty 0.00,
  traded 384,500. This equals U7. `tools.preflight` passes. Server sandbox validation is still needed and was
  not done. Public PnL is not private PnL.

## Limitations
- One hold (20 ms), one window (100 ms), edge-triggered once per run with no re-fire. The full RED_h1.0 model
  (G_sumz, class counts, T_sumz) is not implemented. Only the G_meanz term is used.
- Both tapes are in-sample for the table and for U7's selection, so this is not an out-of-sample test.
