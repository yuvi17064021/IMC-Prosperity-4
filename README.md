# IMC Prosperity 4

This repository contains my final trading code for IMC Prosperity 4.

I built the code around a reusable `ProductTrader` base class so that I could use the same order-book, position-limit, and order-placement logic across multiple products. Each actual strategy is written as a separate trader class on top of that base.

The main idea was to avoid writing the same trading utilities again and again. `ProductTrader` handles the common parts, while each strategy only focuses on its own signal and execution logic.

---
# Rounds 3 and 4 Strategy

For Rounds 3 and 4, I traded:

- `HYDROGEL_PACK`
- `VELVETFRUIT_EXTRACT`
- Velvetfruit Extract vouchers/options: `VEV_4000` to `VEV_6500`

At first, I tried to build an options strategy using the volatility smile of the vouchers. The idea was to compare voucher prices across strikes and find mispriced options. However, after testing, this did not give enough stable profit, so I decided to drop the volatility smile strategy.

Instead, I used a simpler approach based on mean reversion, directional signals, voucher leverage, and in Round 4, counterparty information.

---

## Hydrogel Pack Strategy

For `HYDROGEL_PACK`, I used a mean-reversion style strategy.

I set a fair value around:

```python
fair_value = 9990
```

The strategy looked at the current order book and compared the market level with this fair value.

If the market traded too low, the strategy became bullish.  
If the market traded too high, the strategy became bearish.

```python
if wall_mid < fair_value - buy_threshold:
    signal = +1

elif wall_mid > fair_value + sell_threshold:
    signal = -1
```

The signal was stored in `traderData`, so it could persist across ticks.

---

## Support and Resistance

For Hydrogel, I also added support and resistance levels.

```python
support_level = 9925
resistance_level = 10050
```

If the best ask was below the support level, the strategy bought aggressively.

If the best bid was above the resistance level, the strategy sold aggressively.

This helped the strategy react quickly when the market moved to extreme levels.

---

## Microstructure Trading

When there was no strong support or resistance signal, the strategy looked for small short-term opportunities around `wall_mid`.

It created a small band:

```python
buy_band = wall_mid - micro_band
sell_band = wall_mid + micro_band
```

If an ask was below the buy band, it bought.  
If a bid was above the sell band, it sold.

This was a simple way to capture local mispricing in the order book.

---

## Velvetfruit Extract Strategy

For `VELVETFRUIT_EXTRACT`, I used another mean-reversion signal.

I set a fair value around:

```python
fair_value = 5250
```

and used a threshold:

```python
threshold = 28
```

The strategy calculated the mid price:

```python
mid_price = (best_bid + best_ask) / 2
```

Then it generated a directional signal:

```python
if mid_price < fair_value - threshold:
    signal = +1

elif mid_price > fair_value + threshold:
    signal = -1
```

If the signal was positive, the strategy bought Velvetfruit Extract.  
If the signal was negative, the strategy sold Velvetfruit Extract.

---

## Voucher Strategy

Instead of using the volatility smile in the final version, I used the vouchers as directional leverage on the Velvetfruit Extract signal.

When the main Velvetfruit signal was bullish, the strategy bought vouchers.

When the main Velvetfruit signal was bearish, the strategy sold vouchers.

```text
bullish VELVETFRUIT_EXTRACT signal -> buy vouchers
bearish VELVETFRUIT_EXTRACT signal -> sell vouchers
```

The vouchers traded were:

```python
VEV_5000
VEV_5100
VEV_5200
VEV_5300
VEV_5400
VEV_4000
VEV_4500
```

Each voucher had its own position limit of `300`.

The strategy checked each voucher's order book and traded at the best bid or best ask depending on the signal.

---

## Voucher Market Making

When there was no active Velvetfruit signal, I allowed limited market making on selected vouchers:

```python
mm_vouchers = {"VEV_4000", "VEV_4500"}
```

The strategy only market made when the spread was wide enough:

```python
min_mm_spread = 4
```

It placed small orders inside the spread:

```python
bid_price = best_bid + 1
ask_price = best_ask - 1
```

This gave the strategy another way to earn small profits when there was no strong directional signal.

---

## Round 4 Counterparty Information

In Round 4, counterparty names became visible in the market trades.

I used this information to track one important participant:

```python
INFORMED_TRADER_ID_67 = "Mark 67"
```

The idea was that if Mark 67 was buying or selling persistently, that could give useful information about future price direction.

The strategy tracked whether Mark's activity was recent and whether the signal was still alive using timestamp windows:

```python
MARK_RECENT_WINDOW = 5000
MARK_STALE_WINDOW = 50000
```

This gave the strategy an extra source of information beyond just price and order book data.

---

## Risk Management

The strategy respected the round position limits:

```python
HYDROGEL_PACK: 200
VELVETFRUIT_EXTRACT: 200
Each voucher: 300
```

Before placing trades, the code checked current position and clipped order size so it did not exceed the allowed limit.

Example:

```python
trade_size = min(order_volume, position_limit - current_position)
```

This helped keep the strategy inside the competition rules.

---

## Final Approach

My final approach for Rounds 3 and 4 was:

1. try volatility smile trading on vouchers
2. drop it because it did not produce enough profit
3. use mean reversion for `HYDROGEL_PACK`
4. use mean reversion for `VELVETFRUIT_EXTRACT`
5. use vouchers as directional leverage
6. market make selected vouchers when there was no active signal
7. use Round 4 counterparty information to track Mark 67

The final strategy was simpler than a full options-pricing model, but it was more practical for the competition environment and worked better with the available signals.

# Rounds 5 Strategy

# What I Tried

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
