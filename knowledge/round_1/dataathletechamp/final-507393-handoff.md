# 507393 final observed public record: exact manual-check handoff

**550k target was not achieved.** Highest ORIGINAL public replay:507393,
penalty0. Easy file:
`strategies/round_1/dataathletechamp/pnl_507393_clipped_ridge_maker.py`.
The independently reproduced Maciej incumbent505225 remains an alternative.
Do not claim a private win probability or authenticated competitor benchmark.

Immutable final top-three folder:
`strategies/round_1/dataathletechamp/top_public_snapshot_20261107_507393/`.

| Policy | Public PnL | Source SHA256 |
|---|---:|---|
|price shift clipped±1|507393|b21e633b76bd2b74214ab684666b0faa5316b55761b18eece660e26b7f0152ac|
|price shift clipped±2|505421|e57bda2c6f9ec6a2b96d8900134c8647c8f32e4dbf839ff4a2ca0faf20cd1ed0|
|Maciej8-slot/skew0.001|505225|c1f194668ec83e94bf522e749ce36d266caeedb9244506ede2adeee68e8e3667|

Original tape SHA256:
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
Corrected predictor arrays were originally fitted only on actual0.5s target times
strictly before4800s. Full scores include that fit period; later outcome windows
are already consumed development/robustness, not untouched OOS evidence.

## Actual reproduction and exposure

Three transparent official-engine observer runs:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/trace_final.py --file experiments/round_1/dataathletechamp/urgent-fair-v14/variants/clip1.py --expected-pnl 507393 --id trace-clip1-record-v1
uv run --locked python experiments/round_1/dataathletechamp/evaluation/trace_final.py --file experiments/round_1/dataathletechamp/urgent-fair-v14/variants/clip2.py --expected-pnl 505421 --id trace-clip2-record-v1
uv run --locked python experiments/round_1/dataathletechamp/evaluation/trace_final.py --file macieiej_505kpln.py --expected-pnl 505225 --id trace-maciej505-v1
```

All passed at the exact expected PnLs, independently matching cash and inventory.
Every source: max actual100, upper reserve100, lower reserve-100, penalty0,
time above100=0, rejected messages0.

For507393: cash-495507, inventory100, mark10029:
`-495507+100*10029=507393`;19707 filled orders,32503 matches,2031166 lots.
Approximately50.7% of time is at abs100. The unchanged hard cap does NOT imply
unchanged holding exposure or private-path sensitivity.

## Correctly warmed later trading windows

| Source |4800-8400 PnL|8400-12000 PnL|
|---|---:|---:|
|clipped±1|158129|152340|
|Maciej505225|157162|151897|
|matched clipping delta|+967|+443|

Actual IDs:uf14-clip1-later4800/later8400,maciej505-later4800/later8400.
Every penalty0. Both arms replay all earlier book events and start trading flat
at the declared activation. Do not sum their independent liquidations into a full score.
Small positive deltas on consumed blocks do not establish fresh-market superiority.

## What worked / failed

Large target200 plus side-wise100 pending reserve, FIFO top-ups, smaller price
skew and using the corrected forecast for PRICE rather than mostly-clipped size
tilt improved our343269/344438 baselines. Maciej's8slots/skew0.001 reached505225.
Beyond8slots plateaued; minimum1-lot top-up slightly lost.

Final8 cheap quote-value ablations on505225:

| Change | Actual original-full PnL |
|---|---:|
|width-0.5|433991|
|width-0.25|469432|
|width0.125|493022|
|width0.25|461564|
|forecast price shift clip±1|507393|
|clip±2|505421|
|extra QI0.1|503908|
|extra QI0.25|473205|

The clipping gain2168 is modest. No winning>5000 improvement over505225 appeared.
Twelve other Maciej-neighbour runs all stayed<=505225; seeurgent-teammate505-results.
The9 reversal/control ablations also stayed<=478957, far below the new incumbent.
Tiny IOC controls lost; holding older safe deep layers lost. No IOC enabled here.

Ownership-complete flow was NOT an automatic fix:477516->474767,
459038->461013,344438->344015 in matched original-full tests. Different controls
respond differently; do not blindly replace all flow definitions.

The supplied independent reconstruction had14 zero-mid records, but our actual
official-replay feature grid239995 rows hasZERO nonpositive best bid/ask samples.
No future interpolation or10k-tick placeholder jumps are used in these strategies.
Reversal prototypes also included unfiltered user-taker trades; own ablations
used only external aggressors and valid causal midquotes instead.

## Validation and manual reproduction

`make check` passed: project lint/format, strict types,25 tests, preflight and
unchanged official source/material fingerprints. Source families passed separate
Ruff, strict typing and conservative preflight.13 focused capacity tests and5
mixed-IOC/actual SDK tests passed. All original CSV/PDF/engine bytes were preserved.
Final snapshot formatter check flags ONLY Maciej's original missing end-of-file
newline. Preserve those tested bytes/SHA rather than silently formatting a frozen
submission. The two newly generated clipping files are already formatted; all
three pass Ruff lint, strict types and conservative preflight.

```
uv run --locked python -m tools.preflight strategies/round_1/dataathletechamp/pnl_507393_clipped_ridge_maker.py
uv run --locked exchange-simulator --strategy strategies/round_1/dataathletechamp/pnl_507393_clipped_ridge_maker.py --backtest data/round1/round1.csv --log-dir experiments/round_1/dataathletechamp/your-fresh507393-check/logs --no-logs
```

Use a fresh output path. Server sandbox validation, the10-upload budget and Final
selection remain HUMAN decisions; nothing was uploaded. Earlier files/snapshots
are kept. Raw trial code, plans/outcomes and failed setup/tests remain local under
experiments; curated findings and exact retained files are shared on the branch.
