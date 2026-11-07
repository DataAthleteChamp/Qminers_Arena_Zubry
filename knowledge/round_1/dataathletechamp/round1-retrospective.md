# Round1 retrospective: executed profit, not forecast accuracy

This is the curated handoff, not a new experiment plan. Original development
tape SHA256:362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940.
It had4411336 rows and approximately12000 simulated seconds.
The retained ledger contains**185 successful bounded official CLI replays**,
including window checks, reproductions and stress runs, not185 independent models.
Setup/model-endpoint/static/test-design failures occurred before those successful
CLI runs and are preserved separately. Earlier records are not rewritten.

## What we did and why

We first audited every raw row and replayed the market with no orders. The
anonymous instrument mostly had a one-tick spread, heavy-tailed submitted sizes,
long FIFO queues and short-horizon book/flow predictability. Absolute prices did
not authenticate a real-world ticker or fixed fair-value anchor.

The official SDK, not an independent C++ surrogate, determined price-time fills,
5ms actions, partial/cancel races and depth-based terminal liquidation. We kept
the common same-side envelopeI+B<=100 andI-S>=-100 throughout.

We built a price/inventory maker, then tested size, FIFO top-ups, price skew,
book/flow signals, fitted forecasts, IOC additions and regime controls separately.
Exact source bytes and original-tape results were retained before a file was
offered for manual submission. Public optimisation was labelled as such.

## What worked

| Mechanism / original-public benchmark | PnL |
|---|---:|
|inventory/queue maker,95 nominal|343269|
|corrected ridge-size hybrid|344438|
|200 target, full-capacity3-slot maker|434519|
|same, skew0.005|449661|
|QI plus short-flow price controller|459038|
|corrected0.5s forecast used for price, scale2|477516|
|Maciej8-slot/skew0.001 Final|505225|
|same, forecast-driven price shift clipped at±1|507393|

Target200 is not permission for200 inventory. AtI=+100, a sell200 can end at-100;
at flat inventory each side can reserve at most100. Top-ups retain earlier FIFO
while using REAL unused capacity. Cancel-pending quantity never becomes free early.

The richer predictor was more useful for PRICE selection than a small size tilt
often clipped by headroom. Price multipliers are control settings, not claims
that predictive accuracy multiplied by2 or3. Moderate inventory skew mattered.

## What failed or was too small

Blind market taking did not pay spread/execution/continuation costs. One-lot
adverse reduction, ungated reduction and rare-tail gates lost1968/4307/103 on
their matched first4800s tests. No IOC was enabled in the final candidate.

Safer-looking old deep layers lost32670/74121 in the matched first4800s checks.
FIFO age has value only at an economically useful price; tying up capacity can
cost more than preserving the old slot. Nonblocking admission helped only when
ALL pending/cancel quantities remained reserved.

More slots beyond8 plateaued; minimum1-lot top-ups slightly lost. Zero skew,
strong forecast scaling, arbitrary half-width changes and some QI overlays lost.
Reversal/continuation size gates did not beat the new505225 incumbent.
The final clipping gain over that incumbent was only2168, not550k achieved.

Including market takers hitting our makers was a useful ablation, NOT an automatic
bug fix:477516->474767,459038->461013,344438->344015. Preserve feature definitions
and fit consistency rather than blindly replacing every ownership filter.

Temporal reconciliation of common-fit additive returns was already coherent
near1e-15; it did not create an independent economic edge. More papers/models or
a better midpointR2 cannot substitute for executed net PnL.

## Quality and time lessons

A training-label boundary defect was caught: actual future target timestamps
must stay inside the fitting cutoff, not just their origin timestamps. The
released ridge arrays were corrected before retention. Old trials remain marked.

A cancel test initially forbade all new orders; a BUY fill legitimately frees
SELL headroom. Correct tests check each side's reserve, not an artificial global
no-order rule.13 focused capacity and5 mixed/actual-SDK cases subsequently passed.

Our239995-row official-replay feature grid had no nonpositive BBO samples.
The supplied independent reconstruction's zero-midpoint placeholders were not
used for our fit. Never use future interpolation to invent an online midpoint.

We tried too many marginal policy variants late. In Round2, pair research with
execution/risk, freeze a small useful candidate ladder early, preserve a known
working Final, and leave time for exact server acceptance and two-person hash
verification. Raw experiment volume is not the objective.
