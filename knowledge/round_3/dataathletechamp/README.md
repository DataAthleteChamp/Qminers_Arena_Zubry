# Round 3 knowledge (dataathletechamp)

**Final:** U7 `r3_follower_u7_flow_deepfv.py`. Private tape **+589,202, rank 34
of 53**; validation 538,844; public R3 413,588. Start with
[round3-retrospective.md](round3-retrospective.md), then
[round3-to-round4.md](round3-to-round4.md) for the rules and the opening
checklist.

## Market and data

| Note | What it holds |
|---|---|
| [r3-market-diagnosis.md](r3-market-diagnosis.md) | R3 public tape vs R0–R2: registration, profile, frozen-strategy replays |
| [r3-ioc-limit-structure.md](r3-ioc-limit-structure.md) | IOC limit, not side, carries the forecast; remainders; hidden-IOC volatility precursor; 1 s foresight ceiling |
| [r3-oracle-gap.md](r3-oracle-gap.md) | Where perfect foresight beats us: late entry 57%, counter-swings 36%, deep-insert fair value |
| [r3-literature-synthesis.md](r3-literature-synthesis.md) | Literature and practice reduced to decision rules |
| [r3-strategy-research-wave1.md](r3-strategy-research-wave1.md) | Wave 1: engines, disproofs, experiment backlog |
| [r3-strategy-research-wave2.md](r3-strategy-research-wave2.md) | Wave 2: calibration, insert fair value, queue-behind, burst rejection |

## The strategy line that worked (U1 → U7)

| Note | Step |
|---|---|
| [r3-follower-candidate.md](r3-follower-candidate.md) | D1 informed follower (U1: B 272,176) |
| [r3-follower-tuning.md](r3-follower-tuning.md) | A_SWEEP 3 (fewer, better flips) |
| [r3-alpha-model.md](r3-alpha-model.md) | Ridge flip gate P1 (U4: B 411,302), pooled refit (U6: B 415,828), alpha v2 (rejected) |
| [r3-follower-deepfv.md](r3-follower-deepfv.md) | Deep-insert fair value + flow trigger (TRIG1) |
| [r3-u7-trigger-stack.md](r3-u7-trigger-stack.md) | U7 (B 538,844), neighbourhood, synthetic-tape check, U8 and rejected add-ons |
| [r3-validation-feedback.md](r3-validation-feedback.md) | Every upload, B decomposition (ordinary vs jump seconds), final private result |

## Rejected mechanisms (each kept behind an off-by-default flag)

| Note | Mechanism |
|---|---|
| [r3-aged-maker.md](r3-aged-maker.md) | Aged-queue FV-gated maker |
| [r3-combined-candidate.md](r3-combined-candidate.md) | Regime switch follower/maker (U3: B 258,688) |
| [r3-follower-aged-overlay.md](r3-follower-aged-overlay.md) | Maker overlay on the follower |
| [r3-follower-snipe.md](r3-follower-snipe.md) | Stale-side snipe |
| [r3-hidden-ioc-probe.md](r3-hidden-ioc-probe.md) | 1-lot probes inside wide spreads |
| [r3-follower-wallmid.md](r3-follower-wallmid.md) | Wall-mid deep-book fair value |
| [r3-follower-jump-guard.md](r3-follower-jump-guard.md) | Thin-exit-depth jump guard |
| [r3-follower-trig2.md](r3-follower-trig2.md) | Hidden-price G-insert class trigger |
| [r3-follower-exits.md](r3-follower-exits.md) | Blocked-flat, giveback, stops, opposite-flow flat |
| [r3-follower-revsleeve.md](r3-follower-revsleeve.md) | Slow contrarian (reversion) sleeve |
| [r3-follower-sleeves.md](r3-follower-sleeves.md) | Two-horizon fast/slow sleeves |
| [r3-follower-evidence.md](r3-follower-evidence.md) | Decayed-evidence position sizing |
| [r3-naive-families.md](r3-naive-families.md) | Eight simple families (momentum, EMA, imbalance, makers, fades, jump riding) |

Strategy files and their status are listed in
`strategies/round_3/dataathletechamp/README.md`. Raw experiments, worktrees and
server exports stay untracked under `experiments/round_3/dataathletechamp/`.
