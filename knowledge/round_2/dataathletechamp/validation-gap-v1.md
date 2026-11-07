# Validation rescue: the public record is not a validation winner

**Verified B outcomes:** risk/Ridge -229513; conservative maker -10781;
Grid **+28827**. All zero penalty, elapsed11999.979714s and terminal liquidation
mark10482. Use the positive reported Grid as the B incumbent; do not silently
replace it with a public-only leader.

| Policy | A | B | B lots | B median abs I | B net/lot |
|---|---:|---:|---:|---:|---:|
| Our risk/Ridge | +18916, reproduced | -229513 | 1278205 | 35 | -0.17956 |
| Conservative | about45000, reported | -10781 | 647192 | 13 | -0.01666 |
| Supplied Grid | **+91025, reproduced** | **+28827** | 463695 | 56 | +0.06217 |

A is approximately6000s; B/C approximately12000s under the newly quoted
organizer announcement. B is a different tape, not A replayed twice.
Same throughput does not mean same economics: risk/Ridge's B volume is2.066
times A, and lots/second rise only3.29%, but net/lot changes from+0.03057
to-0.17956. This is not simply lost participation or inventory penalties.

## What the wealth curves actually prove

We independently copied/hashed the three exports and reconciled
`cash + I*actual_liquidation_mark - penalty = finalPnL`.
Risk:137357-35*10482=-229513; conservative198859-20*10482=-10781;
Grid102201-7*10482=28827. PnL CSV endpoints match result JSON.

| Inclusive standing-wealth boundary | Risk/Ridge | Conservative | Grid |
|---|---:|---:|---:|
| 0--3000s | -58220 | -3218 | -6228 |
| 3000--6000s | -58666 | -4286 | +16672 |
| 6000--9000s | -75554 | +2363 | +37166 |
| 9000--11999.979714s | -37073 | -5640 | -18783 |

This convention differs slightly from half-open row endpoints in the supplied
memo; totals are identical. Losing300s windows:32/40 risk,22/40 conservative,
18/40 Grid. Sampled maximum drawdown234178/14175/30811.
At2427->2428s, wealth changes are-11100/+1321/+1944 respectively.
Loss is strategy-specific and persistent, not just one terminal event.

Higher inventory is not automatically worse: Grid's median56 beats risk35 and
conservative13. Direction, prices, fill selection, queue and timing matter.
Nor does a one-arm Grid pnl_se37466 exceeding profit28827 establish negative
expected profit or a probability of winning private.

## Limits: no invented B market distribution

Exports contain **metadata/result/pnl.csv only**, not book deltas, trades or a
replayable event tape. We cannot compute B price volatility, spread/depth,
aggressor volume, cancellation pressure or exact own post-fill markouts.
Wealth increments are portfolio outcomes, **not midpoint returns**.
At2428, wrong inventory direction and/or fills could explain the difference;
the available data cannot identify the exact decomposition.

The A short-liquidation mark9690 versus B10482 establishes a different terminal
state. Calling B's full return+482 requires an unverified10000 starting-price
assumption; it does not establish a steadily rising B path.
Generic `/work/backtest.csv` is not a dataset hash. Strategy associations are
user-reported/class-consistent; exports do not contain uploaded source hashes.

The picture shows median best reported PnL122k and an upper IQR around400k,
not individual team maxima or final-private rankings. Target400k on12000s
means33.33units/s versus Grid's observed2.40units/s. No formula guarantees
that gap closes by increasing quantity.

## Source review: useful mechanisms versus unproved explanations

Risk/Ridge still uses R1 price coefficients and a very small inventory skew,
while its symmetric35 fallback limits new exposure without flattening old
positions. A good jump classifier does not make adverse fills profitable.
The market-on-market flow filter excludes outside fills against our quotes,
but changing it without compatible calibration is a hypothesis, **not a
confirmed correctness fix**; earlier R1 all-external trials were not universally
better.

The conservative code has an active issue worth isolating: "keep reducing quote"
can request50 from I=+10 and create-40 when stressed. It does not cap reducing
quantity at actual inventory minus same-side reservations. Its disabled VPIN,
jump/Hawkes/IOC flags do not explain current performance.

We now have the supplied Grid code, unlike the older memo. It uses50ms
replenishment/flow/lag features, three price layers, EMA3/30/120 target+/-100,
and NORMAL/CAUTION/SHOCK/RECOVERY under one shared100 ledger.
Observed weaknesses: missing-book returns leave NORMAL unchanged; short-lag
history survives long gaps; recovery follows potentially stale+/-100 target;
CAUTION's16 target does not resize already-live32; partial same-price quotes
cannot top up. Each needs an isolated test, not a combined rewrite.

Our typed active-policy port reproduces A **91025** exactly and earns
**149143 on R1** with unchanged source and zero penalty. R1 is a consumed
cross-regime diagnostic, not untouched validation. Provided11-weight fit
window/target remain UNKNOWN.

Retained reference:
`strategies/round_2/dataathletechamp/r2_grid_reference_public_91025.py`,
SHA256 `f732515577b6e7138256e052fed546dfab3118fb5d5b712917fcde1a78f8eee4`,
11540bytes. Local port equivalence is not an authenticated server-source hash.
The reported original Grid B+28827 remains distinct evidence.

## Actual commands/results and next B gate

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/server-validation-intake-v1/analyze.py
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/server-validation-intake-v2/analyze.py
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-reference-A-v1 --strategy experiments/round_2/dataathletechamp/grid-reference-v1/grid_reference.py --tape data/round2/round2_public.csv --stage supplied-Grid-active-policy-reproduction --full-logs
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-reference-on-R1-v1 --strategy experiments/round_2/dataathletechamp/grid-reference-v1/grid_reference.py --tape data/round1/round1.csv --stage unchanged-cross-round-R1-transfer-diagnostic
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-reference-A-repro-v1 --strategy experiments/round_2/dataathletechamp/grid-reference-v1/grid_reference.py --tape data/round2/round2_public.csv --stage Grid91025-exact-public-reproduction
```

All passed. Grid preflight/Ruff/strict mypy and pending-fill/cancel regression
passed. Intake-v1 initial E501 failure is preserved; no fake result followed it.
Report hashes:d20dfb95caa4a273e22fbd3d99245f5810a402e0d643e74d8fb21feef8196c27
and ad159decde93d03f6f93d99e721f8ca7555d46b10c7a4b7b6602c51cc374208b.
Raw outcomes/experiments remain local/ignored; original exports untouched.

The full **local A** explorer is running at `http://127.0.0.1:8050/`,
loopback binding/HTTP200 verified, against r2-grid-reference-A-v1/logs.
B cannot be explored as a book/fill run without missing logs.

Next frozen tests compare quantity64, target50, target0 and guarded neutral
recovery against this Grid. Public improvement alone is **not** the Final gate.
Freeze a small number before human B feedback; compare actual incremental B
PnL against28827, preserve the successful incumbent and keep C blinded.
No automatic upload, Final change, source overwrite or hard100 expansion.
