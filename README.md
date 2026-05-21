# IMC-Prosperity-4

This repository contains my algorithmic trading strategies and implementations for the IMC Prosperity 4 competition.

The repo includes several independent trading systems built around different statistical and structural behaviors observed in historical market data.

---

# Trading Strategies

This repository contains three independent strategy modules:

1. **Snackpacks** — pairs trading and basket mean reversion  
2. **Microchips** — within-family lead-lag prediction  
3. **Lattice Movements** — contrarian grid-based reversal trading  

Each strategy is designed around a specific market structure.

---

# 1. Snackpacks — Pairs Trading

## Overview

The Snackpack products exhibit strong relationships with each other, but not every high-correlation pair produces a tradable signal.

The strongest and most stable signal came from the spread:

```text
SNACKPACK_VANILLA - SNACKPACK_RASPBERRY
```

This spread displayed clear mean-reverting behavior and consistently reacted around the `±100` region.

---

## Core Signal

```python
spread = vanilla_mid - raspberry_mid
```

### If:

```text
spread >= 100
```

Vanilla is considered **rich** relative to Raspberry.

The strategy enters:

```text
short Vanilla
long Raspberry
long Chocolate
short Strawberry
```

---

### If:

```text
spread <= -100
```

Vanilla is considered **cheap** relative to Raspberry.

The strategy enters:

```text
long Vanilla
short Raspberry
short Chocolate
long Strawberry
```

---

## Sticky Signal Logic

The trading signal is intentionally **sticky**.

If the spread moves back inside the neutral zone (`-100 < spread < 100`), the strategy keeps the previous position instead of immediately exiting.

```python
if spread >= 100:
    signal = -1

elif spread <= -100:
    signal = +1

else:
    signal = previous_signal
```

This prevents excessive churn and reduces noisy re-entry behavior around the center of the spread.

---

## Pistachio Handling

`SNACKPACK_PISTACHIO` is excluded from the pairs basket.

Instead, it is traded independently using small passive market-making orders.

---

# 2. Microchips — Within-Family Lead-Lag

## Overview

The Microchip products exhibited delayed movement relationships inside the same product family.

Rather than trading raw correlations directly, the strategy uses a simple:

- threshold
- hold
- vote

framework.

The idea is:

> If one product makes a sufficiently large move, another related product may react shortly afterward.

---

## Rule Structure

Each lead-lag rule follows this structure:

```python
{
    "id": "ov_circle",
    "history": "circle",
    "W": 200,
    "H": 200,
    "T": 110,
    "tgt": "MICROCHIP_OVAL",
    "sign": 1,
}
```

---

## Rule Meaning

| Parameter | Meaning |
|---|---|
| `W` | Lookback window |
| `H` | Signal hold duration |
| `T` | Trigger threshold |
| `tgt` | Target product |
| `sign` | Signal direction mapping |

The strategy:

1. Measures the leader's move over the previous `W` ticks
2. Compares the move against threshold `T`
3. Creates a directional signal
4. Holds that signal for `H` ticks

---

## Example

### Leader

```text
MICROCHIP_CIRCLE
```

### Target

```text
MICROCHIP_OVAL
```

### Parameters

```text
Window    = 200
Hold      = 200
Threshold = 110
```

### Trading Logic

If Circle rises by more than `110` over the previous `200` ticks:

```text
buy Oval
```

If Circle falls by more than `110`:

```text
sell Oval
```

---

## Voting System

Multiple rules can vote on the same target product.

```python
vote > 0  -> target long
vote < 0  -> target short
vote = 0  -> target flat
```

The execution layer then gradually walks the inventory toward the desired target position.

---

# 3. Lattice Movements — Grid-Based Reversal Trading

## Overview

The lattice strategy observes price movement on a rounded grid rather than reacting to every individual price update.

Core idea:

> Did price jump too far too quickly?

If yes, the move may represent an overreaction, creating a mean-reversion opportunity.

---

# Grid Construction

Prices are rounded onto a discrete lattice:

```python
grid_mid = round_to_grid(mid)
```

Example using grid size `10`:

```text
101 -> 100
106 -> 110
114 -> 110
116 -> 120
```

This helps filter out microstructure noise.

---

# Large Jump Detection

The strategy compares consecutive lattice prices:

```python
grid_jump = grid_mid - previous_grid
```

If:

```python
abs(grid_jump) >= jump_min
```

then a large movement is detected.

---

## Contrarian Signal

The signal is intentionally mean-reverting:

```text
price jumps up   -> short
price jumps down -> long
```

---

# Regime Tracking

The strategy tracks several simple internal regimes:

| Regime | Meaning |
|---|---|
| `cold` | No active signal |
| `hundred_snap` | Strong reversal signal active |
| `small_lattice` | Smaller continuation movement after snap |
| `stale` | Signal expired |

---

# Exit Logic

After a large snap move, if smaller lattice movements continue developing in the same direction, the strategy stops aggressively forcing the reversal.

This prevents the system from repeatedly fading strong momentum moves.

Signals also expire after a configurable stale threshold.

---

# Execution Logic

During an active reversal signal:

```text
signal > 0 -> move toward long inventory
signal < 0 -> move toward short inventory
```

When no active signal exists, the strategy may place passive market-making orders depending on the product configuration.

---

# Strategy Summary

| Strategy | Core Signal | Main Behavior |
|---|---|---|
| Snackpacks | Vanilla - Raspberry spread | Mean-reversion basket |
| Microchips | Leader move over window `W` | Lead-lag threshold & hold |
| Lattice | Large rounded-grid jumps | Contrarian snap reversal |

---

# State Persistence

All strategies use persistent `traderData` storage to maintain:

- signal state
- historical windows
- holding timers
- regime information
- execution context

across trading ticks.

---

# Repository Structure

```text
.
├── snackpacks/
├── microchips/
├── lattice/
├── backtests/
├── research/
└── README.md
```

---

# Notes

These strategies were developed specifically for the structure and constraints of the IMC Prosperity simulation environment and are primarily research/competition implementations rather than production trading systems.
