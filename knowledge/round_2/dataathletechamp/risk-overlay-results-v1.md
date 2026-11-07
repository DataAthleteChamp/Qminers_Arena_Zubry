# First positive Round 2 A record: +18916, reproduced

**Retained public research file:**
`strategies/round_2/dataathletechamp/r2_public_research_risk_capacity_18916.py`.
SHA256 `cf31854e1d453f02b7073eb9146afd7ce0eb25115b020b316513e9236096d9a3`,
16,289 bytes. One no-argument BaseStrategy, stdlib/public SDK only.
This is a tested local research leader, **not an uploaded or selected Final**.
Server sandbox, B feedback and C private performance remain UNKNOWN.

## Predeclared official comparison

Same R2A raw hash88ff641e..., installed official SDK digest6dba6395...,
R1 price predictor/skew and IOC_MODE=0. No evaluator or raw data changes.
The only arm changes are in [the frozen risk ladder](jump-risk-model.md).

| Official run ID | Intervention | Net PnL | Penalty | Filled orders | Lots | Median abs inventory |
|---|---|---:|---:|---:|---:|---:|
| r2-overlay-reference-A-v1 | Flags0 equivalence | -143178 | 0 | 11486 | 1159623 | 100 |
| r2-vol-risk-capacity-A-v1 | Vol-only score, caps100/70/35 | +12935 | 0 | 10343 | 632661 | 35 |
| r2-full-risk-capacity-A-v1 | Full score, same caps | **+18916** | 0 | 10494 | 618747 | 35 |
| r2-full-risk-width-A-v1 | Full score,1tick deeper both sides | -70803 | 0 | 3664 | 377793 | 100 |

The flags0 result matches every field of the exact Final seed control.
Full capacity beats that baseline by162094 and vol-only capacity by5981.
Under this particular detector/controller, quantity protection beats triggered
widening by89719. This is one consumed public tape, not a universal rule that
size always beats widening or a predicted private ranking.

The median position falls to35 despite a95th percentile100. Soft reductions
do not erase old positions/orders. Wider quoting reduces fills but still leaves
median inventory100; fewer executions alone do not solve the inventory problem.

**Attribution is partly resolved:** unknown risk history also uses the35
fallback. The new [fixed35/q200 comparator](subsecond-size-results-v1.md)
earns8831, so most baseline-loss prevention also occurs with a simpler envelope.
Full adaptive risk adds10085 beyond fixed35 on A; valid/unknown state occupancy
is still to be measured. Do not label the whole162094 classifier alpha.
Failed/worse width results remain preserved.

## Exact reproduction and cash reconciliation

`r2-full-risk-capacity-A-repro-v1`, full logging only, exactly reproduces
all result fields, including volume/fills/inventory and one-arm pnl_se.
Cash454966 + inventory(-45)*actual terminal liquidation9690 =18916.
The retained file is byte-identical to both official-run snapshots.
Result SHA256:
`1a37625468dddf62b334e59f9d9e25dc90fe110f3cd6b254bdc3ebad67e5f7f5`.

Original successful commands, run from the active R2 worktree:

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-overlay-reference-A-v1 --strategy experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts/reference_instrumented.py --tape data/round2/round2_public.csv --stage flags-zero-c1-equivalence-gate
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-vol-risk-capacity-A-v1 --strategy experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts/volatility_capacity.py --tape data/round2/round2_public.csv --stage frozen-volatility-risk-capacity
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-full-risk-capacity-A-v1 --strategy experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts/microstructure_capacity.py --tape data/round2/round2_public.csv --stage frozen-full-risk-capacity
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-full-risk-width-A-v1 --strategy experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts/microstructure_width.py --tape data/round2/round2_public.csv --stage frozen-full-risk-one-tick-widening
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-full-risk-capacity-A-repro-v1 --strategy experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts/microstructure_capacity.py --tape data/round2/round2_public.csv --stage positive-public-record-reproduction-and-cycle-attribution --full-logs
```

Each succeeded, inputs unchanged, penalty0,32.6--39.5s measured runtime.
Original IDs are immutable; new repetitions require new IDs. Raw plans,
snapshots/results/full logs remain under ignored experiments.
One-arm pnl_se is not paired deltaSE, bootstrap private P(win) or a reason
to claim161k reliably transfers to a fresh tape.

## Validation and decision

All four frozen files passed preflight, Ruff check/format and strict types:

```bash
env -u VIRTUAL_ENV uv run --locked ruff check experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts
env -u VIRTUAL_ENV uv run --locked ruff format --check experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts
env -u VIRTUAL_ENV uv run --locked mypy --strict --follow-imports=silent experiments/round_2/dataathletechamp/risk-overlay-v1/artifacts
env -u VIRTUAL_ENV uv run --locked pytest -q experiments/round_2/dataathletechamp/risk-overlay-v1/test_risk.py
```

All passed; four focused tests cover cancellation-flight reservations,
no opposite-side credit, preserving an old safe head,200-lot reference
headroom and past-only/missing-book volatility. Runtime hard checks stayed
within100 actual and per-side potential exposure during every callback.
Human review/server validation still precede release.

`env -u VIRTUAL_ENV make check` also passed:25 project tests, lint/format,
strict types, guide/upstream fingerprints and existing preflights.
The retained standalone path separately passed conservative preflight, Ruff
check/format and strict mypy; its bytes remain identical to the reproduced file.

Next user-requested wave is bounded: fixed-size/exposure recycling probes,
fixed35 comparator, then one-change risk-leader extensions and separately
validated large-flow IOC. Record every outcome, including lower PnL. Retain/
announce a higher positive public file only after exact reproduction; no automatic
Final switch, uploads, clock-hardcoded crash strategy or penalty expansion.
