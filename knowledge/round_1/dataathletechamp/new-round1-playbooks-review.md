# New Round1 playbooks: strongest next executable question

Read both complete supplied documents; no referenced Python candidates were
provided, so all new variants are rebuilt from OUR exact reviewed source bytes.

| Input | Bytes | SHA256 |
|---|---:|---|
| ROUND1_RESEARCH_PLAYBOOK.md | 31008 |93ad383e3e38aba5508d024a3f674c20d34b7d670069dc11dc82987b4ca6f766|
| ROUND1_EXECUTION_AND_FORECAST_RESEARCH.md |24040|538743ddad095ccccc718255670cf53c615cba1631d0385b32914ca19281891e|

Their331376/370367/381071/etc are INDEPENDENT C++ replay estimates, not official
new records. Their future signal/R2/bootstrap tables are author-reported analyses
which were not freshly reproduced here. The submitted344438 metadata matches
our corrected historic artifact, but the reported server runtime is not measured
by our local tests. Do not claim actual server/private validation of new files.

## Priority1: ownership-consistent external aggressive flow

Current filter excludes market takers hitting our own maker. At small quotes,
that exclusion may be minor; with millions of our executed lots it may materially
shift the signal away from the no-user training definition.

Test ONLY:

```
taker_owner=="market" and maker_owner=="market"
```

versus all trades with`taker_owner=="market"`, STILL excluding our own taker
flow. Keep quote parameters, queues, risk and corrected coefficients unchanged.
This is a feature-definition hypothesis, not a proved bug requiring blind repair.
Our trades influence the observed book; all-external flow can be endogenous too.

Registeredflow-observation-v9 has3 exact one-line arms: current477516 ridge-price
record, simpler459038 flow maker and historic344438 ridge-sizing submission.
Compare original-full net PnL first, then later warmed windows for a winner.
No missing package Python file is assumed to exist or copied from unknown code.

## Already completed / lower-priority instructions

Larger target200 and side-wise100 envelope work; global quantity is NOT position.
Price-based richer forecast outperformed its earlier mostly-clipped size tilt.
Tiny IOC gates lost; no IOC enabled in current record. Safer1/2-tick retained
layers lost strongly; FIFO value alone did not rescue their price competitiveness.
Nonblocking new quotes helped slightly when every old pending/cancel quantity
was STILL reserved. Never grant cancel credit or net opposing orders.

The true clock is scheduled ready-time processing before the next market row,
not charging all actions at the next row timestamp. Actual SDK contract test
verified private events at6000us before a10000us row.

## Remaining ranked questions

After the flow-definition ablation: measured user-as-taker LIMIT fills and
maker-fill-conditional markout; then slow/fast horizon disagreement if warranted.
Own-opposite-price guards are not self-trade prevention: the SDK already excludes
self matches. Add a guard only as an isolated tested execution rule.
Wall clipping is low ROI in the supplied estimates; do not spend remaining time
on dozens of wall constants, Hawkes/deep nets or a big DP before simple controls.
Previously tested hierarchical return reconciliation was already coherent and
did not establish new alpha; no need to repeat it without a new mechanism.

No future prices, memorised path, unconsumed-holdout claim, outside-team help,
evaluator change, automatic upload or private-score tuning. New observed records
are copied to PnL-labelled files before notifying the human; earlier files remain.
