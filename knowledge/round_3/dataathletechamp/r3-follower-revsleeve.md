# R3 follower + slow contrarian sleeve (REVSLEEVE) — rejected

Experiment `20261108-r3-w9-revsleeve-001` (outputs gitignored under
`experiments/round_3/dataathletechamp/20261108-r3-w9-revsleeve-001/`), branch `r3-da-revsleeve`.

## Question

The teammate tape study (`round3-public-tape-analysis.md` sections 5–7) found that R3 reverts at
10 s–5 min. Blocking momentum extensions, or going flat on overextension, inside U7 had already failed.
Would a separate slow contrarian sleeve, added next to the U7 momentum follower, raise both R3 and R2?

## Mechanism (`strategies/round_3/dataathletechamp/r3_follower_revsleeve.py`)

- Copy of U7 (`r3_follower_u7_flow_deepfv.py`, sha256 `d2a0fc9c…f897`) with `REVSLEEVE` (default
  False = U7 exactly).
- Reversion sleeve, evaluated on a 1 s grid: z = (mid − EMA) / σ, where EMA and σ are the exponential
  mean and variance of mid with τ = 60 s and 60 s of warmup.
- When |z| ≥ `REV_ZK`, the sleeve target is −sign(z) × `REV_SIZE`. The sleeve then holds for at least
  20 s after its last trigger and goes flat after that.
- `REV_MODE "sum"` (as specified): the momentum sleeve trades 100 − `REV_SIZE`, and the position target
  is momentum + reversion (|sum| ≤ 100).
- `REV_MODE "flat"` (follow-up): the momentum sleeve keeps 100, and the reversion sleeve trades only
  while the momentum target is 0.
- Execution uses U7's reconcile on the combined target. The exposure cap stays at 100.

## Setup

- Official engine through the wave runner (5 ms, depth 20, ±100, 10,000/s), with 2 workers.
- Data: R3 public `1021586b92a3d9df…`, R2 public `88ff641e962540c6…`. Simulator: `simulator.py`
  `c37b2262186f977d…`.
- The reversion-sleeve parameters were taken from the tape study (60 s, |z| 1–1.5, 20 s hold). Nothing
  was fitted, but both tapes are in-sample for the study that motivated it.
- Acceptance rule: R3 > 413,588 **and** R2 > 167,166, and a neighbouring variant keeps at least half
  of the gain.

## Results (PnL, penalty 0 for all)

| variant | R3 | R2 | lots R3 | est. sleeve contribution R3 / R2 * |
|---|---:|---:|---:|---:|
| base (REVSLEEVE False) | 413,588 | 167,166 | 384,500 | — |
| sum SR20 ZK1.0 | 347,130 | 128,345 | 311,480 | +16.3k / −5.4k |
| sum SR20 ZK1.5 | 347,033 | 133,366 | 310,080 | +16.2k / −0.4k |
| sum SR30 ZK1.0 | 312,699 | 107,921 | 273,910 | +23.2k / −9.1k |
| sum SR30 ZK1.5 | 312,987 | 115,649 | 272,110 | +23.5k / −1.4k |
| flat SR30 ZK1.0 | 413,375 | 165,583 | 384,440 | — |
| flat SR30 ZK1.5 | 413,395 | 165,410 | 384,560 | — |

\* Estimate: variant PnL − (1 − SR/100) × base. This assumes momentum PnL scales linearly with
sleeve size.

- The sleeve fired 45–57 times on R3 (21 / 9 direct flips) and was active for 1,734–3,218 s of the tape.
- In flat mode the sleeve almost never gets capacity, because U7 is nearly always in position: lots
  traded are unchanged. Both flat variants lose 200 on R3 and 1.6k on R2.

## Verdict: REJECTED

All six variants fail on both tapes.

- The reversion edge is real on R3, at about +780 per lot of sleeve size, and close to zero or
  negative on R2.
- However, each lot moved out of the momentum sleeve costs about 4,100 on R3 and 1,700 on R2.
- With the ±100 limit, the reversion sleeve can only be funded by taking capacity from U7, and that
  allocation always loses.

The delivered default is `REVSLEEVE = False`, which is U7 behaviour. Official CLI R3: 413,588,
penalty 0, 40 s. Preflight passes. Server validation is still required.

## Reproduce

Run from MAIN, with W = the worktree and E = the experiment directory:

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy $W/strategies/round_3/dataathletechamp/r3_follower_revsleeve.py --grid $E/grid.json \
  --tapes r3,r2 --out $E/grid1 --workers 2   # grid2_flat.json -> $E/grid2_flat
env -u VIRTUAL_ENV uv run --locked python -m simulator.main --backtest data/round3/round3_public.csv \
  --strategy $W/strategies/round_3/dataathletechamp/r3_follower_revsleeve.py --log-dir $E/cli_r3 --no-logs
```

Grid1 ran on file sha `8e15254e…` (before the `REV_MODE` flag was added). The "sum" code path is
unchanged in the final file, which is sha `1fd03a0e…75ee`.

## Limitations

- Only public tapes were used, and both were in-sample for the tape study.
- The sleeve contribution is an estimate, not a separate run.
- Not tried: passive maker entry for the sleeve; using the sleeve only on R3-like regimes.
