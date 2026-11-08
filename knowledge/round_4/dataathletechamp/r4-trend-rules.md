# R4 trend rules on U8 (experiment 20261108-r4-w4-trend-001)

Owner: dataathletechamp, branch `r4-da-trend`. Status: one weak rule passes the coordinator's rule;
every trend rule that overrides the flow signal fails badly.

## Question and baseline

R4 public trends at 5–60 s (VR at 2/5/10/30/60/120 s = 1.29/1.74/1.98/1.64/1.41/1.35). Can trend-aware
position management on top of U8 (`strategies/round_3/dataathletechamp/r3_follower_u8.py`, sha256
`0075a2bf…8b49a`) use that trend? Pre-registered acceptance rule (coordinator): R4 > 821,664 and a combined
R3 + R2 drop below 5% compared with U8.

Key fact: U8 is effectively always at ±100 (|inv| q50 = q95 = 100). On R4 it makes 7 entries and 1,972
flips, so the average hold is about 1.8 s. The hold deadline almost never binds, which is why HOLD_S
10/15/20 all give the same result.

## Rules

`strategies/round_4/dataathletechamp/r4_follower_trend.py` is U8 plus flags.
trend_W = market-touch mid now − mid in effect W s ago, in ticks; it is 0 until W s of history exist.
With every flag off, the file reproduces U8 exactly: R4 821,664, R3 415,883, R2 171,568.

| rule | mechanism |
|---|---|
| EXT (W, K) | the deadline cannot expire while trend·side ≥ K |
| NOFLIP (W, K2) | opposite signals cannot flip while trend·side ≥ K2 |
| ENTRY (W, K3) | when target = 0, enter the trend side if \|trend\| ≥ K3 |
| GATEFREE (W, K) | (extra) an opposite signal that agrees with the trend by ≥ K skips the alpha gate |
| TREND_FLIP (W, K4) | trend·side ≤ −K4 flips to the trend side; ungated; 2 s refractory |
| TREND_HOLD (K 5, W 30) | at entry/flip: against trend → 15 s hold; with trend → deadline capped at entry + 5 s, including extensions |

## Results (official engine, full public tapes; in-sample, nothing fitted)

Deltas are against U8. r4 is compared with 821,664.

| variant | R4 | ΔR4 | ΔR3 | ΔR2 | Δ(R3+R2) |
|---|---:|---:|---:|---:|---:|
| NOFLIP w10 k5 / k10 | 394,174 / 487,118 | −427k / −335k | −282k / −215k | −104k / −82k | −66% / −51% |
| NOFLIP w30 k5 / k10 | 156,311 / 248,035 | −665k / −574k | −357k / −265k | −83k / −77k | −75% / −58% |
| EXT w10 k3,k6 | 821,664 | 0 | 0 | 0 | 0 |
| EXT w30 k3,k6 | 821,764 | +100 | +200 | 0 | +0.03% (1 episode) |
| ENTRY w10/w30 k6/k10 | 821,369–821,643 | −295…−21 | −52…+200 | −500…0 | ≤ −0.09% |
| TREND_FLIP w10 k8 / k15 | 568,898 / 622,180 | −253k / −199k | −244k / −146k | −134k / −96k | −64% / −41% |
| TREND_FLIP w30 k8 / k15 | 397,204 / 491,653 | −424k / −330k | −317k / −216k | −189k / −138k | −86% / −60% |
| GATEFREE w10 k3 / k6 | 767,417 / 812,231 | −54k / −9.4k | −29k / −31k | −1.9k / +0.8k | −5.2% / −5.2% |
| GATEFREE w30 k3 / k6 | 753,459 / 761,754 | −68k / −60k | −62k / −47k | +4.5k / −0.7k | −9.8% / −8.1% |
| **TREND_HOLD w30 k5** | **825,273** | **+3,609** | **−622** | **−8,553** | **−1.56% ACCEPT** |
| TREND_HOLD against-only | 821,889 | +225 | +200 | +100 | +0.05% (inert) |
| TREND_HOLD with-only (cap 5 s) | 825,048 | +3,384 | −822 | −8,653 | −1.61% |
| pair EXT w30 k3 + ENTRY w30 k10 | 821,643 | −21 | +200 | −500 | −0.05% |
| pair EXT w30 k3 + TREND_HOLD | 821,323 | −341 | +229 | −1,072 | −0.14% (EXT undoes the cap) |

Official CLI (`simulator.main`, R4, final file): pnl 825,273, penalty 0, 405,210 lots.
`tools.preflight` passed.

## Interpretation

- Letting the trend override the flow signal destroys the edge, even on trending R4. NOFLIP, TREND_FLIP and
  GATEFREE all lose. This agrees with the coordinator's A-event study: A events against the prior 30 s
  trend keep running (+6.1 ticks at 5 s, +7.8 at 20 s), while A events with the trend fade (−3.5 at 30 s).
- EXT and ENTRY are inert because U8 is almost never flat and its deadline almost never binds. The +100
  from EXT w30 comes from one deadline episode.
- The whole TREND_HOLD gain comes from the with-trend 5 s cap. That matches the event study: with-trend A
  events fade. The evidence is weak, though. The R4 gain comes from 2 blocks (+4.5k, +2.4k) and only
  4/10 R4 600 s blocks are positive. R2 is negative in 8/10 blocks (−8.6k), so the R2 cost is larger than
  the R4 gain. That is the same profile as the coordinator's plain exit stops (R4 +1–8k, R2 −5–15k).
  Treat it as a regime bet on momentum-friendly tapes, not an established improvement.

## Reproduce

Run from the MAIN checkout. Tape sha256: r4 `61c0b6d1…`, r3 `1021586b…`, r2 `88ff641e…`.

```
env -u VIRTUAL_ENV uv run --locked python experiments/round_4/dataathletechamp/20261108-r4-runner-001/runner.py \
  --strategy <abs strategy> --grid <grid.json> --tapes r4,r3,r2 --out <abs out> --workers 3
env -u VIRTUAL_ENV uv run --locked python -m simulator.main --backtest data/round4/round4_public.csv \
  --strategy strategies/round_4/dataathletechamp/r4_follower_trend.py --log-dir <dir> --no-logs
```

The grids, snapshots v1–v4 and final, and results.jsonl live in
`experiments/round_4/dataathletechamp/20261108-r4-w4-trend-001/`. That directory is uncommitted.

Limitations: public tapes only, so these are in-sample. There is one tape per regime and no paired SE.
The thresholds came from the brief and were not fitted.
