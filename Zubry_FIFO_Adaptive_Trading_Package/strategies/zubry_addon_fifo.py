"""Experimental FIFO-safe size top-ups without replacing existing orders.

Not verified on the official simulator. A preliminary independent replay produced
220,857 versus 221,070 for fixed q200 on Round 0 public data. Queue preservation
is economically plausible, but not empirically superior on this sample.
"""
from __future__ import annotations

import math
from simulator.models import (
    OrderBookSnapshot, OrderRequest, OrderStatus, OrderType,
    PrivateOrderEvent, Side, Trade,
)
from simulator.strategy import BaseStrategy

TARGET_TOTAL = 200
SAFE_LIMIT = 100
INVENTORY_SKEW = 0.05

class ZubryAddOnFIFO(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        self.orders: dict[str, tuple[Side,int,int,bool,bool]] = {}

    def on_private_order_update(self,event:PrivateOrderEvent)->None:
        o=self.orders.get(event.order_id)
        if o is None:
            if event.filled_quantity: raise RuntimeError('untracked fill')
            return
        side,price,remaining,accepted,canceling=o
        if event.filled_quantity:
            self.inventory += event.filled_quantity*(1 if side==Side.BUY else -1)
        if event.status in (OrderStatus.FILLED,OrderStatus.CANCELED,OrderStatus.REJECTED):
            del self.orders[event.order_id]
        elif event.status in (OrderStatus.ACCEPTED,OrderStatus.PARTIALLY_FILLED,OrderStatus.MODIFIED):
            self.orders[event.order_id]=(side,price,event.remaining_quantity,True,canceling)

    def on_order_book_change(self,snapshot:OrderBookSnapshot,trades:list[Trade])->None:
        bid=ask=None
        for o in snapshot.bids:
            if o.owner=='market':bid=o.price;break
        for o in snapshot.asks:
            if o.owner=='market':ask=o.price;break
        if bid is None or ask is None:return
        mid=(bid+ask)*0.5
        c=mid-INVENTORY_SKEW*self.inventory
        pb=max(1,min(bid,math.floor(c-0.5)))
        pa=max(ask,math.ceil(c+0.5),pb+1)
        targets={Side.BUY:pb,Side.SELL:pa}
        for order_id,o in list(self.orders.items()):
            side,price,qty,accepted,canceling=o
            if accepted and not canceling and price!=targets[side]:
                self.cancel_order(order_id)
                self.orders[order_id]=(side,price,qty,accepted,True)
        for side in (Side.BUY,Side.SELL):
            relevant=[o for o in self.orders.values() if o[0]==side]
            if any(o[1]!=targets[side] or o[4] for o in relevant):continue
            reserved=sum(o[2] for o in relevant)
            headroom=(SAFE_LIMIT-self.inventory if side==Side.BUY else SAFE_LIMIT+self.inventory)
            new_qty=min(TARGET_TOTAL-reserved,headroom-reserved)
            if new_qty<=0:continue
            oid=self.send_order(OrderRequest(side=side,price=targets[side],quantity=new_qty,order_type=OrderType.LIMIT))
            self.orders[oid]=(side,targets[side],new_qty,False,False)
