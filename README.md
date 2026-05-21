# IMC Prosperity 4

This repository contains my final trading code for IMC Prosperity 4.

I built the code around a reusable `ProductTrader` base class so that I could use the same order-book, position-limit, and order-placement logic across multiple products. Each actual strategy is written as a separate trader class on top of that base.

The main idea was to avoid writing the same trading utilities again and again. `ProductTrader` handles the common parts, while each strategy only focuses on its own signal and execution logic.

---

## What I Tried

Round 5 introduced 50 new products across 10 different product groups. Since every product had a position limit of `10`, I had to be selective about which products and strategies were worth using.

I tested different ideas across the product groups and kept the ones that looked most useful in backtesting.

The final code mainly uses:

- market making for products where simple spread capture worked best
- Snackpack pairs trading using the Vanilla and Raspberry spread
- Microchip lead-lag rules between related microchip products
- lattice reversal trading for products with large grid-like jumps
- market making on Pebbles after the basket approach did not perform well enough

---

## Code Structure

The code is built around this structure:

```text
ProductTrader
├── StaticTrader
├── SnackpackPairsTrader
├── MicrochipRuleTrader
└── LatticeTrader
```

`ProductTrader` is the base class used by all strategies.

It handles things like:

- reading the order book
- finding the best bid and best ask
- checking current position
- calculating how much I am allowed to buy or sell
- placing buy and sell orders
- storing data between ticks using `traderData`

This made the rest of the code much cleaner because every strategy could reuse the same basic trading tools.

---

## Product Routing

The final `Trader.run()` function decides which strategy should trade each product.

Instead of mixing all logic together, each product is routed to one trader class.

For example:

```text
Microchips     -> MicrochipRuleTrader
Snackpacks     -> SnackpackPairsTrader
Lattice names  -> LatticeTrader
General names  -> StaticTrader
Pebbles        -> StaticTrader
```

This was important because I did not want two different strategies trading the same product at the same time and fighting over the same position limit.

---

# Strategies

## 1. Static Market Making

For many products, the best approach was simple market making.

The strategy places buy and sell orders around the current market. It tries to buy slightly cheaper and sell slightly higher while staying inside the position limit.

The basic idea is:

```text
place buy orders near the best bid
place sell orders near the best ask
take obvious cheap asks or expensive bids when available
```

This worked well as a general strategy because not every product had a strong predictable signal. For those products, capturing spread was more reliable than forcing a complicated model.

I also used this approach for Pebbles in the final version.

---

## 2. Pebbles

At first, I tried to trade Pebbles as a basket.

The idea was to compare the combined value of:

```text
PEBBLES_XS
PEBBLES_S
PEBBLES_M
PEBBLES_L
PEBBLES_XL
```

against a target value.

The basket logic checked:

```python
buy_cost = sum(best_asks)
sell_proceeds = sum(best_bids)
```

If the basket looked cheap or expensive, the strategy tried to trade all Pebbles together.

But in testing, this did not give enough profit. The main problem was that there were five legs, each product had a small position limit, and the edge was not always large enough after considering spread and execution.

So I decided to stop using basket arbitrage for Pebbles and instead trade them with the normal market-making strategy.

This was simpler and gave better results.

---

## 3. Snackpacks

For Snackpacks, I found that the most useful signal came from the spread between Vanilla and Raspberry:

```text
SNACKPACK_VANILLA - SNACKPACK_RASPBERRY
```

The strategy calculates:

```python
spread = vanilla_mid - raspberry_mid
```

When the spread became too high, Vanilla looked expensive compared to Raspberry.

When the spread became too low, Vanilla looked cheap compared to Raspberry.

The entry logic was:

```text
if spread >= 100:
    short Vanilla
    long Raspberry
    long Chocolate
    short Strawberry

if spread <= -100:
    long Vanilla
    short Raspberry
    short Chocolate
    long Strawberry
```

I also made the signal sticky. That means if the spread moved back into the normal range, the strategy did not immediately close everything. It kept the previous signal until a new opposite signal appeared.

This helped reduce unnecessary trading when the spread moved around the threshold.

`SNACKPACK_PISTACHIO` was not included in the main basket. I handled it separately with small passive market-making orders.

---

## 4. Microchips

For Microchips, I used a lead-lag idea.

The idea was that one microchip product could move first, and another related product could follow later.

Instead of using one big model, I wrote simple rules.

Example rule:

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

This means:

- look at the price history of Circle
- compare the current price to the price `200` ticks ago
- if the move is bigger than `110`, create a signal
- hold that signal for `200` ticks
- trade Oval based on that signal

The logic is:

```text
if leader moved up strongly:
    buy target

if leader moved down strongly:
    sell target
```

Some rules can vote on the same product. The votes are combined:

```text
positive vote -> target long
negative vote -> target short
zero vote     -> target flat
```

Then the strategy moves the position toward that target.

This worked well because it kept the logic simple but still captured delayed movement between related products.

---

## 5. Lattice Strategy

Some products had large jump-like price movements.

For these, I used a lattice strategy. Instead of looking at every small price change, I rounded the mid price to a grid.

Example with grid size `10`:

```text
101 -> 100
106 -> 110
114 -> 110
116 -> 120
```

Then I compared the current grid price with the previous grid price:

```python
grid_jump = grid_mid - previous_grid
```

If the jump was large enough, the strategy assumed the move may have gone too far.

The signal was contrarian:

```text
price jumps up   -> short
price jumps down -> long
```

So if the product jumped upward by a large amount, the strategy sold. If it jumped downward by a large amount, the strategy bought.

The strategy also tracked regimes like:

```text
cold
hundred_snap
small_lattice
stale
```

This helped decide whether the reversal signal was still active or whether it should stop trading aggressively.

When there was no active lattice signal, the strategy used small passive market-making orders.

---

## State Persistence

Some strategies need memory across ticks.

For example:

- Snackpacks need to remember the previous signal
- Microchips need to store price histories and hold timers
- Lattice needs to remember the previous grid price and regime

I used `traderData` for this.

At the start of each tick, the code loads the old data:

```python
new_trader_data = json.loads(state.traderData) if state.traderData else {}
```

At the end of each tick, it saves the updated data:

```python
final_trader_data = json.dumps(new_trader_data, separators=(",", ":"))
```

This allowed the strategies to keep their state while still working inside the IMC trading engine.

---

## Risk Management

All products in Round 5 had a position limit of `10`.

The base trader calculates how much more I can buy or sell:

```python
max_allowed_buy_volume = position_limit - current_position
max_allowed_sell_volume = position_limit + current_position
```

Every order is clipped using these limits.

This makes sure the strategy does not place orders that would go beyond the allowed position.

---

## Final Approach

The final approach was not to use one single strategy for everything.

Instead, I used different strategies depending on what worked best for each product group:

| Product Type | Strategy Used |
|---|---|
| General products | Static market making |
| Pebbles | Static market making |
| Snackpacks | Pairs/basket trading |
| Microchips | Lead-lag rule trading |
| Selected jumpy products | Lattice reversal trading |

The most important part was testing which behavior each group had and then choosing the simplest strategy that worked.

---

## Summary

Overall, my approach was:

1. build a reusable base trading class
2. test different strategies on different product groups
3. keep the strategies that showed useful behavior
4. route each product to only one strategy
5. use `traderData` to store state between ticks
6. keep all orders inside the position limit

These strategies were written specifically for the IMC Prosperity 4 simulation environment. They are not meant to be production trading systems, but they show how I approached signal research, strategy design, and code structure during the competition.
