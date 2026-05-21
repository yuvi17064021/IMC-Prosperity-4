# IMC-Prosperity-4
This Github repo contains my codes and strategies for Algorithmic Trading rounds for IMC Prosperity 4

# Trading Strategies

This repository contains three independent strategy modules:

1. Snackpacks - pairs trading
2. Microchips - within-family lead-lag
3. Lattice movements

Each strategy is designed around a specific market structure observed in historical price data.

---

## Snackpacks - Pairs Trading

### Idea

The snackpack products show strong relationships with each other, but not every high-correlation pair is useful for trading.

The strongest practical signal was the spread:

```text
SNACKPACK_VANILLA - SNACKPACK_RASPBERRY
This spread showed mean-reverting behavior and produced a clean trading signal around the +/-100 threshold.

Signal
spread = vanilla_mid - raspberry_mid
If:

spread >= 100
then Vanilla is considered rich relative to Raspberry.

The strategy enters:

short Vanilla
long Raspberry
long Chocolate
short Strawberry
If:

spread <= -100
then Vanilla is considered cheap relative to Raspberry.

The strategy enters:

long Vanilla
short Raspberry
short Chocolate
long Strawberry
Sticky Signal
The signal is sticky.

That means if the spread is between -100 and +100, the strategy keeps the previous signal instead of immediately exiting.

spread >= +100 -> signal = -1
spread <= -100 -> signal = +1
otherwise      -> keep previous signal
This avoids repeatedly entering and exiting around the middle of the range.

Pistachio
SNACKPACK_PISTACHIO is excluded from the pairs basket.

It is traded separately using small passive market-making orders.

Microchips - Within-Family Lead-Lag
Idea
The microchip products showed delayed movement relationships inside the same product family.

Instead of trading every correlation directly, the strategy uses simple threshold-and-hold rules.

A leader product is observed over a window W. If the leader moves by more than a threshold T, the strategy trades the target product in the expected direction and holds the signal for H ticks.

Rule Format
Each rule has this structure:

{
    "id": "ov_circle",
    "history": "circle",
    "W": 200,
    "H": 200,
    "T": 110,
    "tgt": "MICROCHIP_OVAL",
    "sign": 1,
}
Meaning:

Look at the leader's price change over the last W ticks.
If move > T, create a positive signal.
If move < -T, create a negative signal.
Hold that signal for H ticks.
Example
For Oval:

Leader: MICROCHIP_CIRCLE
Target: MICROCHIP_OVAL
Window: 200
Hold: 200
Threshold: 110
If Circle rises by more than 110 over the last 200 ticks:

buy Oval
If Circle falls by more than 110 over the last 200 ticks:

sell Oval
Voting
Multiple rules can vote on the same target.

vote > 0 -> target long
vote < 0 -> target short
vote = 0 -> target flat
The strategy then walks the product toward the desired target position.

Lattice Movements
Idea
The lattice strategy watches price movements on a rounded grid instead of reacting to every small price change.

It asks:

Did the price just jump too far too quickly?
If yes, it assumes the move may be an overreaction and trades for mean reversion.

Grid
Prices are rounded to a lattice grid:

grid_mid = round_to_grid(mid)
Example with grid size 10:

101 -> 100
106 -> 110
114 -> 110
116 -> 120
This filters out small noise.

Big Jump Signal
The strategy compares the current grid price with the previous grid price:

grid_jump = grid_mid - previous_grid
If:

abs(grid_jump) >= jump_min
then a large movement has occurred.

The signal is contrarian:

price jumps up   -> short
price jumps down -> long
Regimes
The strategy tracks simple regimes:

cold          -> no previous signal
hundred_snap  -> active big-jump reversal signal
small_lattice -> smaller grid movement after the snap
stale         -> old signal expired
Exit Logic
After a big jump, if smaller lattice moves appear, the strategy stops forcing the reversal.

This prevents the bot from fighting a move that keeps developing.

Signals also expire after a stale tick limit.

Execution
During an active snap signal:

signal > 0 -> walk toward long limit
signal < 0 -> walk toward short limit
When there is no active snap signal, the strategy may place small passive market-making orders depending on the product configuration.

Summary
Strategy	Core Signal	Main Behavior
Snackpacks	Vanilla - Raspberry spread	Mean-reversion basket
Microchips	Leader move over window W	Lead-lag threshold-and-hold
Lattice	Large rounded-grid price jump	Contrarian snap reversal
Each strategy uses persistent traderData to remember signals, histories, holds, and regimes between ticks.
