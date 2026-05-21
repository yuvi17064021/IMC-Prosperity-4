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

from datamodel import OrderDepth, TradingState, Order
import json
import numpy as np
import math
from statistics import NormalDist

_N = NormalDist()

####### GENERAL ####### GENERAL ####### GENERAL ####### GENERAL ####### GENERAL ####### GENERAL ####### GENERAL ####### GENERAL  


# --- Round 5 Product Constants ---

# Galaxy Sounds Recorders
GALAXY_SOUNDS_DARK_MATTER = 'GALAXY_SOUNDS_DARK_MATTER'
GALAXY_SOUNDS_BLACK_HOLES = 'GALAXY_SOUNDS_BLACK_HOLES'
GALAXY_SOUNDS_PLANETARY_RINGS = 'GALAXY_SOUNDS_PLANETARY_RINGS'
GALAXY_SOUNDS_SOLAR_WINDS = 'GALAXY_SOUNDS_SOLAR_WINDS'
GALAXY_SOUNDS_SOLAR_FLAMES = 'GALAXY_SOUNDS_SOLAR_FLAMES'

# Vertical Sleeping Pods
SLEEP_POD_SUEDE = 'SLEEP_POD_SUEDE'
SLEEP_POD_LAMB_WOOL = 'SLEEP_POD_LAMB_WOOL'
SLEEP_POD_POLYESTER = 'SLEEP_POD_POLYESTER'
SLEEP_POD_NYLON = 'SLEEP_POD_NYLON'
SLEEP_POD_COTTON = 'SLEEP_POD_COTTON'

# Organic Microchips
MICROCHIP_CIRCLE = 'MICROCHIP_CIRCLE'
MICROCHIP_OVAL = 'MICROCHIP_OVAL'
MICROCHIP_SQUARE = 'MICROCHIP_SQUARE'
MICROCHIP_RECTANGLE = 'MICROCHIP_RECTANGLE'
MICROCHIP_TRIANGLE = 'MICROCHIP_TRIANGLE'

# Purification Pebbles
PEBBLES_XS = 'PEBBLES_XS'
PEBBLES_S = 'PEBBLES_S'
PEBBLES_M = 'PEBBLES_M'
PEBBLES_L = 'PEBBLES_L'
PEBBLES_XL = 'PEBBLES_XL'

# Domestic Robots
ROBOT_VACUUMING = 'ROBOT_VACUUMING'
ROBOT_MOPPING = 'ROBOT_MOPPING'
ROBOT_DISHES = 'ROBOT_DISHES'
ROBOT_LAUNDRY = 'ROBOT_LAUNDRY'
ROBOT_IRONING = 'ROBOT_IRONING'

# UV-Visors
UV_VISOR_YELLOW = 'UV_VISOR_YELLOW'
UV_VISOR_AMBER = 'UV_VISOR_AMBER'
UV_VISOR_ORANGE = 'UV_VISOR_ORANGE'
UV_VISOR_RED = 'UV_VISOR_RED'
UV_VISOR_MAGENTA = 'UV_VISOR_MAGENTA'

# Instant Translators
TRANSLATOR_SPACE_GRAY = 'TRANSLATOR_SPACE_GRAY'
TRANSLATOR_ASTRO_BLACK = 'TRANSLATOR_ASTRO_BLACK'
TRANSLATOR_ECLIPSE_CHARCOAL = 'TRANSLATOR_ECLIPSE_CHARCOAL'
TRANSLATOR_GRAPHITE_MIST = 'TRANSLATOR_GRAPHITE_MIST'
TRANSLATOR_VOID_BLUE = 'TRANSLATOR_VOID_BLUE'

# Construction Panels
PANEL_1X2 = 'PANEL_1X2'
PANEL_2X2 = 'PANEL_2X2'
PANEL_1X4 = 'PANEL_1X4'
PANEL_2X4 = 'PANEL_2X4'
PANEL_4X4 = 'PANEL_4X4'

# Liquid Breath Oxygen Shakes
OXYGEN_SHAKE_MORNING_BREATH = 'OXYGEN_SHAKE_MORNING_BREATH'
OXYGEN_SHAKE_EVENING_BREATH = 'OXYGEN_SHAKE_EVENING_BREATH'
OXYGEN_SHAKE_MINT = 'OXYGEN_SHAKE_MINT'
OXYGEN_SHAKE_CHOCOLATE = 'OXYGEN_SHAKE_CHOCOLATE'
OXYGEN_SHAKE_GARLIC = 'OXYGEN_SHAKE_GARLIC'

# Protein Snack Packs
SNACKPACK_CHOCOLATE = 'SNACKPACK_CHOCOLATE'
SNACKPACK_VANILLA = 'SNACKPACK_VANILLA'
SNACKPACK_PISTACHIO = 'SNACKPACK_PISTACHIO'
SNACKPACK_STRAWBERRY = 'SNACKPACK_STRAWBERRY'
SNACKPACK_RASPBERRY = 'SNACKPACK_RASPBERRY'

POS_LIMITS = {
    # Galaxy Sounds Recorders
    GALAXY_SOUNDS_DARK_MATTER: 10,
    GALAXY_SOUNDS_BLACK_HOLES: 10,
    GALAXY_SOUNDS_PLANETARY_RINGS: 10,
    GALAXY_SOUNDS_SOLAR_WINDS: 10,
    GALAXY_SOUNDS_SOLAR_FLAMES: 10,

    # Vertical Sleeping Pods
    SLEEP_POD_SUEDE: 10,
    SLEEP_POD_LAMB_WOOL: 10,
    SLEEP_POD_POLYESTER: 10,
    SLEEP_POD_NYLON: 10,
    SLEEP_POD_COTTON: 10,

    # Organic Microchips
    MICROCHIP_CIRCLE: 10,
    MICROCHIP_OVAL: 10,
    MICROCHIP_SQUARE: 10,
    MICROCHIP_RECTANGLE: 10,
    MICROCHIP_TRIANGLE: 10,

    # Purification Pebbles
    PEBBLES_XS: 10,
    PEBBLES_S: 10,
    PEBBLES_M: 10,
    PEBBLES_L: 10,
    PEBBLES_XL: 10,

    # Domestic Robots
    ROBOT_VACUUMING: 10,
    ROBOT_MOPPING: 10,
    ROBOT_DISHES: 10,
    ROBOT_LAUNDRY: 10,
    ROBOT_IRONING: 10,

    # UV-Visors
    UV_VISOR_YELLOW: 10,
    UV_VISOR_AMBER: 10,
    UV_VISOR_ORANGE: 10,
    UV_VISOR_RED: 10,
    UV_VISOR_MAGENTA: 10,

    # Instant Translators
    TRANSLATOR_SPACE_GRAY: 10,
    TRANSLATOR_ASTRO_BLACK: 10,
    TRANSLATOR_ECLIPSE_CHARCOAL: 10,
    TRANSLATOR_GRAPHITE_MIST: 10,
    TRANSLATOR_VOID_BLUE: 10,

    # Construction Panels
    PANEL_1X2: 10,
    PANEL_2X2: 10,
    PANEL_1X4: 10,
    PANEL_2X4: 10,
    PANEL_4X4: 10,

    # Liquid Breath Oxygen Shakes
    OXYGEN_SHAKE_MORNING_BREATH: 10,
    OXYGEN_SHAKE_EVENING_BREATH: 10,
    OXYGEN_SHAKE_MINT: 10,
    OXYGEN_SHAKE_CHOCOLATE: 10,
    OXYGEN_SHAKE_GARLIC: 10,

    # Protein Snack Packs
    SNACKPACK_CHOCOLATE: 10,
    SNACKPACK_VANILLA: 10,
    SNACKPACK_PISTACHIO: 10,
    SNACKPACK_STRAWBERRY: 10,
    SNACKPACK_RASPBERRY: 10,
}
#CONVERSION_LIMIT = 10

LONG, NEUTRAL, SHORT = 1, 0, -1



# This is the base ProductTrader class that has all the commonly used utility attributes and methods already implemented for individual traders
class ProductTrader:

    def __init__(self, name, state, prints, new_trader_data, product_group=None):

        self.orders = []

        self.name = name
        self.state = state
        self.prints = prints
        self.new_trader_data = new_trader_data
        self.product_group = name if product_group is None else product_group

        self.last_traderData = self.get_last_traderData()

        self.position_limit = POS_LIMITS.get(self.name, 0)
        self.initial_position = self.state.position.get(self.name, 0) # position at beginning of round

        self.expected_position = self.initial_position # update this if you expect a certain change in position e.g. to already hedge


        self.mkt_buy_orders, self.mkt_sell_orders = self.get_order_depth()
        self.bid_wall, self.wall_mid, self.ask_wall = self.get_walls()
        self.best_bid, self.best_ask = self.get_best_bid_ask()

        self.max_allowed_buy_volume, self.max_allowed_sell_volume = self.get_max_allowed_volume() # gets updated when order created
        self.total_mkt_buy_volume, self.total_mkt_sell_volume = self.get_total_market_buy_sell_volume()

    def get_last_traderData(self):
                        
        last_traderData = {}
        try:
            if self.state.traderData != '':
                last_traderData = json.loads(self.state.traderData)
        except: self.log("ERROR", 'td')

        return last_traderData


    def get_best_bid_ask(self):

        best_bid = best_ask = None

        try:
            if len(self.mkt_buy_orders) > 0:
                best_bid = max(self.mkt_buy_orders.keys())
            if len(self.mkt_sell_orders) > 0:
                best_ask = min(self.mkt_sell_orders.keys())
        except: pass

        return best_bid, best_ask


    def get_walls(self):

        bid_wall = wall_mid = ask_wall = None

        try: bid_wall = min([x for x,_ in self.mkt_buy_orders.items()])
        except: pass
        
        try: ask_wall = max([x for x,_ in self.mkt_sell_orders.items()])
        except: pass

        try: wall_mid = (bid_wall + ask_wall) / 2
        except: pass

        return bid_wall, wall_mid, ask_wall
    
    def get_total_market_buy_sell_volume(self):

        market_bid_volume = market_ask_volume = 0

        try:
            market_bid_volume = sum([v for p, v in self.mkt_buy_orders.items()])
            market_ask_volume = sum([v for p, v in self.mkt_sell_orders.items()])
        except: pass

        return market_bid_volume, market_ask_volume
    

    def get_max_allowed_volume(self):
        max_allowed_buy_volume = self.position_limit - self.initial_position
        max_allowed_sell_volume = self.position_limit + self.initial_position
        return max_allowed_buy_volume, max_allowed_sell_volume

    def get_order_depth(self):

        order_depth, buy_orders, sell_orders = {}, {}, {}

        try: order_depth: OrderDepth = self.state.order_depths[self.name]
        except: pass
        try: buy_orders = {bp: abs(bv) for bp, bv in sorted(order_depth.buy_orders.items(), key=lambda x: x[0], reverse=True)}
        except: pass
        try: sell_orders = {sp: abs(sv) for sp, sv in sorted(order_depth.sell_orders.items(), key=lambda x: x[0])}
        except: pass

        return buy_orders, sell_orders
    

    def bid(self, price, volume, logging=True):
        abs_volume = min(abs(int(volume)), self.max_allowed_buy_volume)
        order = Order(self.name, int(price), abs_volume)
        if logging: self.log("BUYO", {"p":price, "s":self.name, "v":int(volume)}, product_group='ORDERS')
        self.max_allowed_buy_volume -= abs_volume
        self.orders.append(order)

    def ask(self, price, volume, logging=True):
        abs_volume = min(abs(int(volume)), self.max_allowed_sell_volume)
        order = Order(self.name, int(price), -abs_volume)
        if logging: self.log("SELLO", {"p":price, "s":self.name, "v":int(volume)}, product_group='ORDERS')
        self.max_allowed_sell_volume -= abs_volume
        self.orders.append(order)

    def log(self, kind, message, product_group=None):
        if product_group is None: product_group = self.product_group

        if product_group == 'ORDERS':
            group = self.prints.get(product_group, [])
            group.append({kind: message})
        else:
            group = self.prints.get(product_group, {})
            group[kind] = message

        self.prints[product_group] = group

    def get_orders(self):
        # overwrite this in each trader
        return {}

PEBBLES = [
    "PEBBLES_XS",
    "PEBBLES_S",
    "PEBBLES_M",
    "PEBBLES_L",
    "PEBBLES_XL",
]

PEBBLES_TARGET = 50_000


class PebblesBasketTrader(ProductTrader):
    def __init__(self, product_name, state, prints, new_trader_data):
        super().__init__(product_name, state, prints, new_trader_data)

    def top_of_book(self, product):
        depth = self.state.order_depths.get(product)
        if not depth or not depth.buy_orders or not depth.sell_orders:
            return None

        best_bid = max(depth.buy_orders)
        best_ask = min(depth.sell_orders)

        return {
            "bid": best_bid,
            "ask": best_ask,
            "bid_vol": abs(depth.buy_orders[best_bid]),
            "ask_vol": abs(depth.sell_orders[best_ask]),
        }

    def basket(self):
        books = {product: self.top_of_book(product) for product in PEBBLES}

        if any(book is None for book in books.values()):
            return None

        return {
            "books": books,
            "buy_cost": sum(books[product]["ask"] for product in PEBBLES),
            "sell_proceeds": sum(books[product]["bid"] for product in PEBBLES),
            "positions": {
                product: self.state.position.get(product, 0)
                for product in PEBBLES
            },
        }

    def passive_market_make(self):
        buy_price = self.best_bid + 1
        sell_price = self.best_ask - 1

        if buy_price >= sell_price:
            return

        self.bid(buy_price, self.max_allowed_buy_volume)
        self.ask(sell_price, self.max_allowed_sell_volume)

    def trade_basket_unwind(self, side, basket):
        books = basket["books"]
        positions = basket["positions"]

        if side == "buy":
            quantity = min(
                min(books[product]["ask_vol"], -positions.get(product, 0))
                for product in PEBBLES
            )

            if quantity > 0:
                self.bid(books[self.name]["ask"], quantity)

        elif side == "sell":
            quantity = min(
                min(books[product]["bid_vol"], positions.get(product, 0))
                for product in PEBBLES
            )

            if quantity > 0:
                self.ask(books[self.name]["bid"], quantity)

    def get_orders(self):
        self.orders = []

        if self.name not in PEBBLES:
            return {self.name: self.orders}

        if self.best_bid is None or self.best_ask is None:
            return {self.name: self.orders}

        basket = self.basket()
        if basket is None:
            return {self.name: self.orders}

        xl_position = basket["positions"].get(PEBBLES_XL, 0)

        if basket["buy_cost"] < PEBBLES_TARGET and xl_position < 0:
            self.trade_basket_unwind("buy", basket)

        elif basket["sell_proceeds"] > PEBBLES_TARGET and xl_position > 0:
            self.trade_basket_unwind("sell", basket)

        else:
            self.passive_market_make()

        return {self.name: self.orders}

SNACK_VANILLA = "SNACKPACK_VANILLA"
SNACK_RASPBERRY = "SNACKPACK_RASPBERRY"
SNACK_CHOCOLATE = "SNACKPACK_CHOCOLATE"
SNACK_STRAWBERRY = "SNACKPACK_STRAWBERRY"
SNACK_PISTACHIO = "SNACKPACK_PISTACHIO"

SNACKPACK_PRODUCTS = [
    SNACK_VANILLA,
    SNACK_RASPBERRY,
    SNACK_CHOCOLATE,
    SNACK_STRAWBERRY,
    SNACK_PISTACHIO,
]

SNACK_ENTRY_THRESHOLD = 100
SNACK_PISTACHIO_MM_SIZE = 2


class SnackpackPairsTrader(ProductTrader):
    DATA_KEY = "_snackpack_pairs"

    PAIR_PRODUCTS = [
        SNACK_VANILLA,
        SNACK_RASPBERRY,
        SNACK_CHOCOLATE,
        SNACK_STRAWBERRY,
    ]

    TARGETS = {
        -1: {
            SNACK_VANILLA: -1,
            SNACK_RASPBERRY: 1,
            SNACK_CHOCOLATE: 1,
            SNACK_STRAWBERRY: -1,
        },
        1: {
            SNACK_VANILLA: 1,
            SNACK_RASPBERRY: -1,
            SNACK_CHOCOLATE: -1,
            SNACK_STRAWBERRY: 1,
        },
    }

    def __init__(self, product_name, state, prints, new_trader_data):
        super().__init__(product_name, state, prints, new_trader_data)

        old = self.last_traderData.get(self.DATA_KEY, {})
        self.shared = self.new_trader_data.setdefault(self.DATA_KEY, {
            "signal": old.get("signal", 0),
            "spread": old.get("spread", 0),
        })

    def mid(self, product):
        depth = self.state.order_depths.get(product)
        if not depth or not depth.buy_orders or not depth.sell_orders:
            return None

        return (max(depth.buy_orders) + min(depth.sell_orders)) / 2

    def trade_to_position(self, target_position):
        delta = target_position - self.initial_position

        if delta > 0:
            self.bid(self.best_ask, min(delta, self.max_allowed_buy_volume))
        elif delta < 0:
            self.ask(self.best_bid, min(-delta, self.max_allowed_sell_volume))

    def passive_market_make(self, size):
        if size <= 0:
            return

        self.bid(self.best_bid, min(size, self.max_allowed_buy_volume))
        self.ask(self.best_ask, min(size, self.max_allowed_sell_volume))

    def update_signal(self):
        vanilla = self.mid(SNACK_VANILLA)
        raspberry = self.mid(SNACK_RASPBERRY)

        if vanilla is None or raspberry is None:
            return

        spread = vanilla - raspberry
        signal = int(self.shared.get("signal", 0))

        if spread >= SNACK_ENTRY_THRESHOLD:
            signal = -1
        elif spread <= -SNACK_ENTRY_THRESHOLD:
            signal = 1

        self.shared.update({
            "signal": signal,
            "spread": spread,
        })

    def get_target_position(self, signal):
        if signal == 0:
            return self.initial_position

        return self.TARGETS.get(signal, {}).get(self.name, 0) * self.position_limit

    def get_orders(self):
        self.orders = []

        if self.best_bid is None or self.best_ask is None:
            return {self.name: self.orders}

        if self.name == SNACK_PISTACHIO:
            self.passive_market_make(SNACK_PISTACHIO_MM_SIZE)
            return {self.name: self.orders}

        self.update_signal()

        signal = int(self.shared.get("signal", 0))
        target_position = self.get_target_position(signal)

        self.trade_to_position(target_position)

        return {self.name: self.orders}

MICRO_CIRCLE = "MICROCHIP_CIRCLE"
MICRO_OVAL = "MICROCHIP_OVAL"
MICRO_RECTANGLE = "MICROCHIP_RECTANGLE"
MICRO_SQUARE = "MICROCHIP_SQUARE"
MICRO_TRIANGLE = "MICROCHIP_TRIANGLE"

MICRO_RESET_HOLD_ON_SAME_DIRECTION_SIGNAL = True

MICRO_RULES = [
    {
        "id": "ov_circle",
        "history": "circle",
        "leader": MICRO_CIRCLE,
        "W": 200,
        "H": 200,
        "T": 110,
        "tgt": MICRO_OVAL,
        "sign": 1,
    },
    {
        "id": "re_circle",
        "history": "circle",
        "leader": MICRO_CIRCLE,
        "W": 175,
        "H": 175,
        "T": 95,
        "tgt": MICRO_RECTANGLE,
        "sign": 1,
    },
    {
        "id": "tr_oval",
        "history": "oval",
        "leader": MICRO_OVAL,
        "W": 250,
        "H": 250,
        "T": 233,
        "tgt": MICRO_TRIANGLE,
        "sign": 1,
    },
]

MICROCHIP_RULE_TARGETS = [
    MICRO_OVAL,
    MICRO_RECTANGLE,
    MICRO_TRIANGLE,
]


class MicrochipRuleTrader(ProductTrader):
    DATA_KEY = "_microchip_rules"

    def __init__(self, product_name, state, prints, new_trader_data):
        super().__init__(product_name, state, prints, new_trader_data)

        old = self.last_traderData.get(self.DATA_KEY, {})
        self.shared = self.new_trader_data.setdefault(self.DATA_KEY, {
            "histories": old.get("histories", {}),
            "signals": old.get("signals", {}),
            "holds": old.get("holds", {}),
            "target_votes": old.get("target_votes", {}),
            "last_timestamp": old.get("last_timestamp"),
        })

    def mid(self, product):
        depth = self.state.order_depths.get(product)
        if not depth or not depth.buy_orders or not depth.sell_orders:
            return None

        return (max(depth.buy_orders) + min(depth.sell_orders)) / 2

    def trade_to_position(self, target_position):
        delta = target_position - self.initial_position

        if delta > 0 and self.best_ask is not None:
            self.bid(self.best_ask, min(delta, self.max_allowed_buy_volume))

        elif delta < 0 and self.best_bid is not None:
            self.ask(self.best_bid, min(-delta, self.max_allowed_sell_volume))

    def update_signals_once(self):
        if self.shared.get("last_timestamp") == self.state.timestamp:
            return

        histories = self.shared["histories"] if isinstance(self.shared.get("histories"), dict) else {}
        signals = self.shared["signals"] if isinstance(self.shared.get("signals"), dict) else {}
        holds = self.shared["holds"] if isinstance(self.shared.get("holds"), dict) else {}

        for key, mid in {
            "circle": self.mid(MICRO_CIRCLE),
            "oval": self.mid(MICRO_OVAL),
        }.items():
            if mid is not None:
                histories.setdefault(key, []).append(mid)

        max_window_by_history = {}

        target_votes = {}

        for rule in MICRO_RULES:
            history_key = rule["history"]
            window = int(rule["W"])
            hold = int(rule["H"])
            threshold = float(rule["T"])
            target = str(rule["tgt"])
            sign = int(rule["sign"])
            rule_id = str(rule["id"])

            max_window_by_history[history_key] = max(
                max_window_by_history.get(history_key, 0),
                window,
            )

            hist = histories.get(history_key, [])
            active = int(signals.get(rule_id, 0))
            left = max(0, int(holds.get(rule_id, 0)) - 1)

            if left == 0:
                active = 0

            new_signal = 0
            if len(hist) > window:
                delta = float(hist[-1]) - float(hist[-1 - window])

                if delta > threshold:
                    new_signal = sign
                elif delta < -threshold:
                    new_signal = -sign

            if new_signal and (
                active == 0
                or new_signal != active
                or MICRO_RESET_HOLD_ON_SAME_DIRECTION_SIGNAL
            ):
                active = new_signal
                left = hold

            signals[rule_id] = active
            holds[rule_id] = left
            target_votes[target] = target_votes.get(target, 0) + active

        for key, max_window in max_window_by_history.items():
            histories[key] = histories.get(key, [])[-(max_window + 1):]

        self.shared.update({
            "histories": histories,
            "signals": signals,
            "holds": holds,
            "target_votes": target_votes,
            "last_timestamp": self.state.timestamp,
        })

    def get_orders(self):
        self.orders = []

        if self.best_bid is None or self.best_ask is None:
            return {self.name: self.orders}

        if self.name not in MICROCHIP_RULE_TARGETS:
            return {self.name: self.orders}

        self.update_signals_once()

        vote = int(self.shared.get("target_votes", {}).get(self.name, 0))
        target_position = self.position_limit if vote > 0 else -self.position_limit if vote < 0 else 0

        self.trade_to_position(target_position)

        return {self.name: self.orders}

LATTICE_GRID_SIZE = 10
LATTICE_JUMP_MIN = 95
LATTICE_STALE_TICKS = 1000
LATTICE_SMALL_EXIT_MOVES = 1


class LatticeTrader(ProductTrader):
    def __init__(self, product_name, state, prints, new_trader_data):
        super().__init__(product_name, state, prints, new_trader_data)

        old = self.last_traderData.get(self.name, {})
        self.data = self.new_trader_data.setdefault(self.name, {
            "prev_grid": old.get("prev_grid"),
            "signal": old.get("signal", 0),
            "ticks_since_jump": old.get("ticks_since_jump", LATTICE_STALE_TICKS),
            "small_moves_since_jump": old.get("small_moves_since_jump", 0),
            "regime": old.get("regime", "cold"),
        })

    def round_to_grid(self, price):
        return int(round(price / LATTICE_GRID_SIZE) * LATTICE_GRID_SIZE)

    def sweep_to_position(self, target_position):
        delta = target_position - self.initial_position

        if delta > 0:
            remaining = min(delta, self.max_allowed_buy_volume)

            for price, volume in self.mkt_sell_orders.items():
                if remaining <= 0:
                    break

                qty = min(volume, remaining)
                self.bid(price, qty)
                remaining -= qty

        elif delta < 0:
            remaining = min(-delta, self.max_allowed_sell_volume)

            for price, volume in self.mkt_buy_orders.items():
                if remaining <= 0:
                    break

                qty = min(volume, remaining)
                self.ask(price, qty)
                remaining -= qty

    def passive_market_make(self):
        mm_size = 2

        self.bid(self.best_bid, min(mm_size, self.max_allowed_buy_volume))
        self.ask(self.best_ask, min(mm_size, self.max_allowed_sell_volume))

    def update_signal(self):
        grid_mid = self.round_to_grid((self.best_bid + self.best_ask) / 2)

        previous = self.data.get("prev_grid")
        signal = int(self.data.get("signal", 0))
        stale = int(self.data.get("ticks_since_jump", LATTICE_STALE_TICKS))
        small_moves = int(self.data.get("small_moves_since_jump", 0))
        regime = str(self.data.get("regime", "cold"))

        big_jump = False

        if previous is None:
            stale = LATTICE_STALE_TICKS
            small_moves = 0
            regime = "cold"

        else:
            jump = grid_mid - int(previous)

            if abs(jump) >= LATTICE_JUMP_MIN:
                big_jump = True
                signal = -1 if jump > 0 else 1
                stale = 0
                small_moves = 0
                regime = "hundred_snap"

            else:
                stale += 1
                small_moves += int(jump != 0)

                if signal != 0 and small_moves >= LATTICE_SMALL_EXIT_MOVES:
                    signal = 0
                    regime = "small_lattice"
                elif signal != 0:
                    regime = "hundred_snap"
                elif jump != 0:
                    regime = "small_lattice"

                if stale >= LATTICE_STALE_TICKS:
                    signal = 0
                    if regime == "hundred_snap":
                        regime = "stale"

        self.data.update({
            "prev_grid": grid_mid,
            "signal": signal,
            "ticks_since_jump": stale,
            "small_moves_since_jump": small_moves,
            "regime": regime,
        })

        return big_jump, signal, regime

    def get_orders(self):
        self.orders = []

        if self.best_bid is None or self.best_ask is None:
            return {self.name: self.orders}

        big_jump, signal, regime = self.update_signal()

        if big_jump or regime == "hundred_snap":
            self.sweep_to_position(signal * self.position_limit)
        else:
            self.passive_market_make()

        return {self.name: self.orders}

class StaticTrader(ProductTrader):
    def __init__(self, product_name, state, prints, new_trader_data):
        # Initialise using the specific product name passed in
        super().__init__(product_name, state, prints, new_trader_data)

    def get_orders(self):
        self.orders = []
        pos_limit = POS_LIMITS.get(self.name, 10) # Using your new limit of 10

        best_bid = max(self.mkt_buy_orders.keys()) if self.mkt_buy_orders else None
        best_ask = min(self.mkt_sell_orders.keys()) if self.mkt_sell_orders else None

        if self.wall_mid is not None and best_bid and best_ask:

            # --- MEAN REVERSION BANDS ---
            buy_band = self.wall_mid - 2  
            sell_band = self.wall_mid + 2 

            ##########################################################
            ####### 1. TAKING (Mean Reversion Aggression)
            ##########################################################
            for sp, sv in self.mkt_sell_orders.items():
                if sp <= buy_band:
                    self.bid(sp, sv, logging=False)
                elif sp <= self.wall_mid and self.initial_position < 0:
                        volume = min(sv, abs(self.initial_position))
                        self.bid(sp, volume, logging=False)

            for bp, bv in self.mkt_buy_orders.items():
                if bp >= sell_band:
                    self.ask(bp, bv, logging=False)
                elif bp >= self.wall_mid and self.initial_position > 0:
                        volume = min(bv, self.initial_position)
                        self.ask(bp, volume, logging=False)

            ###########################################################
            ####### 2. MAKING (Competitive Quoting)
            ###########################################################
            bid_price = best_bid + 1 
            bid_volume = self.max_allowed_buy_volume
            
            ask_price = best_ask - 1
            ask_volume = self.max_allowed_sell_volume

            for bp, bv in self.mkt_buy_orders.items():
                overbidding_price = bp + 1
                if overbidding_price < self.wall_mid:
                    bid_price = max(bid_price, overbidding_price)
                    break

            for sp, sv in self.mkt_sell_orders.items():
                underbidding_price = sp - 1
                if underbidding_price > self.wall_mid:
                    ask_price = min(ask_price, underbidding_price)
                    break

            if ask_volume > 0: ask_volume = -ask_volume
            if bid_price >= ask_price:
                bid_price, ask_price = best_bid, best_ask

            self.bid(bid_price, bid_volume)
            self.ask(ask_price, ask_volume)

        return {self.name: self.orders}



class Trader:
    # 1. Configuration Dictionaries
    STATIC_PRODUCTS = [
        "GALAXY_SOUNDS_BLACK_HOLES", 
        "GALAXY_SOUNDS_DARK_MATTER", 
        "GALAXY_SOUNDS_PLANETARY_RINGS", 
        "GALAXY_SOUNDS_SOLAR_FLAMES", 
        "GALAXY_SOUNDS_SOLAR_WINDS", 
        "MICROCHIP_CIRCLE", 
        # "MICROCHIP_RECTANGLE", 
        # "MICROCHIP_SQUARE", 
        # "MICROCHIP_TRIANGLE", 
        "OXYGEN_SHAKE_GARLIC", 
        "OXYGEN_SHAKE_MINT", 
        "OXYGEN_SHAKE_MORNING_BREATH", 
        "PANEL_1X2", 
        "PANEL_1X4", 
        "PANEL_2X2", 
        "PANEL_2X4", 
        "PANEL_4X4", 
        "PEBBLES_L", 
        "PEBBLES_S", 
        "PEBBLES_XL", 
        "ROBOT_LAUNDRY", 
        #"ROBOT_IRONING",
        "SLEEP_POD_COTTON", 
        "SLEEP_POD_NYLON", 
        "SLEEP_POD_POLYESTER", 
        "SLEEP_POD_SUEDE", 
        # "SNACKPACK_CHOCOLATE", 
        # "SNACKPACK_PISTACHIO", 
        # "SNACKPACK_RASPBERRY", 
        # "SNACKPACK_STRAWBERRY", 
        # "SNACKPACK_VANILLA", 
        "TRANSLATOR_ASTRO_BLACK", 
        "TRANSLATOR_ECLIPSE_CHARCOAL", 
        "TRANSLATOR_GRAPHITE_MIST", 
        "TRANSLATOR_SPACE_GRAY", 
        "TRANSLATOR_VOID_BLUE", 
        "UV_VISOR_AMBER", 
        "UV_VISOR_MAGENTA", 
        "UV_VISOR_ORANGE", 
        "UV_VISOR_RED", 
        "UV_VISOR_YELLOW",
    ]
    
    # Product routing rules for IMC engine matching your architectural style
    LATTICE_PRODUCTS = [
        "ROBOT_DISHES",
        "ROBOT_IRONING",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_CHOCOLATE",
    ]

    MICROCHIP_RULE_TARGETS = [
        "MICROCHIP_OVAL",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_TRIANGLE",
    ]

    SNACKPACK_PRODUCTS = [
        "SNACKPACK_VANILLA",
        "SNACKPACK_RASPBERRY",
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_PISTACHIO",
    ]
    PEBBLES_PRODUCTS = [
        # "PEBBLES_XS",
        # "PEBBLES_S",
        # "PEBBLES_M",
        # "PEBBLES_L",
        # "PEBBLES_XL",
    ]



    TRADER_BY_PRODUCT = {
        **{product: StaticTrader for product in STATIC_PRODUCTS},
        **{product: LatticeTrader for product in LATTICE_PRODUCTS},
        **{product: MicrochipRuleTrader for product in MICROCHIP_RULE_TARGETS},
        **{product: SnackpackPairsTrader for product in SNACKPACK_PRODUCTS},
        **{product: PebblesBasketTrader for product in PEBBLES_PRODUCTS},
    }

    def run(self, state: TradingState):
        result = {}
        prints = {}

        try:
            new_trader_data = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            new_trader_data = {}

        for product, order_depth in state.order_depths.items():
            TraderClass = self.TRADER_BY_PRODUCT.get(product)

            if TraderClass is None:
                continue

            try:
                trader = TraderClass(product, state, prints, new_trader_data)
                orders = trader.get_orders().get(product, [])

                if orders:
                    result[product] = orders

            except Exception as e:
                prints[product] = {"ERROR": str(e)}

        final_trader_data = json.dumps(new_trader_data, separators=(",", ":"))
        return result, 0, final_trader_data
