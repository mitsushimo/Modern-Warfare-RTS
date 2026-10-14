"""
Building Entity.
Supports AoE II style construction by Engineers, training queues, and industrial resource generation.
"""
from typing import List, Optional, Tuple, Dict
from src.config import (
    TILE_SIZE, Faction, ResourceType, BUILDING_TYPES, UNIT_TYPES, Domain
)
from src.entities.base import Entity

class Building(Entity):
    def __init__(
        self,
        building_type_name: str,
        faction: Faction,
        tile_x: int,
        tile_y: int,
        under_construction: bool = False,
    ):
        data = BUILDING_TYPES[building_type_name]
        world_x = (tile_x + data["width_tiles"] / 2.0) * TILE_SIZE
        world_y = (tile_y + data["height_tiles"] / 2.0) * TILE_SIZE

        super().__init__(
            name=data["name"],
            faction=faction,
            x=world_x,
            y=world_y,
            max_hp=data["max_hp"],
            armor=data["armor"],
        )
        self.type_name = building_type_name
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.width_tiles = data["width_tiles"]
        self.height_tiles = data["height_tiles"]
        self.coastal_required = data.get("coastal_required", False)
        self.symbol = data.get("symbol", "BLD")

        # Construction mechanics
        self.under_construction = under_construction
        self.build_time = data["build_time"]
        if under_construction:
            self.build_progress = 0.0
            self.hp = 1.0  # Starts with 1 HP foundation
        else:
            self.build_progress = self.build_time
            self.hp = float(self.max_hp)

        # Production Mechanics
        self.producible_units: List[str] = list(data.get("produces", []))
        self.production_queue: List[str] = []
        self.production_progress = 0.0

        self.rally_point: Optional[Tuple[float, float]] = None

        # Industry mechanics
        self.worker_yield = data.get("worker_yield")
        self.passive_yield = data.get("passive_yield")
        self.assigned_workers = 0

    @property
    def is_operational(self) -> bool:
        return self.is_alive and not self.under_construction

    def progress_construction(self, delta_time: float, build_speed: float = 1.0) -> bool:
        """Called when an Engineer works on this building foundation."""
        if not self.under_construction or not self.is_alive:
            return False

        self.build_progress += delta_time * build_speed
        self.hp = min(self.max_hp, (self.build_progress / self.build_time) * self.max_hp)

        if self.build_progress >= self.build_time:
            self.under_construction = False
            self.hp = self.max_hp
            return True
        return False

    def queue_unit(self, unit_name: str) -> bool:
        if not self.is_operational or unit_name not in self.producible_units:
            return False
        if len(self.production_queue) < 5:  # Queue limit of 5
            self.production_queue.append(unit_name)
            return True
        return False

    def cancel_queued_unit(self, index: int = -1) -> Optional[str]:
        if not self.production_queue:
            return None
        cancelled = self.production_queue.pop(index)
        if index == 0 or len(self.production_queue) == 0:
            self.production_progress = 0.0
        return cancelled

    def update_production(self, delta_time: float) -> Optional[str]:
        """Progresses the current unit in the queue. Returns unit name if completed."""
        if not self.is_operational or not self.production_queue:
            return None

        current_unit = self.production_queue[0]
        required_time = UNIT_TYPES[current_unit]["build_time"]

        self.production_progress += delta_time
        if self.production_progress >= required_time:
            self.production_queue.pop(0)
            self.production_progress = 0.0
            return current_unit

        return None

    def update_industry(self, delta_time: float, economy) -> None:
        """Generates resources from passive generation and assigned workers."""
        if not self.is_operational:
            return

        # Passive production
        if self.passive_yield:
            res_type, rate = self.passive_yield
            economy.add(res_type, rate * delta_time)

        # Worker-boosted production
        if self.worker_yield and self.assigned_workers > 0:
            res_type, rate = self.worker_yield
            economy.add(res_type, rate * self.assigned_workers * delta_time)

    def get_world_rect(self) -> Tuple[float, float, float, float]:
        """Returns (left, top, width_px, height_px)."""
        left = self.tile_x * TILE_SIZE
        top = self.tile_y * TILE_SIZE
        width = self.width_tiles * TILE_SIZE
        height = self.height_tiles * TILE_SIZE
        return (left, top, width, height)

    def contains_point(self, px: float, py: float) -> bool:
        left, top, w, h = self.get_world_rect()
        return left <= px <= left + w and top <= py <= top + h
