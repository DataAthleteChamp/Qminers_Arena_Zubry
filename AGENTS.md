# Zubry agent operating rules

Read `TEAM_START.md`, `competition.json`, the current round brief and
`docs/human/TEAM.md`. Use the official simulator; never substitute the old demo.
Always use uv for project execution and tooling: Python scripts, research,
backtests, tests, linting, formatting, type checks and dependency management.
Use `uv run --locked ...` and `uv sync --locked`; no pip, global Python, direct
`.venv/bin/python` calls or standalone project-tool binaries.

## Workspace layout

For new work, replace `x` with the round number (`round_0`, `round_1`, etc.) and
`user` with the assigned contributor handle/slug. Use the same owner folder
consistently across all three areas.

| Location | Contents |
|---|---|
| `knowledge/round_x/user/` | Valuable, curated research written in `.md` files |
| `strategies/round_x/user/` | Retained, reviewed standalone `.py` strategies |
| `experiments/round_x/user/<experiment-id>/` | All trial strategies, testing/backtest code, notebooks, sweeps, outputs, logs and scratch work |

Experimental variants stay in `experiments/`; promote a strategy to
`strategies/` only after review and appropriate validation. Experiments may be
messy internally, but do not scatter their files through the repository root,
`knowledge/` or `strategies/`.

Use descriptive lowercase kebab-case for research notes and experiment IDs,
and snake_case for Python strategy filenames. For example:
`queue-imbalance.md`, `inventory_maker.py`, and
`20261107-imbalance-skew-001`. Names should identify the topic/variant rather
than opaque labels such as `test`, `new`, or `final2`.

This layout and the commit scope below supersede older examples in
`TEAM_START.md`, other guides and tooling. Apply them to new work; do not move
or delete existing files, frozen artifacts or history without explicit approval.

## Curation, commits and main

- Keep `main` and the repository root clean and focused on useful shared work.
- By default, commit only research `.md` files under `knowledge/` that we deem
  valuable, and retained strategies under `strategies/`. Keep raw experiments,
  testing variants, generated logs/results and scratch files uncommitted.
- Curate experiment findings before committing: record the question, mechanism,
  data/hash, fitting/evaluation windows, reproducible commands, actual results,
  limitations and why the finding is worth retaining. Useful negative findings
  belong in research notes too; raw failed attempts remain in `experiments/`.
- Keep the 30-minute checkpoint discipline for valuable research/strategy
  progress, including meaningful failed-experiment lessons. Do not manufacture
  improvements or commit noise just to produce a checkpoint.
- Stage explicit reviewed paths, not the whole working tree. Check staged
  contents before committing; do not use broad `git add .` or `git add -A`.
- Committing instruction, tooling, configuration, data or other files outside
  `knowledge/` and `strategies/` requires explicit user authorization.

## Non-negotiable

- Never squash, rebase, amend, force-push or rewrite history. Merge normally.
- Per the owner, commit messages must not contain Copilot attribution or trailers.
- Preserve reusable mechanisms behind a parameter/flag instead of deleting
  their research because one round did not benefit.
- Do not modify official simulator/explorer or official examples. Human must
  explicitly approve a real upstream update and refresh fingerprints.
- Work in the assigned branch/clone. Do not overwrite another writer's work.
- Do not edit raw data, completed experiment artifacts or frozen strategies.
- Submitted code is one <=1 MiB Python 3.13 BaseStrategy file. No team-module
  imports, file/network/system/introspection access or sandbox bypass.
- No code, strategies or results shared with other teams, forums or outside
  helpers. Ask organizers for technical clarification. AI is allowed.
- No automatic merge, invitation, permission change, transfer or upload.
  In particular, never silently grant Write when Read was requested.

## Context and tests

Read the relevant `docs/agent/` procedure and knowledge card, not the entire corpus.
Record data/code/simulator hashes, source sections, fit/evaluation windows, time
units, baseline, hypothesis, rejection rule, actual command and actual result.
Public PnL is not private PnL; one-arm `pnl_se` is not a paired-delta SE or P(win).

Record every trial's outcomes, including failures, in its `experiments/` folder.
Use the official simulator and `tools.preflight` for local conservative checks.
Legacy recording tools that write to `research/experiments/` do not implement
the new layout: use a runner with explicit experiment-directory outputs or ask
for approval to adapt the tooling. Do not silently create more legacy outputs.
The official CLI does not run the website's complete static sandbox checker.
Server validation is still needed.
No naive row-slicing of event tapes: preserve order-book warmup and state.

`make check` checks only team additions. Do not run a formatter over original
code, raw data or frozen experiment snapshots. Surface errors; no silent defaults.
Keep callbacks lightweight. 5 ms is simulated exchange latency; CPU runtime has
a separate 15-minute server budget.
