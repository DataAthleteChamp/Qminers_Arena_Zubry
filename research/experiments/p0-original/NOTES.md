# Unchanged official tutorial baseline

Actual run: 1878 public PnL, 305 fills, zero inventory penalty.
This executes the exact original `strategies/trend_follower.py`.

Source review identified missing `_order_in_flight = False` in its
canceled/rejected IOC branch, compared with the getting-started PDF.
The synthetic tape gave the same score as the corrected team copy.
No claim that this run proves the edge case is safe or that private data behaves alike.
