import json
from typing import Any

from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        lo, hi = 0, min(len(value), max_length)
        out = ""

        while lo <= hi:
            mid = (lo + hi) // 2

            candidate = value[:mid]
            if len(candidate) < len(value):
                candidate += "..."

            encoded_candidate = json.dumps(candidate)

            if len(encoded_candidate) <= max_length:
                out = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        return out


logger = Logger()

from datamodel import (
    OrderDepth, TradingState, Order, Listing, Observation,
    ProsperityEncoder, Symbol, Trade,
)
import json
from typing import Any, Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# Strategy parameters
# ─────────────────────────────────────────────────────────────────────────────

HP_PRODUCT   = "HYDROGEL_PACK"
HP_FAIR      = 9990
HP_THRESHOLD_BUY = 8
HP_THRESHOLD_SELL = 40
HP_LIMIT     = 200

VEV_PRODUCT   = "VELVETFRUIT_EXTRACT"
VEV_FAIR      = 5250
VEV_THRESHOLD = 28
VEV_LIMIT     = 200

# Voucher leverage: when VEV signal fires, also trade these in the same direction
LEVERAGE_VOUCHERS = ["VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_4000", "VEV_4500"]
VOUCHER_LIMIT     = 300


def fixed_fair_mr(product, fair, threshold_buy, threshold_sell, limit, state, result, signal):
    """
    Threshold-latched fixed-fair MR. When mid crosses a threshold the signal
    latches (+1 buy / -1 sell) and the strategy keeps filling toward the limit
    on every subsequent tick — regardless of where mid is — until the opposite
    threshold flips it. Mutates `result` and `signal` in place.
    """
    od = state.order_depths.get(product)
    if not (od and od.buy_orders and od.sell_orders):
        return
    pos = state.position.get(product, 0)
    best_bid = max(od.buy_orders)
    best_ask = min(od.sell_orders)
    mid = (best_bid + best_ask) / 2

    sig = signal.get(product, 0)
    if mid < fair - threshold_buy:
        sig = +1
    elif mid > fair + threshold_sell:
        sig = -1
    signal[product] = sig

    orders: List[Order] = []
    if sig > 0 and pos < limit:
        qty = min(-od.sell_orders[best_ask], limit - pos)
        if qty > 0:
            orders.append(Order(product, best_ask, qty))
    elif sig < 0 and pos > -limit:
        qty = min(od.buy_orders[best_bid], limit + pos)
        if qty > 0:
            orders.append(Order(product, best_bid, -qty))

    if orders:
        result[product] = orders


def fixed_fair_mr_with_leverage(product, fair, threshold, limit,
                                  leverage_vouchers, voucher_limit,
                                  state, result, signal):
    """
    Threshold-latched fixed-fair MR on `product` (latches the signal once a
    threshold is crossed, then fills toward the limit on every subsequent tick
    until the opposite threshold flips it). While the signal is non-zero,
    `leverage_vouchers` are filled toward `voucher_limit` in the same
    direction. Mutates `result` and `signal` in place.
    """
    od = state.order_depths.get(product)
    if not (od and od.buy_orders and od.sell_orders):
        return
    pos = state.position.get(product, 0)
    best_bid = max(od.buy_orders)
    best_ask = min(od.sell_orders)
    mid = (best_bid + best_ask) / 2

    sig = signal.get(product, 0)
    if mid < fair - threshold:
        sig = +1
    elif mid > fair + threshold:
        sig = -1
    signal[product] = sig

    if sig > 0 and pos < limit:
        qty = min(-od.sell_orders[best_ask], limit - pos)
        if qty > 0:
            result.setdefault(product, []).append(Order(product, best_ask, qty))
    elif sig < 0 and pos > -limit:
        qty = min(od.buy_orders[best_bid], limit + pos)
        if qty > 0:
            result.setdefault(product, []).append(Order(product, best_bid, -qty))

    if sig == 0:
        return

    for v in leverage_vouchers:
        v_od = state.order_depths.get(v)
        if not (v_od and v_od.buy_orders and v_od.sell_orders):
            continue
        v_pos = state.position.get(v, 0)
        v_bid = max(v_od.buy_orders)
        v_ask = min(v_od.sell_orders)
        if sig > 0 and v_pos < voucher_limit:
            v_qty = min(-v_od.sell_orders[v_ask], voucher_limit - v_pos)
            if v_qty > 0:
                result.setdefault(v, []).append(Order(v, v_ask, v_qty))
        elif sig < 0 and v_pos > -voucher_limit:
            v_qty = min(v_od.buy_orders[v_bid], voucher_limit + v_pos)
            if v_qty > 0:
                result.setdefault(v, []).append(Order(v, v_bid, -v_qty))


class Trader:
    def __init__(self):
        self._signal: Dict[str, int] = {}

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}

        fixed_fair_mr(HP_PRODUCT, HP_FAIR, HP_THRESHOLD_BUY, HP_THRESHOLD_SELL, HP_LIMIT, state, result, self._signal)
        fixed_fair_mr_with_leverage(
            VEV_PRODUCT, VEV_FAIR, VEV_THRESHOLD, VEV_LIMIT,
            LEVERAGE_VOUCHERS, VOUCHER_LIMIT,
            state, result, self._signal,
        )

        trader_data = ""
        conversions = 0

        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data
