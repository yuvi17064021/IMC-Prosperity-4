# Round 5 Trading Strategies Detailed Explanation
---

## Core Architecture

The code is organized around one base trader class:

```python
class ProductTrader:
```

`ProductTrader` handles the common trading mechanics used by all strategies:

- reading the order book
- finding best bid and best ask
- calculating position limits
- tracking current inventory
- computing available buy and sell capacity
- creating buy and sell orders
- storing shared strategy state through `traderData`
- writing debug information into a shared print/log object

Each individual strategy then subclasses `ProductTrader`.

Example:

```python
class StaticTrader(ProductTrader):
    ...

class MicrochipRuleTrader(ProductTrader):
    ...

class SnackpackPairsTrader(ProductTrader):
    ...

class LatticeTrader(ProductTrader):
    ...
```

This keeps the strategy classes focused on trading logic instead of repeating order-book and position-limit code.

---

## Product Routing

The final `Trader.run()` function routes each product to the correct strategy class.

The routing logic ensures that each product is traded by only one strategy at a time. This is important because every product has a position limit of `10`, so running multiple strategies on the same product can cause them to compete with each other.

Example routing structure:

```python
TRADER_BY_PRODUCT = {
    "MICROCHIP_OVAL": MicrochipRuleTrader,
    "MICROCHIP_RECTANGLE": MicrochipRuleTrader,
    "MICROCHIP_TRIANGLE": MicrochipRuleTrader,

    "SNACKPACK_VANILLA": SnackpackPairsTrader,
    "SNACKPACK_RASPBERRY": SnackpackPairsTrader,
    "SNACKPACK_CHOCOLATE": SnackpackPairsTrader,
    "SNACKPACK_STRAWBERRY": SnackpackPairsTrader,
    "SNACKPACK_PISTACHIO": SnackpackPairsTrader,

    "ROBOT_DISHES": LatticeTrader,
    "ROBOT_IRONING": LatticeTrader,

    "PEBBLES_S": StaticTrader,
    "PEBBLES_L": StaticTrader,
    "PEBBLES_XL": StaticTrader,
}
```

Products without a strong statistical signal are handled with a simpler market-making strategy.

---

# Trading Strategies

The repository contains four main strategy types:

1. **Static Market Making**
2. **Snackpacks Pairs Trading**
3. **Microchips Lead-Lag Prediction**
4. **Lattice Movement Reversal Trading**

Each strategy is designed for a different type of market structure.

---

# 1. Static Market Making

## Overview

The static trader is a general-purpose market-making strategy used on products where a more specific alpha signal was either weak, unstable, or not profitable enough.

The strategy tries to capture spread by placing competitive buy and sell orders around the current market.

It is used as a fallback strategy for products that showed reasonable market-making behavior but did not justify a more complex model.

---

## Logic

The strategy first calculates a reference midpoint using the wider book structure.

It then:

1. takes clearly mispriced liquidity when prices cross mean-reversion bands
2. reduces inventory when profitable opportunities appear
3. places passive quotes near the best bid and best ask

Example:

```python
buy_band = wall_mid - 2
sell_band = wall_mid + 2
```

If asks are cheap relative to the band, the trader buys.

If bids are expensive relative to the band, the trader sells.

After taking opportunities, the strategy places passive quotes:

```python
bid_price = best_bid + 1
ask_price = best_ask - 1
```

If the spread is too tight or the quotes would cross, it falls back to quoting at the current best bid and best ask.

---

## Why This Strategy Is Useful

Static market making is simple but robust.

It does not depend on long histories or complex signals. This makes it useful for products where the main edge comes from consistently providing liquidity and capturing small spread opportunities.

---

# 2. Snackpacks — Pairs Trading

## Overview

The Snackpack products showed strong relationships with each other, but not every correlated pair produced a tradable signal.

The strongest observed relationship came from the spread:

```text
SNACKPACK_VANILLA - SNACKPACK_RASPBERRY
```

This spread displayed mean-reverting behavior and reacted strongly around the `+100` and `-100` regions.

---

## Core Signal

The strategy computes:

```python
spread = vanilla_mid - raspberry_mid
```

If the spread is high, Vanilla is treated as rich relative to Raspberry.

If the spread is low, Vanilla is treated as cheap relative to Raspberry.

---

## Entry Logic

When:

```text
spread >= 100
```

the strategy enters a short-Vanilla basket:

```text
short Vanilla
long Raspberry
long Chocolate
short Strawberry
```

When:

```text
spread <= -100
```

the strategy enters a long-Vanilla basket:

```text
long Vanilla
short Raspberry
short Chocolate
long Strawberry
```

The basket is designed to express the spread signal across multiple related Snackpack products instead of only trading Vanilla and Raspberry.

---

## Sticky Signal Logic

The Snackpack signal is sticky.

If the spread moves back inside the neutral zone, the strategy does not immediately flatten. Instead, it keeps the previous signal.

```python
if spread >= 100:
    signal = -1
elif spread <= -100:
    signal = 1
else:
    signal = previous_signal
```

This avoids excessive churn near the threshold.

The goal is to reduce repeated entries and exits when the spread oscillates around the neutral region.

---

## Pistachio Handling

`SNACKPACK_PISTACHIO` is excluded from the main basket signal.

Instead, Pistachio is traded with small passive market-making orders.

This is because Pistachio did not provide the same useful relationship as the other Snackpack products in the basket.

---

# 3. Microchips — Lead-Lag Prediction

## Overview

The Microchip products showed delayed movement relationships within the same product family.

The strategy is based on the idea that a large move in one product can predict a later move in another product.

Instead of trading raw correlations, the strategy uses a rule-based lead-lag framework.

Each rule contains:

- a leader history
- a lookback window
- a movement threshold
- a holding period
- a target product
- a direction mapping

---

## Rule Example

```python
{
    "id": "ov_circle",
    "history": "circle",
    "leader": "MICROCHIP_CIRCLE",
    "W": 200,
    "H": 200,
    "T": 110,
    "tgt": "MICROCHIP_OVAL",
    "sign": 1,
}
```

---

## Rule Parameters

| Parameter | Meaning |
|---|---|
| `id` | Unique rule identifier |
| `history` | Stored history series used by the rule |
| `leader` | Product whose movement is observed |
| `W` | Lookback window |
| `H` | Number of ticks to hold the signal |
| `T` | Movement threshold |
| `tgt` | Product traded by the rule |
| `sign` | Direction relationship between leader and target |

---

## Signal Logic

For each rule, the strategy measures:

```python
move = leader_mid_now - leader_mid_W_ticks_ago
```

If:

```text
move > T
```

then a positive signal is generated.

If:

```text
move < -T
```

then a negative signal is generated.

The signal is then mapped through `sign`:

```text
positive leader move -> sign
negative leader move -> -sign
```

For example, if `sign = 1`, the target is expected to move in the same direction as the leader.

---

## Holding Logic

Once a signal is triggered, it is held for `H` ticks.

This prevents the strategy from immediately losing conviction after one quiet tick.

The strategy can also reset the hold timer when a new signal appears in the same direction:

```python
MICRO_RESET_HOLD_ON_SAME_DIRECTION_SIGNAL = True
```

This allows repeated confirmation from the leader product to extend the target position.

---

## Voting System

Multiple rules can vote on the same target product.

Votes are aggregated by target:

```python
vote > 0  -> target long
vote < 0  -> target short
vote = 0  -> target flat
```

The execution layer then moves the target product toward the desired inventory.

```python
target_position = position_limit if vote > 0 else -position_limit if vote < 0 else 0
```

---

# 4. Lattice Movements — Grid-Based Reversal

## Overview

The lattice strategy looks for large discrete price jumps.

Instead of reacting to every small price update, the strategy rounds prices onto a grid and compares the current grid price to the previous grid price.

The idea is:

> If price jumps too far too quickly, the move may be an overreaction.

When a large snap move is detected, the strategy trades against the move.

---

## Grid Construction

The mid price is rounded to a fixed grid:

```python
grid_mid = round(mid / grid_size) * grid_size
```

Example with grid size `10`:

```text
101 -> 100
106 -> 110
114 -> 110
116 -> 120
```

This filters out small book noise.

---

## Large Jump Detection

The strategy computes:

```python
grid_jump = grid_mid - previous_grid
```

If:

```python
abs(grid_jump) >= LATTICE_JUMP_MIN
```

then a large lattice jump has occurred.

---

## Contrarian Signal

The signal is mean-reverting:

```text
price jumps up   -> short
price jumps down -> long
```

So:

```python
signal = -1 if grid_jump > 0 else 1
```

---

## Regime Tracking

The lattice strategy tracks a simple regime state.

| Regime | Meaning |
|---|---|
| `cold` | No active signal |
| `hundred_snap` | Large jump reversal signal active |
| `small_lattice` | Smaller move observed after the snap |
| `stale` | Signal expired |

This regime is saved in `traderData` so the strategy remembers its state across ticks.

---

## Exit Logic

The signal can stop in two ways:

1. Smaller lattice moves appear after the snap
2. The signal becomes stale after too many ticks

This helps prevent the strategy from repeatedly fading strong trends.

---

## Execution

When a snap signal is active, the trader moves toward:

```python
target_position = signal * position_limit
```

When no snap signal is active, the strategy falls back to small passive market-making orders.

---

# Pebbles Approach

## Initial Basket Attempt

The Pebbles products were initially tested as a five-product basket:

```text
PEBBLES_XS + PEBBLES_S + PEBBLES_M + PEBBLES_L + PEBBLES_XL
```

The idea was to compare the combined top-of-book basket value against a fixed target level.

```python
buy_cost = sum(best_asks)
sell_proceeds = sum(best_bids)
```

The strategy attempted to unwind existing basket risk when the basket appeared cheap or expensive.

---

## Why It Was Changed

In practice, the Pebbles basket approach did not produce enough profit.

The likely reasons were:

- position limits were small
- five legs made execution harder
- opportunities required all products to be available at useful prices
- basket edge was not large enough after spread and fill risk
- capital was better allocated to simpler spread capture

Because of this, Pebbles were moved to the simpler static market-making strategy.

---

# State Persistence

Several strategies depend on memory across ticks.

The code uses `traderData` to persist:

- price histories
- active signals
- hold timers
- spread state
- previous lattice grid
- regime labels
- target votes

At the start of each tick, the previous `traderData` is loaded.

At the end of each tick, updated strategy state is serialized back into JSON.

Example:

```python
new_trader_data = json.loads(state.traderData) if state.traderData else {}
final_trader_data = json.dumps(new_trader_data, separators=(",", ":"))
```

---

# Execution and Risk Management

Every strategy respects the competition position limit of `10` per product.

The base `ProductTrader` computes:

```python
max_allowed_buy_volume = position_limit - current_position
max_allowed_sell_volume = position_limit + current_position
```

Orders are clipped to these limits before being submitted.

This prevents strategies from exceeding product-level risk limits.

---

# Repository Structure

Suggested layout:

```text
.
├── README.md
├── trader.py
├── datamodel.py
├── research/
│   ├── snackpacks.md
│   ├── microchips.md
│   ├── lattice.md
│   └── pebbles.md
├── backtests/
│   └── notebooks/
└── results/
    └── logs/
```

---

# Strategy Summary

| Strategy | Products | Core Signal | Behavior |
|---|---|---|---|
| Static Market Making | Selected general products and Pebbles | Book midpoint / spread | Passive quoting and mean-reversion taking |
| Snackpacks | Vanilla, Raspberry, Chocolate, Strawberry, Pistachio | Vanilla - Raspberry spread | Basket mean reversion |
| Microchips | Oval, Rectangle, Triangle | Leader movement over window | Lead-lag prediction |
| Lattice | Selected jumpy products | Large rounded-grid move | Contrarian snap reversal |

---

# Notes

These strategies were developed specifically for the IMC Prosperity 4 simulation environment.

They are competition strategies, not production trading systems. The implementation prioritizes fast iteration, clear signal logic, position-limit safety, and robustness inside the IMC trading engine.
