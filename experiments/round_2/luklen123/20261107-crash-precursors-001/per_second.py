"""Rebuild the market book and emit one feature row per second (state at the end of the second
plus flow aggregated over that second). Matching mirrors the simulator for market-only flow.

Usage: uv run --locked python per_second.py <tape.csv> <out.pkl>
"""

from __future__ import annotations

import csv
import sys
from collections import deque
from pathlib import Path

import pandas as pd

LEVELS = 10
NEAR = 2  # ticks from best counted as "near the touch"
BIG = 500


def main(tape: Path, out: Path) -> None:
    bid_q: dict[int, int] = {}
    ask_q: dict[int, int] = {}
    queues: dict[str, dict[int, deque]] = {"B": {}, "A": {}}
    live: dict[int, list] = {}
    rows = []
    cur = None
    acc = None

    def fresh() -> dict:
        return {k: 0 for k in (
            "ins_b", "ins_a", "ins_near_b", "ins_near_a", "can_b", "can_a", "can_near_b",
            "can_near_a", "tk_buy", "tk_sell", "tk_n_buy", "tk_n_sell", "big_buy", "big_sell",
            "sweeps_buy", "sweeps_sell", "ioc_b", "ioc_a")}

    def snapshot(sec: int) -> None:
        bb = max(bid_q) if bid_q else None
        ba = min(ask_q) if ask_q else None
        r = {"t": sec, **acc}
        if bb is None or ba is None:
            rows.append(r)
            return
        r.update(bb=bb, ba=ba, mid=(bb + ba) / 2, spr=ba - bb, bq1=bid_q[bb], aq1=ask_q[ba])
        bl = sorted(bid_q, reverse=True)[:LEVELS]
        al = sorted(ask_q)[:LEVELS]
        for k in (3, 5, 10):
            r[f"bdep{k}"] = sum(bid_q[p] for p in bl[:k])
            r[f"adep{k}"] = sum(ask_q[p] for p in al[:k])
        r["bdep_t5"] = sum(q for p, q in bid_q.items() if p > bb - 5)
        r["adep_t5"] = sum(q for p, q in ask_q.items() if p < ba + 5)
        r["n_bid_lv"] = len(bid_q)
        r["n_ask_lv"] = len(ask_q)
        rows.append(r)

    with tape.open() as fh:
        reader = csv.reader(fh)
        next(reader)
        for row in reader:
            t = float(row[0])
            sec = int(t)
            if cur is None:
                cur, acc = sec, fresh()
            while sec > cur:
                snapshot(cur)
                cur += 1
                acc = fresh()
            bb = max(bid_q) if bid_q else None
            ba = min(ask_q) if ask_q else None
            oid = int(row[2])
            if row[1] == "Cancel":
                o = live.pop(oid, None)
                if o is None:
                    continue
                side, price, rem = o
                book = bid_q if side == "B" else ask_q
                book[price] -= rem
                if book[price] == 0:
                    del book[price]
                    queues[side].pop(price, None)
                near = (side == "B" and bb is not None and price >= bb - NEAR) or (
                    side == "A" and ba is not None and price <= ba + NEAR)
                acc["can_b" if side == "B" else "can_a"] += rem
                if near:
                    acc["can_near_b" if side == "B" else "can_near_a"] += rem
                continue
            side, vol, price, life = row[3], int(row[4]), int(row[5]), row[6]
            if life == "F":
                acc["ioc_b" if side == "B" else "ioc_a"] += vol
            rem = vol
            opp = ask_q if side == "B" else bid_q
            oq = queues["A" if side == "B" else "B"]
            levels_hit = 0
            while rem > 0 and opp:
                bp = min(opp) if side == "B" else max(opp)
                if (side == "B" and bp > price) or (side == "A" and bp < price):
                    break
                levels_hit += 1
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
            taken = vol - rem
            if taken:
                s = "buy" if side == "B" else "sell"
                acc[f"tk_{s}"] += taken
                acc[f"tk_n_{s}"] += 1
                if taken >= BIG:
                    acc[f"big_{s}"] += 1
                if levels_hit > 1:
                    acc[f"sweeps_{s}"] += 1
            if life == "G" and rem > 0:
                book = bid_q if side == "B" else ask_q
                book[price] = book.get(price, 0) + rem
                queues[side].setdefault(price, deque()).append(oid)
                live[oid] = [side, price, rem]
                acc["ins_b" if side == "B" else "ins_a"] += rem
                ref_b = max(bid_q) if side == "B" else None
                ref_a = min(ask_q) if side == "A" else None
                if (side == "B" and price >= ref_b - NEAR) or (side == "A" and price <= ref_a + NEAR):
                    acc["ins_near_b" if side == "B" else "ins_near_a"] += rem
    snapshot(cur)
    pd.DataFrame(rows).to_pickle(out)
    print(f"seconds={len(rows)} -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
