# Zubry agent operating rules

Read `TEAM_START.md`, `competition.json`, the current round brief and
`docs/human/TEAM.md`. Use the official simulator; never substitute the old demo.
Use uv for all Python dependency management and execution; no pip or global Python.

## Non-negotiable

- Commit research at least every 30 minutes, including failed experiments and
  a short result note. Checkpoint honestly even without an improvement.
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

Use `tools.run_experiment` to record outcomes, including failures, and
`tools.preflight` for local conservative checks. The official CLI does not run
the website's complete static sandbox checker. Server validation is still needed.
No naive row-slicing of event tapes: preserve order-book warmup and state.

`make check` checks only team additions. Do not run a formatter over original
code, raw data or frozen experiment snapshots. Surface errors; no silent defaults.
Keep callbacks lightweight. 5 ms is simulated exchange latency; CPU runtime has
a separate 15-minute server budget.
