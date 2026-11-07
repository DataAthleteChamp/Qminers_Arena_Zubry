# Mean reversion and residual trading

**Status: statistical hypothesis, not an automatic contrarian rule.**

## Signature

Deviations from a defensible anchor or hedge residual revert across comparable
periods, at a horizon shorter than the usable session and large enough after
costs. Negative return autocorrelation may just be bid-ask bounce.

A possible residual is `x_t = log(P_A) - beta*log(P_B) - c`, for positive prices
where that model makes sense. Other payoffs may require a different transform.
Fit beta, center, scale and thresholds on past data. Correlation or high
level-regression R-squared does not establish a stationary tradable residual.

## Minimal experiment

Compare a simple fixed-reference/threshold policy with the incumbent before
adding OU, Kalman, PCA or dynamic state. State fit window, units, entry, exit,
capital use and leg-execution assumptions. Test with later comparable sessions,
cost-aware fills, parameter neighborhoods and residual/hedge stability.

ADF/Hurst/variance-ratio outputs are screens under their own assumptions, not
standalone entry signals. Tiny samples and repeated pair screening create false
discoveries. Every pair and parameter variant counts as a trial.

## Stop conditions

Residual level/slope changes, hedge beta becomes unstable, reversion time exceeds
the horizon, correlations cluster into one directional position, or legs cannot
be executed/financed as assumed. A stop-loss caps losses but cannot validate a bad model.

## Sources

`avellaneda-lee-primary`: factor-neutral residual model, past-only estimation,
explicit costs and regime-dependent equity results. Its daily windows and
thresholds are NOT defaults for this competition.
`prosperity-concentration`: leave-one-day-out and concentrated strategy examples.
`pbo-primary` / `adaptive-holdout`: selection and repeated-test caveats.
`own-imc`: elegant PCA residuals were not the principal realized profit driver.
