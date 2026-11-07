---
name: paired-validation
description: Compare frozen strategies on matching official public tapes and record limits, failures, timing and reproduction without inventing private-score confidence.
---

Follow [EVALUATION](../../../docs/agent/EVALUATION.md).
Use new immutable IDs with tools.run_experiment and tools.compare. Freeze data,
strategy and original simulator. Keep failures and source snapshots.
One-tape delta and one-arm pnl_se are not independent validation or delta SE.
Use causal window warmup; never naive CSV row slicing or the old demo engine.
Do not overwrite evidence, pick final automatically, or bypass the server sandbox.
