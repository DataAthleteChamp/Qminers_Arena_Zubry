# Selective IOC: continuation value, executable costs and strict joint risk

Question: can a SMALL IOC addition improve the exact selected passive maker,
without changing ordinary quoting or permitting inventory penalties?
Do not infer an answer from midpoint correlation or the current public score.

## Source verification by the research agent

| Primary source | Version / actual read depth | Transfer / limitation |
|---|---|---|
| Guilbaud and Pham, Optimal high frequency trading with limit and market orders | arXiv1106.5040v1,2011-06-24; sections2.1-2.3,3.1-3.3 and part4 | Compare continuation with market-order intervention; immediate small full touch execution and Cox fills are not delayed persistent FIFO |
| Lehalle and Mounjid, Limit Order Strategic Placement with Adverse Selection Risk and the Role of Latency | arXiv1610.00261v4,2018-03-15; sections2.1-2.2,3.1-3.2,4.1-4.2,5 | Fill-conditioned value and slower-control costs; negligible order size, abstract intervention-frequency latency and future microprice are not actual5ms/depth liquidation |

Versioned sources:
https://arxiv.org/html/1106.5040v1 and https://arxiv.org/html/1610.00261v4.
Relevant first-paper equations2.6-2.7,3.1-3.6; second-paper equations3-5.
This was verified section-level reading, not a claim to read all appendices
or independently replicate published plots. No external implementation was executed.

## Derivations versus venue rules

A new buy followed by future aggressive sale costs both entry and exit half
spreads plus depth. `future_mid-current_ask` omits future liquidation cost.
For a pre-owned long lot, compare selling now at bid versus continuation:
the original acquisition cost is sunk, but surrendering a passive ask fill matters.
Neither a small average forecast nor a negative unconditional IOC proxy proves
all rare fill-conditioned tails lose.

Risk remainsI+B<=100 andI-S>=-100 for ALL LIMIT/IOC/pending/canceling quantities.
A sufficient no-flip reducing SELL bound ismax(0,I-S); BUY boundmax(0,-I-B).
If existing full-headroom quotes leave no spare/no-flip capacity, record no
eligibility rather than weaken risk, net opposite orders or invent an IOC gain.
The source's time abstraction is not our clock: due actions are processed before
the next market row, with internal callbacks at their scheduled ready timestamps.

Current SDK emitsPARTIALLY_FILLED only with positive residual, thenCANCELED
for IOC leftovers; zero residual emitsFILLED (`simulator/simulator.py:1194-1213`).
New mixed code must retain reserve until terminal acknowledgement and must not
let a maker reconciler treat an IOC's touch price as a stale maker quote.

## Bounded hypotheses after maker-size selection

Freeze the corrected0.5s predictor trained only on actual target times<4800s.
Freeze the exact selected passive source/hash before intervention.
No new predictor fit, quote-size rescue, intentional breach or new holdout claim.

H1: one-lot provably reducing IOC when inventory blocks increasing maker capacity,
forecast opposes inventory, touch-price cap, once per eligibility episode.
Control: same capacity-blocked reduction WITHOUT forecast gate.
Expected benefit is less adverse carry/capacity restoration, NOT saved penalties
when both arms already stay inside100.

H2: one-lot rare tail gate with spare capacity and a touch-price cap. Use actual
delayed fill selection and future opposite-book liquidation, not a supposed
guaranteed passive exit. A past-only cheap executable-edge diagnostic must be
positive; zero/sparse or losing tails park the mechanism rather than widen gates.

Budget: passive baseline plus at most3 IOC arms. First test H1 and its control.
Reject an improvement claim for nonpositive matched PnL in either consumed
later window, or any ledger/risk/lifecycle discrepancy. Record zero fills,
rejected/blocked opportunities, PnL/volume, actual IOC quantities and costs.
All public windows are development/robustness evidence, not fresh private tests.
