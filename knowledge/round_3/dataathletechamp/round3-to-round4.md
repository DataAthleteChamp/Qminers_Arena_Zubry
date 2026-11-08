# Round 4 opening checklist and rules (from Round 3)

The Round 4 public tape is already downloaded, untracked and unmodified:
`data/round4/round4_public.csv`, 85.9 MB.
Read `round3-retrospective.md` first.

## Rules

1. **Assume the leaderboard is real.** Top teams earned 1.0–1.46M on unseen
   private tapes in R2 and R3. If we are far below the median, we are
   missing a mechanism; don't explain the gap away.
2. **Upload early, decompose every result.** Validation (B) is the only
   same-generator out-of-sample test. Upload a baseline in the first hour,
   then each improved candidate. Compare uploads on ordinary seconds, jump
   seconds and 600 s blocks, not only on totals.
3. **Discover mechanisms before tuning.** In the first two hours run:
   - the market profile against prior rounds;
   - the oracle-gap study (where perfect foresight beats the incumbent);
   - the IOC limit and remainder structure;
   - event studies of new information sources.

   Parameter neighbourhoods come last and are worth about 1%.
4. **Check live/research parity.** Every live feature must reproduce its
   research definition on a null replay before it is judged. Round 3 lost
   hours to `FV_DEPTH = 2`.
5. **Predeclare acceptance.** A change must beat the incumbent on the new
   public tape **and** on at least one other tape: a prior public tape or
   paired synthetic tapes. Its neighbour setting must keep at least half the
   gain. Results selected after seeing them are labelled as such.
6. **Respect the ±100 band.** The penalty is 10,000 PnL per second above 100.
   No over-limit burst survived costs plus penalty in R3.
7. **No passive quoting without measured evidence.** Add a maker leg only if
   fill-conditioned markout, by aggressor size and at our likely queue
   position, is positive on the new tape and on B.
8. **Keep the clock.** Have a validated candidate by T+2 h and freeze by
   T−60 min. Re-upload the chosen final last by T−20 min and confirm its
   sha256 against the server export's class name and PnL. Final = latest
   successful upload.
9. **Agents.** One writer per worktree and branch; merge with `--no-ff`;
   commit only `knowledge/*.md` and `strategies/*.py`; no Copilot trailers;
   record negative results; give each agent a hard deadline and a
   both-tapes acceptance rule.

## First hour

1. Register the R4 data: sha256, rows, duration and integrity. Use the
   same profiler on R1–R4. Check whether momentum and reversion horizons
   changed (R2 trended, R3 reverted at 10 s–5 min).
2. Run the incumbents unchanged on R4 public:
   - U7 `r3_follower_u7_flow_deepfv.py`
   - U8 `r3_follower_u8.py`
   - U4 `r3_alpha_follower_p1_sw3.py`
   - plain D1 `r3_informed_follower.py`
3. Upload the best incumbent to B as the baseline and archive the export
   under `experiments/round_4/dataathletechamp/<id>-validation-feedback/`.
4. Run the oracle-gap study on R4 with the incumbent's position path.
   Scripts are in `experiments/round_3/dataathletechamp/20261108-r3-w6-oracle-gap-001/`.
5. Refit the alpha ridge (pooled public tapes, intercept 0) if R4 behaves
   like R3. The recorder and fitting scripts are in
   `experiments/round_3/dataathletechamp/20261108-r3-w3-alpha-model-001/`;
   the method is in `r3-alpha-model.md`.

## Reusable tools

| Tool | Location |
|---|---|
| Parallel official-engine runner (grid of module-constant overrides) | `experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py` |
| Runner with synthetic tapes added | `experiments/round_3/dataathletechamp/20261108-r3-u7-distribution-001/runner_syn.py` |
| Calibrated synthetic generator (paired comparisons only) | `experiments/round_3/dataathletechamp/20261108-r3-generator-monte-carlo-001/` |
| Null replay (BBO + trades) | `experiments/round_3/dataathletechamp/20261108-r3-deep-diagnostics-001/replay.py` |
| IOC limit, remainder and hidden-IOC screens; B wealth-curve decomposition; 1 s foresight ceiling | `experiments/round_3/dataathletechamp/20261108-r3-ioc-limit-structure-001/` |
| Oracle path and gap decomposition | `experiments/round_3/dataathletechamp/20261108-r3-w6-oracle-gap-001/` |
| Hidden-price (G-insert class) estimator study | `experiments/round_3/dataathletechamp/20261108-r3-w6-latent-filter-001/REPORT.md` |

Commands always use `env -u VIRTUAL_ENV uv run --locked ...` from the
repository root. Run preflight with `python -m tools.preflight <abs file>`.

## Open leads, not tested results

- **Entering about 0.3 s earlier.** Late entry is still 57% of the oracle
  gap. Candidate sources are IOC remainder patterns, insert-class flow and
  queue depletion. Test each by event study first.
- **Flip-cost reduction.** We flip right after sweeps, when the spread
  averages 1.58 ticks. Test timing within the first 20 ms against passive
  partial flips. Earlier passive variants failed because the edge decays
  within about 20 ms.
- **A different generator regime.** If R4 trends at 10–60 s like R2,
  re-test longer holds and the R2-style skew.
