"""
Production-grade Limit Order Book (L3/L2) Reconstruction & Microstructure Analytics Engine.
Designed according to quantitative trading standards (Jane Street / Citadel style).

Processes L3 Market-by-Order event streams, tracks FIFO queue priority,
reconstructs aggregate Level 2 depth, and computes microstructure signals:
- Order Book Imbalance (OBI - Level 1 and Depth-Weighted)
- Micro-Price (Volume-Weighted Midpoint)
- Spread & Mid-Price dynamics
- Order Flow Imbalance (OFI)
"""

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


class OrderSide(Enum):
    BID = "B"
    ASK = "S"


class OrderOp(Enum):
    INSERT = "Insert"
    CANCEL = "Cancel"
    MODIFY = "Modify"
    EXECUTE = "Execute"


@dataclass(slots=True)
class Order:
    order_id: int
    side: OrderSide
    price: int
    volume: int
    timestamp: float
    lifespan: str


class LimitOrderBook:
    """
    In-memory Order-by-Order (L3) reconstruction engine with L2 aggregation.
    Maintains FIFO order queues per price tick for accurate queue tracking.
    """
    def __init__(self):
        # Active order index: order_id -> Order
        self.orders: Dict[int, Order] = {}
        
        # L2 aggregated books: price -> cumulative volume
        self.bids: Dict[int, int] = {}
        self.asks: Dict[int, int] = {}
        
        # L3 FIFO Queues per price level: price -> list of order_ids
        self.bid_queues: Dict[int, List[int]] = {}
        self.ask_queues: Dict[int, List[int]] = {}
        self._previous_bbo: Optional[Tuple[Optional[int], Optional[int], int, int]] = None

    def process_event(
        self,
        timestamp: float,
        op_str: str,
        order_id: int,
        side_str: str,
        volume: int,
        price: int,
        lifespan: str = "G"
    ) -> Dict[str, float]:
        """
        Processes a single L3 event and updates internal book state.
        Returns instantaneous microstructure snapshot.
        """
        side = OrderSide.BID if side_str.upper() in ("B", "BID") else OrderSide.ASK
        op = OrderOp(op_str)

        if op == OrderOp.INSERT:
            self._handle_insert(order_id, side, price, volume, timestamp, lifespan)
        elif op == OrderOp.CANCEL:
            self._handle_cancel(order_id)
        elif op == OrderOp.MODIFY:
            self._handle_modify(order_id, volume, price, timestamp)
        elif op == OrderOp.EXECUTE:
            self._handle_execute(order_id, volume)

        return self.get_microstructure_snapshot(timestamp)

    def _handle_insert(self, order_id: int, side: OrderSide, price: int, volume: int, timestamp: float, lifespan: str):
        order = Order(
            order_id=order_id,
            side=side,
            price=price,
            volume=volume,
            timestamp=timestamp,
            lifespan=lifespan
        )
        self.orders[order_id] = order

        if side == OrderSide.BID:
            self.bids[price] = self.bids.get(price, 0) + volume
            if price not in self.bid_queues:
                self.bid_queues[price] = []
            self.bid_queues[price].append(order_id)
        else:
            self.asks[price] = self.asks.get(price, 0) + volume
            if price not in self.ask_queues:
                self.ask_queues[price] = []
            self.ask_queues[price].append(order_id)

    def _handle_cancel(self, order_id: int):
        if order_id not in self.orders:
            return
        order = self.orders.pop(order_id)
        price = order.price
        vol = order.volume

        if order.side == OrderSide.BID:
            self.bids[price] -= vol
            if self.bids[price] <= 0:
                self.bids.pop(price, None)
            if price in self.bid_queues and order_id in self.bid_queues[price]:
                self.bid_queues[price].remove(order_id)
                if not self.bid_queues[price]:
                    self.bid_queues.pop(price, None)
        else:
            self.asks[price] -= vol
            if self.asks[price] <= 0:
                self.asks.pop(price, None)
            if price in self.ask_queues and order_id in self.ask_queues[price]:
                self.ask_queues[price].remove(order_id)
                if not self.ask_queues[price]:
                    self.ask_queues.pop(price, None)

    def _handle_modify(self, order_id: int, new_volume: int, new_price: int, timestamp: float):
        if order_id not in self.orders:
            return
        # A modify event in exchange matching engines typically loses queue priority
        # if size increases or price changes.
        lifespan = self.orders[order_id].lifespan
        side = self.orders[order_id].side
        self._handle_cancel(order_id)
        self._handle_insert(order_id, side, new_price, new_volume, timestamp, lifespan)

    def _handle_execute(self, order_id: int, exec_volume: int):
        if order_id not in self.orders:
            return
        order = self.orders[order_id]
        if exec_volume >= order.volume:
            self._handle_cancel(order_id)
        else:
            order.volume -= exec_volume
            if order.side == OrderSide.BID:
                self.bids[order.price] -= exec_volume
            else:
                self.asks[order.price] -= exec_volume

    def get_best_bid_ask(self) -> Tuple[Optional[int], Optional[int], int, int]:
        best_bid = max(self.bids.keys()) if self.bids else None
        best_ask = min(self.asks.keys()) if self.asks else None
        bid_vol = self.bids[best_bid] if best_bid is not None else 0
        ask_vol = self.asks[best_ask] if best_ask is not None else 0
        return best_bid, best_ask, bid_vol, ask_vol

    def get_microstructure_snapshot(self, timestamp: float) -> Dict[str, float]:
        bb, ba, vb, va = self.get_best_bid_ask()

        mid_price = np.nan
        spread = np.nan
        obi = np.nan
        micro_price = np.nan
        ofi_event = 0.0

        if self._previous_bbo is not None:
            old_bb, old_ba, old_vb, old_va = self._previous_bbo
            if bb is None and old_bb is not None:
                ofi_event -= old_vb
            elif bb is not None and old_bb is None:
                ofi_event += vb
            elif bb is not None and old_bb is not None:
                ofi_event += vb if bb >= old_bb else -old_vb
            if ba is None and old_ba is not None:
                ofi_event += old_va
            elif ba is not None and old_ba is None:
                ofi_event -= va
            elif ba is not None and old_ba is not None:
                ofi_event += old_va if ba <= old_ba else -va

        if bb is not None and ba is not None:
            mid_price = (bb + ba) / 2.0
            spread = ba - bb
            tot_vol = vb + va
            if tot_vol > 0:
                obi = (vb - va) / tot_vol
                # Micro-price = P_bid * (V_ask / V_tot) + P_ask * (V_bid / V_tot)
                micro_price = bb * (va / tot_vol) + ba * (vb / tot_vol)
        elif bb is not None and ba is None:
            # One-sided market (bid only)
            mid_price = float(bb)
            obi = 1.0
            micro_price = float(bb)
        elif ba is not None and bb is None:
            # One-sided market (ask only)
            mid_price = float(ba)
            obi = -1.0
            micro_price = float(ba)

        depth_bid = sorted(self.bids, reverse=True)[:5]
        depth_ask = sorted(self.asks)[:5]
        depth_bid_volume = sum(self.bids[price] for price in depth_bid)
        depth_ask_volume = sum(self.asks[price] for price in depth_ask)
        depth_total = depth_bid_volume + depth_ask_volume
        depth_obi = ((depth_bid_volume - depth_ask_volume) / depth_total
                 if depth_total else np.nan)

        self._previous_bbo = (bb, ba, vb, va)
        return {
            "timestamp": timestamp,
            "best_bid": bb if bb is not None else np.nan,
            "best_ask": ba if ba is not None else np.nan,
            "bid_vol": vb,
            "ask_vol": va,
            "spread": spread,
            "mid_price": mid_price,
            "micro_price": micro_price,
            "obi_l1": obi,
            "obi_depth5": depth_obi,
            "depth_bid5": depth_bid_volume,
            "depth_ask5": depth_ask_volume,
            "ofi_event": ofi_event,
            "spread_ticks": spread,
            "active_orders_count": len(self.orders),
        }

    def get_queue_ahead(self, order_id: int) -> int:
        """Calculates volume ahead in the FIFO queue for a specific resting order."""
        if order_id not in self.orders:
            return -1
        order = self.orders[order_id]
        queue = self.bid_queues[order.price] if order.side == OrderSide.BID else self.ask_queues[order.price]
        
        vol_ahead = 0
        for q_oid in queue:
            if q_oid == order_id:
                break
            vol_ahead += self.orders[q_oid].volume
        return vol_ahead


def analyze_l3_stream(csv_source, sample_every: int = 1) -> pd.DataFrame:
    """
    Reads L3 data and performs event-by-event simulation and feature extraction.
    """
    if isinstance(csv_source, str) and "\n" in csv_source:
        import io
        df_raw = pd.read_csv(io.StringIO(csv_source))
    else:
        df_raw = pd.read_csv(csv_source)

    # Standardize column names
    df_raw.columns = [c.strip() for c in df_raw.columns]

    lob = LimitOrderBook()
    records = []

    for event_number, (_, row) in enumerate(df_raw.iterrows(), start=1):
        t = float(row["Time"])
        op = str(row["Operation"]).strip()
        oid = int(row["OrderId"])
        side = str(row["Side"]).strip()
        vol = int(row["Volume"]) if pd.notna(row["Volume"]) else 0
        px = int(row["Price"]) if pd.notna(row["Price"]) else 0
        lifespan = str(row.get("Lifespan", "G")).strip()

        # Update book
        metrics = lob.process_event(t, op, oid, side, vol, px, lifespan)
        metrics["event_order_id"] = oid
        metrics["event_op"] = op
        metrics["event_side"] = side
        metrics["event_price"] = px
        metrics["event_volume"] = vol
        metrics["event_number"] = event_number
        if event_number == 1 or event_number % sample_every == 0:
            records.append(metrics)

    res_df = pd.DataFrame(records)
    return res_df


def build_indicator_report(signals: pd.DataFrame) -> Dict[str, object]:
    """Summarize signal ranges and their relationship with future mid-price moves."""
    signals = signals.sort_values("timestamp").reset_index(drop=True)
    report: Dict[str, object] = {
        "events_in_tape_sampled": int(len(signals)),
        "time_start": float(signals["timestamp"].min()),
        "time_end": float(signals["timestamp"].max()),
        "time_span_seconds": float(signals["timestamp"].max() - signals["timestamp"].min()),
        "operation_counts": signals["event_op"].value_counts().to_dict(),
        "missingness": signals.isna().mean().round(6).to_dict(),
        "indicators": {},
        "forward_mid_return_correlation": {},
    }

    indicator_names = [
        "obi_l1", "obi_depth5", "ofi_event", "spread_ticks", "micro_price",
        "depth_bid5", "depth_ask5",
    ]
    for name in indicator_names:
        values = signals[name].dropna()
        report["indicators"][name] = {
            "count": int(values.size),
            "mean": float(values.mean()) if len(values) else None,
            "std": float(values.std()) if len(values) > 1 else None,
            "min": float(values.min()) if len(values) else None,
            "median": float(values.median()) if len(values) else None,
            "max": float(values.max()) if len(values) else None,
        }

    timestamps = signals["timestamp"].to_numpy()
    mids = signals["mid_price"].to_numpy(dtype=float)
    for horizon in (1.0, 5.0, 30.0):
        future_indexes = np.searchsorted(timestamps, timestamps + horizon, side="left")
        valid = future_indexes < len(signals)
        future_returns = np.full(len(signals), np.nan)
        future_returns[valid] = mids[future_indexes[valid]] - mids[valid]
        report["forward_mid_return_correlation"][f"{horizon:g}s"] = {}
        for name in ("obi_l1", "obi_depth5", "ofi_event", "micro_price"):
            usable = valid & signals[name].notna().to_numpy() & np.isfinite(future_returns)
            if usable.sum() >= 3:
                report["forward_mid_return_correlation"][f"{horizon:g}s"][name] = float(
                    np.corrcoef(signals.loc[usable, name], future_returns[usable])[0, 1]
                )

    return report


def analyze_and_save(input_path: str, output_dir: str = "experiments/round1_indicators") -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    signals = analyze_l3_stream(input_path, sample_every=1000)
    signals.to_csv(output_path / "signals.csv", index=False)
    report = build_indicator_report(signals)
    report["input_file"] = input_path
    report["sampling"] = "first event plus every 1000th event; indicators are reconstructed on every event"
    (output_path / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))




if __name__ == "__main__":
    analyze_and_save("data/round1/round1.csv")