# What the score actually proves

The official simulator is now the execution engine, unchanged. There is no fake
demo backend here. Public local runs are useful; public uploads run the SAME
public tape and mainly check server sandbox compatibility. Private data remains unseen.

## Score

Final score is `0.8*z1 + 1.0*z2 + 1.0*z3 + 1.2*z4` using PRIVATE PnLs.
Only positive-PnL teams define each round's mean and standard deviation.
Non-positive PnLs are scored as effective zero, not necessarily zero z-score.
Different rounds' raw PnLs cannot be directly summed or compared.
Zero variance/too few positive teams behavior was not specified.

Current tooling reports public PnL, fills, inventory, penalty, hashes and runtime.
It does not estimate private z-score, paired-delta SE or probability of winning.
`pnl_se` is the simulator's one-strategy statistic, not proof of a new candidate's gain.

## Checks

1. Correct state: incremental private fills, IDs/sides, pending/live/cancel-in-flight.
2. No penalty: account for worst-case outstanding fills before reaching +/-100.
3. Causal features: horizons survive at least 5 ms plus event timing; no future data.
4. Same data/evaluator: compare incumbent and candidate, register every trial.
5. Chronological unseen windows and stress when suitable data exists. **Never
   slice raw event CSV rows naively:** the starting order book and IDs need warmup.
6. Independent reproduction, local preflight, server sandbox check and exact final bytes.

Sample parity is not alpha. Our reset fix is a correctness change with regression
tests; both scripts score 1878 on this synthetic tape. No observed gain is claimed.
Carry, spread capture and penalties must be separated; one lucky product-day
is not replication. Keep an explicit fallback and do not pick only highest public PnL.
