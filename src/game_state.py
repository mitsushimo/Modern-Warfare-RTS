"""
Game State Manager.
Maintains simulation world, entities, selections, economy, and orders.
"""
import math
from typing import List, Optional, Tuple
import os
import json
import datetime

from src.config import (
    TILE_SIZE, Faction, ResourceType, BUILDING_TYPES, UNIT_TYPES, MAP_PRESETS, Domain
)
from src.map_system import GameMap
from src.economy import FactionEconomy
from src.entities.unit import Unit, UnitState
from src.entities.building import Building
from src.entities.base import Entity
from src.combat import CombatManager

class GameState:
    def __init__(self, map_name: str = "Divided Sea"):
        self.current_map_name = map_name
        self.map = GameMap(map_name=map_name)
        self.economies = {
            Faction.PLAYER: FactionEconomy(Faction.PLAYER),
            Faction.ENEMY: FactionEconomy(Faction.ENEMY),
        }
        self.units: List[Unit] = []
        self.buildings: List[Building] = []
        self.selected_entities: List[Entity] = []
        self.combat_manager = CombatManager()
        self.placement_building_type: Optional[str] = None
        self.load_map(map_name)

        self.is_paused = False

    def load_map(self, map_name: str):
        """Loads a chosen map and initializes its starting bases and armies."""
        if map_name not in MAP_PRESETS:
            map_name = "Divided Sea"
        self.current_map_name = map_name
        preset = MAP_PRESETS[map_name]
        width = preset.get("width", 64)
        height = preset.get("height", 48)
        self.map = GameMap(width=width, height=height, map_name=map_name)
        self.economies = {
            Faction.PLAYER: FactionEconomy(Faction.PLAYER),
            Faction.ENEMY: FactionEconomy(Faction.ENEMY),
        }
        self.units.clear()
        self.buildings.clear()
        self.selected_entities.clear()
        self.placement_building_type = None
        self.combat_manager.effects.clear()
        self.is_paused = False

        self._init_map_world(map_name)
        self._resolve_unit_collisions()

    def _init_sandbox_world(self):
        """Backward compatibility for existing tests."""
        self._init_divided_sea()

    def _init_map_world(self, map_name: str):
        if map_name == "Continental Front":
            self._init_continental_front()
        elif map_name == "Shattered Isthmus":
            self._init_shattered_isthmus()
        elif map_name == "Inland Sea":
            self._init_inland_sea()
        elif map_name == "Grand Archipelago":
            self._init_grand_archipelago()
        else:
            self._init_divided_sea()

    def _init_divided_sea(self):
        # PLAYER BASE (West)
        self.place_building("HQ", Faction.PLAYER, 4, 18, under_construction=False)
        self.place_building("Farm", Faction.PLAYER, 4, 14, under_construction=False)
        self.place_building("Barracks", Faction.PLAYER, 9, 18, under_construction=False)
        self.place_building("Shipyard", Faction.PLAYER, 18, 18, under_construction=False)

        # Starter Player Units
        self.spawn_unit("Engineer", Faction.PLAYER, 6 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Engineer", Faction.PLAYER, 8 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 12 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 14 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.PLAYER, 16 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Torpedo Boat", Faction.PLAYER, 26 * TILE_SIZE, 20 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.PLAYER, 28 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Battleship", Faction.PLAYER, 26 * TILE_SIZE, 25 * TILE_SIZE)

        # ENEMY BASE (East)
        self.place_building("HQ", Faction.ENEMY, 54, 18, under_construction=False)
        self.place_building("Factory", Faction.ENEMY, 50, 18, under_construction=False)
        self.place_building("Barracks", Faction.ENEMY, 48, 22, under_construction=False)
        self.place_building("Shipyard", Faction.ENEMY, 41, 18, under_construction=False)

        # Starter Enemy Units
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 46 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 47 * TILE_SIZE, 25 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.ENEMY, 49 * TILE_SIZE, 28 * TILE_SIZE)
        self.spawn_unit("Torpedo Boat", Faction.ENEMY, 36 * TILE_SIZE, 20 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.ENEMY, 35 * TILE_SIZE, 24 * TILE_SIZE)

    def _init_continental_front(self):
        """Map with player territory connected directly by land to enemy territory."""
        # PLAYER BASE (West) - Full land military base
        self.place_building("HQ", Faction.PLAYER, 4, 18, under_construction=False)
        self.place_building("Farm", Faction.PLAYER, 4, 14, under_construction=False)
        self.place_building("Factory", Faction.PLAYER, 4, 23, under_construction=False)
        self.place_building("Barracks", Faction.PLAYER, 9, 18, under_construction=False)
        self.place_building("Refinery", Faction.PLAYER, 9, 23, under_construction=False)
        self.place_building("Shipyard", Faction.PLAYER, 24, 7, under_construction=False)

        # Starter Player Land Armies
        self.spawn_unit("Engineer", Faction.PLAYER, 6 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Engineer", Faction.PLAYER, 8 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 13 * TILE_SIZE, 17 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 13 * TILE_SIZE, 20 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 13 * TILE_SIZE, 23 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 16 * TILE_SIZE, 18 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 16 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.PLAYER, 18 * TILE_SIZE, 17 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.PLAYER, 18 * TILE_SIZE, 23 * TILE_SIZE)

        # ENEMY BASE (East) - Land fortified position
        self.place_building("HQ", Faction.ENEMY, 54, 18, under_construction=False)
        self.place_building("Factory", Faction.ENEMY, 54, 23, under_construction=False)
        self.place_building("Farm", Faction.ENEMY, 54, 14, under_construction=False)
        self.place_building("Barracks", Faction.ENEMY, 48, 18, under_construction=False)
        self.place_building("Refinery", Faction.ENEMY, 48, 23, under_construction=False)
        self.place_building("Shipyard", Faction.ENEMY, 37, 7, under_construction=False)

        # Starter Enemy Land Armies
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 45 * TILE_SIZE, 17 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 45 * TILE_SIZE, 20 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 45 * TILE_SIZE, 23 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 42 * TILE_SIZE, 18 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 42 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.ENEMY, 40 * TILE_SIZE, 17 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.ENEMY, 40 * TILE_SIZE, 23 * TILE_SIZE)

    def _init_shattered_isthmus(self):
        # PLAYER BASE (West)
        self.place_building("HQ", Faction.PLAYER, 4, 22, under_construction=False)
        self.place_building("Farm", Faction.PLAYER, 4, 17, under_construction=False)
        self.place_building("Barracks", Faction.PLAYER, 9, 22, under_construction=False)
        self.place_building("Shipyard", Faction.PLAYER, 14, 18, under_construction=False)

        # Starter Player Units
        self.spawn_unit("Engineer", Faction.PLAYER, 6 * TILE_SIZE, 26 * TILE_SIZE)
        self.spawn_unit("Engineer", Faction.PLAYER, 8 * TILE_SIZE, 26 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 14 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 14 * TILE_SIZE, 25 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 16 * TILE_SIZE, 23 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 16 * TILE_SIZE, 25 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.PLAYER, 13 * TILE_SIZE, 24 * TILE_SIZE)
        self.spawn_unit("Torpedo Boat", Faction.PLAYER, 22 * TILE_SIZE, 12 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.PLAYER, 26 * TILE_SIZE, 12 * TILE_SIZE)

        # ENEMY BASE (East)
        self.place_building("HQ", Faction.ENEMY, 54, 22, under_construction=False)
        self.place_building("Factory", Faction.ENEMY, 54, 26, under_construction=False)
        self.place_building("Barracks", Faction.ENEMY, 48, 22, under_construction=False)
        self.place_building("Shipyard", Faction.ENEMY, 47, 18, under_construction=False)

        # Starter Enemy Units
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 44 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 44 * TILE_SIZE, 25 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 42 * TILE_SIZE, 23 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 42 * TILE_SIZE, 25 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.ENEMY, 45 * TILE_SIZE, 24 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.ENEMY, 38 * TILE_SIZE, 12 * TILE_SIZE)

    def _init_inland_sea(self):
        # PLAYER BASE (West)
        self.place_building("HQ", Faction.PLAYER, 4, 22, under_construction=False)
        self.place_building("Farm", Faction.PLAYER, 4, 17, under_construction=False)
        self.place_building("Barracks", Faction.PLAYER, 8, 10, under_construction=False)
        self.place_building("Factory", Faction.PLAYER, 8, 32, under_construction=False)
        self.place_building("Shipyard", Faction.PLAYER, 15, 22, under_construction=False)

        # Starter Player Units
        self.spawn_unit("Engineer", Faction.PLAYER, 6 * TILE_SIZE, 22 * TILE_SIZE)
        self.spawn_unit("Engineer", Faction.PLAYER, 6 * TILE_SIZE, 24 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 14 * TILE_SIZE, 10 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 16 * TILE_SIZE, 10 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 14 * TILE_SIZE, 34 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 16 * TILE_SIZE, 34 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.PLAYER, 24 * TILE_SIZE, 24 * TILE_SIZE)

        # ENEMY BASE (East)
        self.place_building("HQ", Faction.ENEMY, 54, 22, under_construction=False)
        self.place_building("Farm", Faction.ENEMY, 54, 17, under_construction=False)
        self.place_building("Barracks", Faction.ENEMY, 48, 10, under_construction=False)
        self.place_building("Factory", Faction.ENEMY, 48, 32, under_construction=False)
        self.place_building("Shipyard", Faction.ENEMY, 46, 22, under_construction=False)

        # Starter Enemy Units
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 44 * TILE_SIZE, 10 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 42 * TILE_SIZE, 10 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 44 * TILE_SIZE, 34 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 42 * TILE_SIZE, 34 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.ENEMY, 38 * TILE_SIZE, 24 * TILE_SIZE)

    def _init_grand_archipelago(self):
        """Initializes starter bases and armed forces on the vast 96x64 Grand Archipelago."""
        # PLAYER BASE (Southwest Island)
        self.place_building("HQ", Faction.PLAYER, 8, 42, under_construction=False)
        self.place_building("Farm", Faction.PLAYER, 8, 38, under_construction=False)
        self.place_building("Factory", Faction.PLAYER, 8, 47, under_construction=False)
        self.place_building("Barracks", Faction.PLAYER, 14, 42, under_construction=False)
        self.place_building("Refinery", Faction.PLAYER, 14, 47, under_construction=False)
        self.place_building("Shipyard", Faction.PLAYER, 20, 39, under_construction=False)

        # Starter Player Forces (Amphibious Task Force)
        self.spawn_unit("Engineer", Faction.PLAYER, 10 * TILE_SIZE, 45 * TILE_SIZE)
        self.spawn_unit("Engineer", Faction.PLAYER, 12 * TILE_SIZE, 45 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 17 * TILE_SIZE, 41 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 17 * TILE_SIZE, 43 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.PLAYER, 17 * TILE_SIZE, 45 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 19 * TILE_SIZE, 43 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.PLAYER, 19 * TILE_SIZE, 45 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.PLAYER, 16 * TILE_SIZE, 44 * TILE_SIZE)
        self.spawn_unit("Torpedo Boat", Faction.PLAYER, 25 * TILE_SIZE, 38 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.PLAYER, 27 * TILE_SIZE, 37 * TILE_SIZE)
        self.spawn_unit("Battleship", Faction.PLAYER, 25 * TILE_SIZE, 36 * TILE_SIZE)

        # ENEMY BASE (Northeast Fortress)
        self.place_building("HQ", Faction.ENEMY, 82, 16, under_construction=False)
        self.place_building("Farm", Faction.ENEMY, 82, 12, under_construction=False)
        self.place_building("Factory", Faction.ENEMY, 82, 21, under_construction=False)
        self.place_building("Barracks", Faction.ENEMY, 76, 16, under_construction=False)
        self.place_building("Refinery", Faction.ENEMY, 76, 21, under_construction=False)
        self.place_building("Shipyard", Faction.ENEMY, 71, 18, under_construction=False)

        # Starter Enemy Forces
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 74 * TILE_SIZE, 17 * TILE_SIZE)
        self.spawn_unit("Foot Soldier", Faction.ENEMY, 74 * TILE_SIZE, 19 * TILE_SIZE)
        self.spawn_unit("Tank", Faction.ENEMY, 72 * TILE_SIZE, 17 * TILE_SIZE)
        self.spawn_unit("Cannon", Faction.ENEMY, 72 * TILE_SIZE, 21 * TILE_SIZE)
        self.spawn_unit("Torpedo Boat", Faction.ENEMY, 68 * TILE_SIZE, 15 * TILE_SIZE)
        self.spawn_unit("Destroyer", Faction.ENEMY, 70 * TILE_SIZE, 14 * TILE_SIZE)
        self.spawn_unit("Battleship", Faction.ENEMY, 66 * TILE_SIZE, 14 * TILE_SIZE)

    def spawn_unit(self, unit_type_name: str, faction: Faction, x: float, y: float) -> Unit:
        spawn_x, spawn_y = float(x), float(y)
        for other in self.units:
            if other.is_alive and math.hypot(other.x - spawn_x, other.y - spawn_y) < other.radius * 0.7:
                angle = (len(self.units) * 1.618) * (2.0 * math.pi)
                spawn_x += math.cos(angle) * (other.radius * 1.5)
                spawn_y += math.sin(angle) * (other.radius * 1.5)
                break
        unit = Unit(unit_type_name, faction, spawn_x, spawn_y)
        self.units.append(unit)
        return unit

    def place_building(
        self, type_name: str, faction: Faction, tile_x: int, tile_y: int, under_construction: bool = False
    ) -> Optional[Building]:
        data = BUILDING_TYPES[type_name]
        coastal = data.get("coastal_required", False)
        w, h = data["width_tiles"], data["height_tiles"]

        if not self.map.can_place_building(tile_x, tile_y, w, h, coastal):
            return None

        building = Building(type_name, faction, tile_x, tile_y, under_construction=under_construction)
        self.buildings.append(building)
        self.map.register_building(building.id, tile_x, tile_y, w, h)
        return building

    def clear_selection(self):
        for ent in self.selected_entities:
            ent.is_selected = False
        self.selected_entities.clear()

    def select_single(self, world_x: float, world_y: float):
        self.clear_selection()
        for unit in reversed(self.units):
            if unit.faction == Faction.PLAYER and unit.distance_to_point(world_x, world_y) <= max(unit.radius, 14):
                unit.is_selected = True
                self.selected_entities.append(unit)
                return
        for bld in reversed(self.buildings):
            if bld.faction == Faction.PLAYER and bld.contains_point(world_x, world_y):
                bld.is_selected = True
                self.selected_entities.append(bld)
                return
        for unit in reversed(self.units):
            if unit.distance_to_point(world_x, world_y) <= max(unit.radius, 14):
                unit.is_selected = True
                self.selected_entities.append(unit)
                return
        for bld in reversed(self.buildings):
            if bld.contains_point(world_x, world_y):
                bld.is_selected = True
                self.selected_entities.append(bld)
                return

    def select_box(self, x1: float, y1: float, x2: float, y2: float):
        self.clear_selection()
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        for unit in self.units:
            if unit.faction == Faction.PLAYER:
                if min_x <= unit.x <= max_x and min_y <= unit.y <= max_y:
                    unit.is_selected = True
                    self.selected_entities.append(unit)

    def select_box_screen(self, screen_rect, camera, asset_manager=None):
        """Marquee box selection checking screen-space unit bounding."""
        self.clear_selection()
        zoom = getattr(camera, "zoom", 1.0)
        for unit in self.units:
            if unit.faction == Faction.PLAYER and unit.is_alive:
                sx, sy = camera.world_to_screen(unit.x, unit.y)
                if screen_rect.collidepoint(sx, sy):
                    unit.is_selected = True
                    self.selected_entities.append(unit)
                elif asset_manager:
                    proj_mode = getattr(camera, "projection_mode", "isometric")
                    hull_dir = unit.get_compass_direction(projection_mode=proj_mode)
                    s = asset_manager.get_unit_sprite(unit.type_name, zoom, direction=hull_dir)
                    if s and screen_rect.colliderect(s.get_rect(center=(sx, sy))):
                        unit.is_selected = True
                        self.selected_entities.append(unit)

    def _unit_hit_test(self, unit: Unit, sx: int, sy: int, camera, asset_manager=None) -> bool:
        """Checks if screen coordinate (sx, sy) hits any part of the unit's displayed image or core footprint."""
        u_sx, u_sy = camera.world_to_screen(unit.x, unit.y)
        zoom = getattr(camera, "zoom", 1.0)

        if asset_manager:
            proj_mode = getattr(camera, "projection_mode", "isometric")
            hull_dir = unit.get_compass_direction(projection_mode=proj_mode)
            turret_dir = unit.get_turret_compass_direction(projection_mode=proj_mode)

            hull_sprite, turret_sprite = asset_manager.get_unit_parts(unit.type_name, zoom, hull_dir, turret_dir)
            if not hull_sprite and not turret_sprite:
                hull_sprite = asset_manager.get_unit_sprite(unit.type_name, zoom, direction=hull_dir)

            if hull_sprite:
                h_rect = hull_sprite.get_rect(center=(u_sx, u_sy))
                if h_rect.collidepoint(sx, sy):
                    px = int(sx - h_rect.left)
                    py = int(sy - h_rect.top)
                    if 0 <= px < hull_sprite.get_width() and 0 <= py < hull_sprite.get_height():
                        if hull_sprite.get_at((px, py)).a > 10:
                            return True

            if turret_sprite:
                t_rect = turret_sprite.get_rect(center=(u_sx, u_sy - int(3 * zoom)))
                if t_rect.collidepoint(sx, sy):
                    px = int(sx - t_rect.left)
                    py = int(sy - t_rect.top)
                    if 0 <= px < turret_sprite.get_width() and 0 <= py < turret_sprite.get_height():
                        if turret_sprite.get_at((px, py)).a > 10:
                            return True

        # Fallback to core radius check
        dist = math.hypot(sx - u_sx, sy - u_sy)
        return dist <= max(unit.radius * zoom, 16.0)

    def _building_hit_test(self, bld: Building, sx: int, sy: int, wx: float, wy: float, camera, asset_manager=None) -> bool:
        """Checks if screen coordinate (sx, sy) or world coordinate (wx, wy) hits the building."""
        if bld.contains_point(wx, wy):
            return True

        if getattr(camera, "projection_mode", "isometric") == "isometric":
            zoom = getattr(camera, "zoom", 1.0)
            if asset_manager:
                sprite = asset_manager.get_building_sprite(bld.type_name, zoom)
                if sprite:
                    wx1 = (bld.tile_x + bld.width_tiles) * TILE_SIZE
                    wy1 = (bld.tile_y + bld.height_tiles) * TILE_SIZE
                    gb = camera.world_to_screen(wx1, wy1)
                    s_rect = sprite.get_rect(midbottom=gb)
                    if s_rect.collidepoint(sx, sy):
                        return True
            else:
                ext_h = int((bld.width_tiles + bld.height_tiles) * 10 * zoom)
                wx_eff, wy_eff = camera.screen_to_world(sx, sy + ext_h // 2)
                if bld.contains_point(wx_eff, wy_eff):
                    return True
        return False

    def select_single_screen(self, sx: int, sy: int, camera, asset_manager=None):
        """Selects the topmost entity closest to the screen click coordinate."""
        self.clear_selection()
        zoom = getattr(camera, "zoom", 1.0)

        # Depth sorted: frontmost entities (greater x+y) are drawn on top, so test them first
        depth_sorted_units = sorted(self.units, key=lambda u: u.x + u.y, reverse=True)

        # 1. Check Player units
        for unit in depth_sorted_units:
            if unit.faction == Faction.PLAYER and unit.is_alive:
                if self._unit_hit_test(unit, sx, sy, camera, asset_manager):
                    unit.is_selected = True
                    self.selected_entities.append(unit)
                    return

        # 2. Check Player buildings
        wx, wy = camera.screen_to_world(sx, sy)
        for bld in reversed(self.buildings):
            if bld.faction == Faction.PLAYER and self._building_hit_test(bld, sx, sy, wx, wy, camera, asset_manager):
                bld.is_selected = True
                self.selected_entities.append(bld)
                return

        # 3. Check Enemy units
        for unit in depth_sorted_units:
            if unit.faction != Faction.PLAYER and unit.is_alive:
                if self._unit_hit_test(unit, sx, sy, camera, asset_manager):
                    unit.is_selected = True
                    self.selected_entities.append(unit)
                    return

        # 4. Check Enemy buildings
        for bld in reversed(self.buildings):
            if self._building_hit_test(bld, sx, sy, wx, wy, camera, asset_manager):
                bld.is_selected = True
                self.selected_entities.append(bld)
                return

    def get_entity_at(self, wx: float, wy: float) -> Optional[Entity]:
        for unit in reversed(self.units):
            if unit.distance_to_point(wx, wy) <= max(unit.radius, 14):
                return unit
        for bld in reversed(self.buildings):
            if bld.contains_point(wx, wy):
                return bld
        return None

    def _compute_formation_slots(
        self, target_wx: float, target_wy: float, units: List[Unit]
    ) -> List[Tuple[float, float]]:
        n = len(units)
        if n <= 1:
            return [(target_wx, target_wy)]

        max_rad = max((u.radius for u in units), default=12.0)
        spacing = max_rad * 2.2

        candidate_offsets = [(0.0, 0.0)]
        ring = 1
        while len(candidate_offsets) < max(n * 4, 12):
            ring_radius = ring * spacing
            ring_count = ring * 6
            for k in range(ring_count):
                angle = (2.0 * math.pi * k) / ring_count
                candidate_offsets.append((
                    ring_radius * math.cos(angle),
                    ring_radius * math.sin(angle)
                ))
            ring += 1

        domain = units[0].domain if units else Domain.LAND
        slots = []
        for ox, oy in candidate_offsets:
            wx = max(16.0, min((self.map.width - 0.5) * TILE_SIZE, target_wx + ox))
            wy = max(16.0, min((self.map.height - 0.5) * TILE_SIZE, target_wy + oy))
            tx = int(wx // TILE_SIZE)
            ty = int(wy // TILE_SIZE)
            if self.map.is_passable(tx, ty, domain) and (wx, wy) not in slots:
                slots.append((wx, wy))
                if len(slots) == n:
                    break

        if len(slots) < n:
            for ox, oy in candidate_offsets:
                wx = max(16.0, min((self.map.width - 0.5) * TILE_SIZE, target_wx + ox))
                wy = max(16.0, min((self.map.height - 0.5) * TILE_SIZE, target_wy + oy))
                if (wx, wy) not in slots:
                    slots.append((wx, wy))
                    if len(slots) == n:
                        break

        assigned_slots = [None] * n
        unassigned_units = list(range(n))
        available_slots = list(range(n))

        for _ in range(n):
            best_dist = float("inf")
            best_u_idx = None
            best_s_idx = None
            for u_idx in unassigned_units:
                u = units[u_idx]
                for s_idx in available_slots:
                    sx, sy = slots[s_idx]
                    d = math.hypot(u.x - sx, u.y - sy)
                    if d < best_dist:
                        best_dist = d
                        best_u_idx = u_idx
                        best_s_idx = s_idx
            if best_u_idx is not None and best_s_idx is not None:
                assigned_slots[best_u_idx] = slots[best_s_idx]
                unassigned_units.remove(best_u_idx)
                available_slots.remove(best_s_idx)

        return [assigned_slots[i] or (target_wx, target_wy) for i in range(n)]

    def issue_right_click_order(
        self,
        target_wx: float,
        target_wy: float,
        screen_pos: Optional[Tuple[int, int]] = None,
        camera=None,
        asset_manager=None
    ):
        target_ent = None
        if screen_pos and camera:
            sx, sy = screen_pos
            depth_sorted_units = sorted(self.units, key=lambda u: u.x + u.y, reverse=True)
            for unit in depth_sorted_units:
                if unit.is_alive and self._unit_hit_test(unit, sx, sy, camera, asset_manager):
                    target_ent = unit
                    break
            if not target_ent:
                for bld in reversed(self.buildings):
                    if bld.is_alive and self._building_hit_test(bld, sx, sy, target_wx, target_wy, camera, asset_manager):
                        target_ent = bld
                        break
        if not target_ent:
            target_ent = self.get_entity_at(target_wx, target_wy)

        selected_units = [e for e in self.selected_entities if isinstance(e, Unit) and e.faction == Faction.PLAYER]

        if not selected_units:
            selected_buildings = [
                e for e in self.selected_entities
                if isinstance(e, Building) and e.faction == Faction.PLAYER and e.producible_units
            ]
            if selected_buildings:
                for bld in selected_buildings:
                    if bld.contains_point(target_wx, target_wy):
                        bld.rally_point = None
                    else:
                        tx = int(target_wx // TILE_SIZE)
                        ty = int(target_wy // TILE_SIZE)
                        if 0 <= tx < self.map.width and 0 <= ty < self.map.height:
                            produces_domains = [UNIT_TYPES[u]["domain"] for u in bld.producible_units if u in UNIT_TYPES]
                            if not produces_domains:
                                produces_domains = [Domain.LAND]
                            if any(self.map.is_passable(tx, ty, dom) for dom in produces_domains):
                                bld.rally_point = (float(target_wx), float(target_wy))
            return

        if target_ent and target_ent.faction != Faction.PLAYER and target_ent.is_alive:
            for unit in selected_units:
                path = self.map.find_path((unit.x, unit.y), (target_ent.x, target_ent.y), unit.domain)
                unit.order_attack(target_ent, path)
        elif target_ent and isinstance(target_ent, Building) and any(u.type_name == "Engineer" for u in selected_units):
            for unit in selected_units:
                if unit.type_name == "Engineer":
                    path = self.map.find_path((unit.x, unit.y), (target_ent.x, target_ent.y), unit.domain)
                    if target_ent.under_construction or target_ent.hp < target_ent.max_hp:
                        unit.order_build_or_repair(target_ent, path)
                    elif target_ent.worker_yield is not None:
                        unit.order_work(target_ent, path)
                    else:
                        unit.order_move(path)
                else:
                    path = self.map.find_path((unit.x, unit.y), (target_wx, target_wy), unit.domain)
                    unit.order_move(path)
        else:
            slots = self._compute_formation_slots(target_wx, target_wy, selected_units)
            for unit, slot in zip(selected_units, slots):
                path = self.map.find_path((unit.x, unit.y), slot, unit.domain)
                unit.order_move(path)

    def start_building_placement(self, building_type_name: str):
        self.placement_building_type = building_type_name

    def cancel_building_placement(self):
        self.placement_building_type = None

    def confirm_building_placement(self, tile_x: int, tile_y: int) -> bool:
        if not self.placement_building_type:
            return False

        b_data = BUILDING_TYPES[self.placement_building_type]
        player_econ = self.economies[Faction.PLAYER]

        if not player_econ.can_afford(b_data["cost"]):
            return False

        bld = self.place_building(
            self.placement_building_type, Faction.PLAYER, tile_x, tile_y, under_construction=True
        )
        if bld is None:
            return False

        player_econ.deduct(b_data["cost"])

        selected_engineers = [
            e for e in self.selected_entities if isinstance(e, Unit) and e.type_name == "Engineer" and e.faction == Faction.PLAYER
        ]
        for eng in selected_engineers:
            path = self.map.find_path((eng.x, eng.y), (bld.x, bld.y), eng.domain)
            eng.order_build_or_repair(bld, path)

        self.placement_building_type = None
        return True

    def update(self, delta_time: float):
        if self.is_paused:
            return

        # 1. Update Buildings
        for bld in list(self.buildings):
            if not bld.is_alive:
                continue

            econ = self.economies[bld.faction]
            bld.update_industry(delta_time, econ)

            completed_unit_name = bld.update_production(delta_time)
            if completed_unit_name:
                u_domain = UNIT_TYPES[completed_unit_name]["domain"]
                spawn_tile = self.map.find_spawn_tile(
                    bld.tile_x, bld.tile_y, bld.width_tiles, bld.height_tiles, u_domain
                )
                if spawn_tile:
                    sx = (spawn_tile[0] + 0.5) * TILE_SIZE
                    sy = (spawn_tile[1] + 0.5) * TILE_SIZE
                    new_unit = self.spawn_unit(completed_unit_name, bld.faction, sx, sy)
                    if bld.rally_point and new_unit:
                        path = self.map.find_path((new_unit.x, new_unit.y), bld.rally_point, new_unit.domain)
                        if path:
                            new_unit.order_move(path)

        # 2. Update Units
        for unit in list(self.units):
            if not unit.is_alive:
                continue

            if unit.state == UnitState.IDLE and unit.attack_damage > 5:
                closest_enemy = None
                closest_dist = unit.sight_range
                for other in self.units:
                    if other.faction != unit.faction and other.is_alive:
                        d = unit.distance_to(other)
                        if d <= closest_dist:
                            closest_dist = d
                            closest_enemy = other
                if closest_enemy:
                    path = self.map.find_path((unit.x, unit.y), (closest_enemy.x, closest_enemy.y), unit.domain)
                    unit.order_attack(closest_enemy, path)

            combat_event = unit.update(delta_time, self.map)
            if combat_event:
                self.combat_manager.add_combat_event(combat_event)

        # 3. Resolve unit collisions & separation
        self._resolve_unit_collisions()

        # 4. Update FX & Projectiles
        all_entities = list(self.units) + list(self.buildings)
        self.combat_manager.update(delta_time, entities=all_entities)

        # 5. Cleanup destroyed entities
        self.units = [u for u in self.units if u.is_alive]

        for bld in list(self.buildings):
            if not bld.is_alive:
                self.map.unregister_building(bld.tile_x, bld.tile_y, bld.width_tiles, bld.height_tiles)
        self.buildings = [b for b in self.buildings if b.is_alive]

        self.selected_entities = [e for e in self.selected_entities if e.is_alive]

    def _resolve_unit_collisions(self):
        alive_units = [u for u in self.units if u.is_alive]
        num_units = len(alive_units)
        if num_units < 2:
            return

        for _ in range(2):
            for i in range(num_units):
                u1 = alive_units[i]
                for j in range(i + 1, num_units):
                    u2 = alive_units[j]

                    dx = u2.x - u1.x
                    dy = u2.y - u1.y
                    min_dist = u1.radius + u2.radius
                    dist_sq = dx * dx + dy * dy

                    if dist_sq < min_dist * min_dist:
                        dist = math.sqrt(dist_sq)
                        if dist < 0.001:
                            angle = ((i + 1) * 2.399963) % (2.0 * math.pi)
                            nx = math.cos(angle)
                            ny = math.sin(angle)
                            overlap = min_dist
                        else:
                            nx = dx / dist
                            ny = dy / dist
                            overlap = min_dist - dist

                        push = overlap * 0.5
                        self._apply_separation_push(u1, -nx * push, -ny * push)
                        self._apply_separation_push(u2, nx * push, ny * push)

    def _apply_separation_push(self, unit: Unit, push_x: float, push_y: float):
        target_x = unit.x + push_x
        target_y = unit.y + push_y

        min_x = unit.radius
        max_x = self.map.width * TILE_SIZE - unit.radius
        min_y = unit.radius
        max_y = self.map.height * TILE_SIZE - unit.radius
        target_x = max(min_x, min(max_x, target_x))
        target_y = max(min_y, min(max_y, target_y))

        tx = int(target_x // TILE_SIZE)
        ty = int(target_y // TILE_SIZE)

        if self.map.is_passable(tx, ty, unit.domain):
            unit.x = target_x
            unit.y = target_y
        else:
            cur_ty = int(unit.y // TILE_SIZE)
            if self.map.is_passable(tx, cur_ty, unit.domain):
                unit.x = target_x
            else:
                cur_tx = int(unit.x // TILE_SIZE)
                if self.map.is_passable(cur_tx, ty, unit.domain):
                    unit.y = target_y



    def save_game(self, save_name: str, save_dir: str = "saves") -> str:
        """Saves current game state to a JSON file in save_dir. Returns the file path."""
        os.makedirs(save_dir, exist_ok=True)
        clean_name = "".join(c for c in save_name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not clean_name:
            clean_name = "quicksave"
        filepath = os.path.join(save_dir, f"{clean_name}.json")

        economies_data = {}
        for faction, econ in self.economies.items():
            economies_data[faction.value] = {
                res.value: econ.get_amount(res) for res in ResourceType
            }

        buildings_data = []
        for b in self.buildings:
            buildings_data.append({
                "id": b.id,
                "type_name": b.type_name,
                "faction": b.faction.value,
                "tile_x": b.tile_x,
                "tile_y": b.tile_y,
                "hp": b.hp,
                "max_hp": b.max_hp,
                "under_construction": b.under_construction,
                "build_progress": b.build_progress,
                "production_queue": list(b.production_queue),
                "production_progress": b.production_progress,
                "assigned_workers": getattr(b, "assigned_workers", 0),
                "rally_point": list(b.rally_point) if b.rally_point else None,
            })

        units_data = []
        for u in self.units:
            units_data.append({
                "id": u.id,
                "type_name": u.type_name,
                "faction": u.faction.value,
                "x": u.x,
                "y": u.y,
                "hp": u.hp,
                "max_hp": u.max_hp,
                "state": u.state.name,
                "path": [list(p) for p in u.path],
                "cooldown_timer": u.cooldown_timer,
                "assigned_building_id": u.assigned_building.id if u.assigned_building else None,
                "target_entity_id": u.target_entity.id if u.target_entity else None,
                "_has_counted_work": getattr(u, "_has_counted_work", False),
            })

        save_dict = {
            "save_name": clean_name,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_map_name": self.current_map_name,
            "economies": economies_data,
            "buildings": buildings_data,
            "units": units_data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_dict, f, indent=2)

        return filepath


    def load_game(self, save_name: str, save_dir: str = "saves") -> bool:
        """Loads game state from a JSON file in save_dir. Returns True on success."""
        clean_name = "".join(c for c in save_name if c.isalnum() or c in (" ", "_", "-")).strip()
        filepath = os.path.join(save_dir, f"{clean_name}.json")
        if not os.path.exists(filepath):
            if os.path.exists(save_name):
                filepath = save_name
            else:
                return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return False

        map_name = data.get("current_map_name", "Divided Sea")
        self.current_map_name = map_name
        preset = MAP_PRESETS.get(map_name, {})
        width = preset.get("width", 64)
        height = preset.get("height", 48)
        self.map = GameMap(width=width, height=height, map_name=map_name)
        self.map.building_grid.clear()
        self.units.clear()
        self.buildings.clear()
        self.selected_entities.clear()
        self.placement_building_type = None
        self.combat_manager.effects.clear()
        self.is_paused = False

        # Restore economies
        for faction in (Faction.PLAYER, Faction.ENEMY):
            econ = FactionEconomy(faction)
            f_data = data.get("economies", {}).get(faction.value, {})
            for res_str, amt in f_data.items():
                for res_enum in ResourceType:
                    if res_enum.value == res_str:
                        econ.resources[res_enum] = float(amt)
            self.economies[faction] = econ

        # Restore buildings
        bld_by_id = {}
        for b_data in data.get("buildings", []):
            faction = Faction(b_data["faction"])
            bld = Building(
                b_data["type_name"],
                faction,
                b_data["tile_x"],
                b_data["tile_y"],
                under_construction=b_data.get("under_construction", False),
            )
            bld.id = b_data.get("id", bld.id)
            bld.hp = float(b_data.get("hp", bld.hp))
            bld.max_hp = float(b_data.get("max_hp", bld.max_hp))
            bld.build_progress = float(b_data.get("build_progress", bld.build_progress))
            bld.production_queue = list(b_data.get("production_queue", []))
            bld.production_progress = float(b_data.get("production_progress", 0.0))
            bld.assigned_workers = int(b_data.get("assigned_workers", 0))
            rp = b_data.get("rally_point")
            bld.rally_point = (float(rp[0]), float(rp[1])) if rp else None

            self.buildings.append(bld)
            bld_by_id[bld.id] = bld
            self.map.register_building(bld.id, bld.tile_x, bld.tile_y, bld.width_tiles, bld.height_tiles)

        # Restore units
        unit_by_id = {}
        for u_data in data.get("units", []):
            faction = Faction(u_data["faction"])
            unit = Unit(u_data["type_name"], faction, u_data["x"], u_data["y"])
            unit.id = u_data.get("id", unit.id)
            unit.hp = float(u_data.get("hp", unit.hp))
            unit.max_hp = float(u_data.get("max_hp", unit.max_hp))
            state_str = u_data.get("state", "IDLE")
            unit.state = getattr(UnitState, state_str, UnitState.IDLE)
            unit.path = [(float(p[0]), float(p[1])) for p in u_data.get("path", [])]
            unit.cooldown_timer = float(u_data.get("cooldown_timer", 0.0))
            unit._has_counted_work = bool(u_data.get("_has_counted_work", False))
            self.units.append(unit)
            unit_by_id[unit.id] = unit

        # Re-link entity references
        all_ents = {**bld_by_id, **unit_by_id}
        for u_data in data.get("units", []):
            unit = unit_by_id.get(u_data.get("id"))
            if not unit:
                continue
            b_id = u_data.get("assigned_building_id")
            if b_id in bld_by_id:
                unit.assigned_building = bld_by_id[b_id]
            t_id = u_data.get("target_entity_id")
            if t_id in all_ents:
                unit.target_entity = all_ents[t_id]

        self._resolve_unit_collisions()
        return True

    @staticmethod
    def list_saves(save_dir: str = "saves") -> List[str]:
        """Returns list of save names (without .json extension) sorted by modification time descending."""
        if not os.path.exists(save_dir):
            return []
        files = [f for f in os.listdir(save_dir) if f.endswith(".json")]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(save_dir, f)), reverse=True)
        return [f[:-5] for f in files]

