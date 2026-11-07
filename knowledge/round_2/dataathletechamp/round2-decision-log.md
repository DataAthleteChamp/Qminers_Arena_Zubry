# Round 2 decisions worth remembering

| Decision / mechanism | Actual evidence | Retained conclusion |
|---|---|---|
| Start with exact R1 Final | R2A-143178, penalty0 | A working old-round file is not new-round alpha |
| Predict danger, cap exposure |18916A/-229513B | Risk ranking is not executed fill value |
| Use teammate Grid |91025A/28827B | Keep forecast, target and execution contributions separate |
| Preserve head/replenish deficit |100195A, exact reproduction | Useful turnover can increase net, not just order count |
| Finite gap/warned-side protection |103998A/43782owner-reportedB | Small incremental execution improvements can transfer |
| Update EMA only on clean book |104703A/47150verifiedBexport | A small A delta can still matter on B |
| Tiny fixed-size configurations | Five losses; fixed35+8831 | Smaller individual trades are not automatically profitable |
| Inside spread repair | -18422/62216/-6659A | A long-enough gap is not a favourable fill |
| More children/bigger sizes | Mostly lower A scores | More capacity is not an edge by itself |
| Neutral target |57317A; peer-reported15917B | Less variance is not the same as more net PnL |
| Single price level96 |121235A exact reproduction | Promising allocation; B outcome not supplied |
| Human final joint variant |127559A; export80993, B/CUNKNOWN | Freeze actual selected bytes; do not invent causal attribution |

A has6000s, B/C were reported approximately12000s. Doubling duration only
doubles expected PnL under comparable profit rates, not a realised score.
The same generator does not imply the same direction, gaps or inventory path.

The original Final source's exposure check keeps actual plus all remaining
same-side quantities under100. A200-lot order from-100 can be admissible;
1000 is the exchange acceptance wall, not a free operating target.
Neither cancelling nor requesting a shrink immediately releases quantity.

The official synthetic shrink tests preserved FIFO but also showed that a
partial fill can make an amendment obsolete without a MODIFIED notification.
This is why we did not rush an untested resize-pending state into Final.

References and full measured commands are in the market, execution, validation,
order-reaction and individual experiment notes. Old tables were not rewritten
to hide failed trials. Raw completed plans/snapshots are read-only history.
