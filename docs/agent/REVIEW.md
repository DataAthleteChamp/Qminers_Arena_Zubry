# Read-only evidence review

One bounded pass. State what was inspected versus executed.

- Correct public API, one subclass/no-arg constructor and allowed source?
- Pending/live/cancel-in-flight state, per-match fills and side tracking?
- Positive integer order quantity/price, correct enum side, no double-counted fills?
- Worst-case inventory including outstanding orders; penalty-free 100 not 1000?
- Causal 5 ms horizon, external versus own trade flow, level aggregation/window?
- Data/simulator/strategy hashes match; no modified original matcher?
- Proper warmup/time windows and consumed validation data?
- Genuine public result, fees/spread/liquidation/penalty attribution?
- No bogus private score, paired SE or future win probability?
- Independent reproduction and exact frozen bytes?
- Failed experiments retained, commit cadence and no history rewrite?
- No secrets, unlicensed copying or unauthorized outside-team help?

Return approve / needs-evidence / reject with at most five concrete findings.
No edits, commands, self-approval, upload, permission change or invented passing tests.
The reviewer model's verdict is not authenticated human approval.
