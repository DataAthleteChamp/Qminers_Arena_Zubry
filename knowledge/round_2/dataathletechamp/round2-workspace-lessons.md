# One active folder; explicit archives instead of invisible worktree state

Use `/Users/jakubpiotrowski/PycharmProjects/Qminers_Arena_Zubry` as the owner's
active checkout. Switch the owner's round branches there; do not create another
active `..._Round3` directory. Teammates still require their own writer space.

The separate Round2 worktree was deliberately created to preserve R1's raw
experiments. That protected history, but the workflow was not explained clearly:
Git branches share **committed files**, not ignored tapes, generated models,
logs, scratch code or another worktree's untracked Final.
Main also stayed behind the owner's latest Round2 research until integration.
This explains missing-file/access confusion; prompts/worktrees were never a
sandbox or a shared automatically synchronized workspace.

The new layout keeps the retired Round2 worktree under:
`experiments/round_2/dataathletechamp/worktree-archive-r2/`.
It is detached/read-only history, not the branch to edit.
Loose input/reference files are archived by original relative path with hashes.
Root R1-only tracked references are copied before checkout removes their working
copies; their original Git history remains unchanged.

Raw data, old plans, completed runs and submissions are never deleted to make
status look clean. Only the explicitly approved redundant virtualenv/tool
caches are removable. Archive manifests record moves and byte equivalence.
The original R1 nested worktrees remain registered and untouched.
Update 2026-11-08 (owner-approved): IDEs listed nested worktrees' untracked
files as changes, so both R1 worktrees were retired (scratch moved and
hash-verified) and `worktree-archive-r2` was unregistered from Git in place.
Every file was kept; see `docs/human/WORKSPACE.md` for the exact locations.

Current work paths:
- `knowledge/round_x/dataathletechamp/`: curated transferable Markdown.
- `strategies/round_x/dataathletechamp/`: retained standalone files.
- `experiments/round_x/dataathletechamp/`: local research/checks/results.
- `submissions/round_x/dataathletechamp/`: immutable selected bytes/evidence.

Use `env -u VIRTUAL_ENV uv run --locked ...` from the active folder. The selected
file, active branch, round, dataset hash, fit/feedback role and result should be
visible in every handoff. Stage reviewed paths explicitly; never squash, rebase,
force-push or overwrite another writer's work.
