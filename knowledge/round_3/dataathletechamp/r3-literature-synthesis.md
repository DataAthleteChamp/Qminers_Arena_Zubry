# Round 3 literature and practice synthesis (decision rules only)

Question: what do academic, industry, competition and cross-domain sources
say that changes our Round 3 design? Thirteen parallel research passes
(academic HFT, industry practice, high-volatility/game theory, maths and
statistics, robust selection, poker, betting/prediction markets, chess/
offline RL, trading competitions, GitHub/GitLab code, Chinese, Russian and
French sources). Read depth varied: many claims are abstract-level. Only
rules consistent with our own R3 measurements are listed; each still needs an
official-simulator test. Full source ledgers are in the agents' reports kept
with the experiments.

## Rules supported by both literature and our tape

1. **Alpha comes from taking on flagged informed flow; passive income needs
   gating.** Aggressive HFTs out-earn passive ones (Baron, Brogaard,
   Hagstromer, Kirilenko, JFQA 2019; Brogaard, Hendershott, Riordan, RFS
   2014). HFTs lean against early child orders, then join the most informed
   flow (van Kervel and Menkveld, JF 2019). Our tape: signal A follower
   +39/+49 PnL/s official on R3 A; following every taker loses ~440/s.
2. **Resting orders are profitable only near the front of a deep queue or in
   benign states.** Adverse selection rises with queue position (Moallemi and
   Yuan, SSRN 2996221); front-of-queue fills with a large near queue are
   profitable while back-of-queue fills lose in a live BTC experiment
   (Albers et al., arXiv:2502.18625); always-quote loses and only
   state-gated quoting is positive (Lu and Abergel, MML 2018); drop the
   vulnerable side under imbalance/flow (Cartea, Donnelly, Jaimungal, AMF
   2018). Our tape: fills with >= 300 lots behind are positive on R1-R3;
   fills against the insert-implied fair value lose -1.7 ticks/lot.
3. **Short inventory flips.** Menkveld (JFM 2013): positions held < 5 s
   earn, longer ones lose. Combine with passive unwinds with a timeout
   (Cartea, Jaimungal, Ricci, SIAM JFM 2014).
4. **Hold while the remaining drift exceeds the cost of acting.** Trade
   toward an aim portfolio (Garleanu and Pedersen, JF 2013; Lehalle and
   Neuman, F&S 2019). Our official tests: take-profits and fast exits cut the
   continuation (-16 to -38 PnL/s); 5 s holds beat 1-2 s.
5. **Inventory as a hard budget.** Count resting and in-flight orders, keep a
   soft cap below 100, reduce-only near it, skew quotes with inventory
   (Gueant, Lehalle, Fernandez-Tapia, MAFE 2013). Size by fractional Kelly
   with shrinkage, never to recover losses (Thorp 2006; MacLean, Thorp,
   Ziemba 2010).
6. **Classify flow from observables, update slowly, trust only verified
   buckets** (poker opponent modelling: Ganzfried and Sandholm, ACM TEAC
   2015; betting books reprice on sharp size and ignore square flow,
   Buchdahl/Pinnacle; Levitt, EJ 2004).
7. **Regime gates matter more than tuning.** Industry practice: per-strategy
   lockdown when revenue leaves bounds (Virtu IPO filing, 2015); our screen:
   sitting out low informed-flow rates fixes R1/R2 losses.

## Tools worth using (O(1) per event)

EMAs of signed flow, sweep counts and insert aggressiveness; an exponential
Hawkes intensity is just an EMA and added nothing in our screen; CUSUM for
PnL/regime alarms; jump-robust (bipower/MAD) volatility for scaling;
bucket-mean state tables (generalised micro-price, Stoikov QF 2018).
Spectral/wavelet analysis, BOCPD and Kalman OU fits are diagnostics only:
no periodicity exists and wavelet features reduced out-of-sample R2.

## Selection and validation

Log every configuration; use 12 x 500 s block scoring, CSCV/PBO and the
deflated Sharpe ratio (Bailey et al., J. Comput. Finance 2017; Bailey and
Lopez de Prado, JPM 2014); promote on validation only above one paired SE
(Blum and Hardt, ICML 2015); at most five pre-registered finalists; never
hill-climb thresholds on validation feedback.

## Not transferable here

Wall-mid fair values (Prosperity winners) fail: big orders are random
ordinary orders with ~0.3 s scheduled lives. VPIN-style gates mostly proxy
trade intensity. Stale-quote races are microsecond events in real markets;
our 5 ms stale-side edge exists only because the replay does not react.
Hindsight-DP imitation (EarnHFT, VIPER) is promising but too slow for this
round's time budget.
