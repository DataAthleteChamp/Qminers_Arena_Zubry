# Submit the actual single strategy file

- `make check`; run `tools.preflight` on the exact .py.
- Check an actual official-engine run, penalty, state/queue handling, data/strategy
  hashes and interpretation. Reproduce from the same frozen source.
- One BaseStrategy subclass, no required constructor args; Python 3.13; <=1 MiB.
- Only allowed imports/builtins. Tools may read files; submitted strategy may not.
- Server budget: 1 CPU, 2 GB as published, 15 minutes, no network.
  Local preflight is conservative, not the unpublished server checker.
- Name the reviewed artifact and full hash. One human uploads, a second verifies.
- Record server ID/error/public PnL and whether intended file is Final.
- Failed upload keeps old working Final; successful bad experiments can replace it.
- Preserve rollback, history and notes. No automatic upload or invitation changes.

The playground original and fixed team file both scored 1878 locally. This is
not evidence that either wins private R1. Run on the actual R1 tape when released.
