"""Reconstruct the public market book of a tape and dump BBO/trade/order-lifecycle tables.

Matching mirrors the official simulator for market-only flow: price-time priority,
fills at the resting order's price, IOC ('F') remainder discarded, GTC ('G') rests.
Usage: uv run --locked python reconstruct.py <tape.csv> <out_dir>
"""

from __future__ import annotations

import csv
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd


def main(tape: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    bids: dict[int, deque[int]] = {}
    asks: dict[int, deque[int]] = {}
    bid_qty: dict[int, int] = {}
    ask_qty: dict[int, int] = {}
    live: dict[int, list] = {}  # id -> [side, price, remaining, t_insert, initial]
    best_bid: int | None = None
    best_ask: int | None = None

    snap_t, snap_bb, snap_ba, snap_bq, snap_aq, snap_op = [], [], [], [], [], []
    trades = []  # t, price, qty, aggressor(+1 buy), taker_id, maker_id, maker_age
    lifecycle = []  # id, side, price, vol, lifespan, t_insert, t_end, end, filled, crossed_on_entry
    unknown_cancel = 0

    def recompute_best() -> None:
        nonlocal best_bid, best_ask
        best_bid = max(bid_qty) if bid_qty else None
        best_ask = min(ask_qty) if ask_qty else None

    with tape.open() as fh:
        reader = csv.reader(fh)
        next(reader)
        for row in reader:
            t = float(row[0])
            op = row[1]
            oid = int(row[2])
            if op == "Cancel":
                o = live.pop(oid, None)
                if o is None:
                    unknown_cancel += 1
                    continue
                side, price, rem = o[0], o[1], o[2]
                book_q = bid_qty if side == "B" else ask_qty
                book_q[price] -= rem
                if book_q[price] == 0:
                    del book_q[price]
                    (bids if side == "B" else asks).pop(price, None)
                    if (side == "B" and price == best_bid) or (side == "A" and price == best_ask):
                        recompute_best()
                lifecycle.append((oid, side, price, o[4], "G", o[3], t, "cancel", o[4] - rem, o[5]))
                opcode = 2
            else:
                side = row[3]
                vol = int(row[4])
                price = int(row[5])
                life = row[6]
                rem = vol
                sgn = 1 if side == "B" else -1
                crossed = False
                # match against opposite side
                opp_q = ask_qty if side == "B" else bid_qty
                opp_l = asks if side == "B" else bids
                while rem > 0 and opp_q:
                    bp = min(opp_q) if side == "B" else max(opp_q)
                    if (side == "B" and bp > price) or (side == "A" and bp < price):
                        break
                    crossed = True
                    dq = opp_l[bp]
                    while rem > 0 and dq:
                        mid_ = dq[0]
                        m = live.get(mid_)
                        if m is None:
                            dq.popleft()
                            continue
                        f = min(rem, m[2])
                        m[2] -= f
                        rem -= f
                        opp_q[bp] -= f
                        trades.append((t, bp, f, sgn, oid, mid_, t - m[3]))
                        if m[2] == 0:
                            dq.popleft()
                            live.pop(mid_)
                            lifecycle.append((mid_, m[0], m[1], m[4], "G", m[3], t, "filled", m[4], m[5]))
                    if opp_q[bp] == 0:
                        del opp_q[bp]
                        opp_l.pop(bp, None)
                recompute_best() if crossed else None
                if life == "G" and rem > 0:
                    own_q = bid_qty if side == "B" else ask_qty
                    own_l = bids if side == "B" else asks
                    own_q[price] = own_q.get(price, 0) + rem
                    own_l.setdefault(price, deque()).append(oid)
                    live[oid] = [side, price, rem, t, vol, crossed]
                    if side == "B" and (best_bid is None or price > best_bid):
                        best_bid = price
                    if side == "A" and (best_ask is None or price < best_ask):
                        best_ask = price
                else:
                    lifecycle.append((oid, side, price, vol, life, t, t, "ioc" if life == "F" else "filled",
                                      vol - rem, crossed))
                opcode = 1 if not crossed else 3
            snap_t.append(t)
            snap_op.append(opcode)
            snap_bb.append(best_bid if best_bid is not None else -1)
            snap_ba.append(best_ask if best_ask is not None else -1)
            snap_bq.append(bid_qty.get(best_bid, 0) if best_bid is not None else 0)
            snap_aq.append(ask_qty.get(best_ask, 0) if best_ask is not None else 0)

    for oid, o in live.items():
        lifecycle.append((oid, o[0], o[1], o[4], "G", o[3], np.nan, "open", o[4] - o[2], o[5]))

    pd.DataFrame({"t": snap_t, "op": np.array(snap_op, dtype=np.int8), "bb": snap_bb, "ba": snap_ba,
                  "bq": snap_bq, "aq": snap_aq}).to_pickle(out / "bbo.pkl")
    pd.DataFrame(trades, columns=["t", "price", "qty", "aggr", "taker", "maker", "maker_age"]).to_pickle(
        out / "trades.pkl")
    pd.DataFrame(lifecycle, columns=["id", "side", "price", "vol", "life", "t_in", "t_end", "end", "filled",
                                     "crossed"]).to_pickle(out / "orders.pkl")
    print(f"events={len(snap_t)} trades={len(trades)} orders={len(lifecycle)} unknown_cancel={unknown_cancel}"
          f" open_at_end={len(live)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
