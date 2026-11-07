# Qminers Algo Trade Arena 2026 — Penalty-Aware Trading & Order Management

**Team:** Zubry  
**Purpose:** Repository-ready research and engineering specification for deciding when to **add, keep, shrink, cancel, or cross orders** under Qminers' inventory penalty and 5 ms action latency.  
**Research date:** 7 November 2026  
**Status:** Official exchange rules verified from the organizer's *Algo Trade Arena 2026 — Getting Started* PDF (especially pp. 17–18, 28–37, 41–49) and [public starter README](https://github.com/QminersOrg/qminers-algo-arena). All optimization rules and numerical parameters proposed here are **hypotheses to validate on the current round's recorded public tape**; they are not organizer-supplied optimal strategies.

> **TL;DR:** Use the **penalty-free ±100** inventory band by default; count **live AND pending** same-side orders when deciding whether another bid/ask is safe. Exceed ±100 only if the *incremental expected executable profit* over the best in-band policy exceeds **10,000 × additional expected seconds spent outside the band**, plus execution cost and model-risk reserve. If already outside, the penalty has **zero marginal rate per extra lot** but an enormous **marginal rate per extra second**. Prioritize a fast, sufficient reduction to ±100, not necessarily zero. When managing a stale bid/ask, compare **keep vs reduce in place vs cancel**, accounting for the 5 ms cancel race and the value of FIFO priority.

---

## 1. Official simulator facts — non-negotiable

| Mechanic | Verified rule | Trading consequence |
|---|---|---|
| Asset and tape | One instrument. A fixed recorded stream of other participants' inserts and cancels is replayed. Your orders participate in the exchange but the exogenous tape does not adapt to you. | Do not assume interactive opponent responses. Your orders still change the available book and fills. |
| Matching | Price-time priority (FIFO); execution at the resting order's price. LIMIT residual rests; IOC residual cancels. No fees. | Queue position and crossing the spread matter. |
| Latency | Every send, cancel, or shrink is effective at `t + 5 ms`, **immediately before the first tape event at or after that time**. | A pending cancel does **not** eliminate fill risk. Actual activation may be later than exactly 5 ms. |
| Inventory penalty | For actual inventory `I`, when `abs(I) > 100`: **10,000 P&L units per simulated second**, based on time spent outside the band. | It is **a flat threshold-rate penalty**, **not 10,000 per extra lot per second**. |
| Order-acceptance limit | At acceptance, a same-side exposure test `abs(I + s*(R + q)) > 1000` rejects the order; `s=+1` buy, `-1` sell, `R` is same-side resting quantity. | ±1,000 is an **acceptance limit**, not a free-to-use inventory limit. Maintain a conservative local pending-order ledger too. |
| Score | `PnL = cash + liquidation_markout(I) − breach_penalty`. | Final inventory is marked against **resting market liquidity**, not simply `I * mid`. |
| Book information | Orders visible 20 ticks deep per side by default; `price`, `quantity`, `owner`, plus private updates for own fills/order state. | Estimate queue ahead; account for depth and stale/silent orders. |
| Actions | `send_order`, `cancel_order`, `modify_order` (shrink only, preserving queue place), `now_us()`. | When reducing size, **prefer shrink** over cancel/repost if the remaining quote has value. |
| Round scoring | `0.8*z1 + 1.0*z2 + 1.0*z3 + 1.2*z4`; each `z` standardizes private-test PnL among positive-PnL teams and uses the score associated with zero PnL for nonpositive results. | Focus on robust **net** PnL in each round; do not maximize unpenalized PnL. |

**References:** [Organizer starter repository / README](https://github.com/QminersOrg/qminers-algo-arena); workshop PDF p. 29 (latency), p. 30 (cancel race), p. 33 (order states), p. 34 (actions), p. 35 (two inventory walls), p. 36 (liquidation score). Tournament scoring and repository rules come from the team's logged-in event rules supplied to the team; these are not fully documented in the public README.

### Exact penalty formula

Let `I(t)` be actual signed filled inventory, not the sum of intended orders. Then

$$
\boxed{C_{penalty}[t_0,t_1] = 10{,}000\int_{t_0}^{t_1}{\bf1}\{|I(t)|>100\}\,dt.}
$$

In microsecond timestamps (`self.now_us()`): **0.01 PnL units per microsecond outside ±100**.

- `I = 100` or `I = -100`: **zero** penalty.
- `I = 101`, `I = 500`, or `I = -999`: **same penalty per second** while continuously out of band.
- At `I = 120`, selling **20 filled lots** to reach 100 stops penalty. Merely submitting the sell or cancelling a bid does not stop it.
- A market fill can change inventory before a pending cancellation takes effect.
- Do not hardcode “a breach always costs at least 50.” A position may be reduced by already-live passive orders or other fills sooner. But if the bot observes a breach and only then submits an IOC, that action needs **at least 5 ms before eligibility**, and possibly longer until the next tape event.

| Time actually outside band | Penalty |
|---:|---:|
| 1 ms | 10 |
| 5 ms | 50 |
| 10 ms | 100 |
| 20 ms | 200 |
| 50 ms | 500 |
| 100 ms | 1,000 |
| 1 s | 10,000 |
| 5 s | 50,000 |

**Important:** There is no mechanism in the published rules to receive a reward *for incurring* a penalty. Intentional breaches are worthwhile only when the **additional net trading profit** exceeds the induced penalty and risks.

---

## 2. Formulate the actual optimization problem

The decision is **not** “is the next trade profitable?”; it is “is this action better than the best available alternative, including not placing the order, shrinking an existing order, or reducing inventory?”

For action `a` (new LIMIT, new IOC, keep, shrink, cancel), compare against baseline policy `a0`:

$$
\boxed{\Delta EV(a,a_0)=\mathbb E[\Delta G]-10{,}000\cdot\mathbb E[\Delta T_{out}]-\lambda\,Risk(a,a_0).}
$$

Where:

- `ΔG`: additional **cash plus liquidation-value change** through the chosen horizon, **already including** spread, adverse selection, price impact, partial fills and slippage. Do **not** deduct spread a second time if it is already in `ΔG`.
- `ΔT_out`: additional *total* time outside `[-100,100]` relative to the alternative, including future re-breaches, **not** merely the nominal order latency.
- `Risk`: a separate robustness/uncertainty reserve (for example a downside quantile, expected shortfall, or calibrated model-error buffer). `λ` is a chosen risk coefficient, **not an official parameter**.

Decide `a` over `a0` only if `ΔEV > 0` **and** the action is allowed by the exchange/competition rules.

A more exact state-value formulation is

$$
V(s,t)=\max_a\mathbb E\left[\Delta cash +\Delta markout -10{,}000\Delta T_{out}+V(s',t')\mid s,a\right],
$$

where state `s` includes inventory, public book, outstanding and in-flight orders, queue positions, recent order flow, time remaining, and the prediction model. Full HJB/MDP optimization is likely too expensive to engineer during a round; use short-horizon policy evaluation or small scenario rollouts first.

### When a breach can make sense

If the expected *incremental net trading advantage before penalty* is `A` PnL units and the position remains out of band an **additional** `τ` seconds, then

$$\Delta EV \approx A-10{,}000\,\tau-\text{risk reserve}. $$

The naive break-even duration is `τ_max = A / 10000` seconds (before reserve). For example, 600 units of incremental net advantage can pay for at most **60 ms of incremental breach time**. If worst-case/upper-quantile recovery takes 200 ms, do not approve simply because the mean recovery time is 20 ms.

### The unusual economics of the flat penalty

If a candidate trade pushes inventory from safe to over-limit, the **first excess lot** can be unusually expensive because it starts the whole 10,000/s clock. Further lots are *not charged per lot*, but can deepen the position, worsen slippage, decrease fill probability and extend the time needed to return below 101. So:

- **At the boundary:** require a substantial positive edge to cross it.
- **Already outside the boundary:** adding one more lot has no *instantaneous* incremental penalty if it doesn't change current out-of-band status; it can still greatly increase **future** breach duration and liquidation cost.
- **Returning to the boundary:** the **last filled lot(s) that get inventory back to ±100** have extraordinary value because they switch off the continuous penalty.
- This creates a **non-convex, threshold-based inventory control problem**. Ordinary quadratic inventory-penalty formulas (e.g., Avellaneda–Stoikov) do not describe this tournament exactly.

---

## 3. Position budget: distinguish actual fills, pending and live orders

### 3.1 Define the state explicitly

For every own order store: `order_id`, `side`, `limit_price`, `remaining_quantity`, `status`, `sent_at_us`, `effective_not_before_us`, `cancel_pending`, `modify_pending`, and (when observable) `quantity_ahead` and queue position.

Let:

- `I`: **filled actual** inventory.
- `B_live`, `S_live`: residual accepted buy and sell quantities currently resting.
- `B_flight`, `S_flight`: quantities of buy/sell **new orders sent but not yet definitively accepted/rejected or completed**. Include IOC in flight.
- Pending cancels and pending shrinks **still count at their old full quantity** until confirmed. Avoid counting one order twice when it moves from flight to live.

A conservative one-sided exposure envelope is

$$
I_{max}=I+B_{live}+B_{flight}, \qquad I_{min}=I-S_{live}-S_{flight}.
$$

Assume the opposite-side orders do **not** rescue you. This is conservative but avoids relying on uncertain fills to cancel the risk of other fills.

A simple no-breach new-order budget:

$$
q^{safe}_{buy}=\max(0,100-I_{max}),\qquad
q^{safe}_{sell}=\max(0,100+I_{min}).
$$

**Examples:**

| Current inventory | Existing buy exposure | Existing sell exposure | Possible interval | Maximum *additional* no-breach BUY / SELL |
|---:|---:|---:|---:|---:|
| +85 | 10 | 25 | [60,95] | 5 / 160 |
| +95 | 20 | 0 | [95,115] | 0 / 195 (already exposed to a possible long breach) |
| −90 | 0 | 15 | [−105,−90] | 190 / 0 (already exposed to a possible short breach) |
| +120 | 0 | 40 | [80,120] | 0 / 180 (already penalized until actual fills bring `I` to 100) |

All budgets are **conservative scenario bounds**, not official acceptance calculations. The official acceptance rule at activation is the separate **±1,000 same-side** check. Check both.

### 3.2 Which bid/ask is dangerous?

- **Long or near +100:** a filled **BUY/bid** increases inventory, so it can create or extend a breach. A filled **SELL/ask** reduces inventory (until you approach the other side).
- **Short or near −100:** a filled **SELL/ask** increases short exposure. A filled **BUY/bid** reduces it.
- If already **long +140**, preserving an attractive **sell** quote may be sensible, while a stale **buy** quote should face a very high acceptance threshold.
- If already **short −140**, reverse the logic.
- **Always** consider both sides simultaneously: an outstanding order on the “good” side can overshoot and create an opposite-sign breach if it is too large.

### 3.3 Concrete order-management policy

1. Update actual `I` immediately on each private fill. Track partial fills individually.
2. Recompute `I_min`/`I_max` after each order update and important market change.
3. For a **new order**, first compute safe-size budget under all still-live/in-flight orders; default to `min(desired, safe_budget)`.
4. If the new order would cross ±100 in any plausible fill sequence, route it through the **explicit over-limit EV evaluator** in §5. Never breach as an accidental side effect of a naive size calculation.
5. If existing orders already threaten a breach, **shrink or cancel the risk-increasing orders** based on §6. Remember the requested action remains in flight for 5 ms.
6. If actual inventory is outside ±100, enter **RECOVER** mode (§7); do not confuse projected risk with actual charged time.

---

## 4. Compute fair value and executable edge quickly

### 4.1 A minimal O(depth) signal set

From the visible book, exclude our own quantities when estimating external supply/demand:

- Best market bid `b`, best market ask `a`, spread `s=a-b`, mid `m=(a+b)/2`.
- External best-level volumes `Vb`, `Va` and 3–10 level depth sums.
- Top-of-book imbalance `OBI=(Vb−Va)/(Vb+Va)` (guard against zero denominator).
- Weighted top-of-book microprice candidate: `(a*Vb + b*Va)/(Vb+Va)`.
- Signed market trade flow: `+size` for a trade taking the ask; `−size` for one hitting the bid (the workshop uses `trade.book_side == 'ask'/'bid'`).
- Exponentially smoothed flow, mid-price changes, recent realized volatility, spread regime, event count and local depth.
- Queue ahead of **each own resting order** at its price, from the visible individual orders (if within displayed depth).

Fit a lightweight short-horizon alpha model:

$$\hat F_{t,h}=m_t+\beta_1 OBI_t+\beta_2 OFI_t+\beta_3 Momentum_t+\beta_4(Microprice_t-m_t).$$

`β` and horizon `h` must be estimated on a **chronological training segment** and assessed on later held-out segments. Do not assume real-stock coefficients transfer to the anonymous Qminers instrument. For latency-sensitive IOC decisions, test `h = 10,20,50,100,250,500 ms` and label the **post-activation** price/markout, not a price unavailable when the order arrives.

### 4.2 IOC expected value

For a BUY IOC of `q` with limit `p_lim`, approximate

$$
EV_{IOC,BUY}=\mathbb E\left[\sum_{j \in fills}q_j\,(F_{after,j}-p_j)\right]
-\Delta E[Penalty]-RiskBuffer.
$$

For SELL change the sign: `sum(q_j*(p_j−F_after,j))`. `p_j` are **actual resting-maker execution prices** after the 5 ms delay. This captures different prices across multiple book levels, partial fills, and no-fill outcomes. `F_after` should represent a realistic future **executable/terminal value**, not a clairvoyant price.

For **reducing a penalized position**, add the expected penalty *saved* from getting back to ±100 faster. This can make a spread-crossing IOC rational **even when its purely price-based edge is negative**.

### 4.3 Resting LIMIT order expected value

For BUY LIMIT `q` at price `p`:

$$
EV_{LIMIT,BUY}\approx E\left[Q_{fill}(F_{after\ fill}-p)\right]
-\Delta E[Penalty]-RiskBuffer+QueueOptionValue.
$$

For SELL use `E[Q_fill*(p−F_after fill)]`. Model the **conditional** post-fill markout: the orders that fill are not a random subset of all market observations. A resting bid often fills *because* informed sellers anticipate downward movement; spread capture before adverse selection is misleading.

A queued order's value depends on its price, size, position, fill probability, adverse-selection risk, and option value from keeping an early position for favorable future states [Moallemi–Yuan 2017; Donnelly–Gan 2018].

---

## 5. Exact *decision framework* for allowing a deliberate inventory breach

### 5.1 Compare policy paths, not quantities in isolation

Suppose the safe alternative trades at most 100 lots, and candidate trade `A` goes beyond it. Simulate or estimate both:

1. `Policy_safe`: stay inside band, trade with remaining legal headroom, keep or cancel existing orders optimally.
2. `Policy_breach`: execute candidate quantity, then exit according to a credible liquidation policy (IOC and/or already-live opposing orders).

Compare

$$
\Delta EV_{breach}=E[PnL_{candidate}-PnL_{safe}] - RiskBuffer.
$$

This comparison **must include both policies' penalties** and terminal liquidation values. An `I=120` state is already charged; adding an order may add only the extra time/cost it causes, not an entirely new penalty for the entire original breach.

### 5.2 Quick conservative admission test

For a candidate that **starts** an otherwise absent breach, let:

- `A`: estimated incremental P&L if no penalty, net of spread/slippage/markout impact (PnL units);
- `τ_p90`: 90th-percentile additional time outside band under planned recovery;
- `U`: uncertainty reserve (PnL units, fitted to prediction errors).

A cautious gate:

$$\boxed{ A > 10{,}000\,\tau_{p90} + U. }$$

This is **a chosen conservative heuristic**, not a theorem. A better optimizer uses the entire distribution or expected shortfall. The p90 choice and buffer size require calibration.

**Sanity-check examples:**

| Incremental advantage `A` | Extra time out of band | Penalty | Decision before uncertainty |
|---:|---:|---:|---|
| 300 | 10 ms | 100 | Potentially profitable (+200) |
| 300 | 40 ms | 400 | Unprofitable (−100) |
| 1,000 | 50 ms | 500 | Potentially profitable (+500) |
| 1,000 | 200 ms | 2,000 | Unprofitable (−1,000) |

### 5.3 The discontinuity at +100 and −100

Example: `I=99`, a buy of 2 fully fills and position reaches `+101`. If it stays there for 20 ms, the *total* charge is **200 units**. If its incremental expected gross return is 3 ticks on each of 2 lots = 6, it is a bad trade even before execution costs. At `I=101` already breached, an additional +100 fill might have almost no **immediate** change in penalty rate, but could take longer to unwind. Comparing against the correct existing-breach baseline is essential.

### 5.4 When should an order of 300–900 lots be considered?

Only when **all** the following pass:

- A credible, market-data-based price signal produces enough **incremental expected net edge**.
- The market has enough **post-latency** depth to enter and **exit** without unacceptable sweep cost.
- The model predicts return to ±100 quickly, with an acceptable **tail** of unfilled/partial exits.
- Existing pending orders cannot accidentally extend or reverse the breach.
- The official **±1,000 acceptance** rule and local conservative exposure guard pass.
- Out-of-sample runs outperform the smaller-position baseline **after** recorded penalties.

Do not use very large size merely because penalty is flat; the order book and exit time generally get worse as size rises.

---

## 6. Keep, shrink or cancel? Order-level decision rules

**Key official fact:** `modify_order(order_id, new_quantity)` only shrinks; it **keeps queue priority**. Cancelling and reposting forfeits existing priority. Both changes become effective after 5 ms. A cancel request can fail if the order fills during the delay.

### 6.1 Rank orders by danger and expected value

For each live/in-flight order `o`, estimate:

1. **Direction of inventory change** if filled: `+q` buy, `−q` sell.
2. **Projected band breach** if it and other same-side orders fill.
3. Probability of filling **before a cancel/shrink takes effect** (unavoidable race).
4. Expected fill edge **conditioned on being filled**, including post-fill adverse selection.
5. Expected incremental *future* out-of-band time caused by that fill.
6. Current queue position and value of retaining it.
7. Whether a **partial shrink** can preserve the profitable portion.

Define (heuristic):

$$
KeepValue(o) \approx E[TradingEdge_o]+QueueOption_o
-10{,}000 E[\Delta T_{out,o}]-Risk_o.
$$

Cancel when the **expected value of cancel now (effective after delay)** exceeds keep; shrink when a subset of quantity remains valuable. Never assume cancelling at current timestamp removes pre-activation risk.

### 6.2 Suggested action matrix

| Actual or projected state | New BUY bid | New SELL ask | Existing BUY bid | Existing SELL ask |
|---|---|---|---|---|
| Near flat, both-sided headroom | Quote if positive fill-edge | Quote if positive fill-edge | Keep if positive EV | Keep if positive EV |
| Long near +100 | Restrict to remaining long headroom | Often useful; still assess overshoot | **Shrink/cancel** if breach risk exceeds queue value | Usually **keep**, if economically sensible |
| Long > +100 | Normally disable new buys unless explicit breach-edge gate | Prefer sufficient sells; possibly IOC | **Cancel/shrink promptly**, acknowledging 5 ms race | Keep/reprice/reduce intelligently; use IOC if waiting is costly |
| Short near −100 | Often useful, within opposite overshoot guard | Restrict to remaining short headroom | Usually keep if useful | **Shrink/cancel** if breach risk |
| Short < −100 | Prefer sufficient buys; possibly IOC | Normally disable new sells unless explicit breach-edge gate | Keep/reprice/reduce intelligently; use IOC if waiting costly | **Cancel/shrink promptly**, acknowledging 5 ms race |

**Do not blindly cancel every order on the side that increases risk:** a near-front quote can still have strong positive expected fill edge. But once the risk-creating fill would incur penalty, that edge must exceed the risk and *time penalty* it creates.

### 6.3 A concrete shrinking example

Current `I=+85`; open BUY #A is 30 lots at the best bid, BUY #B is 20 lots one tick lower. Total potential long exposure is `+135`. Without deliberate-breach approval, you have only **15 lots** of unfilled buy capacity.

- If #A has much better queue position / expected maker edge, request **shrink #A from 30 to 15** and **cancel #B**.
- Or keep #A 10 and #B 5, depending on measured order value.
- **Until acknowledgements arrive**, assume the old total of 50 is still at risk. Avoid immediately posting another 15-lot buy as though the shrink had already happened.
- A risk event can fill #A or #B during 5 ms, so a late shrink may be unsuccessful or insufficient.

### 6.4 Cancel *because of adverse selection*, not only limits

Cancel a resting **bid** when a sell-pressure signal predicts a down-move exceeding the expected bid spread advantage, adjusted for queue priority and the 5 ms race. Cancel an **ask** under strong upward pressure. If queue position is excellent, estimate its **future option value** before surrendering it. An old first-in-line quote can be economically valuable even when immediate execution is not attractive [Moallemi–Yuan; Donnelly–Gan].

### 6.5 Pending cancels: avoid the common accounting bug

**Wrong:** send cancel for 40 BUY lots, immediately subtract 40 from potential inventory.  
**Right:** keep all 40 in the risk envelope until a `CANCELED` or `FILLED`/`PARTIALLY_FILLED` state confirms the actual remaining exposure. Recompute position from fill messages, not intentions.

---

## 7. When already in a breach: sell/buy enough to stop the clock

### 7.1 The correct recovery target

- If `I > 100`, the minimum required sale to return to the band is `x = I−100` lots.
- If `I < −100`, the minimum required purchase is `x = −100−I` lots.
- Flattening the entire position to zero can **waste spread** and may increase total PnL costs. First determine the value of returning to the boundary; then separately consider reducing residual inventory further.

### 7.2 IOC vs passive exit: a short, powerful inequality

Compare an **aggressive exit now** against waiting `Δt` *additional* seconds for a better passive exit, with all other factors equal. Let `D` = extra passive execution proceeds (after fill probability and quantity) if waiting instead of exiting. Waiting is worthwhile only if approximately

$$\boxed{D > 10{,}000\,\Delta t + \text{additional price/shortfall risk}.}$$

If you are long +300 and need to sell 200 to reach +100, a passive price improvement averaging **one tick per lot** is only `D=200`. This advantage is entirely erased after **20 ms of additional penalized waiting** (before risk). If only 20 lots are needed, the same one-tick improvement is worth **2 ms** of waiting.

This is a **comparison between feasible policies after accounting for their respective order latencies**: an IOC also has 5 ms delay and may not fill. Do not assume immediate liquidity at the displayed snapshot.

### 7.3 Recovery policy

1. **Disable/reduce risk-increasing orders** (BUY if long, SELL if short), but keep their residual exposure in the ledger until confirmed.
2. **Compute exactly how many filled lots end the penalty**, based on actual inventory.
3. Estimate the shortest plausible reduction using existing exit-side resting orders, with queue position and projected fills.
4. Price IOC exits through enough **available market depth** to reduce to the target, allowing for depth changes during 5 ms; cap maximum adverse sweep price.
5. Compare expected penalty saved by IOC versus expected spread/sweep/impact cost and optionality of passive fills. If net savings positive, use the IOC. Partial fills still help even if they don't finish the recovery.
6. Monitor every private fill. Once `abs(I) <= 100`, exit RECOVER mode, but maintain a buffer against remaining same-side orders.

**Special case:** If an existing opposite-side quote is already near the front and likely to fill within a few ms, it may be better to preserve it than to send an IOC; test that with the real tape and the 5 ms action model.

---

## 8. Implementation: fast, explicit risk-decision helpers

The following are **drop-in pure-Python mathematical helpers**, not a complete `BaseStrategy`. They use no blocked modules or reflection. The state ledger that feeds them must correctly interpret Qminers callbacks and avoid double-counting orders.

```python
# Penalty math in simulator PnL units. Timestamp unit: microseconds.
SAFE_POS = 100
HARD_ACCEPTANCE_POS = 1000
PENALTY_PER_SECOND = 10_000.0
PENALTY_PER_US = 0.01
ORDER_LATENCY_US = 5_000


def breach_penalty_for_interval(inventory: int, interval_us: int) -> float:
    """Exact cost for a CONSTANT position over a known interval."""
    if abs(inventory) <= SAFE_POS or interval_us <= 0:
        return 0.0
    return PENALTY_PER_US * interval_us


def exposure_envelope(
    inventory: int,
    live_buy: int,
    flight_buy: int,
    live_sell: int,
    flight_sell: int,
) -> tuple[int, int]:
    """Conservative upper/lower fill exposures (not an exchange guarantee)."""
    highest = inventory + live_buy + flight_buy
    lowest = inventory - live_sell - flight_sell
    return lowest, highest


def safe_new_order_budgets(
    inventory: int,
    live_buy: int,
    flight_buy: int,
    live_sell: int,
    flight_sell: int,
) -> tuple[int, int]:
    low, high = exposure_envelope(
        inventory, live_buy, flight_buy, live_sell, flight_sell
    )
    extra_buy = max(0, SAFE_POS - high)
    extra_sell = max(0, SAFE_POS + low)
    return extra_buy, extra_sell


def hard_limit_allows(
    inventory_at_acceptance: int,
    same_side_resting_qty: int,
    candidate_qty: int,
    side_sign: int,
) -> bool:
    """README rule, evaluated using the ACTUAL state at order acceptance."""
    projected = inventory_at_acceptance + side_sign * (
        same_side_resting_qty + candidate_qty
    )
    return abs(projected) <= HARD_ACCEPTANCE_POS


def incremental_action_value(
    expected_incremental_gross_pnl: float,
    incremental_expected_breach_us: float,
    risk_reserve: float,
) -> float:
    """Only use with gross PnL already net of spread/impact/markout."""
    return (
        expected_incremental_gross_pnl
        - PENALTY_PER_US * incremental_expected_breach_us
        - risk_reserve
    )


def risk_adjusted_breach_gate(
    incremental_gross_pnl: float,
    incremental_p90_breach_us: float,
    model_error_reserve: float,
) -> bool:
    """Conservative admission rule; tune with out-of-sample backtests."""
    return incremental_action_value(
        incremental_gross_pnl,
        incremental_p90_breach_us,
        model_error_reserve,
    ) > 0.0


def minimum_recovery_lots(inventory: int) -> tuple[int, int]:
    """(side_sign, quantity); +1 means BUY, -1 means SELL."""
    if inventory > SAFE_POS:
        return -1, inventory - SAFE_POS
    if inventory < -SAFE_POS:
        return 1, -SAFE_POS - inventory
    return 0, 0
```

### Example outputs you can unit-test

```python
assert breach_penalty_for_interval(100, 500_000) == 0
assert breach_penalty_for_interval(101, 20_000) == 200
assert breach_penalty_for_interval(900, 20_000) == 200
assert breach_penalty_for_interval(-101, 5_000) == 50
assert safe_new_order_budgets(85, 10, 0, 25, 0) == (5, 160)
assert safe_new_order_budgets(95, 20, 0, 0, 0) == (0, 195)
assert minimum_recovery_lots(135) == (-1, 35)
assert minimum_recovery_lots(-125) == (1, 25)
assert risk_adjusted_breach_gate(450, 20_000, 100) is True  # +150
assert risk_adjusted_breach_gate(450, 50_000, 100) is False # -150
```

**Implementation caution:** `hard_limit_allows()` uses `inventory_at_acceptance`, not current time's position. Future inventory, resting exposure and tape state may differ during the 5 ms delay. Therefore use it for preflight plus the simulator's actual `REJECTED` message as the authoritative verdict. Do **not** treat planned sells as netting out planned buys when calculating worst-case exposure.

### A cheap per-callback decision tree

```text
on_private_order_update(event):
    apply accepted / rejected / partial-fill / fill / modified / canceled
    update ACTUAL inventory only from fills
    update in-flight / remaining order quantities; avoid double counting
    recompute conservative exposure envelope

on_order_book_change(snapshot, trades):
    update external bid/ask, microprice, flow, depth, queue estimates
    read current time in microseconds

    if abs(actual_inventory) > 100:
        RECOVER:
          cancel/shrink harmful same-side orders (if worthwhile)
          estimate exit-side passive fill time and executable IOC VWAP
          submit inventory-reducing IOC if penalty saved > execution loss
          do not leave recovery mode until real fills restore safe inventory
        return

    for existing live quote:
        compute E[KEEP], E[SHRINK], E[CANCEL] with 5-ms race
        choose the highest-value action; throttle repeated amendments

    compute conservative safe BUY/SELL budgets including ALL in-flight orders
    consider new quotes / IOC up to safe budgets first
    for any candidate that can breach ±100:
        compare with safe alternative using incremental PnL and breach time
        require positive risk-adjusted improvement, credible fast exit,
        and headroom under ±1000 acceptance rule

    submit; record the order immediately as IN_FLIGHT, not FILLED
```

For runtime, calculate simple O(depth) features on frequent callbacks; update expensive model estimates every configurable number of microseconds or on meaningful price/flow changes. Submission sandbox: one Python file ≤1 MiB, 1 CPU, 2 GB memory, 15-minute time budget, restricted imports. **Research notebooks and analysis scripts are separate**; do not import file access, `os`, `sys`, introspection, or other banned features into the strategy file. See official README.

---

## 9. Better modeling: fill probabilities and penalty *occupancy* risk

### 9.1 Position-process models

The exact penalty is an **occupation-time** functional. Instead of predicting only end inventory, predict the probability of being outside at each future time:

$$
E[C_{penalty}] = 10{,}000\int_0^H P(|I_{t+u}|>100\mid State_t, Policy)\,du.
$$

This is more informative than a single expected inventory. Because the penalty turns on at a threshold, `E[penalty(I)]` is **not** the penalty of `E[I]`.

**Example:** 50% probability of +110 and 50% of +90 for 100 ms means expected penalty **500**, even though expected inventory is **100** (and penalty evaluated at mean inventory would be incorrectly zero).

### 9.2 Practical scenario-rollout approximation

For each candidate order, generate a small number of possible sequences over the next 20–500 ms:

- delayed acceptance at first eligible tape event;
- market changes and possible own fills;
- conservative IOC partial/no-fill cases;
- passive queue execution/no-execution;
- order cancellation effective after delay;
- recovery orders and final liquidation.

Compute PnL and **cumulative simulated time outside** for each sequence. With historical tape the exact organizer simulator is the reference; a fast approximate rollout should be used for pruning, not replacing official backtests. Use quantiles or worst-reasonable scenarios to guard against catastrophic slow exits.

### 9.3 Shadow cost of a resting quote near the boundary

An order at the bid may have positive expected raw spread profit but negative total value if it can take you from +100 to +101. Approximate its penalty contribution as:

$$
E[PenaltyIncrement_o]\approx P(fill_o\text{ causes breach})\times 10{,}000\times E[T_{out}\mid fill_o, breach],
$$

adjusted for other already-present breaches and alternative policies. It is important to condition on a *fill* and on the entire order set. The approximation double-counts penalties if applied to many orders independently; the **joint scenario model** is the preferred final implementation.

---

## 10. Backtests and experiments — run these before trusting the policy

**Do not train on the synthetic `sample.csv`.** The starter README states that it has artificial trends, while scored rounds use recorded market data. Use sample only to validate API behavior and accounting.

### Experimental ladder

| ID | Hypothesis | Experiment | Pass criterion |
|---|---|---|---|
| E00 | Simulator integration is correct | Existing starter strategy, verify dashboard PnL | Runs, identical scoring locally/server on public data |
| E01 | Risk ledger is correct | Synthetic unit tests for fills, rejects, delayed cancels | No pending-state double counting; penalty predictions consistent |
| E02 | Strict control has positive PnL | `I` targeted in ±60, ±80, ±100 | Best positive holdout net PnL with acceptable downside |
| E03 | Better order preservation | Cancel/repost vs shrink-to-size vs keep | Improved PnL **and** queue/fill diagnostics |
| E04 | IOC recovery beats passive waiting | Exit immediately vs wait 5/10/20/50 ms after breach | Higher penalty-adjusted holdout PnL |
| E05 | Deliberate breaches add value | Enable `±120/±150/±250/±500` max actual inventory | Positive **incremental** PnL vs safe baseline on multiple time blocks |
| E06 | Large burst amortizes flat penalty | Sweep size and predicted exit-time limits | Improvement remains after slippage and recovery-time tails |
| E07 | Short-term alpha is real | OFI/microprice/trades at latency-adjusted horizons | Chronological holdout executable edge, not just directional accuracy |
| E08 | Keeping queue position pays | Model queue-ahead at each order | Better fill-conditioned PnL and lower adverse-selection loss |
| E09 | Endgame policy helps | Force `abs(I) <= 100`, possibly near 0, before close | Better liquidation markout net of spread costs |
| E10 | Strategy generalizes across rounds | Replay each round under shared flags/recalibrated parameters | Robustness under different market regimes |

### Suggested log fields per experiment

`round`, `strategy_hash`, `parameters`, `pnl`, `breach_penalty`, `gross_pre_penalty_pnl`, `cash`, `markout`, `fills`, `traded_volume`, `max_abs_inventory`, `time_outside_safe_us`, `longest_breach_us`, `recovery_time_p50/p90/p99`, `IOC_miss_rate`, `queue_ahead`, `maker_fill_markout_10/50/100ms`, `cancel_race_fills`, `rejected_orders`, `PnL_by_chronological_segment`.

Not all are provided automatically. Official `result.json` documents `pnl`, `cash`, `inventory`, `mark_price`, `breach_penalty`, `traded_volume`, `fills`, `pnl_se` and time-weighted `abs(inventory)` quantiles; compute other metrics in your own **offline research code** from full logs, not in the sandbox submission.

### Official backtest commands

```bash
uv run exchange-simulator \
  --strategy strategies/your_strategy.py \
  --backtest data/round_public.csv \
  --log-dir logs/round1_candidate_a \
  --no-logs

# When a surprising cliff / fill / penalty requires inspection:
uv run exchange-simulator \
  --strategy strategies/your_strategy.py \
  --backtest data/round_public.csv \
  --log-dir logs/round1_debug
uv run backtest-explorer --log-dir logs/round1_debug
```

Replace the placeholder filename with the actual downloaded round CSV. **Never assume current market data look like the sample.** Split the real tape chronologically for **research diagnostics**; benchmark entire original tape for the official published score. Avoid training predictors on future rows, using tape features that would not be visible until after order submission, or optimizing dozens of knobs on one result.

### Lightweight chronological validation

- Early 50–60%: estimate fair-value and fill-duration models.
- Next 20–25%: select policy parameters (within a limited grid).
- Final 20–25%: evaluate untouched strategy; look at **net PnL and penalty** separately.
- Repeat with rolling windows and parameter perturbations. The private test is from a different tape; no guarantee of distribution match.

Use `--no-logs` for the majority of trials; the official README says full event logs can be very large. Only run full logs on selected failure and success cases.

### Critical adversarial tests

1. `I=100`, a BUY fill of 1 switches the penalty on; `I=99`, BUY 1 does not.
2. Cancel BUY at `t`, fill at `t+2 ms`, cancel rejected at first event ≥`t+5 ms`: inventory **must include the fill**.
3. Modify 50 BUY down to 10, but a 20-lot fill occurs before effective shrink: do not pretend the 20 could not fill.
4. Simultaneous pending BUY and SELL orders: do not net them to zero exposure.
5. Partial liquidation from `I=150` to `I=110` still penalized; the next 10 filled lots stop the clock.
6. Exit IOC misses because quote moved during 5 ms: penalty continues; retry logic must throttle and reassess current depth.
7. Risk check rejects an otherwise attractive order at the hard exposure wall: inventory and ledger remain unchanged until acceptance/fills.
8. Final inventory +100 marked at shallow bids can be much worse than +100 × mid; terminal policy must compare liquidation depth.
9. If **actual** inventory briefly reaches +101 and returns to +100 between market timestamps, use the simulator's recorded time integration rather than approximating all fills as equally spaced.
10. When no public market bid/ask is present, do not compute a fabricated executable price; respect the simulator's documented markout fallback **for scoring only**.

---

## 11. Round-by-round deployment and research workflow

The exact exchange mechanics above are stable rules; **market dynamics and special challenges can change each round**, so parameters need re-estimation.

- **Round 1 (0.8 weight):** get a strict ±100/±80 strategy working, then test a short breach mode; log failed experiments.
- **Round 2 (1.0):** identify differences in fill rates, spread, volatility and adverse selection; retune without abandoning stable code.
- **Round 3 (1.0):** assess new market mechanism and whether breach duration can still be controlled. Disable high-inventory mode if exit uncertainty rises.
- **Round 4 (1.2):** deploy the highest-quality validated policy, with a clearly chosen risk level. Later-round weight increases score sensitivity but **does not make negative-net-PnL breaches profitable**.

### Mandatory research-repo discipline

- Private template repository; grant `antoninkriz` Read access.
- **Commit at least every 30 minutes**; include unsuccessful experiments and observations.
- No squash, rebase, force-push; preserve genuine chronological history.
- Preserve experiment variants behind flags instead of destroying old code.
- Log *why* decisions were made, not just the final winning parameter.

Example entry:

```markdown
### 2026-11-07 15:30 — E05: penalty burst after positive OFI
- Hypothesis: 180-lot IOC BUY on strong OFI pays for <30 ms breach.
- Code: `strategies/arena.py`, `ENABLE_BREACH=True`, `MAX_INV=180`.
- Dataset: Round 1 public, train/validation time ranges recorded.
- Baseline: gross / penalty / net = ... / ... / ...
- Candidate: gross / penalty / net = ... / ... / ...
- Recovery p90 = ... ms; 5-ms IOC miss rate = ...
- Conclusion: ACCEPT / REJECT; why, and next question.
```

The numeric placeholders above are intentional; **do not fabricate results before backtesting**.

---

## 12. Relevant papers — what transfers, what does not

These papers provide the **market-microstructure theory** behind our implementation. **None specifies Qminers' unusual 10,000/s flat threshold penalty**; that formula comes from the organizer's rules. In particular, academic risk-aversion parameters and optimal spreads are not Qminers-specific defaults.

| Source | Verified contribution | Practical use for Qminers | Limitations |
|---|---|---|---|
| **Avellaneda & Stoikov (2008)**, [*High-frequency trading in a limit order book*](https://math.nyu.edu/inmemoriam/avellaneda/HighFrequencyTrading.pdf), [DOI](https://doi.org/10.1080/14697680701381228) | Reservation-price / optimal-quote approach under inventory risk | Skew quotes away from accumulating unwanted inventory; starting baseline | Continuous price/arrival assumptions; does not incorporate Qminers' flat breach rate, deterministic 5 ms, or exact FIFO |
| **Guéant, Lehalle & Fernandez-Tapia (2013)**, [*Dealing with the Inventory Risk*](https://arxiv.org/abs/1105.3115), [DOI](https://doi.org/10.1007/s11579-012-0087-0) | Stochastic control of bid/ask quotes with inventory constraints | Value function and inventory-dependent quoting/position control | Requires new boundary-cost functional and fill model for this competition |
| **Gao & Wang (2020)**, [*Optimal market making in the presence of latency*](https://doi.org/10.1080/14697688.2020.1741670) | Market-making order value under latency via MDP; delay can make quotes unprofitable | Explicit value of delayed quote and stale-order/cancel risk | Paper's market model is not the Qminers replay engine |
| **Moallemi & Yuan (2017)**, [*A Model for Queue Position Valuation in a Limit Order Book*](https://moallemi.com/ciamac/papers/queue-value-2016.pdf), [Columbia](https://business.columbia.edu/faculty/research/model-queue-position-valuation-limit-order-book) | Static adverse-selection and dynamic option value of FIFO queue positions | Keep vs cancel vs replace, size management and queue-ahead | Calibration from the tournament tape is necessary |
| **Donnelly & Gan (2018)**, [*Optimal Decisions in a Time Priority Queue*](https://doi.org/10.1080/1350486X.2018.1506257), [open accepted manuscript](https://kclpure.kcl.ac.uk/ws/files/115267487/Optimal_Decisions_DONNELLY_Accepted_20_Jul_18_GREEN_AAM.pdf) | Cancelling/staying can depend strongly on queue position and prevailing market conditions | Estimate quote-level cancellation value rather than cancel everything | Qminers matching is specific; calibrate rather than copy paper numbers |
| **Cont, Kukanov & Stoikov (2014)**, [*The Price Impact of Order Book Events*](https://doi.org/10.1093/jjfinec/nbt003), [arXiv](https://arxiv.org/abs/1011.6402) | Short-horizon price changes linked to order-flow imbalance (OFI), with depth dependence | Alpha and adverse-selection features | Statistical relation is asset-dependent and may decay before 5 ms activation |
| **Stoikov (2018)**, [*The micro-price: a high-frequency estimator of future prices*](https://doi.org/10.1080/14697688.2018.1489139), [author's code](https://github.com/sstoikov/microprice) | Book-conditional future price estimator | Better initial fair-value signals than unadjusted mid | A predictive microprice is not automatically executable PnL |
| **Huang, Lehalle & Rosenbaum (2015)**, [*Simulating and Analyzing Order Book Data: The Queue-Reactive Model*](https://ideas.repec.org/a/taf/jnlasa/v110y2015i509p107-122.html) | State-dependent arrival intensities for order flow in a Markov queuing model | Estimate probability and timing of fills/recovery | Requires data/model fitting; do not replace the official simulator |
| **Dahlström, Hagströmer & Nordén (2018/2023)**, [*The Determinants of Limit Order Cancellations*](https://doi.org/10.2139/ssrn.3012831) | Evidence linking cancellation to expected execution profit, depth and queue position | Better quote-value features for cancellation | Empirical market behavior, not a ready-made Qminers trading rule |

### Read order under competition time pressure

1. Organizer README and PDF (must read; **they control the score**).
2. Gao–Wang's abstract/results and Moallemi–Yuan's introduction (latency and FIFO value).
3. Cont–Kukanov–Stoikov and Stoikov microprice (signals).
4. Avellaneda–Stoikov / Guéant et al. (inventory-skew math).
5. Donnelly–Gan and queue-reactive model if you have time for a more precise fill model.

### Relevant public GitHub implementations (research references, not drop-in strategies)

| Repository | Why useful | Caution |
|---|---|---|
| [QminersOrg/qminers-algo-arena](https://github.com/QminersOrg/qminers-algo-arena) | **Authoritative** models, exchange behavior, scoring and CLI | Use this simulator for final scoring; validate rules against its code |
| [nkaz001/hftbacktest](https://github.com/nkaz001/hftbacktest) | Examples of order latency, queue-position models, tick-by-tick replay | Different execution model/API; do not substitute for Qminers |
| [sstoikov/microprice](https://github.com/sstoikov/microprice) | Published microprice estimator reference and research code | Features and parameters require recalibration |
| [fedecaccia/avellaneda-stoikov](https://github.com/fedecaccia/avellaneda-stoikov) | Small, comprehensible inventory-aware quoting simulation | No tournament-specific 5 ms FIFO/flat penalty |
| [ragoragino/avellaneda-stoikov](https://github.com/ragoragino/avellaneda-stoikov) | Replication and inventory-vs-symmetric comparison | Simplified academic simulation, not a ready Qminers solution |
| [Hummingbot inventory skew docs](https://hummingbot.org/strategies/v1-strategies/strategy-configs/inventory-skew/) | Practical inventory skew configuration and intuitions | Live crypto market assumptions differ markedly from fixed replay |

For external libraries or examples, only use code that is compatible with the competition rules. No online access is permitted in the strategy sandbox, and only the specified modules are importable.

---

## 13. Critical mistakes to avoid

1. **Treating penalty as per-lot.** It's a time-based step cost once outside ±100.
2. **Treating ±1,000 as a no-penalty allowance.** It is only a hard acceptance guard.
3. **Considering only current filled inventory.** Live and pending same-side orders can all fill.
4. **Assuming a sent cancel worked.** Cancel latency is 5 ms; a quote can fill in the interim.
5. **Cancelling/reposting good FIFO orders unnecessarily.** Shrink can preserve their queue place.
6. **Subtracting full spread twice.** Use either fill-to-future-markout PnL or an explicit spread-cost decomposition, not both.
7. **Estimating penalty from expected inventory.** Model probability and duration of *actual boundary crossing*.
8. **Assuming IOC exits are instant or guaranteed.** They are delayed and may partially fill or miss.
9. **Optimizing the sample's synthetic trend.** Actual round tapes have different dynamics.
10. **Counting a submitted IOC as a fill.** Only private fill updates change inventory and cash.
11. **Ignoring terminal markout.** A big position can be expensive to liquidate against shallow book depth.
12. **Letting the final 10 submissions consume all evaluation time.** Preserve a confirmed functional final submission and maintain clean research history.

---

## 14. Immediate implementation checklist

- [ ] Verify the repo is private, team is invited, and `antoninkriz` has Read access.
- [ ] Implement actual inventory, cash, and one coherent live/in-flight order ledger.
- [ ] Unit-test every order-state transition, partial fill and cancel race.
- [ ] Add conservative `I_min / I_max` exposure bounds and explicit no-breach budgets.
- [ ] Add a `RECOVER` state that reduces inventory to **±100**, not blindly to zero.
- [ ] Log time outside ±100 and compare with official `breach_penalty`.
- [ ] Add configurable cancel / shrink / keep policy for each quote.
- [ ] Add separate IOC executable-depth check after 5 ms.
- [ ] Backtest strict ±80 and ±100 baselines on the actual round's public data.
- [ ] Only then test penalty-enabled controlled bursts (`ENABLE_BREACH=True`).
- [ ] Compare gross edge, actual penalty, terminal markout and net PnL on chronological holdouts.
- [ ] Commit notes/results at least every 30 minutes, including failures, without history rewriting.

**Final rule of thumb:** A breach is not “leverage for free”; it is a time-limited trade financed by a **10,000-PnL-units-per-second clock**. Buy/sell more only when an order-level, latency-aware, incremental PnL model says the additional expected edge can pay that clock. Cancel (or better, shrink) quotes when their fill may trigger a breach whose expected total cost outweighs their **conditional fill profit plus queue value**. When already over the threshold, trade enough **actual filled volume** to stop the clock as economically as possible.
