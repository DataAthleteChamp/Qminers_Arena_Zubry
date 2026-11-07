# Round1 decisions: known reasons and unknown human choices

## Evidence hierarchy

Official rules/SDK and participant-supplied official results outrank independent
replay estimates. Papers, GitHub examples and supplied research memos suggested
mechanisms; their reported figures were not scored as our official results.
Raw data, completed plans/runs and frozen submissions were never retuned in place.

The four policy decisions we can justify from executed tests were:

1. Stay inside100 with separate filled+pending BUY/SELL extrema: naive overflow
   and fast forced-exit examples lost heavily;1000 is an acceptance wall.
2. Use larger SAFE quoted quantity and FIFO-preserving top-ups: original-public
   PnL rose substantially without penalties or ledger discrepancy.
3. Convert short-horizon forecasts into price controls, not indiscriminate IOC:
   the price ladder improved while tested taking gates lost.
4. Keep controls simple enough to reproduce: every retained candidate had exact
   hashes, original-tape replay and local SDK/risk/static checks.

## Actual Final is not the last local research maximum

The participant confirmed the LAST submitted/final strategy was Maciej's505225
file, SHA256c1f194668ec83e94bf522e749ce36d266caeedb9244506ede2adeee68e8e3667.
It is frozen in`submissions/round_1/dataathletechamp/final_20261107/strategy.py`.
The official public archive reproduces505225; the supplied private archive
reconciles504903. The reported official leaderboard placed Zubry14th.

The507393 clipping candidate was a LOCAL public research maximum. It was not
the Round1 Final. Its private result isUNKNOWN. Do not replace the Final record
with the largest filename number, or infer that its private score was507393.

The exact human reason for choosing505225 over507393 was not recorded; do not
invent a safety, private-validation or deadline justification. The operational
lesson is to record uploaded bytes, successful sandbox result, submission ID
and the dashboard's Final selection explicitly while time remains.

## Why the private result matters, and what it does not prove

505225 public versus504903 private differs by-322 (-0.0637%). One selected
strategy transferred closely on these two tapes despite different terminal
prices/inventory. This is one observation, not proof that all fitted knobs,
R1 forecasts, Round2 mechanics or future private paths will transfer.

Rank14 and the leader's792696 show a genuine performance gap. The full copied
leaderboard skips rank56; no officialz-score or aggregate tournament standing
can be computed honestly from that incomplete pool alone.

## Integration and cleanup decision

The human approved a fresh Round2 worktree, not deleting old experiments.
The original`Qminers_Arena_Zubry` checkout stays on the R1 branch with archives,
raw experiments, logs, input documents and its two nested worktrees intact.
The new`Qminers_Arena_Zubry_Round2` workspace starts from curatedmain.

Only reusable notes, exact Final/public-private result summaries, provenance and
the507393 carry-forward candidate go tomain. Large raw ZIPs and research-package
clutter stay out. No squash, rebase, amend, force-push or competition upload.
