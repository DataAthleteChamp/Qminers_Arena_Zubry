---
name: market-diagnosis
description: Inspect a named real Arena tape and its provenance, timing, depth, flow and missingness before choosing one-instrument strategies.
---

Read [research contract](../../../docs/agent/RESEARCH.md).
Record source/hash/role and actual time horizon. Do not infer ticker/currency from
price or confuse the playground sample with Round 1. Aggregate individual-order
depth correctly and account for user orders, the 20-tick window and 5 ms delay.
Output at most three falsifiable mechanisms and a cheapest test, not alpha proof.
Preserve original data and commit notes regularly. No tools are pre-approved.
