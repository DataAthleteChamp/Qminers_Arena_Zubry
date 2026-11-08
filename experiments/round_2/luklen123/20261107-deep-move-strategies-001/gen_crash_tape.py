"""Synthetic order tape with frequent deep moves, for stress-testing strategies in the official
simulator. Output columns match the official format: Time,Operation,OrderId,Side,Volume,Price,
Lifespan. It is a deliberately simple agent model, not a replica of any round:

- latent fair value F: calm diffusion; crash/rally episodes (random direction) with drift, higher
  diffusion and jumps; some episodes are followed by a partial rebound;
- makers quote around F (wider and thinner during episodes), orders live ~0.3 s then cancel;
- noise takers trade both ways; informed takers trade toward F when the mid lags it.

Usage: gen_crash_tape.py <out.csv> <seed> [duration_s]
"""

from __future__ import annotations

import csv
import heapq
import math
import random
import sys
from collections import deque

# --- parameters (episode-heavy market) ---
START = 10_000.0
CALM_SIGMA = 0.8  # ticks / sqrt(s)
EPISODE_RATE = 1 / 300  # per second
EP_DUR = (40.0, 200.0)
EP_DRIFT = (1.5, 4.0)  # ticks / s
EP_SIGMA = 3.0
EP_JUMP_RATE = 0.1  # per second inside an episode
EP_JUMP_MEAN = 8.0
REBOUND_P = 0.4
MAKER_RATE = (120.0, 60.0)  # calm, episode (per second)
MAKER_GEOM_P = (0.55, 0.35)
MAKER_LIFE = (0.35, 0.2)
NOISE_RATE = 5.0
INFORMED_K = 4.0
INFORMED_CAP = 40.0


def lognorm(rng: random.Random, median: float, sigma: float, cap: int) -> int:
    return max(1, min(cap, int(round(median * math.exp(sigma * rng.gauss(0, 1))))))


def geom(rng: random.Random, p: float) -> int:
    k = 0
    while rng.random() > p and k < 10:
        k += 1
    return k


def main(out: str, seed: int, duration: float) -> None:
    rng = random.Random(seed)
    bid_q: dict[int, int] = {}
    ask_q: dict[int, int] = {}
    queues = {"B": {}, "A": {}}
    live: dict[int, list] = {}
    cancels: list[tuple[float, int]] = []
    rows = []
    oid = 1_000_000
    last_us = 0
    F = START
    t = 0.0
    ep_end = -1.0
    ep_dir = 0
    ep_drift = 0.0
    next_ep = rng.expovariate(EPISODE_RATE)
    pending_rebound = None

    def emit(op, i, side="", vol="", price="", life=""):
        nonlocal last_us
        us = max(last_us + 1, int(t * 1e6))
        last_us = us
        rows.append((f"{us / 1e6:.6f}", op, i, side, vol, price, life))

    def best():
        return (max(bid_q) if bid_q else None, min(ask_q) if ask_q else None)

    def insert(side, vol, price, life):
        nonlocal oid
        oid += 1
        emit("Insert", oid, side, vol, price, life)
        rem = vol
        opp, oq = (ask_q, queues["A"]) if side == "B" else (bid_q, queues["B"])
        while rem > 0 and opp:
            bp = min(opp) if side == "B" else max(opp)
            if (side == "B" and bp > price) or (side == "A" and bp < price):
                break
            dq = oq[bp]
            while rem > 0 and dq:
                m = live.get(dq[0])
                if m is None:
                    dq.popleft()
                    continue
                f = min(rem, m[2])
                m[2] -= f
                rem -= f
                opp[bp] -= f
                if m[2] == 0:
                    live.pop(dq.popleft())
            if opp[bp] == 0:
                del opp[bp]
                oq.pop(bp, None)
        if life == "G" and rem > 0:
            book = bid_q if side == "B" else ask_q
            book[price] = book.get(price, 0) + rem
            queues[side].setdefault(price, deque()).append(oid)
            live[oid] = [side, price, rem]
            return oid
        return None

    def cancel(i):
        o = live.pop(i, None)
        if o is None:
            return
        side, price, rem = o
        book = bid_q if side == "B" else ask_q
        book[price] -= rem
        if book[price] == 0:
            del book[price]
            queues[side].pop(price, None)
        emit("Cancel", i)

    while t < duration:
        in_ep = t < ep_end
        k = 1 if in_ep else 0
        bb, ba = best()
        mid = (bb + ba) / 2 if bb is not None and ba is not None else F
        gap = F - mid
        r_inf = min(INFORMED_CAP, INFORMED_K * max(0.0, abs(gap) - 0.5))
        rates = (MAKER_RATE[k], NOISE_RATE, r_inf)
        total = sum(rates)
        dt = rng.expovariate(total)
        # next scheduled cancel may come first
        if cancels and cancels[0][0] <= t + dt:
            ct, ci = heapq.heappop(cancels)
            step = max(0.0, ct - t)
            t = ct
            F += (ep_dir * ep_drift if in_ep else 0.0) * step + (EP_SIGMA if in_ep else CALM_SIGMA) * math.sqrt(step) * rng.gauss(0, 1)
            cancel(ci)
            continue
        t += dt
        sig = EP_SIGMA if in_ep else CALM_SIGMA
        F += (ep_dir * ep_drift if in_ep else 0.0) * dt + sig * math.sqrt(dt) * rng.gauss(0, 1)
        if in_ep and rng.random() < EP_JUMP_RATE * dt:
            F += ep_dir * rng.expovariate(1 / EP_JUMP_MEAN)
        # episode scheduling
        if not in_ep and t >= next_ep:
            if pending_rebound is not None:
                ep_dir, ep_drift, dur = pending_rebound
                pending_rebound = None
            else:
                ep_dir = rng.choice((-1, 1))
                ep_drift = rng.uniform(*EP_DRIFT)
                dur = rng.uniform(*EP_DUR)
                if rng.random() < REBOUND_P:
                    pending_rebound = (-ep_dir, ep_drift / 2, dur / 2)
            ep_end = t + dur
            print(f"episode t={t:7.1f} dir={ep_dir:+d} drift={ep_drift:.2f} dur={dur:5.1f} F={F:.1f}",
                  file=sys.stderr)
            next_ep = ep_end + (rng.uniform(10, 40) if pending_rebound else rng.expovariate(EPISODE_RATE))
        u = rng.random() * total
        bb, ba = best()
        if u < rates[0]:
            side = "B" if rng.random() < 0.5 else "A"
            g = geom(rng, MAKER_GEOM_P[k])
            if side == "B":
                price = math.ceil(F) - 1 - g
                if ba is not None:
                    price = min(price, ba - 1)
            else:
                price = math.floor(F) + 1 + g
                if bb is not None:
                    price = max(price, bb + 1)
            i = insert(side, lognorm(rng, 15, 1.3, 3000), price, "G")
            if i is not None:
                heapq.heappush(cancels, (t + rng.expovariate(1 / MAKER_LIFE[k]), i))
        elif u < rates[0] + rates[1]:
            side = "B" if rng.random() < 0.5 else "A"
            if side == "B" and ba is not None:
                insert("B", lognorm(rng, 30, 1.4, 5000), ba + 2, "F")
            elif side == "A" and bb is not None:
                insert("A", lognorm(rng, 30, 1.4, 5000), bb - 2, "F")
        else:
            if gap > 0 and ba is not None:
                insert("B", lognorm(rng, 80, 1.0, 5000), max(ba, round(F)), "F")
            elif gap < 0 and bb is not None:
                insert("A", lognorm(rng, 80, 1.0, 5000), min(bb, round(F)), "F")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["Time", "Operation", "OrderId", "Side", "Volume", "Price", "Lifespan"])
        w.writerows(rows)
    print(f"seed={seed} rows={len(rows)} final_F={F:.1f}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 1800.0)
