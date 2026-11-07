# Observed Round 1 experiment ledger

**Finite search, not a global optimum or private-performance guarantee.**

Actual bounded CLI replay records: **85**. Additional transparent observer runs reconcile fills/cash/positions; they are repetitions, not independent statistical samples.

Stage counts: `{'clean-hybrid-discovery': 1, 'clean-hybrid-final-check': 1, 'clean-hybrid-validation': 1, 'clean-hybrid-whole-public': 1, 'discovery-0-4800': 43, 'discovery': 2, 'metamorphic-stress-not-private': 4, 'reserved-final-check': 3, 'validation-4800-8400': 23, 'validation': 2, 'whole-public': 3, 'benchmark-incumbent-no-selection': 1}`.

Discovery0-4800; selection validation4800-8400; reserved strategy check8400-12000. Full-tape descriptions consume distribution information. Final ridge cutoff bug was corrected without policy retuning; its retests use consumed windows.

All completed artifacts are immutable under `experiments/round_1/dataathletechamp/`. The two failed model workers and finalist path-setup failure are preserved too.

| Experiment | Evidence stage | PnL | Penalty | Filled orders | abs inventory q95 | Seconds |
|---|---|---:|---:|---:|---:|---:|
| clean-hybrid-discovery | clean-hybrid-discovery | 132865 | 0 | 9565 | 100 | 22.7 |
| clean-hybrid-final-check | clean-hybrid-final-check | 104829 | 0 | 7180 | 83 | 35.8 |
| clean-hybrid-validation | clean-hybrid-validation | 106580 | 0 | 7330 | 91 | 27.5 |
| clean-hybrid-whole-public | clean-hybrid-whole-public | 344438 | 0 | 24076 | 100 | 56.2 |
| discovery-depth-size100-cap100-skew01 | discovery-0-4800 | 124951 | 0 | 9200 | 100 | 14.6 |
| discovery-depth-size100-cap100-skew02 | discovery-0-4800 | 121837 | 0 | 8103 | 100 | 14.5 |
| discovery-depth-size20-weight05 | discovery-0-4800 | 42687 | 0 | 11651 | 42 | 14.3 |
| discovery-depth-size20-weight10 | discovery-0-4800 | 46282 | 0 | 10783 | 38 | 14.3 |
| discovery-depth-size40-cap90 | discovery-0-4800 | 76429 | 0 | 9577 | 60 | 14.8 |
| discovery-depth-size40-skew03 | discovery-0-4800 | 73502 | 0 | 8928 | 53 | 14.6 |
| discovery-depth-size40-weight05 | discovery-0-4800 | 72305 | 0 | 10173 | 60 | 14.7 |
| discovery-depth-size40-weight10 | discovery-0-4800 | 76394 | 0 | 9558 | 59 | 14.7 |
| discovery-depth-size40-width025 | discovery-0-4800 | 73001 | 0 | 7876 | 50 | 14.6 |
| discovery-depth-size60-cap95 | discovery-0-4800 | 97937 | 0 | 8732 | 78 | 14.7 |
| discovery-depth-size60-skew03 | discovery-0-4800 | 92517 | 0 | 8217 | 66 | 14.5 |
| discovery-depth-size60-weight10 | discovery-0-4800 | 95701 | 0 | 8823 | 76 | 14.8 |
| discovery-depth-size60-width025 | discovery-0-4800 | 94057 | 0 | 7548 | 67 | 14.6 |
| discovery-depth-size80-cap95 | discovery-0-4800 | 113227 | 0 | 8245 | 89 | 14.7 |
| discovery-depth-size80-skew015 | discovery-0-4800 | 111361 | 0 | 9186 | 80 | 14.1 |
| discovery-depth-size80-skew025 | discovery-0-4800 | 105863 | 0 | 8292 | 80 | 14.2 |
| discovery-depth-size80-weight10 | discovery-0-4800 | 110746 | 0 | 8715 | 80 | 14.7 |
| discovery-depth-size80-width025 | discovery-0-4800 | 106864 | 0 | 7157 | 80 | 14.2 |
| discovery-depth-size95-cap100-skew01 | discovery-0-4800 | 125344 | 0 | 9219 | 100 | 14.6 |
| discovery-depth-size95-cap95-skew01 | discovery-0-4800 | 120070 | 0 | 9314 | 95 | 14.7 |
| discovery-depth-size95-cap95-skew02 | discovery-0-4800 | 117101 | 0 | 8238 | 95 | 14.8 |
| discovery-depth-size95-cap95-skew03 | discovery-0-4800 | 108357 | 0 | 7541 | 95 | 14.5 |
| discovery-depth-size95-cap95-skew04 | discovery-0-4800 | 106503 | 0 | 7306 | 90 | 14.6 |
| discovery-flow-depth-size20 | discovery-0-4800 | 44676 | 0 | 11441 | 40 | 14.2 |
| discovery-flow-depth-size40 | discovery-0-4800 | 76356 | 0 | 10041 | 59 | 14.5 |
| discovery-flow-depth-size80 | discovery-0-4800 | 107549 | 0 | 8657 | 80 | 14.2 |
| discovery-flow-depth-size80-cap95 | discovery-0-4800 | 114915 | 0 | 8552 | 95 | 14.6 |
| discovery-gate-size20-qi06 | discovery-0-4800 | 25040 | 0 | 5386 | 42 | 13.8 |
| discovery-hysteresis-size20 | discovery-0-4800 | 30339 | 0 | 7806 | 74 | 14.1 |
| discovery-mid-size10-skew02 | discovery-0-4800 | 19807 | 0 | 13184 | 34 | 14.7 |
| discovery-mid-size100-cap100-skew01 | discovery-0-4800 | 106561 | 0 | 9613 | 100 | 14.3 |
| discovery-mid-size2-skew05 | discovery-0-4800 | 4346 | 0 | 9121 | 3 | 14.5 |
| discovery-mid-size20-skew00 | discovery-0-4800 | 33252 | 0 | 13363 | 80 | 14.2 |
| discovery-mid-size20-skew01 | discovery-0-4800 | 35369 | 0 | 12878 | 63 | 14.3 |
| discovery-mid-size20-skew02 | discovery-0-4800 | 36982 | 0 | 11997 | 44 | 14.5 |
| discovery-mid-size40-skew02 | discovery-0-4800 | 67073 | 0 | 10468 | 63 | 14.5 |
| discovery-mid-size60-skew02 | discovery-0-4800 | 88348 | 0 | 9633 | 80 | 14.5 |
| discovery-mid-size80-skew02 | discovery-0-4800 | 100980 | 0 | 8848 | 80 | 14.3 |
| discovery-mid-size95-cap95-skew02 | discovery-0-4800 | 111219 | 0 | 8407 | 95 | 14.4 |
| discovery-queue-topup | discovery-0-4800 | 100564 | 0 | 9088 | 77 | 16.0 |
| discovery-queue95 | discovery | 129851 | 0 | 9528 | 100 | 15.1 |
| discovery-rest-size20-50ms | discovery-0-4800 | 36044 | 0 | 11837 | 44 | 14.3 |
| discovery-ridge-size | discovery-0-4800 | 95243 | 0 | 8958 | 74 | 21.5 |
| discovery-ridge-topup-hybrid | discovery-0-4800 | 97035 | 0 | 9224 | 73 | 22.7 |
| discovery-ridge-topup95 | discovery | 132864 | 0 | 9565 | 100 | 22.2 |
| mirror-depth | metamorphic-stress-not-private | 333188 | 0 | 23222 | 100 | 35.2 |
| mirror-queue | metamorphic-stress-not-private | 343269 | 0 | 23979 | 100 | 38.4 |
| mirror-ridge-clean | metamorphic-stress-not-private | 345081 | 0 | 24107 | 100 | 55.2 |
| reserved-final-check-depth_inventory_maker | reserved-final-check | 102832 | 0 | 6952 | 94 | 29.2 |
| reserved-final-check-queue_retention_maker | reserved-final-check | 106725 | 0 | 7203 | 90 | 30.1 |
| reserved-final-check-ridge_queue_hybrid | reserved-final-check | 104829 | 0 | 7180 | 83 | 35.4 |
| shift-queue | metamorphic-stress-not-private | 343269 | 0 | 23979 | 100 | 38.4 |
| validation-depth-size100-cap100-skew01 | validation-4800-8400 | 105381 | 0 | 7069 | 100 | 21.8 |
| validation-depth-size100-cap100-skew02 | validation-4800-8400 | 99821 | 0 | 6256 | 90 | 21.8 |
| validation-depth-size40-weight10 | validation-4800-8400 | 61751 | 0 | 7428 | 46 | 22.3 |
| validation-depth-size60-skew03 | validation-4800-8400 | 71765 | 0 | 6217 | 53 | 21.2 |
| validation-depth-size60-weight10 | validation-4800-8400 | 77029 | 0 | 6745 | 60 | 22.2 |
| validation-depth-size60-width025 | validation-4800-8400 | 71930 | 0 | 5753 | 57 | 21.3 |
| validation-depth-size80-cap95 | validation-4800-8400 | 91390 | 0 | 6405 | 73 | 21.0 |
| validation-depth-size80-skew025 | validation-4800-8400 | 88336 | 0 | 6393 | 76 | 20.9 |
| validation-depth-size80-weight10 | validation-4800-8400 | 89161 | 0 | 6692 | 80 | 21.2 |
| validation-depth-size80-width025 | validation-4800-8400 | 83667 | 0 | 5433 | 77 | 21.1 |
| validation-depth-size95-cap100-skew01 | validation-4800-8400 | 104159 | 0 | 7012 | 92 | 21.1 |
| validation-depth-size95-cap95-skew01 | validation-4800-8400 | 101166 | 0 | 7142 | 95 | 21.3 |
| validation-depth-size95-cap95-skew02 | validation-4800-8400 | 98501 | 0 | 6377 | 88 | 21.3 |
| validation-depth-size95-cap95-skew03 | validation-4800-8400 | 91136 | 0 | 5833 | 79 | 21.2 |
| validation-flow-depth-size40 | validation-4800-8400 | 60774 | 0 | 7691 | 48 | 21.3 |
| validation-flow-depth-size80-cap95 | validation-4800-8400 | 93048 | 0 | 6525 | 77 | 21.1 |
| validation-mid-size100-cap100-skew01 | validation-4800-8400 | 90639 | 0 | 7399 | 100 | 20.9 |
| validation-mid-size2-skew05 | validation-4800-8400 | 3402 | 0 | 6902 | 2 | 21.8 |
| validation-mid-size40-skew02 | validation-4800-8400 | 53306 | 0 | 7975 | 51 | 21.8 |
| validation-mid-size80-skew02 | validation-4800-8400 | 81461 | 0 | 6781 | 80 | 21.0 |
| validation-queue-topup | validation-4800-8400 | 78072 | 0 | 6927 | 61 | 22.8 |
| validation-queue95 | validation | 106617 | 0 | 7248 | 94 | 22.5 |
| validation-ridge-size | validation-4800-8400 | 77577 | 0 | 6835 | 60 | 27.1 |
| validation-ridge-topup-hybrid | validation-4800-8400 | 78933 | 0 | 7049 | 60 | 26.4 |
| validation-ridge-topup95 | validation | 106580 | 0 | 7330 | 91 | 27.5 |
| whole-public-depth_inventory_maker | whole-public | 333188 | 0 | 23222 | 100 | 35.7 |
| whole-public-incumbent-scaffold | benchmark-incumbent-no-selection | 11206 | 0 | 22716 | 3 | 33.9 |
| whole-public-queue_retention_maker | whole-public | 343269 | 0 | 23979 | 100 | 38.8 |
| whole-public-ridge_queue_hybrid | whole-public | 344437 | 0 | 24076 | 100 | 56.9 |

Mirrored/shifted stress data are not the original public tape and cannot define its best score. Earlier unclean ridge records are historical; only the corrected retained file is a candidate.

Window runs preserve all earlier market rows for warmup but start with zero user inventory. **Do not sum window PnLs to invent the whole-tape score.** Whole files were tested separately.

The unchanged2-lot scaffold scored11206 on the whole public tape. Capacity scaling explains a large fraction of improvement; no claim that it is all novel alpha.

One-arm pnl_se is not a paired-delta SE. Return normality/ACF/variance-ratio/Hurst results are descriptive/ref-test evidence, not an identified exact law. ADF-style t statistics do not include a calibrated MacKinnon p-value.
