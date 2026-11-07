# Correctness baseline, not alpha

Actual run: 1878 public PnL, 305 fills, zero penalty; equal to the original on this tape.
Change: canceled/rejected IOC releases the busy slot and allows same-side retry.
Direct callback regression tests exercise both missing-fill statuses.

`IGNORE_USER_TAKERS=False` preserves original signal behavior. The optional filter
is parked and unvalidated, not promoted. Quantity stays one; do not increase it
without handling partial fills and pending inventory correctly.

No observed public profit improvement, private-score estimate or P(win) is claimed.
The frozen snapshot in this directory is the exact evaluated code.
