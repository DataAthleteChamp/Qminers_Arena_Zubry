# Single-instrument decision menu

This is an anonymised order-event tape, not the named multi-asset IMC world.
No currency, fixed fair value, basket or options universe is established.

| Observation | First investigation | Main trap |
|---|---|---|
| Predictive external flow/depth | Small lagged IOC or adaptive quote overlay | Signal decays inside 5 ms; own trades pollute it |
| Stable reference, executable reversion | Small anchored maker/taker | False peg or midpoint profit that cannot be liquidated |
| Trend lasting beyond costs | Controlled directional inventory | Inventory penalty, carry mistaken for spread capture |
| Queue-dependent spread capture | Persistent limit quotes and selective updates | Lost queue priority and cancel races |
| No demonstrated edge | Safe baseline, more diagnosis | Optimizing the synthetic sample as if it were R1 |

Best bid/ask objects are individual orders, not total price-level volume. Aggregate
properly and distinguish market/user liquidity. The visible window is 20 ticks,
not proof of the full market book or true "wall fair value."

Update position from private per-match fills, not send/accept intentions or the
public trade feed twice. Track in-flight and resting orders; sent cancel != canceled.
Modify can only shrink and preserves place; cancel/reinsert loses queue priority.

Keep callbacks light. CPU duration controls the server time budget; exchange
latency is simulation time. No universal z=2, one-tick edge, full-limit sizing or
asset-name analogy is preapproved. Retain unused research behind disabled flags.
