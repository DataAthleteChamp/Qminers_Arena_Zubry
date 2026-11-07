# Supplied Round0 diagnostics and adaptive FIFO package

Inputs explicitly authorised for sharing in this PRIVATE team repository:

- `Zubry_V2_diagnostics.md`.
- `Qminers_Aggressive_Risk_Round0_Research.md`.
- `Qminers_Penalty_Aware_Trading_Research.md`.
- `public_vs_private_best_mid.png`, `public_vs_private_spread.png`, `size_sweep.png`.
- `Zubry_FIFO_Adaptive_Trading_Package/` and its supplied ZIP.

## Read/status boundary

The Round0 documents report an old private run at10798 PnL and public/private
book distributions. That is historical diagnostic evidence, not current Round1
validation. The charts show similar spread distributions but different price
paths; matching marginal distributions is not proof of identical joint dynamics.

The package explicitly labels its sweep scores as an INDEPENDENT C++ replay,
not the official engine. We do not execute that replay or promote its estimated
221070 as an official score. Supplied Python variants remain reference candidates
until preflight, risk tests and actual official-simulator runs establish results.
Original inputs are retained rather than silently correcting their claims.

The aggressive document has a five-number round-weight typo. The actual four
weights in competition.json are **[0.8,1.0,1.0,1.2]**.
Its nominal-latency descriptions also need the actual engine's ready-time clock:
due actions are processed before the next row with internal time advanced to ready.

## Useful new hypothesis: greater quote size without a breach

For filled positionI and all remaining pending/live same-side quantitiesB,S:

```
new_buy_budget  = max(0,100-I-B)
new_sell_budget = max(0,100+I-S)
```

AtI=+100, no pending sells, a new sell of200 ends no lower than-100.
This is not a200-lot inventory allowance. Opposite orders cannot be netted away
to invent capacity, and cancel-pending lots remain reserved.

Nominal sizes160/200 or full adaptive headroom can improve turnover compared
with our95/100 nominal targets. Above200 is inert in a strictly bounded100
position envelope: maximum additional side capacity cannot exceed200.
Do not waste runs treating500/1000 nominal targets as new independent mechanisms.

The package's one-order-per-side V2 variants use this envelope by headroom.
Its add-on version explicitly subtracts all same-side reserve, but has no small
order-count bound and no missing-book cancellation. Review/test those separately.
The fixed-large-size baseline must be included when evaluating adaptive sizing.

## More aggressiveness is not unbounded risk

We will first test actual larger/adaptive quotes, then selective IOC taking or
inventory-reducing IOC with a joint ledger. All stock exposure still passes the
common100 envelope. Average0.5-second forecast below spread does not forbid
profitable tails, but no unconditional taker or instant-cancel assumptions are valid.

Do not enable deliberate >100 inventory simply because another team allegedly
has450k/575k. Compare their same-data/same-engine net PnL including penalties,
and validate their code before drawing conclusions. Other teams' private strategies
are not authorised research; only this team's branches and public sources are used.

After the earlier final checks, this public tape is DEVELOPMENT/selection data.
New chronological windows are robustness checks, not a newly untouched holdout.
No price-path memorisation, private-tape tuning, sandbox bypass or automatic upload.

## Publication verification

All17 archive members match their supplied extracted files byte-for-byte.
ZIP SHA256: `51acd57eded4e46c4f9599be80ac4bf45600ddf463ec7b2831668f86c84e639a`.
The three PnL-named copies match their previously tested source bytes and passed
`tools.preflight.inspect_source` on their exact new paths.

The whole staged whitespace check reports original Markdown hard line breaks
and CRLF in the supplied reference CSVs. Those inputs are preserved intentionally;
we do not rewrite CSV bytes to satisfy a whitespace check.
