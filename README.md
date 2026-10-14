# Age of Modernity 🎖️⚓

A modern warfare Real-Time Strategy (RTS) game built in **Python** with **`pygame-ce`**, inspired by *Age of Empires II*.

Control an industrial nation, manage key wartime resources (Food, Steel, Fuel), and command combined land and naval forces against opposing nations.

---

## 🎮 Quick Start

### 1. Requirements
* Python 3.10+
* `pygame-ce` (installed via `pip install -r requirements.txt`)

### 2. Launching the Game
```bash
python main.py
```

### 3. Running Automated Tests
```bash
python -m pytest -v
```

---

## 🕹️ Controls

| Action | Control | Description |
| :--- | :--- | :--- |
| **Select Unit / Building** | `Left-Click` | Click on any unit or building to inspect its stats in the bottom HUD |
| **Box Select** | `Click & Drag (Left)` | Marquee box to select multiple friendly units simultaneously |
| **Move Order** | `Right-Click Ground` | Orders selected units to pathfind to target coordinates |
| **Attack Order** | `Right-Click Enemy` | Orders selected military or naval units to engage target |
| **Engineer: Build / Repair** | `Right-Click Structure` | With an Engineer selected, right-click an unfinished foundation or damaged building |
| **Engineer: Work Industry** | `Right-Click Farm/Plant` | Orders Engineer to work inside Farm, Factory, or Refinery to boost output |
| **Build Foundation** | `HUD Button` or `[1] - [5]` | With Engineer selected, select building from HUD and place foundation on map |
| **Train Units** | `HUD Button` or `[1] - [3]` | With HQ, Barracks, or Shipyard selected, queue unit production |
| **Pause / Menu** | `ESC` (when no unit selected) | Pauses simulation and opens menu with Resume, Save, Load a saved game, and Quit buttons |
| **Save / Load Progress** | `Pause Menu -> Save / Load` | Save new progress, overwrite existing saves, or load a saved game |
| **Building Rally Point** | `Right-Click` (with building selected) | Sets unit rally point marked with "X"; right-clicking building reverts to default |
| **Minimap Navigation** | `Left-Click Minimap` | Lower-right radar shows entire map and viewport rectangle; click to pan camera |
| **Cancel / Deselect** | `ESC` or `Right-Click` | Cancels building placement ghost or clears current selection |
| **Pan Camera** | `W, A, S, D` or `Arrows` | Smoothly scroll across the map and strait |

---

## 🏭 Economy & Industries

Modern countries run on three core strategic resources:
1. **🌾 Food:** Sustains personnel; used to train Engineers and Infantry. Produced by **Farms**.
2. **⚙️ Steel:** Heavy industrial metal; required for armored vehicles, artillery, ships, and structures. Produced by **Factories**.
3. **🛢️ Fuel:** Refined petroleum; required for mechanized armor, warships, and heavy weapons. Produced by **Oil Refineries**.

*Note: All production industries generate a baseline passive income, but assigning **Engineers** to work them drastically boosts their resource output.*

---

## ⚔️ Modern Military Roster

### Civilian Division
* **Engineer (`ENG`):** The backbone of your nation's industry. Constructs building foundations, repairs damaged armor and structures, and operates resource industries.

### Army (Land Operations)
* **Foot Soldier (`INF`):** Fast to train, cheap, short-to-medium rifle range.
* **Tank (`TNK`):** Heavily armored combat vehicle with high hit points and direct cannon fire.
* **Cannon (`ART`):** Slow heavy artillery delivering long-range siege bombardment against land and coastal targets.

### Navy (Maritime Operations)
* **Torpedo Boat (`TB`):** Fast, nimble patrol boat delivering devastating high-yield naval torpedo strikes.
* **Destroyer (`DD`):** Versatile warship with rapid-fire deck guns and solid armor.
* **Battleship (`BB`):** Capital dreadnought with massive armor and long-range naval guns capable of bombarding both naval vessels and coastal land installations.

---

## 🏛️ Buildings & Facilities

* **Command Center (`HQ`):** Main headquarters and drop-off depot. Trains Engineers.
* **Farm (`FRM`):** Agricultural facility producing Food.
* **Factory (`FAC`):** Heavy industrial plant refining raw materials into Steel.
* **Refinery (`REF`):** Petrochemical plant refining Fuel.
* **Barracks (`BAR`):** Army depot training Foot Soldiers, Tanks, and Cannons.
* **Naval Shipyard (`SHP`):** Must be placed on coastal shoreline bordering water. Constructs Torpedo Boats, Destroyers, and Battleships directly into the sea.

---

## 🏗️ Project Architecture

```
AgeOfModernity/
├── main.py                 # Game loop, window management, and frame runner
├── requirements.txt        # Dependencies (pygame-ce, pytest)
├── README.md               # User guide and control manual
├── assets/
│   └── sounds/             # Audio SFX (.wav / .ogg): gunfire, cannons, torpedoes
├── src/
│   ├── config.py           # Unit & building stat tables, terrain colors, dimensions
│   ├── audio.py            # SoundManager & procedural SFX synthesizer
│   ├── map_system.py       # Land/Coast/Water tile generator & domain-aware A* pathfinding
│   ├── economy.py          # Stockpile manager (Food, Steel, Fuel)
│   ├── combat.py           # Projectiles, artillery tracers, audio triggers, and combat effects
│   ├── entities/
│   │   ├── base.py         # Base entity with HP, armor, and damage calculations
│   │   ├── unit.py         # Unit state machine (Idle, Move, Attack, Build, Work)
│   │   └── building.py     # Foundations, construction progress, production queues
│   ├── game_state.py       # World coordinator, selection, orders, entity updates
│   ├── input_handler.py    # Marquee box, click handling, keyboard hotkeys
│   └── renderer.py         # Camera viewport, sprite silhouettes, health bars, AoE HUD
└── tests/
    └── test_mvp.py         # Automated pytest suite covering all MVP systems
```
