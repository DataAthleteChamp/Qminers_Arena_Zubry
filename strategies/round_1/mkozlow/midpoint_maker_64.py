from collections import deque
from math import log1p,floor,ceil
from simulator.models import OrderRequest,OrderStatus,OrderType,Side
from simulator.strategy import BaseStrategy

MODE = 'adaptive'
TAKER_WEIGHTS = (-0.03627646363064456, 0.05784728798026153, -0.021041026624157994, 0.03420091255606494, -0.0252261376787838, 0.047070054864665, 0.0829938635695938, -0.08217458887303644, -0.3685606800889238)
TAKER_INTERCEPT = -0.028963560481047472
TAKER_SIZE = 100
BURST_US = 50_000
MAKER_ENABLED = True
TAKER_ENABLED = False
PASSIVE_EXIT = True
WEIGHTS = ()
INTERCEPT = 0.0
ACTIVATE_US = 0
CAP = 100
QUOTE_SIZE = 64
FILTER_EDGE = 0.15


class SignalExecution(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.inventory=0
        self.orders={}
        self.previous_ids=set()
        self.previous_bid=None
        self.previous_ask=None
        self.recent=deque()
        self.totals=[0,0,0]
        self.expires=0
        self.burst=False
        self.taker_entries=0
        self.order_kind_counts={}
        self.fills=[]
        self.cancel_requests=0
        self.cancel_races=0
        self.rejections=0
        self.max_inventory=0
        self.max_exposure=0

    def cancel(self,order_id,order):
        if order['state']=='live':
            order['state']='cancel_pending'
            self.cancel_requests+=1
            self.cancel_order(order_id)

    def submit(self,side,price,quantity,kind,now):
        buys=sum(o['remaining'] for o in self.orders.values() if o['side']==Side.BUY)
        sells=sum(o['remaining'] for o in self.orders.values() if o['side']==Side.SELL)
        limit=min(CAP,100) if kind==OrderType.LIMIT and not self.burst else CAP
        capacity=limit-self.inventory-buys if side==Side.BUY else limit+self.inventory-sells
        quantity=min(quantity,capacity)
        if quantity<=0:
            return
        order_id=self.send_order(OrderRequest(side=side,price=price,quantity=quantity,order_type=kind))
        self.orders[order_id]=dict(side=side,price=price,remaining=quantity,state='submit_pending',born=now,kind=kind)
        key=kind.value
        self.order_kind_counts[key]=self.order_kind_counts.get(key,0)+1
        buys=sum(o['remaining'] for o in self.orders.values() if o['side']==Side.BUY)
        sells=sum(o['remaining'] for o in self.orders.values() if o['side']==Side.SELL)
        exposure=max(abs(self.inventory+buys),abs(self.inventory-sells))
        self.max_exposure=max(self.max_exposure,exposure)
        if exposure>CAP:
            raise RuntimeError('Reserved exposure exceeds cap')

    def on_order_book_change(self,snapshot,trades):
        now=self.now_us()
        bids=[o for o in snapshot.bids if o.owner=='market']
        asks=[o for o in snapshot.asks if o.owner=='market']
        if not bids or not asks:
            for order_id,order in self.orders.items():
                self.cancel(order_id,order)
            self.previous_ids={o.order_id for o in bids+asks}
            self.previous_bid=bids[0].price if bids else None
            self.previous_ask=asks[0].price if asks else None
            return
        bid,ask=bids[0].price,asks[0].price
        bq=sum(o.quantity for o in bids if o.price==bid)
        aq=sum(o.quantity for o in asks if o.price==ask)
        added_bid=sum(o.quantity for o in bids if o.price==bid and bid==self.previous_bid and o.order_id not in self.previous_ids)
        added_ask=sum(o.quantity for o in asks if o.price==ask and ask==self.previous_ask and o.order_id not in self.previous_ids)
        flow=sum(t.quantity*(1 if t.book_side=='ask' else -1) for t in trades if t.taker_owner=='market' and t.maker_owner=='market')
        self.previous_ids={o.order_id for o in bids+asks}
        self.previous_bid,self.previous_ask=bid,ask
        self.recent.append((now,added_bid,added_ask,flow))
        self.totals[0]+=added_bid
        self.totals[1]+=added_ask
        self.totals[2]+=flow
        while self.recent and self.recent[0][0]<=now-50_000:
            old=self.recent.popleft()
            self.totals[0]-=old[1]
            self.totals[1]-=old[2]
            self.totals[2]-=old[3]
        if now<ACTIVATE_US:
            return
        ab,aa,flow=self.totals
        imbalance=(bq-aq)/(bq+aq)
        features=(imbalance,imbalance**3,ask-bid,log1p(bq),log1p(aq),(1 if flow>0 else -1)*log1p(abs(flow)),log1p(ab),log1p(aa),ab/(ab+bq)-aa/(aa+aq))
        score=INTERCEPT+sum(w*f for w,f in zip(WEIGHTS,features))
        fair=(bid+ask)/2+score
        take_score=TAKER_INTERCEPT+sum(w*f for w,f in zip(TAKER_WEIGHTS,features))
        take_fair=(bid+ask)/2+take_score
        desired={}
        if self.burst:
            if self.inventory==0:
                for order_id,order in self.orders.items():
                    self.cancel(order_id,order)
                if not self.orders:
                    self.burst=False
                return
            if now>=self.expires:
                for order_id,order in self.orders.items():
                    self.cancel(order_id,order)
                if not self.orders:
                    side=Side.SELL if self.inventory>0 else Side.BUY
                    self.submit(side,max(1,bid-19) if side==Side.SELL else ask+19,abs(self.inventory),OrderType.IOC,now)
                return
            if PASSIVE_EXIT:
                if self.inventory>0:
                    desired[Side.SELL]=max(bid+1,ceil(fair+0.5))
                else:
                    desired[Side.BUY]=max(1,min(ask-1,floor(fair-0.5)))
        else:
            signal=TAKER_ENABLED and (take_fair>ask+0.05 or take_fair<bid-0.05)
            if signal and self.inventory==0:
                for order_id,order in self.orders.items():
                    self.cancel(order_id,order)
                if not self.orders:
                    side=Side.BUY if take_fair>ask else Side.SELL
                    price=floor(take_fair-0.05) if side==Side.BUY else ceil(take_fair+0.05)
                    self.burst=True
                    self.expires=now+BURST_US
                    self.taker_entries+=1
                    self.submit(side,max(1,price),TAKER_SIZE,OrderType.IOC,now)
                return
            if MAKER_ENABLED:
                desired={Side.BUY:max(1,min(ask-1,floor(fair-0.5))),Side.SELL:max(bid+1,ceil(fair+0.5))}
        for order_id,order in self.orders.items():
            price=desired.get(order['side'])
            if price is None or (price!=order['price'] and now-order['born']>=20_000):
                self.cancel(order_id,order)
        for side,price in desired.items():
            if not any(o['side']==side for o in self.orders.values()):
                self.submit(side,price,min(QUOTE_SIZE,abs(self.inventory)) if self.burst else QUOTE_SIZE,OrderType.LIMIT,now)

    def on_private_order_update(self,event):
        order=self.orders.get(event.order_id)
        if order is None:
            if event.status==OrderStatus.REJECTED:
                return
            raise RuntimeError('Unexpected private order update')
        if event.status==OrderStatus.ACCEPTED:
            order['state']='live'
        if event.filled_quantity:
            sign=1 if order['side']==Side.BUY else -1
            was_flat=self.inventory==0
            self.inventory+=sign*event.filled_quantity
            if was_flat and self.burst:
                self.expires=event.timestamp_us+BURST_US
            self.max_inventory=max(self.max_inventory,abs(self.inventory))
            if abs(self.inventory)>CAP:
                raise RuntimeError('Inventory exceeds cap')
            race=order['state']=='cancel_pending'
            self.cancel_races+=event.filled_quantity if race else 0
            self.fills.append((event.timestamp_us,sign,event.fill_price,event.filled_quantity,race))
        order['remaining']=event.remaining_quantity
        if event.status==OrderStatus.REJECTED:
            self.rejections+=1
            if order['state']=='cancel_pending':
                order['state']='live'
                return
        if event.status in (OrderStatus.FILLED,OrderStatus.CANCELED,OrderStatus.REJECTED):
            del self.orders[event.order_id]
