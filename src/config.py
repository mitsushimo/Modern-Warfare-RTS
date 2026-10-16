"""
Age of Modernity - Configuration & Balance Data
"""
from enum import Enum, auto

# Display & Window Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768
FPS = 60
TILE_SIZE = 32

# Map Dimensions in Tiles
MAP_WIDTH = 64
MAP_HEIGHT = 48

# Colors (R, G, B)
COLOR_BLACK = (20, 20, 24)
COLOR_WHITE = (245, 245, 245)
COLOR_GRAY = (120, 125, 130)
COLOR_DARK_GRAY = (50, 52, 58)
COLOR_PANEL_BG = (30, 33, 40)
COLOR_PANEL_BORDER = (65, 72, 85)

# Terrain Colors
COLOR_GRASS = (58, 125, 68)
COLOR_DIRT = (142, 114, 73)
COLOR_COAST = (194, 178, 128)
COLOR_WATER = (40, 95, 165)
COLOR_DEEP_WATER = (24, 62, 118)

# Faction Colors
COLOR_PLAYER = (60, 140, 230)
COLOR_PLAYER_ACCENT = (140, 200, 255)
COLOR_ENEMY = (220, 60, 60)
COLOR_ENEMY_ACCENT = (255, 130, 130)

# UI Elements
COLOR_SELECTION_BOX = (50, 220, 80)
COLOR_HEALTH_GOOD = (46, 204, 113)
COLOR_HEALTH_MED = (241, 196, 15)
COLOR_HEALTH_LOW = (231, 76, 60)
COLOR_BUTTON_NORMAL = (50, 56, 68)
COLOR_BUTTON_HOVER = (70, 80, 98)
COLOR_BUTTON_DISABLED = (35, 38, 44)
COLOR_BUTTON_TEXT = (230, 235, 240)
COLOR_BUTTON_TEXT_MUTED = (130, 135, 140)

# Projectile / Tracer Colors
COLOR_TRACER_BULLET = (255, 230, 110)
COLOR_TRACER_CANNON = (255, 120, 40)
COLOR_TRACER_TORPEDO = (200, 240, 255)
COLOR_TRACER_ARTILLERY = (255, 90, 30)

class Domain(Enum):
    LAND = "Land"
    SEA = "Sea"

class Faction(Enum):
    PLAYER = "Player"
    ENEMY = "Enemy"

class TerrainType(Enum):
    LAND = auto()
    COAST = auto()
    WATER = auto()

class ResourceType(Enum):
    FOOD = "Food"
    STEEL = "Steel"
    FUEL = "Fuel"

STARTING_RESOURCES = {
    ResourceType.FOOD: 300,
    ResourceType.STEEL: 350,
    ResourceType.FUEL: 150,
}

MAP_PRESETS = {
    "Divided Sea": {
        "name": "Divided Sea",
        "tag": "Naval & Amphibious",
        "description": "Western & Eastern landmasses separated by a central channel. Heavy naval focus.",
        "land_connected": False,
    },
    "Continental Front": {
        "name": "Continental Front",
        "tag": "Direct Land Warfare",
        "description": "A vast continuous land corridor directly connecting player & enemy bases. Perfect for testing tanks, artillery, and infantry.",
        "land_connected": True,
    },
    "Shattered Isthmus": {
        "name": "Shattered Isthmus",
        "tag": "Chokepoint & Flanking",
        "description": "Player and enemy bases are connected across a central land bridge, flanked by northern and southern seas.",
        "land_connected": True,
    },
    "Inland Sea": {
        "name": "Inland Sea",
        "tag": "Dual Land Corridors",
        "description": "A central body of water encircled by northern and southern land corridors connecting both factions.",
        "land_connected": True,
    },
    "Grand Archipelago": {
        "name": "Grand Archipelago",
        "tag": "Large Showcase Theater",
        "description": "Vast 96x64 theater of war. Intricate organic coastlines, winding straits, and central archipelagic chains ideal for showcasing isometric 2.5D view and zooming.",
        "land_connected": True,
        "width": 96,
        "height": 64,
    },
}

UNIT_TYPES = {
    "Engineer": {
        "name": "Engineer",
        "domain": Domain.LAND,
        "branch": "Civilian",
        "description": "Constructs & repairs structures, works industries.",
        "cost": {ResourceType.FOOD: 50, ResourceType.STEEL: 10, ResourceType.FUEL: 0},
        "build_time": 6.0,
        "max_hp": 60,
        "armor": 0,
        "attack_damage": 5,
        "attack_range": 1.2,
        "reload_time": 1.4,
        "projectile_speed": 20.0,
        "weapon_type": "bullet",
        "speed": 2.4,
        "sight_range": 5.0,
        "radius": 9,
        "symbol": "ENG",
    },
    "Foot Soldier": {
        "name": "Foot Soldier",
        "domain": Domain.LAND,
        "branch": "Army",
        "description": "Standard infantry rifle squad.",
        "cost": {ResourceType.FOOD: 60, ResourceType.STEEL: 15, ResourceType.FUEL: 0},
        "build_time": 8.0,
        "max_hp": 90,
        "armor": 1,
        "attack_damage": 12,
        "attack_range": 3.0,
        "reload_time": 1.2,
        "projectile_speed": 22.0,
        "weapon_type": "bullet",
        "speed": 2.0,
        "sight_range": 6.0,
        "radius": 10,
        "symbol": "INF",
    },
    "Tank": {
        "name": "Tank",
        "domain": Domain.LAND,
        "branch": "Army",
        "description": "Armored combat vehicle with heavy armor and cannon.",
        "cost": {ResourceType.FOOD: 40, ResourceType.STEEL: 120, ResourceType.FUEL: 40},
        "build_time": 18.0,
        "max_hp": 280,
        "armor": 7,
        "attack_damage": 32,
        "attack_range": 4.5,
        "reload_time": 2.2,
        "projectile_speed": 14.0,
        "weapon_type": "tank_shell",
        "speed": 1.6,
        "sight_range": 6.5,
        "radius": 13,
        "symbol": "TNK",
    },
    "Cannon": {
        "name": "Cannon",
        "domain": Domain.LAND,
        "branch": "Army",
        "description": "Long-range field artillery for land & coastal bombardment.",
        "cost": {ResourceType.FOOD: 30, ResourceType.STEEL: 140, ResourceType.FUEL: 10},
        "build_time": 20.0,
        "max_hp": 110,
        "armor": 2,
        "attack_damage": 52,
        "attack_range": 8.0,
        "reload_time": 3.5,
        "projectile_speed": 7.5,
        "weapon_type": "artillery_shell",
        "speed": 1.1,
        "sight_range": 8.5,
        "radius": 12,
        "symbol": "ART",
    },
    "Torpedo Boat": {
        "name": "Torpedo Boat",
        "domain": Domain.SEA,
        "branch": "Navy",
        "description": "Fast agile warship armed with naval torpedoes.",
        "cost": {ResourceType.FOOD: 20, ResourceType.STEEL: 90, ResourceType.FUEL: 40},
        "build_time": 12.0,
        "max_hp": 150,
        "armor": 2,
        "attack_damage": 34,
        "attack_range": 4.0,
        "reload_time": 2.2,
        "projectile_speed": 5.0,
        "weapon_type": "torpedo",
        "speed": 2.6,
        "sight_range": 6.5,
        "radius": 9,
        "symbol": "TB",
    },
    "Destroyer": {
        "name": "Destroyer",
        "domain": Domain.SEA,
        "branch": "Navy",
        "description": "Versatile warship with rapid-fire naval guns.",
        "cost": {ResourceType.FOOD: 30, ResourceType.STEEL: 170, ResourceType.FUEL: 60},
        "build_time": 20.0,
        "max_hp": 300,
        "armor": 5,
        "attack_damage": 26,
        "attack_range": 5.5,
        "reload_time": 1.4,
        "projectile_speed": 15.0,
        "weapon_type": "naval_shell",
        "speed": 1.9,
        "sight_range": 7.5,
        "radius": 15,
        "symbol": "DD",
    },
    "Battleship": {
        "name": "Battleship",
        "domain": Domain.SEA,
        "branch": "Navy",
        "description": "Dreadnought capital ship with massive armor and guns.",
        "cost": {ResourceType.FOOD: 50, ResourceType.STEEL: 320, ResourceType.FUEL: 130},
        "build_time": 32.0,
        "max_hp": 650,
        "armor": 11,
        "attack_damage": 78,
        "attack_range": 9.0,
        "reload_time": 3.8,
        "projectile_speed": 8.5,
        "weapon_type": "artillery_shell",
        "speed": 1.2,
        "sight_range": 9.5,
        "radius": 36,
        "symbol": "BB",
    },
}

BUILDING_TYPES = {
    "HQ": {
        "name": "HQ",
        "description": "Command Center. Drop-off hub; trains Engineers.",
        "width_tiles": 3,
        "height_tiles": 3,
        "max_hp": 1200,
        "armor": 10,
        "cost": {ResourceType.FOOD: 60, ResourceType.STEEL: 250, ResourceType.FUEL: 50},
        "build_time": 25.0,
        "produces": ["Engineer"],
        "coastal_required": False,
        "resource_yield": None,
        "symbol": "HQ",
    },
    "Farm": {
        "name": "Farm",
        "description": "Agricultural industry. Produces Food.",
        "width_tiles": 2,
        "height_tiles": 2,
        "max_hp": 350,
        "armor": 2,
        "cost": {ResourceType.FOOD: 20, ResourceType.STEEL: 40, ResourceType.FUEL: 0},
        "build_time": 10.0,
        "produces": [],
        "coastal_required": False,
        "worker_yield": (ResourceType.FOOD, 4.0),
        "passive_yield": (ResourceType.FOOD, 1.2),
        "symbol": "FRM",
    },
    "Factory": {
        "name": "Factory",
        "description": "Heavy industry. Produces Steel.",
        "width_tiles": 3,
        "height_tiles": 2,
        "max_hp": 550,
        "armor": 6,
        "cost": {ResourceType.FOOD: 30, ResourceType.STEEL: 90, ResourceType.FUEL: 0},
        "build_time": 15.0,
        "produces": [],
        "coastal_required": False,
        "worker_yield": (ResourceType.STEEL, 3.5),
        "passive_yield": (ResourceType.STEEL, 1.0),
        "symbol": "FAC",
    },
    "Refinery": {
        "name": "Refinery",
        "description": "Oil refinery industry. Produces Fuel.",
        "width_tiles": 2,
        "height_tiles": 2,
        "max_hp": 450,
        "armor": 4,
        "cost": {ResourceType.FOOD: 20, ResourceType.STEEL: 80, ResourceType.FUEL: 0},
        "build_time": 14.0,
        "produces": [],
        "coastal_required": False,
        "worker_yield": (ResourceType.FUEL, 2.5),
        "passive_yield": (ResourceType.FUEL, 0.8),
        "symbol": "REF",
    },
    "Barracks": {
        "name": "Barracks",
        "description": "Military Depot. Trains Soldiers, Tanks, and Cannons.",
        "width_tiles": 3,
        "height_tiles": 3,
        "max_hp": 750,
        "armor": 7,
        "cost": {ResourceType.FOOD: 30, ResourceType.STEEL: 120, ResourceType.FUEL: 20},
        "build_time": 18.0,
        "produces": ["Foot Soldier", "Tank", "Cannon"],
        "coastal_required": False,
        "resource_yield": None,
        "symbol": "BAR",
    },
    "Shipyard": {
        "name": "Shipyard",
        "description": "Coastal Naval Yard. Builds Torpedo Boats, Destroyers, Battleships.",
        "width_tiles": 3,
        "height_tiles": 3,
        "max_hp": 850,
        "armor": 8,
        "cost": {ResourceType.FOOD: 40, ResourceType.STEEL: 170, ResourceType.FUEL: 30},
        "build_time": 20.0,
        "produces": ["Torpedo Boat", "Destroyer", "Battleship"],
        "coastal_required": True,
        "resource_yield": None,
        "symbol": "SHP",
    },
}

