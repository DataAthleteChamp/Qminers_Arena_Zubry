# Research ledger, including failures

Plans, exact strategy snapshots and outcomes live under `experiments/<unique-id>/`.
Keep notes explaining what was tried, including rejected and failed variants.
Large raw logs stay under ignored `logs/`; small summary results are committed.

At least every 30 minutes checkpoint code/research on the current branch, even
without an improvement. No squash, rebase, amend, force-push or Copilot attribution
in commit messages. Preserve experiments and unused mechanics behind parameters.

`upstream.json` pins unchanged organiser files. `materials.json` pins the supplied
PDF and exact synthetic playground file. Public PnL is not private z-score evidence.

The initial bootstrap records used `data/playground.csv`. The same bytes now live
at `data/round0/sample.csv`, with the same SHA-256. Those past plans are preserved;
canonical-path repetitions use new IDs rather than rewriting evidence.
