# Real simulator, honest evidence

The original `simulator/` and `explorer/` are unchanged and fingerprinted.
The CLI loader does NOT implement the website's full static restrictions.
Use our conservative preflight, then the actual server sandbox check.

```bash
uv run --locked python -m tools.preflight strategies/zubry.py
uv run --locked python -m tools.run_experiment \
  --id r0-yourname-003 --owner yourname --round playground \
  --strategy strategies/zubry.py --backtest data/round0/sample.csv \
  --hypothesis "State the hypothesis before running" \
  --reject-if "State the rejection condition"
uv run --locked python -m tools.compare p0-original-r0 r0-yourname-003
```

IDs are immutable. `--full-logs` produces explorer inputs; default `--no-logs`
keeps runs fast. Wrapper timeout is at most 900 seconds; it sets BLAS thread
budgets to one. It does not enforce a 2 GB OS memory boundary or full server sandbox.
Only execute trusted team code.

Each run records its plan and exact strategy snapshot before execution, hashes
of strategy/data/simulator, Python, prior Git commit, dirty-state disclosure,
actual command, success or failure, elapsed time and actual `result.json`.
Large logs remain ignored; commit small results/notes and source.

## Interpretation

Local and uploaded public runs use the same public tape; uploads confirm server
compatibility, not new independent evidence. One-arm `pnl_se` is not difference
SE. Do not bootstrap ticks into a probability of winning future private data.
Normalize final PRIVATE PnL only with actual positive-team field statistics; those
statistics and zero-variance edge cases are not available locally.

PnL is cash plus liquidation against market liquidity minus exact-time inventory
penalty. No fees does not remove spread, slippage, queue cost or cancel races.
Stay within +/-100 with pending/resting worst-case fills. 1000 is a rejection wall.

## Causal windows

Do not cut event rows and start with an empty book. Earlier inserts/resting orders
and IDs matter. Replay warmup, define a trading-activation time and inventory/cash
convention, then evaluate the chosen interval. Fit parameters on prior data only.
Report start/end liquidation consistently. Private tapes may differ; composition
and duration are not promised by the public data.

Preserve all tested variants, even failures. The reset fix is deterministic
correctness, not a statistical alpha claim: original and fixed files both score
1878 on the current synthetic tape.
