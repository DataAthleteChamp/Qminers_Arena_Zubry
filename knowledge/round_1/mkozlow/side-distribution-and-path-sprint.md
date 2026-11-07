# Distribution and path-model improvement sprint

Result: best verified public PnL505225 versus416852 at sprint start and477516 for supplied477k.py. Target700000 was not reached. Preserve the best submission candidate; no private-performance guarantee.

## Best submission candidate

strategies/round_1/mkozlow/505225_ridge_queue_maker.py. Exact source from side-skew-refinement-035/a2_s0010. Nominal target200, cap100 with pending/cancel exposure reserved, eight FIFO orders per side, full replenishment, minimum10-lot top-up, forecast multiplier2, inventory skew.001. Center is midpoint+2*ridge−.001*inventory; bid and ask clamp passively against current market touches. IOC disabled. Existing repricing cancels and replaces after acknowledgment.

Forecast inputs are touch imbalance, full visible market-depth imbalance and exponentially decayed market-to-market aggressive flow at.2/1/3s. Frozen supplied coefficients; training provenance was not supplied with477k.py. Flow excludes market aggression hitting our own quotes. Changing ownership filter without refitting reduced PnL here; not an assured correction.

Best PnL505225; segments249132 /130236 /125857; zero penalty; max actual/reserved position100; inventory median absolute100.175 LIMIT-taker lots and2019923 maker lots. All quoted orders are LIMIT; latency can make a LIMIT take. Bytes8419. Source SHA256 c1f194668ec83e94bf522e749ce36d266caeedb9244506ede2adeee68e8e3667. Preflight passes; official local engine is not the complete server sandbox checker.

## Integrity and evaluation

Data: data/round1/round1.csv;4411336 events, approximately12000s. SHA256362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940. Official simulator digest6dba6395cd6104e47132c53a251f2f0781b4d66d910c34e0025cc7843fbeadb5. Raw data and official source unchanged. Every successful strategy replay reconciles independent trade-derived cash/inventory with engine totals and audits reservations continuously.5ms exchange latency and10000/s exact breach charge unchanged.

User explicitly requested aggressive distribution-level overfitting. All public tape is tuning data; segment results at6000/9000s are reused stability checks, not independent validation. Parameter sweeps run the full tape without slicing. Learned new models fit only with complete labels before6000s, then affect quoting after6000s. Their first-half baselines differ by source and are reported. No future labels or tape-specific price/time schedules are used online;6000s gates in experimental learned variants are evaluation controls.

No paired SE, private P(win), or future700k claim. Best parameters increased absolute inventory persistence; this is a measured tradeoff, not free PnL. Best505225 beats477516 in every segment but does not beat496928 in the middle segment.

## Questions, mechanisms and outcomes

Test full replenishment versus remainder60; more FIFO slots; linear/zero/cubic inventory skew; source477k reproduction and forecast strength; ownership-complete flow; path-level probabilities and continuation/reversal; volume-weighted expected execution profit; nonlinear short-return models. Reject changes that do not beat the appropriate exact control, and disclose chronological inconsistency.

### side-capacity-skew-029

Command: uv run --locked python experiments/round_1/mkozlow/side-capacity-skew-029/run.py

- full_two: PnL429954.0; segments[206514.0, 112893.0, 110547.0]; volume2330394.
- full_eight: PnL435759.0; segments[210125.0, 113663.0, 111971.0]; volume2359526.
- zero_skew_eight: PnL423550.0; segments[201344.0, 112005.0, 110201.0]; volume2642200.
- half_skew_eight: PnL451276.0; segments[215892.0, 118417.0, 116967.0]; volume2455646.
- cubic_skew_eight: PnL442897.0; segments[213551.0, 115443.0, 113903.0]; volume2523928.
- fine_topup_eight: PnL435866.0; segments[210425.0, 113690.0, 111751.0]; volume2361200.

### side-477-maker-032

Command: uv run --locked python experiments/round_1/mkozlow/side-477-maker-032/run.py

- source477: PnL477516.0; segments[232677.0, 125017.0, 119822.0]; volume2232620.
- stack8: PnL478290.0; segments[233146.0, 125104.0, 120040.0]; volume2238648.
- alpha1: PnL452241.0; segments[218222.0, 118877.0, 115142.0]; volume2504418.
- alpha3: PnL473373.0; segments[232797.0, 122556.0, 118020.0]; volume1895108.
- flow_complete: PnL474767.0; segments[231879.0, 123680.0, 119208.0]; volume2231778.

### side-path-quoting-033

Command: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run --locked python experiments/round_1/mkozlow/side-path-quoting-033/run.py

- path_inventory: PnL479306.0; segments[232677.0, 124456.0, 122173.0]; volume2196988.
- path_replace: PnL466942.0; segments[232677.0, 118193.0, 116072.0]; volume2370450.
- execution_value: PnL469643.0; segments[232677.0, 120666.0, 116300.0]; volume2182622.
- path_inventory_ev: PnL473899.0; segments[232677.0, 123514.0, 117708.0]; volume2148638.

### side-distribution-tuning-034

Command: uv run --locked python experiments/round_1/mkozlow/side-distribution-tuning-034/run.py

- a2_s0025: PnL496928.0; segments[241354.0, 132151.0, 123423.0]; volume2154346.
- a2_s0075: PnL461768.0; segments[222579.0, 120723.0, 118466.0]; volume2254128.
- a3_s0075: PnL465637.0; segments[226728.0, 121437.0, 117472.0]; volume2007454.
- a4_s0100: PnL434127.0; segments[213813.0, 111967.0, 108347.0]; volume1798838.
- a4_s0050: PnL443223.0; segments[217596.0, 113874.0, 111753.0]; volume1595604.
- a2_s0150: PnL431098.0; segments[208149.0, 112698.0, 110251.0]; volume2199386.
- a3_s0150: PnL424655.0; segments[205812.0, 109274.0, 109569.0]; volume2058998.
- a6_s0200: PnL391801.0; segments[190992.0, 101574.0, 99235.0]; volume1677846.

### side-skew-refinement-035

Command: uv run --locked python experiments/round_1/mkozlow/side-skew-refinement-035/run.py

- a2_s0000: PnL493447.0; segments[245076.0, 124532.0, 123839.0]; volume1887352.
- a2_s0010: PnL505225.0; segments[249132.0, 130236.0, 125857.0]; volume2020098.
- a15_s0010: PnL481392.0; segments[231487.0, 129375.0, 120530.0]; volume2332648.
- a25_s0010: PnL488504.0; segments[242646.0, 124221.0, 121637.0]; volume1779064.

### side-nonlinear-return-036

Command: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run --locked python experiments/round_1/mkozlow/side-nonlinear-return-036/run.py

- replace: PnL471839.0; segments[241354.0, 113591.0, 116894.0]; volume2056314.
- blend: PnL489830.0; segments[241354.0, 124551.0, 123925.0]; volume2135030.
- multihorizon: PnL489418.0; segments[241354.0, 124587.0, 123477.0]; volume2142204.

## Path and execution models

Collector side-path-execution-model-031 exactly reproduces416852. Initial030 failed on a missing book side before producing a successful dataset; failure retained and corrected in fresh031. Collector uses20ms causal snapshots, actual queue ahead and first-fill labels5–100ms. It saves15 market-path features and29 oriented order features. Future midpoint labels are offline training/evaluation only.

After a recent100ms move, the next250ms midpoint outcome is continuation about22–23%, reversal20–21%, unchanged57%. Do not assume every short move continues. A three-class gradient-boosted model improves classification after those moves. Six binary models estimate reaching up/down1/2/3ticks within3s. Both directions can be reached; these events are not mutually exclusive.1tick Brier improves about8–9% relative to fitted constant; gains shrink for2ticks and3ticks. Accuracy at distant levels is dominated by no-hit prevalence.

Standalone exported-tree predictions match installed sklearn predictions within1e-10. Model constants remain under1MiB in generated strategies. New-price hitting probabilities are not endpoint expected returns or executable profit. The small path-inventory gain479306 versus477516 is inconsistent across later segments and below the tuned best.

Joint execution models predict first-fill quantity and first-fill quantity times250ms signed midpoint markout, using no-fill observations as zero. Candidate noquote/half/full quantity is valued with queue-ahead, age, adverse selection and inventory-distance cost. These variants lose against477516; do not retain their quoting rule just because markout regression predicts adverse fills.

Nonlinear250ms endpoint return correlation is.52 and1s correlation.38–.40 in reused later checks. Prediction improvements do not establish maker-profit improvements; actual strategy tests are above.

Reproduction: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run --locked python experiments/round_1/mkozlow/side-path-execution-model-031/fit.py. Collector: uv run --locked python experiments/round_1/mkozlow/side-path-execution-model-031/run.py. Completed immutable experiment paths are write-once; reproduce with fresh IDs rather than overwriting outcomes.

Limits: baseline-policy cancellation censoring; overlapping observations share fills; first-fill proxy omits later order fills; hypothetical new queue ahead uses current depth rather than unknowable future depth; fitted flow observes different executed quantities once our liquidity is added; new HGB path features omit deeper-book imbalance used by the supplied ridge. Models do not learn causal FIFO continuation value or an optimal cancel/replace policy.

## Retain

Retain505225 candidate and this report. Keep all raw candidates/results in experiments. Older496928 and416852 candidates remain available; no frozen source was edited. No commit, push, pull, upload or official-source mutation.
