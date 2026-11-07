# Round clock and release discipline

See `competition.json` for schedule. R1 is 13:00-18:00 Saturday; R2 19:00-00:00;
R3 01:00-06:00 Sunday; R4 07:00-12:00. Confirm dashboard closing time, not only round end.

1. Intake the actual round file, source/hash, horizon, rules and deadline.
2. Run a valid small incumbent with the official engine; inspect penalty and failures.
3. Diagnose only the relevant one-instrument mechanisms. One hypothesis per pair.
4. Predeclare, run under a new ID, keep successes AND failures, compare on same tape.
5. Use proper warmup for time windows, test out-of-sample when data supports it,
   and retain mechanics behind flags if they do not help this round.
6. Another person reproduces and reviews; freeze before upload.
7. At least every 30 minutes commit work/notes/results, without rewriting history.

At most 10 uploads per round, only one being evaluated at a time. Latest successful
upload becomes final unless explicitly changed; failed uploads do not replace a
working final. Verify Final after EVERY successful exploratory upload.
Public uploads are not fresh private-data evidence. Save slots/time for validation.
Round 4 has no published leaderboard until closing.
