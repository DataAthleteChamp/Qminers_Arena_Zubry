# Round 0 v2: reject v1 flow carryover; investigate depth-aware quoting

**Research only. No new submission or trading policy has been implemented.**
The official simulator, original strategies and raw CSV files remain unchanged.

## Inputs and method

- V1: `data/round0/sample.csv`, SHA-256
  `33dd6764c54000244f1a2e0691e6efbac226684554843147f622e0431b35e8dc`.
- V2: `data/round0/sample_v2.csv`, SHA-256
  `dd4e00e281abe50c9a19e16c147ccbc0b5b69835fee567f00136402ef1e01d08`.
- V1's observer uses official replay without orders. Fixed tests: external flow,
  causal time since flow, and static best-queue imbalance.
- First 20 minutes: discovery; next two 20-minute blocks: chronological checks.
  V2 additionally covers 3600-4800 and 4800-5750 seconds, declared before analysis.
- Signal definitions and horizons were not tuned after seeing v2.
- `tools/research_round0.py` produces immutable plans/results and script snapshots.
  `causal-profile-v1` retains the failed integer-second sampler; v2 corrects it
  to wait causally for a complete quote. All versions are preserved.
- The first tape was previously used by full baseline runs; it is not a newly
  untouched holdout. V2 is a separately supplied file, but independent sampling
  and the private-data distribution are not verified.

## Structural observations

| Quantity | First tape | V2 |
|---|---:|---:|
| Market event rows | 53,758 | 2,000,000 |
| Observed duration | About 3600 s | 5749.869 s |
| Complete-book spread | Always 2 ticks | Mean 1.579 ticks; range 1-4 |
| Visible resting orders | One per side when complete | Many orders; common states around 60-70 per side |
| External signed-flow callbacks | 604 | 33,718 |
| Median event interval | 1 microsecond, with quote-refresh bursts | 1.901 milliseconds |
| Mean aggressive-flow interval | 5.942 s | 0.171 s |

Event-weighting is misleading on v1: quote cancel/reinsert callbacks are mostly
one microsecond apart. Complete quotes cover 99.9989% of wall-clock time despite
many missing-side rows. V2 has complete quotes for 99.9991% of wall-clock time.
Neither result identifies a currency, stock, future or fundamental fair value.

## Frozen flow test

Isolated one-lot entry at the old touch with actual 5 ms eligibility, then mark
against the available opposite quote at the delayed exit horizon:

| Four-second diagnostic, ticks | 0-1200 s | 1200-2400 s | 2400-3600 s |
|---|---:|---:|---:|
| V1 same-direction flow | +7.46 | +8.40 | +8.08 |
| V2 same-direction flow | -1.67 | -1.67 | -1.66 |

The remaining v2 blocks are negative too. V1's continuation is a synthetic
tutorial mechanism, not a transferable ticker identity. Flipping v2 flow direction
does not solve the spread cost: its opposite-direction diagnostics are negative too.

These numbers are **not strategy PnL**. Signals overlap, entries are hypothetical
one-lot executions against a no-user-order tape, exits are quote markouts, and
our own counterfactual book impact and exit-IOC behavior are not simulated.
Never multiply these means by all signals/size and call the result a profit forecast.

## Actual existing-policy simulator tests

Both strategies were executed and repeated on the exact v2 file:

| Existing strategy | Actual public PnL | Filled orders | Final inventory | Penalty |
|---|---:|---:|---:|---:|
| Unchanged official trend follower | -531 | 618 | 0 | 0 |
| Team one-lot follower with missed-IOC reset | -14,125 | 16,594 | 0 | 0 |

IDs: `r0-v2-original-check`, `r0-v2-team-check`, and their `-repeat` runs.
The corrected callback is mechanically necessary but makes a losing policy
continue trading. The original's smaller loss is not proof of a better signal:
its missed-IOC busy-slot bug can stop further trading.

**Do not promote the current `strategies/zubry.py` as a profitable v2 strategy.
Do not undo a correctness fix to hide the policy's losses.**
These are local official-engine results, not server-sandbox validation or private PnL.

## Depth hypothesis is the next candidate, not an adopted model

At the same causal one-second grid, correlation of best-queue imbalance with
one-second subsequent midpoint changes is:

| Block | V1 | V2 |
|---|---:|---:|
| 0-1200 s | 0.035 | 0.325 |
| 1200-2400 s | 0.025 | 0.343 |
| 2400-3600 s | approximately 0 | 0.341 |
| 3600-4800 s | Not available | 0.353 |
| 4800-5750 s | Not available | 0.339 |

Correlation is a hypothesis screen, not executable edge. Prediction magnitude,
conditional-on-fill markouts, queue position, cancellation delay and the spread
must still be tested. No parameter is fitted or strategy promoted by this report.

### Hypothesis card A: depth-aware inventory-controlled maker

- Mechanism: queued demand/supply helps estimate near-term fair value and avoid
  unfavorable passive fills in a persistent multi-order book.
- Start with midpoint versus a depth-weighted BBO heuristic:
  `(ask * bid_size + bid * ask_size) / (bid_size + ask_size)`.
  Aggregate price-level quantity and exclude our own liquidity. This heuristic
  is not the full estimated dynamic Stoikov micro-price model.
- Compare small quotes around the estimate, with explicit inventory adjustment,
  pending-order reservation, queue-preserving shrink and delayed cancel state.
- Fit any coefficient on declared discovery data; freeze it before later tests.
  Compare actual PnL with a plain midpoint maker and no-trade reference.
- Reject if held-out/blocked net PnL depends on optimistic fills, a single block,
  a fixed 10000 anchor, excess inventory, stale cancels or fragile parameters.
- No taker overlay until the forecast's magnitude covers the executable spread.
  Keep unused mechanisms disabled behind flags, with their failed results.

## Real-market analogy and reference limits

V1 resembles a toy flow-impulse/temporary-pressure experiment. V2 is closer in
structure to a large-tick electronic equity/futures order book with queue-dependent
liquidity. This is an analogy, **not instrument identification**. The fixed tape
does not recreate adaptive market participants or prove real-money profitability.

- [Headlands, Quantitative Trading Summary](https://blog.headlandstech.com/2017/08/03/quantitative-trading-summary/):
  public educational book pressure/trade impulse and execution/reconciliation.
- [Gould and Bonart, Queue Imbalance as a One-Tick-Ahead Price Predictor](https://arxiv.org/html/1512.03492):
  simple depth hypothesis; original random pooled split is not our forward test,
  and direction prediction is not executed trading profit.
- [Optiver, adversarial research](https://www.optiver.com/insights/technology-blog/machine-learning-in-trading-an-adversarial-research-problem/):
  public discussion of conditional fills, adverse selection and venue differences.
- [Bouchaud, Farmer and Lillo, supply/demand digestion](https://arxiv.org/abs/0809.0822):
  abstract reviewed for the order-splitting/impact analogy only, not a fitted model.

## Reproduce research using uv

Existing IDs deliberately refuse overwrites. Choose a new ID for reproduction:

```bash
uv run --locked python -m tools.research_round0 \
  --id your-v2-reproduction --data data/round0/sample_v2.csv --end-seconds 5750
uv run --locked python -m tools.compare r0-v2-original-check r0-v2-team-check
make check
```

Ten tests pass, including pre-activation book timing, spread-aware delayed
markout, window boundaries and the causal complete-quote sampler.
All results and negative findings are retained. No new strategy file, upload,
private z-score or probability-of-winning claim is produced.
