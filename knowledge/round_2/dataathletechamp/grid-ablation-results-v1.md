# Grid experiments: profitable turnover beats blanket risk-off on A

Same registered A and unchanged official SDK; supplied eleven prediction
weights are frozen, fit provenance UNKNOWN. No B raw replay or automatic Final.

| Frozen A arm | Net PnL | Lots | Median abs I | Finding |
|---|---:|---:|---:|---|
| Original Grid reference | 91025 | 252321 | 52 | Exactly reproduced; reported original B28827 |
| Quote64, same hard100 | 90088 | 344508 | 43 | More volume did not raise net |
| EMA target amplitude50 | 71570 | 334305 | 36 | -19455 versus reference |
| Neutral target0 | 57317 | 350693 | 20 | Profitable A, but33708 below reference |
| Guarded neutral recovery | 63876 | 248921 | 40 | Avoiding/reducing shock exposure costs27149 on A |
| FIFO head replenishment | 100195 | 284916 | 52 | +9170 versus reference |
| FIFO plus warned-side gap protection | **103998** | 283395 | 52 | +3803 versus FIFO; +12973 versus reference |

Target50's exact loss is19455 versus91025. All arms penalty0; hard actual/
same-side potential100 assertions held. An optional risk-averse objective might
prefer lower dispersion, but our contest metric is net PnL.
None of the lower-A arms has been tested on B: they are not proven worse on B.

FIFO improves A primarily through useful turnover: lots increase12.9% and net
profit10.1%, while median inventory stays52. Gap protection adds3.8% net versus
FIFO with about0.5% fewer lots. This is stronger evidence than fill-count growth.
Net/lot includes inventory gains/losses, not pure maker spread or causal
adverse-selection attribution.

The control versions with every new flag disabled exactly match all91025
reference fields. Both positive FIFO/gap arms exactly reproduce every result
field under new immutable IDs, with unchanged input bytes and penalty0.
Raw result/snapshots and failed static
checks remain in ignored experiments; no old artifact was rewritten.

## What changed

Original Grid has one working order per price. It keeps a partial head but
never replenishes that level until its order vanishes. New FIFO mode preserves
that old head and submits only admissible deficit>=8 as a separate back child,
at most2children/price and6/side. Original aggregate price target remains32
(or state16), and every live/inflight/cancel-pending residual is reserved.

Gap mode observes **finite** second-level market prices within20ticks:
L1<=100 and next distinct gap>=2 warns that side. Only its state quantity is
capped at12; opposite prices/quantity/forecast/target are unchanged.
Oversized younger children are canceled first. The old residual stays reserved
until actual private ACK; no instant resize or unlimited trade budget.

No model of another trader's intention/news was added. No second visible price
is censored, not an infinite gap. See
[order reaction audit](order-reactions-and-gaps.md) and the actual shrink
contract tests; production modifier remains disabled because obsolete shrink
requests may fail without MODIFIED notifications.

## Recorded commands and outcomes

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-quote64-A-v1 --strategy experiments/round_2/dataathletechamp/grid-variants-v1/artifacts/quote64.py --tape data/round2/round2_public.csv --stage grid-front-quantity64-common-hard100
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-target50-A-v1 --strategy experiments/round_2/dataathletechamp/grid-variants-v1/artifacts/target50.py --tape data/round2/round2_public.csv --stage grid-inventory-target50
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-target0-A-v1 --strategy experiments/round_2/dataathletechamp/grid-variants-v1/artifacts/target0.py --tape data/round2/round2_public.csv --stage grid-neutral-target-ablation
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-safe-recovery-A-v1 --strategy experiments/round_2/dataathletechamp/grid-variants-v1/artifacts/safe_recovery.py --tape data/round2/round2_public.csv --stage grid-gap-recovery-neutral-reserved-exposure
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-fifo-replenish-A-v1 --strategy experiments/round_2/dataathletechamp/grid-fragility-v1/artifacts/fifo_replenish.py --tape data/round2/round2_public.csv --stage preserved-head-aggregate32-deficit-replenishment
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-gap-protection-A-v1 --strategy experiments/round_2/dataathletechamp/grid-fragility-v1/artifacts/gap_protection.py --tape data/round2/round2_public.csv --stage visible-gap-side-quantity12-preserved-head-baseline
```

All succeeded with input hashes unchanged. A-reference replication91025 and
unchanged R1 transfer149143 were already verified. Preflight/Ruff/strict mypy
passed on both frozen families; two recovery/reservation tests and two
head/gap tests passed. E501/I001 setup failures were preserved before fixes;
they generated no fabricated simulation outcome.

## Validation gate now

Human confirmed current Final is original Grid+28827 and9upload slots remain.
Compare two frozen, reproduced **FIFO** versus **FIFO+gap** files on B before
changing Final. They isolate the incremental protection mechanism.

Files under `strategies/round_2/dataathletechamp/`:
`r2_grid_fifo_public_100195.py` SHA256
`506e03b0154d6ebde759945a6b2fc3f4a1e14b1d2f7e53d2b794f943a0ccaf58`;
`r2_grid_gap_public_103998.py` SHA256
`ac3d1814a3566e7e0507e2d2964b89e3aed8e572515f8c659b22aeff6600d8de`.
Both are one no-argument BaseStrategy, stdlib/public SDK, below14KB.

Successful reproduction commands:

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-fifo-replenish-A-repro-v1 --strategy experiments/round_2/dataathletechamp/grid-fragility-v1/artifacts/fifo_replenish.py --tape data/round2/round2_public.csv --stage positive100195-fifo-B-comparator-reproduction
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-grid-gap-protection-A-repro-v1 --strategy experiments/round_2/dataathletechamp/grid-fragility-v1/artifacts/gap_protection.py --tape data/round2/round2_public.csv --stage positive103998-public-record-reproduction --full-logs
```

No publicA score predicts a2x realized B result. B feedback is selection data,
not a fresh holdout; C stays blinded.
400k B has **not** been achieved or established by these A results.
