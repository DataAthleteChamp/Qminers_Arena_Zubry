# Maker/taker quote memo: test mechanism, not its quoted score

Read the complete supplied `Zubry_Maker_Taker_Quote_Research.md`.
Input10750bytes, SHA256`c180a9fb591a42f44b0ca73a82fc646a4181dbb1e5768bf77494fdab8e75222a`.
Its221070/252305 are selected **independent C++ Round0 replay estimates**.
They are not original Round1 official PnL, private results or valid ranking inputs.
Do not replace our343269/344438 files on that evidence alone.

## Mechanisms to incorporate as separately frozen experiments

1. Target200 clipped by filled position plus all possible same-side fills.
2. Reduce inventory price skew independently of size.
3. QI/microprice-sided widening at half-width0.5, not indiscriminate taking.
4. Bounded same-price top-ups to use capacity while preserving existing FIFO.
5. Separate inventory-reducing IOC and profitable-tail IOC, each against the
   exact corresponding passive-only policy and a joint reservation ledger.

For a one-tick spread and skew0, adding any small positive microprice weight
with half-width0.5 widens the adverse side by one tick after floor/ceil rounding.
It is therefore a discontinuous QI-sign execution gate, not merely a small
continuous fair-value change. At half-width0, weights<=1 mostly leave both
touches unchanged until inventory skew moves a rounding boundary.
Keep width, skew and order-retention policy explicit when comparing models.

The memo's unconditional IOC proxies omit delay, executable depth, quantity
and inventory. They reject that proxy, not every profitable IOC tail.
Current weighted-depth liquidation, private fills and delayed-action processing
remain authoritative; no midpoint replacement, instant cancellation or netted risk.

## New registered wave

`experiments/round_1/dataathletechamp/capacity-pricing-v1/plan.json` freezes10
variants before replay: control95; sizes128/160/200; size200 with2/3 bounded
full-headroom FIFO slots; four single-slot V2-style pricing ablations.
The old supplied V2 price logic is recreated from our own reviewed maker,
not by executing the independent replay or blindly importing reference code.

No new learned fit. Development uses the already-consumed first4800s prefix,
then selected exact files get original-full and later time-gated robustness checks.
Penalty, reservation violations, invalid SDK, timeout or ledger mismatch reject release.
No positive matched gain means no improvement claim.
Keep every actual outcome, including failures. Further combinations have budget4.

The first generator hit E501 after replacing a literal byTOPUP_REMAINDER.
No simulator was run onv1. Preserve that failure and plan; the same parameters
are registered as new formatted source bytes incapacity-pricing-v2 before replay.

The document suggests private comparisons through submissions, but public uploads
run the **same public tape**. Private scoring occurs after close; it cannot serve
as an available iterative tuning target. Public optimisation remains public.
