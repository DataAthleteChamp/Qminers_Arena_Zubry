# R3 follower: decayed-evidence sizing instead of binary ±100 (rejected)

Experiment `20261108-r3-w9-evidence-001`, branch `r3-da-evidence`, base U7
`r3_follower_u7_flow_deepfv.py` (R3 413,588, R2 167,166, penalty 0).
File: `strategies/round_3/dataathletechamp/r3_follower_evidence.py`, flag `EVIDENCE` (default False).

## Question and mechanism

Does a size that follows a decayed evidence score beat U7's binary target with a 5 s hold?
`S = Σ w_type·sign·exp(−(t − t_i)/τ)` over accepted signal events (A, FLOW_TRIG, TRIG1, all weights 1.0),
optionally `+ EV_C·alpha` (alpha refreshed on the 50 ms grid). Target = `round(100·clip(S/S_full, −1, 1)/50)·50`,
changed only when `|new − current| >= EV_HYST = 50`. With STEP 50 that deadband never binds, so this is plain
rounding. `EV_GATE`: an event that opposes the current target sign is dropped unless the P1 alpha gate passes
(TRIG1 only when TRIG1_GATED), the same rule as U7. There is no deadline: decay exits the position. Execution
(`_reconcile`) is unchanged. A size reduction starts a fresh join-touch exit unless one is already resting.
`EV_RESET` (exploratory, default False): an accepted opposing event sets S to zero first, like a U7 flip.

## Data, engine, windows

Official engine in process (runner `20261108-r3-wave-runner-001`): 5 ms, depth 20, ±100, 10,000/s penalty.
Full R3 public tape (sha256 `1021586b92a3d9df…`) and full R2 public tape (`88ff641e962540c6…`).
`simulator/simulator.py` `c37b2262186f977d…`. Both tapes are in sample for U7's thresholds and alpha refit.
There is no holdout. Rule fixed before running: ACCEPT only if R3 > 413,588 AND R2 > 167,166 AND a neighbour
keeps at least half of the gain. The grid was τ ∈ {2, 5} s × S_full ∈ {1, 2}, then the best variant with c = 0.3.

## Results (PnL; penalty 0 everywhere)

| variant | R3 | R2 | lots R3 |
|---|---:|---:|---:|
| U7 base (EVIDENCE False, official CLI R3) | 413,588 | 167,166 | 384,500 |
| τ2 S_full1 | 165,140 | 42,508 | 242,622 |
| τ2 S_full2 | 136,106 | 18,327 | 263,566 |
| τ5 S_full1 | 35,733 | 69,530 | 126,946 |
| τ5 S_full2 | 12,878 | 42,718 | 134,592 |
| τ2 S_full1 + c 0.3 (best + alpha) | 199,756 | 33,473 | 284,118 |
| exploratory, not predeclared: τ2 S_full1 + EV_RESET | 400,371 | 155,151 | 410,136 |
| exploratory, not predeclared: τ5 S_full1 + EV_RESET | 410,886 | 176,002 | 386,100 |

Verdict: **REJECTED**. All five predeclared variants lose 52–97% of the R3 PnL. The file keeps U7 as its
default. The official CLI on R3 with the delivered default gave 413,588, penalty 0, 1,975 fills. The file passes
the local preflight. File sha256 `963a1383f5c6e643…75ad` (38,791 B).

## Why (diagnostics)

Each tape has about 14–16k accepted events. Same-sign bursts, such as repeated
FLOW_TRIG fires, build S far above S_full. A gated opposite event then only reduces S, so the book stops
flipping. U7's edge is the immediate gated flip. U7 is also at |100| almost all the time (q50 = q95 = 100).
Resetting S on an accepted opposite event (EV_RESET) recovers almost all of U7's PnL: τ5 gives R3 −0.7% and
R2 +5.3%. That result is post hoc and mixed, so it is not an accept. The useful lesson is that accumulating
evidence across sign changes is harmful here. Fractional (50-lot) sizing adds turnover without adding edge.

## Reproduce (from MAIN)

```bash
W=experiments/round_3/dataathletechamp/worktrees/evidence; E=$W/experiments/round_3/dataathletechamp/20261108-r3-w9-evidence-001
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy $PWD/$W/strategies/round_3/dataathletechamp/r3_follower_evidence.py --grid $E/grid1.json --tapes r3,r2 --out $E/wave1 --workers 2
# grid2.json = best + EV_C 0.3 and the τ2 EV_RESET variant; grid3.json = the τ5 EV_RESET variant (--workers 1)
env -u VIRTUAL_ENV uv run --locked python -m simulator.main --backtest data/round3/round3_public.csv \
  --strategy $W/strategies/round_3/dataathletechamp/r3_follower_evidence.py --log-dir $E/cli_r3 --no-logs
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight $W/strategies/round_3/dataathletechamp/r3_follower_evidence.py
```

Wave 1 ran on the file before the `EV_RESET` flag was added. Its sha256 was `ccafc548c2f6…`, and a snapshot is
kept in the experiment folder. With `EV_RESET` False the code path is identical. Limitations: only one weight
set (all 1), no per-type calibration, two in-sample public tapes, no server validation of this file.
