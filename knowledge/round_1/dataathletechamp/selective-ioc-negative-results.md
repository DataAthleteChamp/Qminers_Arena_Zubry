# Tiny maker/taker combinations: rejected first-stage gates

Same consumed first4800s prefix, correct frozen0.5s forecast, unchanged ordinary
skew0.005/200-lot/3-slot maker, one IOC at a time, touch-price cap, joint±100.

| Policy | Actual prefix PnL | Delta vs passive |
|---|---:|---:|
| passive-equivalence control | 171650 | 0 |
| adverse-forecast capacity-blocked one-lot reduction | 169682 | -1968 |
| capacity-blocked one-lot reduction without alpha gate | 167343 | -4307 |
| rare-tail one-lot IOC, prediction>spread+0.25 | 171547 | -103 |

Every penalty0. The passive control reproduces the untouched maker's171650 exactly.
The forecast-gated reduction beats the ungated reduction, but neither beats
passive continuation. More counted fills did not mean more profit.
The sparse-tail gate loses even in its past-period cheap test, so do not scale
it into larger taker size or rescue its threshold using later-window outcomes.
These reject the tested gates, not all possible market-taking strategies.

Actual command:

```
uv run --locked python experiments/round_1/dataathletechamp/selective-ioc-v1/run_past.py
```

Artifacts, parameters/hashes and negative results are frozen underselective-ioc-v1
and itsioc1-* run IDs. No IOC is enabled in the current retained449661 file.

Five focused mixed tests passed, including an ACTUAL official-engine three-lot
IOC on a tiny synthetic tape: ACCEPTED / PARTIALLY_FILLED1 / CANCELED2 all at
the scheduled6000us ready time before the next10000us market row. The source
ledger is flat of pending IDs afterward; inventory1 and official PnL-1.
This verifies lifecycle/timing/reservation, not profitable alpha.

Next distinct question is using the richer forecast for **passive pricing**
rather than crossing the spread. Frozen fit window and common risk are unchanged.
