# Start a new session here

Open this exact checkout:
`/Users/jakubpiotrowski/PycharmProjects/Qminers_Arena_Zubry`

Read `TEAM_START.md`, `AGENTS.md`, `competition.json` and the current round brief.
The official simulator is the base. Do not import the old `Qminers_dev` demo engine.

```bash
uv sync --locked
make check
make compare
copilot --agent zubry-researcher
```

Other roles are `zubry-builder` and `zubry-reviewer`. Restart after adding agent
files; use `/agent` to inspect them. `/skills reload` refreshes skills.
Subagents explicitly inherit repository instructions. Roles and tool lists do
not create a filesystem sandbox.

## Task examples

- Researcher: "Read r0 and its data manifest. Diagnose one flow/queue phenomenon.
  Give two falsifiable hypotheses, relevant sources and cheapest test. No code changes."
- Builder: "Implement experiment r1-a2-003 in my branch, preserve the official
  simulator, run local preflight and record success/failure. Do not upload."
- Reviewer: "Read the diff and recorded public results. Check timing, inventory,
  data leakage and assumptions. Give approve/needs-evidence/reject; do not edit."

Commit at least every 30 minutes, including failures. No squash, rebase, amend,
force-push or Copilot attribution in messages. Handoff with a commit, file hash,
experiment IDs, limitation and next action. Public sandbox checks are not private tests.
