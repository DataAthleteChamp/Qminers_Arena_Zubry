# Final standalone midpoint candidate

File: `strategies/zubry_v2.py`.
Frozen copy: `submissions/playground/cae618bb5b61/strategy.py`.
SHA-256: `cae618bb5b616c4579d0178def01d9c84ad45c946e952ad132f651596000cf9e`.
Size: 4333 bytes.

Exact final bytes were run twice on `data/round0/sample_v2.csv`:
10395 PnL, 7528 filled orders, 15030 volume, final inventory -2, zero penalty.
Final runtime was about 18 seconds locally. Reproduction is the same tape, not
independent statistical validation or an authenticated second human review.

All 16 tests, lint/format, strict tool/strategy typing and local preflight passed.
A test-only syntax error and an incomplete order-price variable rename were caught
and corrected before final runs. Earlier depth/control snapshots/results are kept.

Depth overlay remains implemented but default-disabled. No hardcoded asset price
or future schedule, no flow-follower policy, no team-module/file/network imports.
Server sandbox acceptance and Final selection still require manual website upload.
This is public-tape evidence only, not private-round profitability.
