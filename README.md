# Age of Modernity 🎖️⚓

A modern warfare Real-Time Strategy (RTS) game built in **Python** with **`pygame-ce`**, inspired by *Age of Empires II*.

Control an industrial nation, manage key wartime resources (Food, Steel, Fuel), and command combined land and naval forces against opposing nations.

<img width="1915" height="1079" alt="image" src="https://github.com/user-attachments/assets/59215205-eb1e-4868-ab73-accf3f02b8e5" />


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
| **Build Foundation** | `HUD Button` or `[1] - [6]` | With Engineer selected, select building from HUD and place foundation on map |
| **Train Units** | `HUD Button` or `[1] - [3]` | With HQ, Barracks, or Shipyard selected, queue unit production |
| **Pause / Menu** | `ESC` (when no unit selected) | Pauses simulation and opens menu with Resume, Save, Load a saved game, and Quit buttons |
| **Save / Load Progress** | `Pause Menu -> Save / Load` | Save new progress, overwrite existing saves, or load a saved game |
| **Building Rally Point** | `Right-Click` (with building selected) | Sets unit rally point marked with "X"; right-clicking building reverts to default |
| **Zoom Camera** | `Mouse Wheel` | Smooth cursor-anchored zoom in and out (50% to 250%) |
| **Minimap Navigation** | `Left-Click Minimap` | Lower-right radar shows entire map and viewport rectangle; click to pan camera |
| **Cancel / Deselect** | `ESC` or `Right-Click` | Cancels building placement ghost or clears current selection |
| **Pan Camera** | `W, A, S, D` or `Arrows` | Smoothly scroll across the map and strait |

---

## 🗺️ Strategic Theaters & Maps

Select theaters via the top bar **MAPS** button:
1. **🏝️ Grand Archipelago (96x64 Showcase Theater):** A vast theater of war spanning across multiple large and small islands, sprawling peninsulas, organic bays, and central archipelagic chains. Specifically designed to showcase natural multi-frequency coastlines, sub-tile triangular terrain facets, and wide zoom scaling (50% to 250%).
2. **🌊 Divided Sea (64x48):** Western and Eastern landmasses separated by a central maritime strait. Heavy naval focus.
3. **⚔️ Continental Front (64x48):** A continuous land corridor connecting player and enemy territories for direct mechanized land warfare.
4. **🌉 Shattered Isthmus (64x48):** Flanked by northern and southern seas, connected across a central land bridge.
5. **🌀 Inland Sea (64x48):** A central sea encircled by northern and southern land corridors connecting both factions.

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

## 🎨 Customizing Graphics & Generative AI Asset Guide

Age of Modernity features an automatic sprite loading pipeline via `AssetManager` (`src/asset_manager.py`). You can replace the procedural 2.5D geometric shapes with custom artwork for any building or unit simply by dropping image files into `assets/sprites/`.

* **Format Support:** Supports `.png`, `.jpg`, `.jpeg`, `.webp`, and `.bmp` (with `.png` taking precedence if both exist).
* **In-Memory Downscaling & Crash Prevention:** High-resolution images (such as `2752 × 1536` AI outputs) are safely pre-normalized in memory to match their in-game isometric footprint, preventing memory exhaustion and crashes. **Original image files on disk are never altered**.
* **Automatic White Background Removal:** For `.jpg` images generated on solid white backgrounds, the engine automatically keys out outer white backgrounds using corner-connected flood-fill masking in memory, preserving white details (like vehicle stars or flag stripes) inside the entity.
* **Automatic Mirroring:** 8-direction units can be provided with just 5 directions (`n`, `ne`, `e`, `se`, `s`); western angles (`sw`, `w`, `nw`) are automatically mirrored in memory.
* **Procedural Fallback:** If an image is missing, the game smoothly falls back to its procedural vector graphics—allowing you to replace assets incrementally without crashes.

---

### 📁 1. Directory Structure & File Naming Reference

Sprites can be placed in `assets/sprites/` or its subdirectories (which are scanned recursively). Files are matched by converting the entity's configuration name to lowercase with underscores (`name.lower().replace(" ", "_") + ".png"` or `.jpg`).

#### Exact Folder Hierarchy
```text
AgeOfModernity/
└── assets/
    └── sprites/
        ├── buildings/
        │   ├── hq.png                  # Command Center (HQ)
        │   ├── farm.png                # Farm
        │   ├── factory.png             # Factory
        │   ├── refinery.png            # Refinery
        │   ├── barracks.png            # Barracks
        │   └── shipyard.png            # Naval Shipyard
        └── units/
            ├── engineer.png            # Engineer (Civilian)
            ├── foot_soldier.png        # Foot Soldier (Infantry)
            ├── tank.png                # Tank (Base static fallback)
            ├── cannon.png              # Heavy Artillery (Base static fallback)
            ├── torpedo_boat.png        # Torpedo Boat (Patrol craft)
            ├── destroyer.png           # Destroyer (Warship)
            ├── battleship.png          # Battleship (Dreadnought)
            │
            └── directional/            # Advanced: 8-way directional & split turret assets
                ├── tank_hull_n.png     # Tank hull facing North
                ├── tank_hull_ne.png    # Tank hull facing North-East
                ├── ...
                ├── tank_turret_n.png   # Tank turret facing North
                └── ...
```

#### Complete Entity File Mapping & Recommended Canvas Sizes

| Category | In-Game Name (`config.py`) | Folder Destination | Required Filename | In-Game Footprint | Base `1×` Size (px) | Hi-DPI `2×` Size (px) *(Recommended)* |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Building** | `HQ` | `assets/sprites/buildings/` | `hq.png` | 3×3 tiles | 192 × 160 | 384 × 320 |
| **Building** | `Farm` | `assets/sprites/buildings/` | `farm.png` | 2×2 tiles | 128 × 96 | 256 × 192 |
| **Building** | `Factory` | `assets/sprites/buildings/` | `factory.png` | 3×2 tiles | 160 × 128 | 320 × 256 |
| **Building** | `Refinery` | `assets/sprites/buildings/` | `refinery.png` | 2×2 tiles | 128 × 128 | 256 × 256 |
| **Building** | `Barracks` | `assets/sprites/buildings/` | `barracks.png` | 3×3 tiles | 192 × 160 | 384 × 320 |
| **Building** | `Shipyard` | `assets/sprites/buildings/` | `shipyard.png` | 3×3 tiles | 192 × 160 | 384 × 320 |
| **Unit** | `Engineer` | `assets/sprites/units/` | `engineer.png` | `radius: 10` | 48 × 48 | 96 × 96 |
| **Unit** | `Foot Soldier` | `assets/sprites/units/` | `foot_soldier.png` | `radius: 10` | 48 × 48 | 96 × 96 |
| **Unit** | `Tank` | `assets/sprites/units/` | `tank.png` | `radius: 14` | 64 × 64 | 128 × 128 |
| **Unit** | `Cannon` | `assets/sprites/units/` | `cannon.png` | `radius: 14` | 64 × 64 | 128 × 128 |
| **Unit** | `Torpedo Boat` | `assets/sprites/units/` | `torpedo_boat.png` | `radius: 13` | 80 × 64 | 160 × 128 |
| **Unit** | `Destroyer` | `assets/sprites/units/` | `destroyer.png` | `radius: 15` | 96 × 72 | 192 × 144 |
| **Unit** | `Battleship` | `assets/sprites/units/` | `battleship.png` | `radius: 18` | 128 × 96 | 256 × 192 |

---

### 🔍 2. Ensuring High-Quality Graphics: Standards & Best Practices

To ensure graphics blend seamlessly with Age of Modernity's visual engine, follow these technical guidelines:

#### A. Preventing Blur at Max Zoom (Hi-DPI Supersampling)
* The camera supports smooth zooming from **`0.5×` (far out) up to `2.5×` (close-up)**.
* Standard map tiles are `32×32` world units (`64×32` pixels on screen at `1.0×`). At `2.5×` zoom, a tile expands to `160×80` screen pixels.
* **Best Practice:** Author your assets at the **Hi-DPI `2×` resolution** listed in the table above. When zooming into `2.5×`, the engine downsamples from clean, high-resolution source art rather than upscaling low-resolution pixels, preventing blur.

#### B. Isometric Perspective & Lighting Geometry
* **Projection Angle:** Dimetric 2:1 isometric projection (~30° camera inclination angle, true dimetric angle `atan(0.5) ≈ 26.565°`).
* **Directional Lighting:** Key light shines from the **Top-Left (North-West)** at roughly 45° elevation. Right-facing and bottom-facing surfaces must have ambient shadow for visual depth.
* **Alpha Channel:** 32-bit RGBA PNG with clean, anti-aliased alpha borders (no matte fringe or halo around edges).
* **Drop Shadow:** Keep ground contact shadows semi-transparent (black at ~30%–45% opacity) hugging the base of the hull or foundation.


---

### 🧭 3. Directional Movement & Independent Turret Architecture

For units, realistic combat motion requires two distinct mechanics: **heading direction** (where the unit moves) and **turret aim** (where weapons fire).

#### A. 8-Directional Movement (5 Sprites + Horizontal Flip)
Simple 2D rotation (`pygame.transform.rotate`) distorts isometric art by spinning the 30° camera pitch. Instead, units use 8 discrete isometric facing angles:
* **The 8 Compass Facings:** `N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`.
* **5-Direction Economy:** Because isometric projections have bilateral horizontal symmetry, you only need to create **5 facing angles**:
  * `n` (facing away/up)
  * `ne` (facing up-right)
  * `e` (facing right)
  * `se` (facing down-right)
  * `s` (facing front/down)
* **Mirror Flipping:** West-facing angles (`sw`, `w`, `nw`) can be rendered in code by horizontally flipping `se`, `e`, and `ne` via `pygame.transform.flip(surface, True, False)`.

#### B. Multi-Layer Turret Separation (Tanks, Artillery, Warships)
Units with rotating guns (Tank, Cannon, Destroyer, Battleship) look highest quality when split into two independent sprite layers:
1. **Hull Layer (`<unit>_hull_<dir>.png`):** The chassis, tracks, or naval hull with the turret removed, revealing the flat circular turret mounting ring.
2. **Turret Layer (`<unit>_turret_<dir>.png`):** The turret dome, mantlet, and gun barrel isolated on transparent background.
3. **The Pivot Pin Rule:** The turret sprite's canvas must be authored such that the **rotation pin/turret ring center is at the exact center `(W/2, H/2)` of the PNG canvas**. Even though the gun barrel extends outward, centering the canvas on the rotation point guarantees the turret can rotate or switch angles without its base sliding across the hull.

#### Render Layer Order:
```text
[1. Ground Shadow] ➔ [2. Selection Decal] ➔ [3. Hull Sprite] ➔ [4. Turret Sprite] ➔ [5. Health Bar / HUD]
```


---

### 🤖 4. Generative AI Prompting Guide for RTS Sprites

Modern Generative AI models (Midjourney v6, Stable Diffusion XL / ComfyUI, DALL-E 3 / GPT-4o) can generate high-quality RTS assets when given precise isometric perspective keywords.

#### Essential Prompt Keywords for Consistency:
* **Perspective:** `dimetric isometric projection`, `classic 2.5D RTS video game sprite`, `30 degree camera angle`, `orthographic view`, `no perspective distortion`
* **Style:** `industrial military RTS style`, `clean hard surface details`, `weathered painted metal`, `Age of Empires inspired`, `command and conquer style`
* **Lighting:** `directional sunlight from top-left`, `subtle ambient occlusion`, `neutral studio lighting`
* **Isolation:** `isolated on solid clean white background`, `asset sprite sheet`, `no background elements`, `die-cut sticker style edge`
* **Negative Prompts:** `perspective tilt`, `fisheye lens`, `photorealistic clutter`, `muddy textures`, `text`, `watermark`, `blurry edges`

---

#### 📋 Copy-Paste Prompt Templates

##### 1. Buildings & Industrial Facilities
```text
Isometric game asset sprite of a dieselpunk industrial military command center headquarters HQ, 2.5D RTS game building asset, dimetric projection 30 degree camera angle, brick and reinforced steel armor plates, radio antennae array and radar dish on roof, solid concrete foundation, top-left directional sunlight, crisp clean details, isolated on a pure solid pure white background, white background only, no shadows cutting off --no ground clutter, landscape, terrain
```

##### 2. Coastal Naval Shipyard
```text
Isometric game asset sprite of a military naval shipyard and drydock, 2.5D RTS game building asset, dimetric projection 30 degree camera angle, heavy industrial gantry crane, steel construction docks, coastal slipway, reinforced concrete piers, top-left directional sunlight, crisp details, isolated on solid white background --no water, terrain, boats
```

##### 3. Tank Hull (Turretless Chassis)
```text
Isometric 2.5D RTS vehicle sprite of a heavy diesel military tank hull and caterpillar tracks, chassis only without turret, showing empty flat circular turret mounting ring on top deck, angled 45 degrees towards bottom-right (South-East view), dimetric projection, olive drab painted steel with subtle rivet details, directional sunlight from top-left, isolated on pure white background
```

##### 4. Tank Turret (Isolated on Rotation Pin)
```text
2.5D RTS game sprite of a heavy tank turret with long rifled cannon barrel, turret assembly only, viewed at a 30 degree isometric angle facing directly East, weapon mantlet, muzzle brake, the pivot mounting ring is positioned at the exact geometrical center of the canvas, directional sunlight from top-left, isolated on pure white background
```

##### 5. Naval Warships (Destroyer & Battleship)
```text
Isometric 2.5D RTS naval warship sprite of a modern naval destroyer, dimetric projection 30 degree camera angle, facing South-East, haze gray painted naval hull, bridge superstructure, radar mast, gun turrets, clean waterline, directional sunlight from top-left, isolated on solid pure white background --no ocean, water ripples, waves
```

##### 6. Infantry & Engineers
```text
Isometric RTS soldier character sprite of a military combat engineer holding field tools and wrench, wearing helmet and tactical gear, standing pose facing South-East, 30 degree isometric camera angle, clean readable silhouette, crisp cell-shaded game asset style, top-left directional sunlight, isolated on solid pure white background
```

---

### 🚀 5. Recommended Production Workflow: AI 2D-to-3D Pipeline

While generating direct 2D sprite turnarounds with AI can work, getting consistent 8-direction alignment and turret alignment from pure 2D prompts is challenging. The gold standard RTS workflow is:

1. **Generate Hero Concept with AI:**
   Use Midjourney or DALL-E to generate a single pristine concept image of your vehicle or building.
2. **Convert Concept to 3D with Image-to-3D AI:**
   Submit the image to automated Image-to-3D tools such as **Tripo3D**, **Meshy**, or **Rodin / Trellis**.
3. **Separate Hull and Turret in Blender (or Free 3D Tool):**
   * Separate the turret mesh from the hull mesh.
   * Place the turret's origin `(0, 0, 0)` at the center of its rotation ring.
4. **Batch Render 8 Angles:**
   * Set camera to **Orthographic**, pitch to **30°** (or `54.736°` isometric in Blender).
   * Rotate the model by 45° steps (`0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°`).
   * Render transparent PNGs for all 8 directions with identical lighting and scale.
5. **Background Clean & Name:**
   Save into `assets/sprites/buildings/` and `assets/sprites/units/` following the table above. Launch `python main.py`—your custom graphics will appear live in-game!

---

## 🏗️ Project Architecture

```
AgeOfModernity/
├── main.py                 # Game loop, window management, and frame runner
├── requirements.txt        # Dependencies (pygame-ce, pytest)
├── README.md               # User guide, control manual, and asset guide
├── assets/
│   ├── sounds/             # Audio SFX (.wav / .ogg): gunfire, cannons, torpedoes
│   └── sprites/            # Custom transparent PNG artwork (auto-loaded)
│       ├── buildings/      # hq.png, farm.png, factory.png, barracks.png, etc.
│       └── units/          # foot_soldier.png, tank.png, battleship.png, etc.
├── src/
│   ├── config.py           # Unit & building stat tables, terrain colors, dimensions
│   ├── asset_manager.py    # Sprite loader, zoom caching, and procedural fallback
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
└── tests/                  # Automated pytest suite (MVP, Zoom, Graphics, Maps)
```
