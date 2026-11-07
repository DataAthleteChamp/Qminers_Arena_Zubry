# Zubry: start here

This is the private official-template workspace, with team tools added on top.
The original `simulator/`, `explorer/` and two official strategies remain untouched.
See `research/upstream.json` for their fingerprints.

## Ready now

- Python 3.13 and the organiser's original locked runtime versions.
- `data/round0/sample.csv`: exact organiser synthetic sample, unchanged, 53,758 events.
- `strategies/zubry.py`: one-lot tutorial baseline with the PDF's missing IOC reset restored.
- Original and team runs both earned **1878 public PnL, 305 fills, zero penalty**.
  That is parity on one synthetic tape, not private-round alpha.
- Failed/successful runs are recorded under `research/experiments/`; large logs are ignored.
- Public references live under `knowledge/`; private predecessor code is not copied.

## Commands

```bash
uv sync --locked
make check
make compare
uv run python -m tools.preflight strategies/zubry.py
```

Use uv only; do not install/run this project with pip or global Python.
`make playground-original` and `make playground-team` use immutable run IDs.
Use a new ID for subsequent runs (see `docs/agent/EVALUATION.md`).
The preflight is conservative and local, not the complete server validator.
Upload only one allowed `BaseStrategy` file manually; never submit team tools.

## Read before round 1

- [Team/history rules](docs/human/TEAM.md): commit at least every 30 minutes,
  include failures, **no squash/rebase/amend/force-push**.
- [Round workflow](docs/human/ROUND.md), [playbook](docs/human/PLAYBOOK.md),
  [evaluation](docs/human/EVALUATION.md), [agent usage](docs/human/RUN_AGENTS.md),
  [release](docs/human/RELEASE.md).
- `competition.json`: current published mechanics and weighted private-score rules.
- [Access status](docs/human/ACCESS.md): `antoninkriz` has a pending **Write**
  invitation. True Read-only access is unavailable on a personal private repo.
  Owner must confirm an acceptable arrangement with organizers before round 1.

## Important boundaries

Keep inventory within +/-100 including in-flight/resting risk; 1000 is a rejection
wall, not a target. Orders/cancels arrive at least 5 ms later. Public upload is a
sandbox check on this same public tape; only private PnL decides the round.
No fake simulator, guessed currency identity, automatic upload or rank-chasing.
The old `Qminers_dev` research/demo repository is not the execution engine here.
The supplied PDF is in `materials/Algo Trade Arena Getting Started (1).pdf`.
