# First diagnostic: valid flow results, failed calendar-grid sampler

The official null observer recorded 53,758 callbacks, 604 external-flow callbacks
and a two-tick spread in every complete two-sided snapshot.

The predeclared whole-second grid returned **zero** valid observations:
the synthetic tape cancels quotes at integer seconds and replaces them a few
microseconds later. This is a sampling defect, not absence of a depth signal.
The result is retained rather than discarded or presented as evidence against imbalance.

Next research version uses the first complete callback at or after each fixed
calendar target, a causal rule available online. It also time-weights transient
missing books instead of treating every event as equal wall-clock exposure.
This correction is not a tuned trading-strategy change. No strategy was written.

Flow-horizon results are isolated one-lot quote-path diagnostics, not portfolio
PnL: signals overlap, execution is based on the null tape, and exits are markouts.
The whole tape was previously used by baseline runs, so later blocks are not
claimed to be a genuinely untouched final holdout or a second independent tape.

