# Four-person work and history rules

Pair A: data/research + strategy implementation.
Pair B: execution/risk + validation/integration. Assign actual names before round 1.
One person submits; another verifies final file/hash. Name a backup.

## Commit policy is mandatory

- Commit at least every 30 minutes on your work branch, even without an improvement.
- Commit failed experiments and a short note: hypothesis, command, outcome and reason.
- No squash, rebase, amend, force-push or history rewriting. Use ordinary merges.
- Owner requires commit messages without Copilot attribution/trailers.
- Keep discarded mechanics behind a default-disabled parameter/flag and keep their notes.
- Do not manufacture a model change just to have a commit; checkpoint research honestly.
- `main` should remain runnable. Exploratory failures can live on a named branch.

Use one active hypothesis per pair initially. Separate clones/worktrees; one
writer per owned file. The author is not the sole approver. Preserve frozen run
artifacts; a new attempt gets a new ID. Never format original simulator/explorer.

Handoff: commit, experiment ID, data/hash, result, limitation, current final file
and next action. Git records are the memory, not an agent chat.

Do not share code, strategies or results with other teams or outside helpers.
Use organizers on Discord for technical clarification. AI is allowed, but
submission code cannot bypass the sandbox.

Read [access status](ACCESS.md) before assuming the mandatory reviewer is connected.
