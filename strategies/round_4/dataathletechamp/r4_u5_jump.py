"""R4 U5 candidate: U2 + latent-jump onset trigger, baked JMP_ON True, W 20 ms, K 3, spread <= 1, mode "both"
(ungated flip + burst to +-300 for 50 ms, IOC cap 5), experiment 20261108-r4-jump-onset-001 variant
x_w20_n300_c5_h50. Runner (official engine): R4 912,274 / R3 407,508 / R2 152,088 (U2 886,626 / 415,404 /
159,515); breach penalty included (R4 4,488). Setting JMP_ON False reproduces U2 exactly.

Research file r4_follower_jump.py with these defaults baked; flag description follows.

R4 U2 + latent-jump onset trigger (JMP_*), experiment 20261108-r4-jump-onset-001.

Copy of r4_follower_hidden.py (sha256 a94f9585...) plus JMP_* flags; JMP_ON False (and all HID_* off)
reproduces U2 (r4_u2_trig2_ungated.py) exactly. Mechanism (knowledge note r4-jump-onset.md): when the latent
price jumps, the jump's far-side new G orders land > 20 ticks behind their own best (invisible, each one an
order-id gap) and its near-side new orders pile in at / inside the touch. Live detector:
  gap sum: hidden inserts (order-id gaps from the HID detector) revealed within the last JMP_WIN_MS;
  trigger: gap sum >= JMP_K at a callback that reveals a new gap, first per JMP_COOLDOWN_MS (the cooldown is
           consumed by the first trigger even when the filters below skip it, as in the offline study);
  filter:  JMP_MAX_SPREAD > 0 -> act only if the market spread of the PREVIOUS snapshot (before the
           gap-revealing insert) is <= JMP_MAX_SPREAD;
  direction: sign of the visible near-touch insert imbalance over the same window (new market resting
           inserts at <= 1 tick behind their own best of the previous snapshot: bid +1, ask -1, inside the
           spread x2); 0 -> skip.
  JMP_MODE "flip":  ungated follower signal (target d * LOTS); IOCs in direction d use limit touch +- JMP_CAP
                    for JMP_CAP_MS.
           "burst": target d * JMP_N for JMP_H_MS (IOC limit touch +- JMP_CAP, building only during the first
                    JMP_BUILD_MS if > 0), then IOC unwind to the follower target (HID_BURST machinery); pays
                    the 10,000/s penalty while |inventory| > 100.
           "both":  flip + burst.
  JMP_BURST_K / JMP_BURST_IMB > 0: the burst part only fires when the trigger's hidden sum >= JMP_BURST_K and
           |imbalance| >= JMP_BURST_IMB (strong onsets); the flip part is unaffected.
  JMP_CONFIRM_MS > 0: end the burst early (IOC unwind) unless the mid moved >= JMP_CONFIRM_TICKS in the jump
           direction within JMP_CONFIRM_MS of the trigger.
  JMP_GAP_EXACT: count hidden ids as (largest new id - previous max) - distinct visible new ids per callback.

Previous header (r4_follower_hidden.py):
R4 U2 + hidden-IOC (market order-ID gap) triggers, experiment 20261108-r4-w6-hidden-001.

All HID_* flags off reproduces U2 (r4_u2_trig2_ungated.py) exactly. Live detector (knowledge note
r4-hidden-ioc-precursor.md): track the max market order id seen among visible snapshot orders and market
trades' taker ids; when the smallest new id of an event > max_id + 1, (lo - max_id - 1) inserts were
invisible since the last visible insert (97% hidden non-trading IOCs). The book part reuses the TRIG2 scan.
  HID_ARM:   for HID_ARM_MS after a detection, a market taker sweep against our target (fill span >=
             HID_ARM_SPAN ticks or filled >= HID_ARM_FILL) is an A event (P1 gate if HID_ARM_GATED).
  HID_FLOW:  on a detection, |signed market-taker flow over the prior HID_FLOW_WIN_MS| >= HID_FLOW_F
             signals in the flow direction (P1 gate if HID_FLOW_GATED).
  HID_BURST: >= HID_BURST_K detections within HID_BURST_WIN_MS and |prior flow| >= HID_BURST_F -> target
             +-HID_BURST_N in the flow direction for HID_BURST_H_MS (IOC both ways, limit touch +-
             HID_BURST_CAP), then back to the follower's +-LOTS target. Breaches +-100: pays the penalty.

U2 description (unchanged):
R4 U2: U7 + TRIG2 (G-insert class hidden-price trigger, THR 0.95, ungated) + HOLD_S 10.
R4 public 886,626 (U7 821,692); R3 415,404 (413,588); R2 159,515 (167,166). Bet on R4-like tapes.

U7 + TRIG2 (hidden-price G-insert estimator trigger, flag TRIG2_ON, default False = U7 exactly).

TRIG2 (experiment 20261108-r3-w8-trig2-001, rule from 20261108-r3-w6-latent-filter-001): each new
resting market insert gets z = side * T2_ITAB[class] (implied 1 s mid drift, R3 fit-half table; class =
side, ticks behind own best before the event k clipped [-3, 7], prior spread clipped [1, 3]).
G_meanz = mean z over the last TRIG2_WIN_MS. |G_meanz| >= TRIG2_THR with the same sign for >= TRIG2_HOLD_MS
fires _on_signal(t, sign, TRIG2_GATED) once per run (lower priority than A / FLOW / TRIG1 events).

U7: U6 (pooled no-intercept alpha refit, A_SWEEP 3) + TRIG1 deep-FV flow trigger + FLOW_TRIG 600.

Official engine: R3 public 413,588 (U6 357,488), R2 public 167,166 (U6 107,856), penalty 0.
FLOW_TRIG: |signed market-taker volume over FLOW_WIN_US| >= FLOW_TRIG acts as an A event of that sign.
TRIG1 = False and FLOW_TRIG = 0 reproduce U6 exactly.

U6 base description:
R3 informed follower D1 + alpha flip gate + A_SWEEP 3, alpha REFIT on pooled full R3 + R2 public.

U6 candidate copy of r3_alpha_follower_p1_sw3_refit.py with defaults MODEL "rlin0" (pooled ridge,
intercept 0) and FLIP_MARGIN 1.0: R3 357,488, R2 107,856 (in-sample), R1 -105,152. The refit file's own
default was MODEL "rsym" (mirror-symmetric ridge, zero intercept, h = 2 s) and FLIP_MARGIN 1.2; U4 behaviour
= MODEL "lin", FLIP_MARGIN 1.0. Official engine: R3 307,228, R2 119,847 (both in-sample), R1 -72,584
Plus TRIG1 deep-FV flow trigger ported from r3_follower_deepfv.py (flow 300, FV 0.5, gated by default).

TRIG1 (experiment 20261108-r3-w7-deepfv-001): long when the net market-taker fill volume over
the last TRIG1_WIN_MS (taker buy +) >= TRIG1_FLOW and the mean of (new resting market insert
price - mid just before the event) over the same window, both sides, ALL visible depth, is
>= TRIG1_FV ticks; short mirrored. Edge-triggered (fires when the condition starts holding in a
direction); handled exactly like an A event of that sign (entry / hold extension / flip). The
P1 alpha gate applies to TRIG1 flips unless TRIG1_GATED is False. TRIG1 = False reproduces
r3_alpha_follower_p1_sw3.py exactly (the deep scan keeps its own max id).

Base description (unchanged):
R3 informed follower D1 + alpha flip gate (P1, lin, FLIP_MARGIN 1.0) + A_SWEEP 3 by default.

Same code as r3_alpha_follower_p1.py plus one flag: A_SWEEP sets the sweep span that triggers
a trade (default 3; 2 reproduces P1 exactly). Model features keep the original >= 2 definition.
R3 public 330,208 (P1 318,172; D1 270,035); R2 public 109,317 (P1 73,799; D1 26,175).

Default flags reproduce D1 exactly (POLICY = "d1"): signal A per market taker order
(same-sign run position >= 4 and filled >= 100, or fill span >= 2 ticks, or filled >= 500);
A -> target +-LOTS via IOC at the touch; same-sign A extends a 5 s hold; opposite A flips
(IOC limit touch -+ 3); deadline -> join exit-side touch for 1 s, then IOC.

The alpha model (frozen constants fitted on R3 public t < 2400 s, see the knowledge note
r3-alpha-model.md) predicts the mid change over ALPHA_H seconds in ticks from O(1) live
features. It only changes D1 decisions:
  p1: an opposite A flips only if alpha * new_sign > FLIP_MARGIN, else it is ignored
  p2: from flat, enter on the 50 ms grid when |alpha| > ENTRY_MARGIN even without A
  p3: in position, alpha * side > EXT_MARGIN extends the hold to >= EXT_HOLD_S;
      alpha * side < EXIT_MARGIN exits early (join-touch exit)
  p4: p1 + p3
FV rules inside D1 (any POLICY; same IOC execution): V1 FV_FLIP pre-emptive flip, V2 FV_HOLD
hold extension, V3 FV_ENTRY entry from flat (spread-capped); V4 = V1 + V2.
MODEL "sym" is a mirror-symmetric ridge (alpha(mirror x) = -alpha(x), zero intercept),
which removes the directional drift bias a plain ridge can learn from one tape.
Execution is D1's. Exposure incl. pending orders never exceeds LOTS (sends that would
break it are skipped and counted).
"""

import math
from collections import deque

from simulator.models import OrderRequest, OrderStatus, OrderType, Side
from simulator.strategy import BaseStrategy

LOTS = 100
HOLD_S = 10.0
RUN_MIN = 4
FILL_MIN = 100
BIG_FILL = 500
A_SWEEP = 3  # trade-trigger sweep span (features keep the >= 2 definition)
TOUCH_WAIT_S = 1.0
EXIT_CAP = 3
ENTRY_CAP = 0
POLICY = "p1"  # d1 | p1 | p2 | p3 | p4
MODEL = "rlin0"  # lin | sym | tree (R3 t < 2400 s fits) | rlin | rlin0 | rsym (pooled full R3 + R2 refits)
FLOW_TRIG = 600  # >0: |signed market-taker volume over FLOW_WIN_US| >= FLOW_TRIG acts as an A event
FLOW_WIN_US = 200_000
FLIP_MARGIN = 1.0  # ticks over ALPHA_H
ENTRY_MARGIN = 2.0
EXT_MARGIN = 1.0
EXT_HOLD_S = 2.0
EXIT_MARGIN = -1.0
ALPHA_DT_MS = 50
FEATURES_ON = False  # compute features even for d1 (research recorder)
FV_DEPTH = 2  # ticks from each touch scanned for new market inserts (insert-implied FV, insert counts)
FV_FLIP = 0.0  # V1: >0 -> holding and FV50 opposes the position by >= FV_FLIP ticks -> flip now
FV_HOLD = 0.0  # V2: >0 -> while FV50 agrees with the position by >= FV_HOLD, the deadline cannot expire
FV_ENTRY = 0.0  # V3: >0 -> from flat enter when |FV50| >= FV_ENTRY and spread <= FV_ENTRY_SPREAD
FV_ENTRY_SPREAD = 2
FV_TAKERS = False  # True -> market taker fills also enter the FV windows (buy: max fill as a bid insert)
TRIG1 = True  # deep insert-implied FV + taker flow trigger (see module docstring); False = U4 exactly
TRIG1_FLOW = 300  # lots of net market-taker volume in the window (taker buy +)
TRIG1_FV = 0.5  # ticks: mean (insert price - prior mid) over new resting market inserts in the window
TRIG1_WIN_MS = 200
TRIG1_GATED = True  # True -> TRIG1 flips must pass the P1 alpha gate like A flips; False -> bypass
TRIG2_ON = True  # hidden-price G-insert estimator trigger (see module docstring); False = U7 exactly
TRIG2_THR = 0.95  # ticks of mean implied 1 s drift over the window
TRIG2_HOLD_MS = 20  # condition must hold (same sign, evaluated at events) this long before firing
TRIG2_WIN_MS = 100
TRIG2_GATED = False  # True -> TRIG2 flips must pass the P1 alpha gate; False -> bypass
# Hidden-IOC order-ID gap triggers (module docstring); all False = U2 exactly.
HID_ARM = False
HID_ARM_MS = 200
HID_ARM_SPAN = 1  # ticks of taker fill span (max - min fill price)
HID_ARM_FILL = 200  # or lots filled by the taker
HID_ARM_FLAT = True  # True -> while armed and flat, a qualifying sweep also enters
HID_ARM_GATED = True
HID_FLOW = False
HID_FLOW_F = 200  # lots of |net market-taker flow| (taker buy +) over HID_FLOW_WIN_MS before the detection
HID_FLOW_WIN_MS = 200
HID_FLOW_GATED = True
HID_FLOW_DIR = "flow"  # flow: sign of the window flow (needs |flow| >= F) | a_flow_mid: last A-like sweep
# within HID_A_WIN_MS, else flow sign, else 200 ms mid move (|flow| >= F only if F > 0)
HID_FLOW_STRONG = False  # True -> HID_FLOW fires only on strong events (gap >= HID_GAP_STRONG or cluster)
HID_A_WIN_MS = 1000
HID_MID_WIN_MS = 200
HID_GAP_STRONG = 2  # one ID gap hiding >= this many inserts is a strong event
HID_BURST = False
HID_BURST_K = 3  # detection events within HID_BURST_WIN_MS (inclusive of the current one)
HID_BURST_WIN_MS = 300
HID_BURST_F = 200
HID_BURST_N = 300
HID_BURST_H_MS = 200
HID_BURST_CAP = 3
HID_BURST_STRONG = False  # True -> trigger on strong events (gap >= HID_GAP_STRONG or >= K in window), no flow
HID_BURST_DIR = "flow"  # flow: window flow sign | a_mid: last A-like sweep within HID_A_WIN_MS, else mid move
# Latent-jump onset trigger (module docstring); JMP_ON False = U2 exactly. Requires TRIG2_ON (shared scan).
JMP_ON = True
JMP_WIN_MS = 20  # window for the hidden-insert sum and the near-touch insert imbalance
JMP_K = 3  # hidden inserts (order-id gap sizes) within the window
JMP_COOLDOWN_MS = 1000
JMP_MAX_SPREAD = 1  # > 0: act only if the previous snapshot's market spread <= this (ticks); 0 = off
JMP_MODE = "both"  # flip | burst | both
JMP_CAP = 5  # ticks beyond the touch for jump IOCs (flip / burst build / burst unwind)
JMP_CAP_MS = 50  # flip: IOCs in the jump direction use JMP_CAP for this long after the trigger
JMP_N = 300  # burst target size
JMP_H_MS = 50  # burst hold
JMP_BUILD_MS = 0  # > 0: the burst only builds during this many ms after the trigger, then holds; 0 = whole hold
JMP_BURST_K = 0  # > 0: the burst part needs the trigger's hidden sum >= this (flip part unaffected); 0 = JMP_K
JMP_BURST_IMB = 0  # > 0: the burst part needs |near-touch imbalance| >= this at the trigger
JMP_GAP_EXACT = False  # True: hidden count per callback = (largest new id - previous max id) - distinct visible
# new ids in the callback (also counts ids hidden between two visible inserts of one callback); False: the HID
# detector's (smallest new id - previous max id - 1)
JMP_CONFIRM_MS = 0  # > 0: end the burst early (unwind) if, this long after the trigger, the mid has not moved
JMP_CONFIRM_TICKS = 2.0  # at least this many ticks in the jump direction; 0 = off
# 66-cell class table: index (side==bid)*33 + (k+3)*3 + (min(spread,3)-1); value = 1 s drift toward the
# insert's side (R3 public fit half [60, 3000) s; cells with n < 200 set to 0). final_model.json["itab"].
T2_ITAB = (
    0.0, 0.0, 0.0, 0.0, 0.0, 2.417, 0.0, 1.086, -0.165, 0.691, 0.216, 0.602, -0.185, -0.19, -0.48,
    -0.257, -0.287, -0.995, -0.621, -0.611, -0.564, -1.399, -0.68, -1.412, -1.957, -0.801, -1.869,
    -2.259, -0.618, -0.979, -2.275, -0.812, -1.418,
    0.0, 0.0, 0.0, 0.0, 0.0, 2.206, 0.0, 1.107, 0.649, 0.547, 0.226, 0.139, -0.196, -0.366, -0.002,
    -0.382, -0.325, -0.575, -0.941, -0.52, -1.125, -1.808, -0.619, -1.078, -2.784, -0.73, -1.764,
    -3.172, -0.694, -1.733, -3.77, -0.583, -1.61,
)

FEATURE_NAMES = (
    "ev_a",
    "ev_run",
    "ev_fill",
    "ev_span",
    "a1",
    "a5",
    "as2",
    "sw1",
    "ta_pos",
    "ta_neg",
    "arate",
    "fv20",
    "fv50",
    "fv200",
    "ib50",
    "ia50",
    "ib200",
    "ia200",
    "last_side",
    "fl02",
    "fl1",
    "fl5",
    "qi",
    "spread",
    "dsign",
)

# BEGIN MODEL (frozen; fitted on R3 public t < 2400 s; regenerated by fit_alpha.py)
ALPHA_H = 2.0
LIN_B = -0.1636
LIN_COEF = (2.7e-05, 0.132874, -0.002752, 0.612848, 0.600416, -0.343892, -0.32632, 0.97516, -1.259597, 0.228259, -0.362184, 0.004549, 0.388523, 0.431737, 0.552822, -1.006421, 0.322181, 0.285618, 0.197824, 0.967262, 1.227504, -0.41272, 0.202175, 0.362252, 0.275728)
LIN_LO = (-1.0, -10.0, -13.6351, -3.0, -4.102208, -7.976761, -4.175055, -2.974284, 0.0, 0.0, 0.048635, -1.5, -2.0, -3.0, 0.0, 0.0, 0.0, 0.0, -1.0, -2.244627, -3.624127, -5.894347, -0.99893, 1.0, -1.0)
LIN_HI = (1.0, 10.0, 12.8363, 2.0, 4.171324, 8.385785, 3.935529, 2.748214, 1.0, 1.0, 1.459869, 1.5, 2.0, 3.0, 1.840752, 1.847885, 4.569958, 4.551416, 1.0, 1.799149, 2.649841, 4.380143, 0.999127, 7.0, 1.0)
TREE_FEAT = (19, 7, 14, 5, 19, 5, -1, -1, 23, -1, -1, -1, 21, -1, -1, 10, 7, 23, 19, -1, -1, -1, 10, 10, -1, -1, -1, 5, -1, -1, 5, 10, 10, 4, -1, 4, -1, -1, 10, -1, -1, 14, -1, 6, -1, -1, 19, 21, 10, 24, -1, -1, 16, -1, -1, 7, -1, 5, -1, -1, 7, 10, 7, -1, -1, 21, -1, -1, 21, 10, -1, -1, -1)
TREE_THR = (-0.012193, -0.301113, 0.000147, -0.389919, -0.173888, -4.357226, -2.0, -2.0, 1.5, -2.0, -2.0, -2.0, -1.108011, -2.0, -2.0, 1.334879, 0.094858, 2.5, -0.142096, -2.0, -2.0, -2.0, 1.151252, 1.036332, -2.0, -2.0, -2.0, 0.394969, -2.0, -2.0, -2.227564, 1.060291, 0.922409, -0.746707, -2.0, -0.282279, -2.0, -2.0, 0.971005, -2.0, -2.0, 8e-06, -2.0, -0.928685, -2.0, -2.0, 0.188739, -0.665223, 1.056672, 0.5, -2.0, -2.0, 0.01528, -2.0, -2.0, -0.148743, -2.0, 1.72409, -2.0, -2.0, 0.521145, 1.051494, -0.005101, -2.0, -2.0, -0.166478, -2.0, -2.0, 2.026765, 1.046868, -2.0, -2.0, -2.0)
TREE_LEFT = (1, 2, 3, 4, 5, 6, -1, -1, 9, -1, -1, -1, 13, -1, -1, 16, 17, 18, 19, -1, -1, -1, 23, 24, -1, -1, -1, 28, -1, -1, 31, 32, 33, 34, -1, 36, -1, -1, 39, -1, -1, 42, -1, 44, -1, -1, 47, 48, 49, 50, -1, -1, 53, -1, -1, 56, -1, 58, -1, -1, 61, 62, 63, -1, -1, 66, -1, -1, 69, 70, -1, -1, -1)
TREE_RIGHT = (30, 15, 12, 11, 8, 7, -1, -1, 10, -1, -1, -1, 14, -1, -1, 27, 22, 21, 20, -1, -1, -1, 26, 25, -1, -1, -1, 29, -1, -1, 46, 41, 38, 35, -1, 37, -1, -1, 40, -1, -1, 43, -1, 45, -1, -1, 60, 55, 52, 51, -1, -1, 54, -1, -1, 57, -1, 59, -1, -1, 68, 65, 64, -1, -1, 67, -1, -1, 72, 71, -1, -1, -1)
TREE_VALUE = (-0.119871, -0.991804, -2.864087, -3.580596, -3.098084, -4.077035, -2.436916, -4.706401, -1.761387, -2.270888, -0.992307, -6.479138, -1.021094, -0.390799, -2.128701, -0.714261, -0.589629, -0.496439, -0.565917, -0.884907, -0.353243, 2.099303, -1.639105, -1.09076, -1.440329, -0.184389, -3.669173, -4.589391, -2.313487, -6.599019, 0.619711, 2.390296, 1.095426, 0.711523, 0.432053, 0.85353, 0.748751, 1.021804, 1.712806, 2.351681, 1.270337, 4.901441, 2.810682, 5.819001, 5.004679, 6.869477, 0.413008, 0.138917, 0.884837, 0.646557, 0.477303, 0.967095, 1.663743, 0.678835, 2.287673, -0.028648, -1.688271, 0.038676, 0.198723, -0.456703, 1.136113, 0.816589, 0.579135, 1.492457, 0.499062, 1.771272, 2.657625, 1.401613, 2.721414, 3.191799, 1.964067, 3.967209, 1.679846)
# END MODEL
# BEGIN SYM MODEL (frozen mirror-symmetric ridge, h = 2 s; fitted on R3 public t < 2400 s; fit_alpha_sym.py)
SYM_COEF = (0.015832, 0.137872, -0.007728, 0.57541, 0.56144, -0.342443, -0.350385, 1.008111, -0.618157, 0.618157, 0.0, 0.01909, 0.389793, 0.432763, 0.75553, -0.75553, 0.034602, -0.034602, 0.196517, 0.991925, 1.137293, -0.352844, 0.191969, 0.0, 0.257552)
SYM_LO = (-1.0, -10.0, -17.33, -3.0, -4.451746, -8.567125, -4.362877, -3.132839, 0.0, 0.0, 0.048627, -2.0, -2.0, -4.0, 0.0, 0.0, 0.0, 0.0, -1.0, -2.541322, -3.774192, -5.936242, -0.999335, 1.0, -1.0)
SYM_HI = (1.0, 10.0, 17.33, 3.0, 4.451746, 8.567125, 4.362877, 3.132839, 1.0, 1.0, 1.459896, 2.0, 2.0, 4.0, 1.84846, 1.84846, 4.566767, 4.566767, 1.0, 2.541322, 3.774192, 5.936242, 0.999335, 7.0, 1.0)
# END SYM MODEL
# BEGIN REFIT MODELS (frozen ridge h = 2 s, pooled FULL R3 public + FULL R2 public; refit/fit_pooled.py)
RLIN_B = 0.231186
RLIN_COEF = (0.012998, 0.097964, -0.00566, 0.740379, -0.024305, -0.128793, -0.065937, 0.103195, -0.188355, -0.02178, -0.61115, 0.065696, 0.353405, 0.567624, 0.50469, -0.714737, 0.229604, 0.042376, 0.13988, 1.410207, 0.403164, -0.079392, 0.048541, 0.21401, 0.056383)
RLIN_LO = (-1.0, -10.0, -13.55042, -3.0, -4.179031, -8.503733, -4.096269, -2.806923, 0.0, 0.0, 0.080534, -1.5, -2.0, -3.5, 0.0, 0.0, 0.0, 0.0, -1.0, -1.933809, -3.048565, -5.563245, -0.999088, 1.0, -1.0)
RLIN_HI = (1.0, 10.0, 13.59521, 2.0, 4.0089, 8.005595, 3.87575, 2.694892, 1.0, 1.0, 1.640592, 1.5, 2.0, 3.5, 1.859315, 1.919202, 4.433524, 4.703781, 1.0, 1.815717, 2.75295, 4.861557, 0.999052, 7.0, 1.0)
RLIN0_COEF = (0.013724, 0.097982, -0.005837, 0.742574, -0.027209, -0.126858, -0.065188, 0.103508, -0.163388, 0.00305, -0.405961, 0.06637, 0.353393, 0.567864, 0.529177, -0.690916, 0.205106, 0.017536, 0.139762, 1.410512, 0.404159, -0.081439, 0.048651, 0.22884, 0.057256)
RSYM_COEF = (0.006714, 0.099397, -0.008696, 0.746853, -0.043316, -0.123017, -0.071173, 0.105859, -0.056848, 0.056848, 0.0, 0.080547, 0.340283, 0.571138, 0.611341, -0.611341, 0.101074, -0.101074, 0.140542, 1.381149, 0.414266, -0.083201, 0.051236, 0.0, 0.055317)
RSYM_LO = (-1.0, -10.0, -16.799999, -3.0, -4.495482, -8.844574, -4.44739, -3.092388, 0.0, 0.0, 0.08053, -2.0, -2.0, -5.0, 0.0, 0.0, 0.0, 0.0, -1.0, -2.223761, -3.314195, -5.654811, -0.999342, 1.0, -1.0)
RSYM_HI = (1.0, 10.0, 16.799999, 3.0, 4.495482, 8.844574, 4.44739, 3.092388, 1.0, 1.0, 1.640622, 2.0, 2.0, 5.0, 1.893206, 1.893206, 4.57211, 4.57211, 1.0, 2.223761, 3.314195, 5.654811, 0.999342, 7.0, 1.0)
# END REFIT MODELS


class Ema:
    def __init__(self, tau_s: float) -> None:
        self.tau = tau_s * 1e6
        self.v = 0.0
        self.t = 0

    def add(self, t: int, x: float) -> None:
        if t != self.t:
            self.v *= math.exp(-(t - self.t) / self.tau)
            self.t = t
        self.v += x

    def get(self, t: int) -> float:
        if t == self.t:
            return self.v
        return self.v * math.exp(-(t - self.t) / self.tau)


class AlphaFollower(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.L = int(LOTS)
        self.hold = int(HOLD_S * 1e6)
        self.policy = POLICY
        self.model = MODEL
        self.flip_margin = float(FLIP_MARGIN)
        self.entry_margin = float(ENTRY_MARGIN)
        self.ext_margin = float(EXT_MARGIN)
        self.ext_hold = int(EXT_HOLD_S * 1e6)
        self.exit_margin = float(EXIT_MARGIN)
        self.alpha_dt = int(ALPHA_DT_MS * 1000)
        self.touch_wait = int(TOUCH_WAIT_S * 1e6)
        self.gate_flip = POLICY in ("p1", "p4")
        self.grid_entry = POLICY == "p2"
        self.grid_hold = POLICY in ("p3", "p4")
        self.fv_depth = int(FV_DEPTH)
        self.fv_flip = float(FV_FLIP)
        self.fv_hold = float(FV_HOLD)
        self.fv_entry = float(FV_ENTRY)
        self.fv_entry_spread = int(FV_ENTRY_SPREAD)
        self.fv_takers = bool(FV_TAKERS)
        self.fv_on = bool(self.fv_flip > 0 or self.fv_hold > 0 or self.fv_entry > 0)
        self.feat = bool(FEATURES_ON or POLICY != "d1" or self.fv_on)
        self.pos = 0
        self.orders: dict = {}  # oid -> [sign, remaining, kind, price, send_mid]
        self.cancelling: set = set()
        self.target = 0
        self.deadline = 0
        self.last_sign = 0
        self.run = 0
        self.wait_until = 0
        self.mid = 0.0
        self.next_alpha_t = 0
        # features
        self.e_a1 = Ema(1.0)
        self.e_a5 = Ema(5.0)
        self.e_as2 = Ema(2.0)
        self.e_sw1 = Ema(1.0)
        self.e_f02 = Ema(0.2)
        self.e_f1 = Ema(1.0)
        self.e_f5 = Ema(5.0)
        self.e_rate = Ema(120.0)
        self.e_ib50 = Ema(0.05)
        self.e_ia50 = Ema(0.05)
        self.e_ib200 = Ema(0.2)
        self.e_ia200 = Ema(0.2)
        self.t_apos = -(10**12)
        self.t_aneg = -(10**12)
        self.ev = (0, 0, 0, 0, 0)  # sign of last A, run, fill, span, sign of last taker (this event)
        self.ev_taker = 0  # 0 none, 1 A, 2 other market taker in this event
        self.last_side = 0
        self.max_id = 0
        self.bins: deque = deque()
        self.ains: deque = deque()
        self.qi = 0.0
        self.spread = 0
        self.prev_bid = 0
        self.prev_ask = 0
        self.vsign = 0  # virtual D1 target sign (feature)
        self.vdead = 0
        self.alpha = 0.0
        # stats
        self.n_A = 0
        self.flow = deque()
        self.flow_sum = 0
        self.n_entry = 0
        self.n_flip = 0
        self.n_ignored = 0
        self.n_alpha_entry = 0
        self.n_ext = 0
        self.n_early_exit = 0
        self.n_skip_send = 0
        self.n_fv_flip = 0
        self.n_fv_hold = 0
        self.n_fv_entry = 0
        self.fill_stats: dict = {}
        # TRIG1 state
        self.trig1 = bool(TRIG1)
        self.t1_flow = int(TRIG1_FLOW)
        self.t1_fv2 = 2.0 * float(TRIG1_FV)  # samples are stored as 2 * (price - mid) integers
        self.t1_win = int(TRIG1_WIN_MS * 1000)
        self.t1_gated = bool(TRIG1_GATED)
        self.t1_flow_q: deque = deque()
        self.t1_flow_sum = 0
        self.t1_ins_q: deque = deque()
        self.t1_ins_sum = 0
        self.t1_max_id = 0
        self.t1_prev_b = None
        self.t1_prev_a = None
        self.t1_state = 0
        self.n_t1 = 0
        self.n_t1_entry = 0
        self.n_t1_flip = 0
        self.n_t1_ext = 0
        self.n_t1_ignored = 0
        self.n_t1_scans = 0
        # TRIG2 state
        self.trig2 = bool(TRIG2_ON)
        self.t2_thr = float(TRIG2_THR)
        self.t2_hold = int(TRIG2_HOLD_MS * 1000)
        self.t2_win = int(TRIG2_WIN_MS * 1000)
        self.t2_gated = bool(TRIG2_GATED)
        self.t2_q: deque = deque()
        self.t2_sum = 0.0
        self.t2_max_id = 0
        self.t2_prev_b = None
        self.t2_prev_a = None
        self.t2_pb = 0
        self.t2_pa = 0
        self.t2_dir = 0
        self.t2_t0 = 0
        self.t2_fired = False
        self.n_t2 = 0
        self.n_t2_entry = 0
        self.n_t2_flip = 0
        self.n_t2_ext = 0
        self.n_t2_ignored = 0
        self.n_t2_ins = 0
        # hidden-IOC detector state
        self.h_arm = bool(HID_ARM)
        self.h_flow_on = bool(HID_FLOW)
        self.h_burst = bool(HID_BURST)
        self.jmp_on = bool(JMP_ON)
        self.hid_on = bool(self.h_arm or self.h_flow_on or self.h_burst or self.jmp_on)
        self.h_arm_ms = int(HID_ARM_MS * 1000)
        self.h_arm_span = int(HID_ARM_SPAN)
        self.h_arm_fill = int(HID_ARM_FILL)
        self.h_arm_flat = bool(HID_ARM_FLAT)
        self.h_arm_gated = bool(HID_ARM_GATED)
        self.h_flow_f = int(HID_FLOW_F)
        self.h_flow_win = int(HID_FLOW_WIN_MS * 1000)
        self.h_flow_gated = bool(HID_FLOW_GATED)
        self.h_burst_k = int(HID_BURST_K)
        self.h_burst_win = int(HID_BURST_WIN_MS * 1000)
        self.h_burst_f = int(HID_BURST_F)
        self.h_burst_n = int(HID_BURST_N)
        self.h_burst_h = int(HID_BURST_H_MS * 1000)
        self.h_burst_cap = int(HID_BURST_CAP)
        self.h_flow_dir = str(HID_FLOW_DIR)
        self.h_flow_strong = bool(HID_FLOW_STRONG)
        self.h_burst_strong = bool(HID_BURST_STRONG)
        self.h_burst_dir = str(HID_BURST_DIR)
        if self.h_flow_dir not in ("flow", "a_flow_mid") or self.h_burst_dir not in ("flow", "a_mid"):
            raise ValueError("unknown HID_FLOW_DIR / HID_BURST_DIR")
        self.h_a_win = int(HID_A_WIN_MS * 1000)
        self.h_mid_win = int(HID_MID_WIN_MS * 1000)
        self.h_gap_strong = int(HID_GAP_STRONG)
        self.h_a_t = -(10**12)  # time / sign of the last A-like market taker (features' is_a definition)
        self.h_a_s = 0
        self.h_mq: deque = deque()  # (t, mid) at mid changes
        self.h_max_id = 0
        self.h_lo = 0  # smallest / largest new market id seen since the last evaluation (0 = none)
        self.h_hi = 0
        self.h_fq: deque = deque()
        self.h_fsum = 0
        self.h_dq: deque = deque()
        self.h_arm_until = 0
        self.b_until = 0
        self.b_sign = 0
        self.b_n = self.h_burst_n  # active burst size / IOC cap / order label (HID_BURST or JMP burst)
        self.b_cap = self.h_burst_cap
        self.b_kind = "ioc_burst"
        self.b_build_until = 0
        self.h_kind = ""
        self.h_stats: dict = {}
        # latent-jump onset state
        self.j_win = int(JMP_WIN_MS * 1000)
        self.j_k = int(JMP_K)
        self.j_cool = int(JMP_COOLDOWN_MS * 1000)
        self.j_max_spread = int(JMP_MAX_SPREAD)
        self.j_mode = str(JMP_MODE)
        if self.j_mode not in ("flip", "burst", "both"):
            raise ValueError("unknown JMP_MODE")
        if self.jmp_on and not self.trig2:
            raise ValueError("JMP_ON needs TRIG2_ON (the near-touch imbalance reuses the TRIG2 scan)")
        self.j_cap = int(JMP_CAP)
        self.j_cap_ms = int(JMP_CAP_MS * 1000)
        self.j_n = int(JMP_N)
        self.j_h = int(JMP_H_MS * 1000)
        self.j_build = int(JMP_BUILD_MS * 1000)
        self.j_bk = int(JMP_BURST_K)
        self.j_bimb = int(JMP_BURST_IMB)
        self.j_exact = bool(JMP_GAP_EXACT)
        self.j_conf = int(JMP_CONFIRM_MS * 1000)
        self.j_conf_ticks = float(JMP_CONFIRM_TICKS)
        self.j_bpending = False
        self.j_bt0 = 0
        self.j_bmid0 = 0.0
        self.h_newset: set = set()  # distinct visible new market ids of the current callback (JMP_GAP_EXACT)
        self.j_strong = False
        self.j_q: deque = deque()  # (t, gap size) at gap-revealing callbacks
        self.j_sum = 0
        self.j_iq: deque = deque()  # (t, weight) near-touch visible inserts
        self.j_isum = 0
        self.j_sp = 0  # market spread of the previous snapshot (0 = unknown)
        self.j_last = -(10**15)
        self.j_sig = 0
        self.j_sign = 0
        self.j_cap_until = 0
        self.j_chk: deque = deque()  # [due_t, horizon_ms, record index]
        self.j_recs: list = []
        self.j_stats: dict = {}

    # ---------------- helpers
    def _send(self, sign: int, qty: int, price: int, kind: str, ioc: bool, cap: int = 0) -> None:
        if qty <= 0 or price <= 0:
            return
        lim_ = cap if cap else self.L
        buys = 0
        sells = 0
        for o in self.orders.values():
            if o[0] > 0:
                buys += o[1]
            else:
                sells += o[1]
        if sign > 0:
            buys += qty
        else:
            sells += qty
        if self.pos + buys > lim_ or sells - self.pos > lim_:
            self.n_skip_send += 1
            return
        oid = self.send_order(
            OrderRequest(
                side=Side.BUY if sign > 0 else Side.SELL,
                price=int(price),
                quantity=int(qty),
                order_type=OrderType.IOC if ioc else OrderType.LIMIT,
            )
        )
        self.orders[oid] = [sign, qty, kind, price, self.mid]

    def _cancel(self, oid: str) -> None:
        if oid not in self.cancelling:
            self.cancelling.add(oid)
            self.cancel_order(oid)

    def _fv(self, t: int, win_us: int) -> float:
        lo = t - win_us
        bmax = None
        for tt, p in reversed(self.bins):
            if tt <= lo:
                break
            if bmax is None or p > bmax:
                bmax = p
        if bmax is None:
            return 0.0
        amin = None
        for tt, p in reversed(self.ains):
            if tt <= lo:
                break
            if amin is None or p < amin:
                amin = p
        if amin is None:
            return 0.0
        return 0.5 * (bmax + amin) - self.mid

    def _x(self, t: int) -> list:
        ev = self.ev
        return [
            float(ev[0]),
            float(ev[1]),
            float(ev[2]),
            float(ev[3]),
            self.e_a1.get(t),
            self.e_a5.get(t),
            self.e_as2.get(t),
            self.e_sw1.get(t),
            math.exp(-(t - self.t_apos) / 1e6) if t - self.t_apos < 30_000_000 else 0.0,
            math.exp(-(t - self.t_aneg) / 1e6) if t - self.t_aneg < 30_000_000 else 0.0,
            self.e_rate.get(t) / 120.0,
            self._fv(t, 20_000),
            self._fv(t, 50_000),
            self._fv(t, 200_000),
            self.e_ib50.get(t),
            self.e_ia50.get(t),
            self.e_ib200.get(t),
            self.e_ia200.get(t),
            float(self.last_side),
            self.e_f02.get(t) / 1000.0,
            self.e_f1.get(t) / 1000.0,
            self.e_f5.get(t) / 1000.0,
            self.qi,
            float(self.spread),
            float(self.vsign),
        ]

    def _alpha(self, t: int) -> float:
        x = self._x(t)
        if self.model == "tree":
            node = 0
            while TREE_FEAT[node] >= 0:
                if x[TREE_FEAT[node]] <= TREE_THR[node]:
                    node = TREE_LEFT[node]
                else:
                    node = TREE_RIGHT[node]
            a = TREE_VALUE[node]
        else:
            if self.model == "sym":
                a = 0.0
                cs, los, his = SYM_COEF, SYM_LO, SYM_HI
            elif self.model == "rlin":
                a = RLIN_B
                cs, los, his = RLIN_COEF, RLIN_LO, RLIN_HI
            elif self.model == "rlin0":
                a = 0.0
                cs, los, his = RLIN0_COEF, RLIN_LO, RLIN_HI
            elif self.model == "rsym":
                a = 0.0
                cs, los, his = RSYM_COEF, RSYM_LO, RSYM_HI
            else:
                a = LIN_B
                cs, los, his = LIN_COEF, LIN_LO, LIN_HI
            for i in range(len(x)):
                c = cs[i]
                if c:
                    v = x[i]
                    if v < los[i]:
                        v = los[i]
                    elif v > his[i]:
                        v = his[i]
                    a += c * v
        self.alpha = a
        return a

    # ---------------- private feed
    def on_private_order_update(self, event) -> None:
        oid = event.order_id
        st = event.status
        o = self.orders.get(oid)
        if st == OrderStatus.FILLED or st == OrderStatus.PARTIALLY_FILLED:
            if o is None:
                return
            q = event.filled_quantity
            s = o[0]
            self.pos += s * q
            o[1] -= q
            fs = self.fill_stats.get(o[2])
            if fs is None:
                fs = [0, 0.0]
                self.fill_stats[o[2]] = fs
            fs[0] += q
            if event.fill_price is not None:
                fs[1] += q * s * (event.fill_price - o[4])
            if o[1] <= 0:
                del self.orders[oid]
                self.cancelling.discard(oid)
        elif st == OrderStatus.CANCELED or st == OrderStatus.REJECTED:
            self.orders.pop(oid, None)
            self.cancelling.discard(oid)

    # ---------------- public feed
    def on_order_book_change(self, snapshot, trades) -> None:
        bids = snapshot.bids
        asks = snapshot.asks
        t = snapshot.timestamp_us
        feat = self.feat
        hid = self.hid_on
        sig = 0
        groups = ()
        self.ev_taker = 0
        if feat:
            self.ev = (0, 0, 0, 0, 0)
        if trades:
            cur = None
            gs = 0
            filled = 0
            pmin = pmax = 0
            groups = []
            for tr in trades:
                if tr.taker_owner != "market":
                    continue
                if tr.taker_order_id != cur:
                    if cur is not None:
                        groups.append((gs, filled, pmax - pmin, pmin, pmax))
                    cur = tr.taker_order_id
                    if hid:
                        i = int(cur)
                        if i > self.h_max_id:
                            if self.h_lo == 0 or i < self.h_lo:
                                self.h_lo = i
                            if i > self.h_hi:
                                self.h_hi = i
                            if self.j_exact:
                                self.h_newset.add(i)
                    gs = 1 if tr.book_side == "ask" else -1
                    filled = 0
                    pmin = pmax = tr.price
                filled += tr.quantity
                if tr.price < pmin:
                    pmin = tr.price
                elif tr.price > pmax:
                    pmax = tr.price
            if cur is not None:
                groups.append((gs, filled, pmax - pmin, pmin, pmax))
            for gs, filled, lv, gmin, gmax in groups:
                if hid:
                    self.h_fq.append((t, gs * filled))
                    self.h_fsum += gs * filled
                if self.trig1:
                    self.t1_flow_q.append((t, gs * filled))
                    self.t1_flow_sum += gs * filled
                if gs == self.last_sign:
                    self.run += 1
                else:
                    self.run = 1
                    self.last_sign = gs
                st_ = lv >= 2 or filled >= BIG_FILL
                is_a = st_ or (self.run >= RUN_MIN and filled >= FILL_MIN)
                is_a_trade = (
                    lv >= A_SWEEP or filled >= BIG_FILL or (self.run >= RUN_MIN and filled >= FILL_MIN)
                )
                if feat:
                    sf = gs * filled
                    self.e_f02.add(t, sf)
                    self.e_f1.add(t, sf)
                    self.e_f5.add(t, sf)
                    if lv >= 2:
                        self.e_sw1.add(t, gs)
                    if self.fv_takers:
                        if gs > 0:
                            self.bins.append((t, gmax))
                        else:
                            self.ains.append((t, gmin))
                    self.last_side = gs
                    self.ev = (
                        gs if is_a else self.ev[0],
                        gs * (self.run if self.run < 10 else 10),
                        gs * (filled if filled < 2000 else 2000) / 100.0,
                        gs * (lv if lv < 5 else 5),
                        gs,
                    )
                    if self.ev_taker != 1:
                        self.ev_taker = 1 if is_a else 2
                if is_a:
                    self.n_A += 1
                    if feat:
                        self.e_rate.add(t, 1.0)
                        self.e_a1.add(t, gs)
                        self.e_a5.add(t, gs)
                        if st_:
                            self.e_as2.add(t, gs)
                        if gs > 0:
                            self.t_apos = t
                        else:
                            self.t_aneg = t
                        self.vsign = gs
                        self.vdead = t + self.hold
                    if hid:
                        self.h_a_t = t
                        self.h_a_s = gs
                    if is_a_trade:
                        sig = gs
            if FLOW_TRIG > 0:
                fl = self.flow
                for gs, filled, lv, gmin, gmax in groups:
                    fl.append((t, gs * filled))
                    self.flow_sum += gs * filled
                lim = t - FLOW_WIN_US
                while fl and fl[0][0] < lim:
                    self.flow_sum -= fl.popleft()[1]
                if sig == 0 and (self.flow_sum >= FLOW_TRIG or -self.flow_sum >= FLOW_TRIG):
                    sig = 1 if self.flow_sum > 0 else -1
        if not bids or not asks:
            return
        b0 = bids[0]
        if b0.owner == "market":
            bid = b0.price
        else:
            bid = 0
            for o in bids:
                if o.owner == "market":
                    bid = o.price
                    break
        a0 = asks[0]
        if a0.owner == "market":
            ask = a0.price
        else:
            ask = 0
            for o in asks:
                if o.owner == "market":
                    ask = o.price
                    break
        if bid <= 0 or ask <= 0:
            return
        mid2_prev = int(2.0 * self.mid)
        self.mid = 0.5 * (bid + ask)
        if self.j_chk and t >= self.j_chk[0][0]:
            self._j_check(t)
        if feat:
            self._scan(t, bid, ask, bids, asks)
            if self.vsign and t >= self.vdead:
                self.vsign = 0
        tsig = self._trig1(t, bids, asks, mid2_prev) if self.trig1 else 0
        t2sig = self._trig2(t, bids, asks, bid, ask) if self.trig2 else 0
        hsig = 0
        jsig = 0
        if hid:
            mq = self.h_mq
            m = self.mid
            if not mq or mq[-1][1] != m:
                mq.append((t, m))
                lim = t - self.h_mid_win
                while len(mq) >= 2 and mq[1][0] <= lim:
                    mq.popleft()
            if not self.trig2:
                self._h_scan(bids, asks)
            hsig = self._hidden(t, groups)
            if self.j_sig:
                jsig = self.j_sig
                self.j_sig = 0
        if sig:
            self._on_signal(t, sig)
        elif hsig:
            self._h_signal(t, hsig)
        elif tsig or t2sig:
            if not tsig:
                self.n_t2 += 1
                cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
                before = self.n_ignored
                self._on_signal(t, t2sig, self.t2_gated)
                if cur == t2sig:
                    self.n_t2_ext += 1
                elif self.n_ignored != before:
                    self.n_t2_ignored += 1
                elif cur == 0:
                    self.n_t2_entry += 1
                else:
                    self.n_t2_flip += 1
                if jsig:
                    self._jump(t, jsig)
                self._settle(t, bid, ask)
                return
            self.n_t1 += 1
            cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
            before = self.n_ignored
            self._on_signal(t, tsig, self.t1_gated)
            if cur == tsig:
                self.n_t1_ext += 1
            elif self.n_ignored != before:
                self.n_t1_ignored += 1
            elif cur == 0:
                self.n_t1_entry += 1
            else:
                self.n_t1_flip += 1
        else:
            if t >= self.next_alpha_t and (self.grid_entry or self.grid_hold):
                self.next_alpha_t = t + self.alpha_dt
                self._on_grid(t)
            if self.fv_on:
                self._fv_rules(t, ask - bid)
        if jsig:
            self._jump(t, jsig)
        self._settle(t, bid, ask)

    def _jump(self, t: int, d: int) -> None:
        mode = self.j_mode
        st = self.j_stats
        if mode != "burst":
            cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
            self._on_signal(t, d, False)
            k = "ext" if cur == d else ("entry" if cur == 0 else "flip")
            st[k] = st.get(k, 0) + 1
            self.j_sign = d
            self.j_cap_until = t + self.j_cap_ms
        if mode != "flip" and self.j_strong:
            self.b_until = t + self.j_h
            self.b_sign = d
            self.b_n = self.j_n
            self.b_cap = self.j_cap
            self.b_kind = "ioc_jburst"
            self.b_build_until = t + self.j_build if self.j_build else 0
            if self.j_conf:
                self.j_bpending = True
                self.j_bt0 = t
                self.j_bmid0 = self.mid
            st["burst"] = st.get("burst", 0) + 1

    def _j_check(self, t: int) -> None:
        # post-hoc outcome bookkeeping (diagnostics only): signed mid move and inventory at each horizon
        q = self.j_chk
        while q and t >= q[0][0]:
            due, h, idx = q.popleft()
            rec = self.j_recs[idx]
            rec["mv" + str(h)] = round((rec["d"] or 1) * (self.mid - rec["mid"]), 1)
            rec["pos" + str(h)] = self.pos

    def _settle(self, t: int, bid: int, ask: int) -> None:
        if self.j_bpending and t >= self.j_bt0 + self.j_conf:
            self.j_bpending = False
            if self.b_until and self.b_sign * (self.mid - self.j_bmid0) < self.j_conf_ticks:
                self.b_until = t
                self.j_stats["unconfirmed"] = self.j_stats.get("unconfirmed", 0) + 1
            else:
                self.j_stats["confirmed"] = self.j_stats.get("confirmed", 0) + 1
        if self.target != 0 and t >= self.deadline:
            self.target = 0
        if self.b_until and t >= self.b_until:
            self.b_until = 0
        if self.target != self.pos or self.orders or self.b_until or self.pos > self.L or -self.pos > self.L:
            self._reconcile(t, bid, ask)

    def _h_scan(self, bids, asks) -> None:
        # fallback book scan when TRIG2 (whose scan the detector reuses) is off
        hm = self.h_max_id
        lo = self.h_lo
        hi = self.h_hi
        for side in (bids, asks):
            for o in side:
                if o.owner == "market":
                    i = int(o.order_id)
                    if i > hm:
                        if lo == 0 or i < lo:
                            lo = i
                        if i > hi:
                            hi = i
        self.h_lo = lo
        self.h_hi = hi

    def _hidden(self, t: int, groups) -> int:
        lo = self.h_lo
        hi = self.h_hi
        self.h_lo = 0
        self.h_hi = 0
        fq = self.h_fq
        lim = t - self.h_flow_win
        while fq and fq[0][0] < lim:
            self.h_fsum -= fq.popleft()[1]
        mx = self.h_max_id
        out = 0
        if lo:
            if hi > mx:
                self.h_max_id = hi
            if self.j_exact:
                nvis = len(self.h_newset)
                self.h_newset.clear()
                if mx and self.jmp_on and hi - mx > nvis:
                    self._j_gap(t, hi - mx - nvis)
            if mx and lo > mx + 1:
                gap = lo - mx - 1
                st = self.h_stats
                st["det"] = st.get("det", 0) + 1
                st["missing"] = st.get("missing", 0) + gap
                fl = self.h_fsum
                dq = self.h_dq
                dq.append(t)
                lim2 = t - self.h_burst_win
                while dq[0] < lim2:
                    dq.popleft()
                strong = gap >= self.h_gap_strong or len(dq) >= self.h_burst_k
                if strong:
                    st["strong"] = st.get("strong", 0) + 1
                if self.h_arm:
                    self.h_arm_until = t + self.h_arm_ms
                if self.h_flow_on and (strong or not self.h_flow_strong):
                    big = fl >= self.h_flow_f or -fl >= self.h_flow_f
                    if self.h_flow_dir == "flow":
                        if big:
                            out = 1 if fl > 0 else -1
                    elif big or self.h_flow_f <= 0:
                        out = self._h_dir(t, True)
                    if out:
                        self.h_kind = "flow"
                if self.h_burst and (self.b_until == 0 or t >= self.b_until):
                    d = 0
                    if self.h_burst_strong:
                        if strong:
                            d = (1 if fl > 0 else (-1 if fl < 0 else 0)) if self.h_burst_dir == "flow" else self._h_dir(t, False)
                    elif len(dq) >= self.h_burst_k and (fl >= self.h_burst_f or -fl >= self.h_burst_f):
                        d = (1 if fl > 0 else -1) if self.h_burst_dir == "flow" else self._h_dir(t, False)
                    if d:
                        self.b_until = t + self.h_burst_h
                        self.b_sign = d
                        self.b_n = self.h_burst_n
                        self.b_cap = self.h_burst_cap
                        self.b_kind = "ioc_burst"
                        self.b_build_until = 0
                        st["burst"] = st.get("burst", 0) + 1
                if self.jmp_on and not self.j_exact:
                    self._j_gap(t, gap)
        if self.h_arm and groups and not out and t <= self.h_arm_until:
            cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
            for gs, filled, lv, gmin, gmax in groups:
                if (gs == -cur or (cur == 0 and self.h_arm_flat)) and (
                    lv >= self.h_arm_span or filled >= self.h_arm_fill
                ):
                    out = gs
                    self.h_kind = "arm"
        return out

    def _j_gap(self, t: int, gap: int) -> None:
        # one gap-revealing callback: update the windowed hidden sum, maybe trigger (sets self.j_sig)
        jq = self.j_q
        jq.append((t, gap))
        self.j_sum += gap
        lim = t - self.j_win
        while jq and jq[0][0] <= lim:
            self.j_sum -= jq.popleft()[1]
        if self.j_sum < self.j_k or t - self.j_last < self.j_cool:
            return
        self.j_last = t
        iq = self.j_iq
        while iq and iq[0][0] <= lim:
            self.j_isum -= iq.popleft()[1]
        imb = self.j_isum
        d = 1 if imb > 0 else (-1 if imb < 0 else 0)
        sp = self.j_sp
        st = self.j_stats
        st["trig"] = st.get("trig", 0) + 1
        ok = True
        if self.j_max_spread > 0 and (sp <= 0 or sp > self.j_max_spread):
            st["spread_skip"] = st.get("spread_skip", 0) + 1
            ok = False
        elif d == 0:
            st["dir0_skip"] = st.get("dir0_skip", 0) + 1
            ok = False
        rec = {"t": round(t / 1e6, 3), "hid": self.j_sum, "imb": imb, "d": d, "sp": sp,
               "act": ok, "pos": self.pos, "tgt": self.target, "mid": self.mid}
        self.j_recs.append(rec)
        idx = len(self.j_recs) - 1
        for h in (50, 200):
            self.j_chk.append((t + h * 1000, h, idx))
        if ok:
            self.j_sig = d
            self.j_strong = self.j_sum >= self.j_bk and (imb >= self.j_bimb or -imb >= self.j_bimb)
            rec["strong"] = self.j_strong

    def _h_dir(self, t: int, use_flow: bool) -> int:
        # direction chain: last A-like sweep within HID_A_WIN_MS, else (flow sign), else mid move over 200 ms
        if self.h_a_s and t - self.h_a_t <= self.h_a_win:
            return self.h_a_s
        if use_flow:
            fl = self.h_fsum
            if fl:
                return 1 if fl > 0 else -1
        mq = self.h_mq
        lim = t - self.h_mid_win
        while len(mq) >= 2 and mq[1][0] <= lim:
            mq.popleft()
        if not mq:
            return 0
        d = self.mid - mq[0][1]
        return 1 if d > 0 else (-1 if d < 0 else 0)

    def _h_signal(self, t: int, s: int) -> None:
        kind = self.h_kind
        gate = self.h_arm_gated if kind == "arm" else self.h_flow_gated
        cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
        before = self.n_ignored
        self._on_signal(t, s, gate)
        if cur == s:
            k = kind + "_ext"
        elif self.n_ignored != before:
            k = kind + "_ignored"
        elif cur == 0:
            k = kind + "_entry"
        else:
            k = kind + "_flip"
        self.h_stats[k] = self.h_stats.get(k, 0) + 1

    def _scan(self, t: int, bid: int, ask: int, bids, asks) -> None:
        mx = self.max_id
        new_mx = mx
        pb = self.prev_bid
        pa = self.prev_ask
        lim = bid - self.fv_depth
        bq = 0
        for o in bids:
            p = o.price
            if p < lim:
                break
            if o.owner == "market":
                if p == bid:
                    bq += o.quantity
                i = int(o.order_id)
                if i > mx:
                    self.bins.append((t, p))
                    if i > new_mx:
                        new_mx = i
                    if pb and p > pb:
                        self.e_ib50.add(t, 1.0)
                        self.e_ib200.add(t, 1.0)
        lim = ask + self.fv_depth
        aq = 0
        for o in asks:
            p = o.price
            if p > lim:
                break
            if o.owner == "market":
                if p == ask:
                    aq += o.quantity
                i = int(o.order_id)
                if i > mx:
                    self.ains.append((t, p))
                    if i > new_mx:
                        new_mx = i
                    if pa and p < pa:
                        self.e_ia50.add(t, 1.0)
                        self.e_ia200.add(t, 1.0)
        self.max_id = new_mx
        old = t - 250_000
        bq_ = self.bins
        while bq_ and bq_[0][0] < old:
            bq_.popleft()
        aq_ = self.ains
        while aq_ and aq_[0][0] < old:
            aq_.popleft()
        self.qi = (bq - aq) / (bq + aq) if bq + aq else 0.0
        self.spread = ask - bid
        self.prev_bid = bid
        self.prev_ask = ask

    def _t1_side(self, t: int, orders, prev, mid2: int, mx: int) -> int:
        # Single-row snapshots: a new resting order either changes the side's first view (new best,
        # or a fill/replacement at the touch) or adds a view with the same first view. Otherwise skip.
        if prev is not None and orders and prev and orders[0] is prev[0] and len(orders) <= len(prev):
            return mx
        self.n_t1_scans += 1
        new_mx = mx
        q = self.t1_ins_q
        for o in orders:
            if o.owner == "market":
                i = int(o.order_id)
                if i > mx:
                    if i > new_mx:
                        new_mx = i
                    if mid2 > 0:
                        v = 2 * o.price - mid2
                        q.append((t, v))
                        self.t1_ins_sum += v
        return new_mx

    def _trig1(self, t: int, bids, asks, mid2: int) -> int:
        mx = self.t1_max_id
        m1 = self._t1_side(t, bids, self.t1_prev_b, mid2, mx)
        m2 = self._t1_side(t, asks, self.t1_prev_a, mid2, mx)
        self.t1_max_id = m1 if m1 > m2 else m2
        self.t1_prev_b = bids
        self.t1_prev_a = asks
        lo = t - self.t1_win
        q = self.t1_ins_q
        while q and q[0][0] <= lo:
            self.t1_ins_sum -= q.popleft()[1]
        f = self.t1_flow_q
        while f and f[0][0] <= lo:
            self.t1_flow_sum -= f.popleft()[1]
        n = len(q)
        d = 0
        if n:
            fl = self.t1_flow_sum
            s2 = self.t1_ins_sum
            thr = self.t1_fv2 * n
            if fl >= self.t1_flow and s2 >= thr:
                d = 1
            elif fl <= -self.t1_flow and s2 <= -thr:
                d = -1
        prev = self.t1_state
        self.t1_state = d
        if d != 0 and d != prev:
            return d
        return 0

    def _t2_side(self, t: int, orders, prev, side: int, own: int, spc: int, mx: int) -> int:
        # Same single-row shortcut as _t1_side; z needs the market best of the PREVIOUS event (own > 0).
        if prev is not None and orders and prev and orders[0] is prev[0] and len(orders) <= len(prev):
            return mx
        new_mx = mx
        q = self.t2_q
        base = 33 if side > 0 else 0
        hid = self.hid_on
        hm = self.h_max_id
        jmp = self.jmp_on
        for o in orders:
            if o.owner == "market":
                i = int(o.order_id)
                if i > mx:
                    if i > new_mx:
                        new_mx = i
                    if hid and i > hm:
                        if self.h_lo == 0 or i < self.h_lo:
                            self.h_lo = i
                        if i > self.h_hi:
                            self.h_hi = i
                        if self.j_exact:
                            self.h_newset.add(i)
                    if own > 0:
                        k = side * (own - o.price)
                        if jmp and k <= 1:
                            w = side * 2 if k < 0 else side
                            self.j_iq.append((t, w))
                            self.j_isum += w
                        if k < -3:
                            k = -3
                        elif k > 7:
                            k = 7
                        z = side * T2_ITAB[base + (k + 3) * 3 + spc]
                        q.append((t, z))
                        self.t2_sum += z
                        self.n_t2_ins += 1
        return new_mx

    def _trig2(self, t: int, bids, asks, bid: int, ask: int) -> int:
        pb = self.t2_pb
        pa = self.t2_pa
        if pb > 0 and pa > 0:
            sp = pa - pb
            spc = (0 if sp <= 1 else (1 if sp == 2 else 2))
        else:
            pb = pa = 0
            spc = 0
            sp = 0
        if self.jmp_on:
            self.j_sp = sp
            lim = t - self.j_win
            iq = self.j_iq
            while iq and iq[0][0] <= lim:
                self.j_isum -= iq.popleft()[1]
        mx = self.t2_max_id
        m1 = self._t2_side(t, bids, self.t2_prev_b, 1, pb, spc, mx)
        m2 = self._t2_side(t, asks, self.t2_prev_a, -1, pa, spc, mx)
        self.t2_max_id = m1 if m1 > m2 else m2
        self.t2_prev_b = bids
        self.t2_prev_a = asks
        self.t2_pb = bid
        self.t2_pa = ask
        lo = t - self.t2_win
        q = self.t2_q
        while q and q[0][0] <= lo:
            self.t2_sum -= q.popleft()[1]
        n = len(q)
        d = 0
        if n:
            m = self.t2_sum / n
            if m >= self.t2_thr:
                d = 1
            elif m <= -self.t2_thr:
                d = -1
        else:
            self.t2_sum = 0.0
        if d != self.t2_dir:
            self.t2_dir = d
            self.t2_t0 = t
            self.t2_fired = False
        if d != 0 and not self.t2_fired and t - self.t2_t0 >= self.t2_hold:
            self.t2_fired = True
            return d
        return 0

    def _on_signal(self, t: int, s: int, gate: bool = True) -> None:
        cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
        if cur == s:
            if t + self.hold > self.deadline:
                self.deadline = t + self.hold
            return
        if cur != 0:
            if self.gate_flip and gate:
                a = self._alpha(t)
                if a * s <= self.flip_margin:
                    self.n_ignored += 1
                    return
            self.n_flip += 1
        else:
            self.n_entry += 1
        self.target = s * self.L
        self.deadline = t + self.hold
        self.wait_until = 0

    def _fv_rules(self, t: int, spread: int) -> None:
        fv = self._fv(t, 50_000)
        cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
        if cur == 0:
            if self.fv_entry and self.pos == 0 and not self.orders and spread <= self.fv_entry_spread:
                if fv >= self.fv_entry or fv <= -self.fv_entry:
                    self.n_fv_entry += 1
                    self.target = (1 if fv > 0 else -1) * self.L
                    self.deadline = t + self.hold
                    self.wait_until = 0
            return
        f = fv * cur
        if self.fv_flip and f <= -self.fv_flip:
            self.n_fv_flip += 1
            self.target = -cur * self.L
            self.deadline = t + self.hold
            self.wait_until = 0
            return
        if self.fv_hold and f >= self.fv_hold and self.deadline - t < 500_000:
            self.n_fv_hold += 1
            self.deadline = t + 500_000

    def _on_grid(self, t: int) -> None:
        cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
        if cur == 0:
            if not self.grid_entry or self.pos != 0 or self.orders:
                return
            a = self._alpha(t)
            if a > self.entry_margin or a < -self.entry_margin:
                s = 1 if a > 0 else -1
                self.n_alpha_entry += 1
                self.target = s * self.L
                self.deadline = t + self.hold
                self.wait_until = 0
            return
        if not self.grid_hold:
            return
        a = self._alpha(t) * cur
        if a > self.ext_margin:
            if t + self.ext_hold > self.deadline:
                self.deadline = t + self.ext_hold
                self.n_ext += 1
        elif a < self.exit_margin:
            self.n_early_exit += 1
            self.target = 0

    def _reconcile(self, t: int, bid: int, ask: int) -> None:
        if self.cancelling:
            return
        for o in self.orders.values():
            if o[2][0] == "i":
                return
        if self.b_until or self.pos > self.L or -self.pos > self.L:
            # HID_BURST / JMP burst: build to +-N during the burst, unwind beyond +-LOTS afterwards; IOC both ways
            tgt = self.b_sign * self.b_n if self.b_until else self.target
            want = tgt - self.pos
            if self.orders:
                for oid in list(self.orders):
                    self._cancel(oid)
                return
            if want:
                ws = 1 if want > 0 else -1
                if self.b_until and self.b_build_until and t >= self.b_build_until and ws == self.b_sign:
                    return
                lim = ask + self.b_cap if ws > 0 else bid - self.b_cap
                self._send(ws, abs(want), lim, self.b_kind, True, self.b_n)
            return
        want = self.target - self.pos
        resting = list(self.orders.items())
        if want == 0:
            if resting:
                for oid, _ in resting:
                    self._cancel(oid)
            return
        ws = 1 if want > 0 else -1
        jc = self.j_cap if (self.j_cap_until and t < self.j_cap_until and ws == self.j_sign) else -1
        exiting = self.target == 0 or (
            self.pos != 0 and (self.target > 0) == (self.pos > 0) and abs(self.target) < abs(self.pos)
        )
        flipping = self.pos != 0 and self.target != 0 and (self.target > 0) != (self.pos > 0)
        if exiting:
            px_orders = [oid for oid, o in resting if o[2] == "px"]
            others = [oid for oid, o in resting if o[2] != "px"]
            if others:
                for oid in others:
                    self._cancel(oid)
                return
            if not px_orders:
                if self.wait_until != -1:
                    self._send(ws, abs(want), bid if ws > 0 else ask, "px", False)
                    self.wait_until = t + self.touch_wait
                    return
            else:
                if t >= self.wait_until:
                    for oid in px_orders:
                        self._cancel(oid)
                    self.wait_until = -1
                return
            lim = ask + EXIT_CAP if ws > 0 else bid - EXIT_CAP
            self._send(ws, abs(want), lim, "ioc_out", True)
            return
        if flipping:
            if resting:
                for oid, _ in resting:
                    self._cancel(oid)
                return
            if jc >= 0:
                lim = ask + jc if ws > 0 else bid - jc
                self._send(ws, abs(want), lim, "ioc_jflip", True)
                return
            lim = ask + EXIT_CAP if ws > 0 else bid - EXIT_CAP
            self._send(ws, abs(want), lim, "ioc_flip", True)
            return
        if resting:
            for oid, _ in resting:
                self._cancel(oid)
            return
        if jc >= 0:
            lim = ask + jc if ws > 0 else bid - jc
            self._send(ws, abs(want), lim, "ioc_jin", True)
            return
        lim = (ask + ENTRY_CAP) if ws > 0 else (bid - ENTRY_CAP)
        self._send(ws, abs(want), lim, "ioc_in", True)

    def diagnostics(self) -> dict:
        return {
            "n_A": self.n_A,
            "entries": self.n_entry,
            "flips": self.n_flip,
            "ignored_opposite": self.n_ignored,
            "alpha_entries": self.n_alpha_entry,
            "extensions": self.n_ext,
            "early_exits": self.n_early_exit,
            "skipped_sends": self.n_skip_send,
            "fv_flips": self.n_fv_flip,
            "fv_hold_ext": self.n_fv_hold,
            "fv_entries": self.n_fv_entry,
            "t1_fires": self.n_t1,
            "t1_entries": self.n_t1_entry,
            "t1_flips": self.n_t1_flip,
            "t1_ext": self.n_t1_ext,
            "t1_ignored": self.n_t1_ignored,
            "t1_scans": self.n_t1_scans,
            "t2_fires": self.n_t2,
            "t2_entries": self.n_t2_entry,
            "t2_flips": self.n_t2_flip,
            "t2_ext": self.n_t2_ext,
            "t2_ignored": self.n_t2_ignored,
            "t2_inserts": self.n_t2_ins,
            "hidden": dict(self.h_stats),
            "jump": {"stats": dict(self.j_stats), "events": list(self.j_recs)},
            "fill_stats": {k: [v[0], round(v[1] / v[0], 4) if v[0] else 0.0] for k, v in self.fill_stats.items()},
        }
