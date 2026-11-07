# Depth overlay: positive but inferior to the midpoint control

Predeclared pair differs only in `IMBALANCE_WEIGHT` (1.0 versus 0.0).
Same v2 tape, inventory skew 0.05, two-lot quotes, 20-lot internal cap and unchanged
official engine.

- Depth: 8992 PnL, 5128 filled orders, final inventory -4, zero penalty.
- Midpoint: 10395 PnL, 7528 filled orders, final inventory -2, zero penalty.
- Depth loses 1403 relative PnL on this consumed public tape. Keep it disabled.

A predictive depth correlation did not guarantee better executed profit.
No private-data gain, paired-delta SE or P(win) is claimed.
The original depth-enabled code is preserved in this experiment's strategy snapshot.
