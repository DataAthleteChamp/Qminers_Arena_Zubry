# Review of supplied penalty-aware research

Source: `Qminers_Penalty_Aware_Trading_Research.md`, 49,067 bytes, SHA-256
`1d45ce018a5040b64df14b98639236e0b335ed6b42c81dbe80f477ec37b0d893`.
Read the entire supplied document. The original root file is preserved unchanged.
This is a critical synthesis, not automatic acceptance of every proposed model.

## Confirmed and incorporated

The source correctly states:

- Inventory charge is `10000 * integral(1[abs(I)>100] dt)`, not per excess lot.
  Inventory exactly100 is free. Actual filled position and actual time matter.
- In-flight new orders and cancel/shrink-in-flight residuals stay reserved.
  Opposite orders do not cancel worst-case same-side exposure.
- Orders pay execution/markout costs even without explicit fees.
- The1000 acceptance wall is not a penalty-free inventory allowance.
- Shrink may retain FIFO, while cancel/reinsert loses it; priority is not guaranteed alpha.
- When outside the band, reaching100 stops the clock; going all the way to zero
  is a separate decision. This matters only if a policy actually enters a breach.
- A source's queue option value or adverse-selection model is not a Qminers
  coefficient, and expected inventory cannot substitute for expected occupation cost.

Current tested families cap actual and reserved same-side inventory at80 or95.
They have zero recorded penalties. That result does not validate an over-limit mode.
All sends and delayed cancels remain tracked until authoritative terminal events.

## Important qualifications

1. The simulator's exact timing must control calculations: it processes due actions
   before the next market row, advancing its internal clock to each action's ready
   timestamp. Do not equate observed callback processing with a guaranteed longer
   charged interval or assume every reactive recovery necessarily pays50.
2. `A > 10000 * p90(recovery time) + U` is a proposed conservative screen, not a
   theorem or calibrated guarantee. The recovery distribution, partial/no-fill tails
   and incremental comparison against a safe policy must first be measured.
3. If future execution/continuation value is already included in an order-value
   model, adding a separate queue-option value can double-count it. Define horizons
   and continuation accounting explicitly.
4. A size-weighted midpoint is a heuristic, not the full dynamic micro-price model.
5. Source bibliography was not automatically endorsed. A-S, GLFT and
   Cartea-Donnelly-Jaimungal were verified by the paper-research wave.
   Moallemi-Yuan was independently checked at Columbia's abstract/working-paper
   record. Gao-Wang full publisher access returned403; methods are not claimed read.
6. A preset end-of-public-tape flattening rule can overfit a known boundary. Any
   endgame policy requires a real documented runtime horizon or evidence and
   separate testing; no historical path lookup or future schedule is used.

## Current experiments and decisions

The retained source motivates joint pending-order risk and FIFO-preserving size
replenishment. Our new top-up experiment allows at most two orders per side,
reserves BOTH, never adds during pending placement/cancel, and tests the cap under
partial fills and cancellation races. It is compared with the same60-lot depth
maker, not an unrelated lower-size strategy.

The predictor-sizing experiment first instrumented the unchanged60-lot baseline:
monitored PnL exactly matches95701 on discovery. At0.5 seconds after actual fills,
the lowest/middle/highest quote-time forecast buckets have volume-weighted
midpoint markouts0.205/0.261/0.305 ticks, but opposite-quote markouts remain
-0.333/-0.275/-0.236. These are diagnostics, not additional realized profit.

Frozen +/-15-lot sizing around60 produces discovery95243 versus baseline95701
and validation77577 versus77029, all penalty-free. The tiny mixed delta is not
strong evidence for adding complexity or scaling the effect linearly.

The stronger current size/skew family has positive discovery and later-window
PnL, but high inventory occupation near95. A protected95 cap is not a license
to target1000 or intentionally pay the penalty.

## Retained hypotheses, not automatic deployments

- Keep safe pending/live envelopes and cancellation-race handling.
- Compare preserving partial-fill FIFO plus a bounded top-up with baseline.
- Estimate conditional fill value before changing size or crossing the spread.
- Consider zero-penalty cap100 only after a deterministic common-risk invariant
  test; boundary inclusion is published but leaves no error buffer.
- Park300-900-lot bursts and recovery optimization: no calibrated incremental
  recovery-time distribution or positive out-of-band policy evidence exists.

No raw/evaluator edits, private PnL claim, inferred ticker/currency or sandbox bypass.
Public validation has informed selection; the final outcome block remains separate.

## References

- Official starter/PDF/`competition.json`: source of the actual charge and controls.
- A-S: https://doi.org/10.1080/14697680701381228, Eqs29-30, paper wave method read.
- GLFT: https://arxiv.org/html/1105.3115v4, bounded-inventory model, §§2-5 read.
- Cartea-Donnelly-Jaimungal:
  https://doi.org/10.1080/1350486X.2018.1434009, §§3.2-3.3 read by research agent.
- Moallemi-Yuan:
  https://business.columbia.edu/faculty/research/model-queue-position-valuation-limit-order-book,
  abstract only independently checked.
- Gao-Wang: https://doi.org/10.1080/14697688.2020.1741670, supplied reference;
  publisher full text not accessible during this review.
