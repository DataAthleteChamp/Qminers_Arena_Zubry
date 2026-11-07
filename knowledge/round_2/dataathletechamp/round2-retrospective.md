# Round 2 retrospective: execution improved, preparation did not scale

The objective of350k--450k was not established. The exact human-selected Final
is now frozen in
`submissions/round_2/dataathletechamp/final_actual_20261108/`.
Its supplied server export reports **80993**, zero penalty and923464lots.
The owner cannot distinguish validationB from finalprivateC, so its stage is
**UNKNOWN**, not an invented private leaderboard result.

Source SHA256:
`1d2c63ea53bc9497d5901d799fd4bf6964d46a406e8ca18493ca234de917e350`.
The unchanged source earned **127559** on registered publicA in
r2-actual-human-final-A-v1. This is one actual public replay, not live trading,
private probability or proof of a global optimum.

## What happened

R1's actual505225 maker lost143178 on R2A. Risk-aware sizing first stopped
some loss: the risk/Ridge variant earned18916 on A but lost229513 on suppliedB.
This was not a penalty failure; it traded comparable lots/second with worse
net economics. Jump-risk AUC did not rescue its price/inventory policy.

The teammate Grid became the better reference:91025A/28827reportedB.
FIFO replenishment plus finite-gap quantity protection reached103998A and
owner-reported43782B. A clean-book-only EMA update reached104703A and
**verified export47150B**. A single-level96 trial reached121235A, but its B
result was never supplied. It is not the actual selected Final.

The human Final changed several things together: one quote price per side,
up to8 same-price children, full32-lot top-ups, stronger0.05 inventory skew,
EMA10/60/120 and target100 from the10--60 EMA sign only.
**GRID_LEVELS=8 is a child-slot limit here, not eight price levels.**
Its result cannot isolate the value of any one change.

## What worked

The unchanged official matcher, explicit same-side reservations, byte freezing,
exact reproduction and cash/liquidation reconciliation made results auditable.
Price-time priority, pending cancels and quantity conservation mattered.
Useful FIFO heads plus admissible back-of-queue replenishment beat tiny-ticket
count maximization. Moderate capacity reduction prevented many bad fills.
Carrying inventory was sometimes useful: smallest inventory did not win B.

## What failed

Unconditional R1 transfer, bigger quotes without a new edge, generic spread
repair and blanket risk-off all failed important comparisons.
Three inside-spread repair arms returned-18422/62216/-6659 versus103998.
Global192 quotes returned54640; normal-only192 returned94156.
Smaller target0/50 and guarded neutral recovery reduced A profit; that alone
does not prove they are worse on B.

We spent too long circulating broad research/proxy packages and too little time
maintaining one visible selected file and early matched B feedback.
Different sampling/horizon/quantity definitions made plausible claims look more
comparable than they were. The final source remained untracked in the original
R1 checkout while Round2 work was in another worktree.

## Rules to carry forward

One active owner checkout, one writer, one source hash per candidate.
Profile new data and run the exact incumbent before strategy changes.
Freeze a short mechanism ladder, not a long parameter menu.
Use positive **incremental net PnL**, not more fills, AUC, lower variance or
standalone one-arm pnl_se. Treat B feedback as consumed selection and keep C
blinded until official release. Never infer B market volatility from wealth CSV.
Do not promise profit on every path or expand past100 as a substitute for edge.

All completed local trials and failures remain archived. The retained owner
runner ledger has54successful runs, including controls/reproductions and one
R1 diagnostic; it is **not54 independent models**. Setup/type/serialization
failures are separate preserved records.
