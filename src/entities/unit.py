"""
Unit Entity and State Machine.
Supports Army, Navy, and Engineer units with combat, movement, building, and working tasks.
"""
import math
from enum import Enum, auto
from typing import List, Tuple, Optional, Any
from src.config import TILE_SIZE, Faction, Domain, UNIT_TYPES
from src.entities.base import Entity

class UnitState(Enum):
    IDLE = auto()
    MOVING = auto()
    ATTACKING = auto()
    BUILDING = auto()
    REPAIRING = auto()
    WORKING = auto()

class Unit(Entity):
    def __init__(
        self,
        unit_type_name: str,
        faction: Faction,
        x: float,
        y: float,
    ):
        data = UNIT_TYPES[unit_type_name]
        super().__init__(
            name=data["name"],
            faction=faction,
            x=x,
            y=y,
            max_hp=data["max_hp"],
            armor=data["armor"],
        )
        self.type_name = unit_type_name
        self.domain: Domain = data["domain"]
        self.branch: str = data["branch"]
        self.speed: float = data["speed"] * TILE_SIZE
        self.attack_damage: float = float(data["attack_damage"])
        self.attack_range: float = float(data["attack_range"]) * TILE_SIZE
        self.reload_time: float = float(data["reload_time"])
        self.sight_range: float = float(data["sight_range"]) * TILE_SIZE
        self.radius: float = float(data["radius"])
        self.symbol: str = data.get("symbol", "UNT")
        self.projectile_speed: float = float(data.get("projectile_speed", 15.0)) * TILE_SIZE
        self.weapon_type: str = data.get("weapon_type", "bullet")

        self.state: UnitState = UnitState.IDLE
        self.path: List[Tuple[float, float]] = []
        self.target_entity: Optional[Entity] = None
        self.cooldown_timer: float = 0.0
        self.assigned_building: Optional[Any] = None
        self._has_counted_work: bool = False

    def distance_to(self, target: Entity) -> float:
        return math.hypot(target.x - self.x, target.y - self.y)

    def distance_to_point(self, px: float, py: float) -> float:
        return math.hypot(px - self.x, py - self.y)

    def _update_velocity_from_path(self):
        if not self.path or not self.is_alive:
            self.vx = 0.0
            self.vy = 0.0
            return
        target_pt = self.path[0]
        for pt in self.path:
            d = math.hypot(pt[0] - self.x, pt[1] - self.y)
            if d > 2.0:
                target_pt = pt
                break
        dx = target_pt[0] - self.x
        dy = target_pt[1] - self.y
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
        else:
            self.vx = 0.0
            self.vy = 0.0

    def order_move(self, path: List[Tuple[float, float]]):
        self._detach_worker()
        self.target_entity = None
        self.path = list(path)
        self.state = UnitState.MOVING if self.path else UnitState.IDLE
        self._update_velocity_from_path()

    def order_attack(self, target: Entity, path: Optional[List[Tuple[float, float]]] = None):
        self._detach_worker()
        self.target_entity = target
        if path:
            self.path = list(path)
        self.state = UnitState.ATTACKING
        self._update_velocity_from_path()

    def order_build_or_repair(self, building: Any, path: Optional[List[Tuple[float, float]]] = None):
        self._detach_worker()
        self.assigned_building = building
        if path:
            self.path = list(path)
        self.state = UnitState.BUILDING if building.under_construction else UnitState.REPAIRING
        self._update_velocity_from_path()

    def order_work(self, building: Any, path: Optional[List[Tuple[float, float]]] = None):
        self._detach_worker()
        self.assigned_building = building
        if path:
            self.path = list(path)
        self.state = UnitState.WORKING
        self._update_velocity_from_path()

    def update(self, delta_time: float, game_map=None) -> Optional[dict]:
        if not self.is_alive:
            self.vx = 0.0
            self.vy = 0.0
            self._detach_worker()
            return None

        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - delta_time)

        if self.state == UnitState.MOVING:
            self._update_movement(delta_time, game_map)
            return None
        elif self.state == UnitState.ATTACKING:
            return self._update_attacking(delta_time, game_map)
        elif self.state in (UnitState.BUILDING, UnitState.REPAIRING):
            self._update_building(delta_time, game_map)
            return None
        elif self.state == UnitState.WORKING:
            self._update_working(delta_time, game_map)
            return None
        return None

    def _update_movement(self, delta_time: float, game_map=None):
        if not self.path:
            self.state = UnitState.IDLE
            self.vx = 0.0
            self.vy = 0.0
            return

        target_pt = self.path[0]
        dx = target_pt[0] - self.x
        dy = target_pt[1] - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * delta_time

        if dist <= step or dist < 2.0:
            next_x, next_y = target_pt
            if game_map and not game_map.is_passable(int(next_x // TILE_SIZE), int(next_y // TILE_SIZE), self.domain):
                self.path = []
                self.state = UnitState.IDLE
                self.vx = 0.0
                self.vy = 0.0
                return

            self.x, self.y = next_x, next_y
            self.path.pop(0)
            if not self.path:
                self.state = UnitState.IDLE
                self.vx = 0.0
                self.vy = 0.0
            else:
                self._update_velocity_from_path()
        else:
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
            next_x = self.x + self.vx * delta_time
            next_y = self.y + self.vy * delta_time

            if game_map and not game_map.is_passable(int(next_x // TILE_SIZE), int(next_y // TILE_SIZE), self.domain):
                self.path = []
                self.state = UnitState.IDLE
                self.vx = 0.0
                self.vy = 0.0
                return

            self.x = next_x
            self.y = next_y

    def predict_intercept_position(self, target: Entity) -> Tuple[float, float]:
        """
        Calculates predicted future intercept position based on target's position
        and velocity at the time of firing, using projectile speed.
        """
        tx = float(target.x)
        ty = float(target.y)
        t_vx = float(getattr(target, "vx", 0.0))
        t_vy = float(getattr(target, "vy", 0.0))

        v_sq = t_vx * t_vx + t_vy * t_vy
        if v_sq < 0.001:
            return (tx, ty)

        sp = float(self.projectile_speed)
        if sp <= 0.001:
            return (tx, ty)

        rx = tx - self.x
        ry = ty - self.y
        r_sq = rx * rx + ry * ry

        # Solve (v_sq - sp^2) * t^2 + 2 * (rx*t_vx + ry*t_vy) * t + r_sq = 0
        a = v_sq - sp * sp
        b = 2.0 * (rx * t_vx + ry * t_vy)
        c = r_sq

        if abs(a) < 1e-6:
            if abs(b) > 1e-6:
                t = -c / b
                if t > 0:
                    return (tx + t_vx * t, ty + t_vy * t)
            t = math.sqrt(r_sq) / sp
            return (tx + t_vx * t, ty + t_vy * t)

        disc = b * b - 4.0 * a * c
        if disc < 0:
            t = math.sqrt(r_sq) / sp
            return (tx + t_vx * t, ty + t_vy * t)

        sqrt_disc = math.sqrt(disc)
        t1 = (-b - sqrt_disc) / (2.0 * a)
        t2 = (-b + sqrt_disc) / (2.0 * a)

        valid_roots = [t for t in (t1, t2) if t > 0.0001]
        if valid_roots:
            t = min(valid_roots)
        else:
            t = math.sqrt(r_sq) / sp

        return (tx + t_vx * t, ty + t_vy * t)

    def _update_attacking(self, delta_time: float, game_map=None) -> Optional[dict]:
        if not self.target_entity or not self.target_entity.is_alive:
            self.target_entity = None
            self.state = UnitState.IDLE
            self.vx = 0.0
            self.vy = 0.0
            return None

        dist = self.distance_to(self.target_entity)
        if dist <= self.attack_range:
            self.path = []
            self.vx = 0.0
            self.vy = 0.0
            if self.cooldown_timer <= 0:
                self.cooldown_timer = self.reload_time
                target_pred = self.predict_intercept_position(self.target_entity)
                pred_dist = math.hypot(target_pred[0] - self.x, target_pred[1] - self.y)
                max_rng = max(self.attack_range, pred_dist)
                return {
                    "attacker": self,
                    "target": self.target_entity,
                    "damage": self.attack_damage,
                    "origin": (self.x, self.y),
                    "target_pos": target_pred,
                    "projectile_speed": self.projectile_speed,
                    "weapon_type": self.weapon_type,
                    "max_range": max_rng,
                }
        else:
            if not self.path and game_map:
                self.path = game_map.find_path((self.x, self.y), (self.target_entity.x, self.target_entity.y), self.domain)
                self._update_velocity_from_path()
            self._update_movement(delta_time, game_map)
        return None

    def _update_building(self, delta_time: float, game_map=None):
        if not self.assigned_building or not self.assigned_building.is_alive:
            self._detach_worker()
            self.state = UnitState.IDLE
            self.vx = 0.0
            self.vy = 0.0
            return

        dist = self.distance_to(self.assigned_building)
        interact_dist = max(TILE_SIZE * 2.0, (self.assigned_building.width_tiles * TILE_SIZE) * 0.8)

        if dist > interact_dist:
            if not self.path and game_map:
                self.path = game_map.find_path((self.x, self.y), (self.assigned_building.x, self.assigned_building.y), self.domain)
                self._update_velocity_from_path()
            self._update_movement(delta_time, game_map)
        else:
            self.path = []
            self.vx = 0.0
            self.vy = 0.0
            if self.state == UnitState.BUILDING:
                finished = self.assigned_building.progress_construction(delta_time, build_speed=2.0)
                if finished:
                    self.state = UnitState.IDLE
            elif self.state == UnitState.REPAIRING:
                self.assigned_building.repair_or_heal(delta_time * 30.0)
                if self.assigned_building.hp >= self.assigned_building.max_hp:
                    self.state = UnitState.IDLE

    def _update_working(self, delta_time: float, game_map=None):
        if not self.assigned_building or not self.assigned_building.is_alive:
            self._detach_worker()
            self.state = UnitState.IDLE
            self.vx = 0.0
            self.vy = 0.0
            return

        dist = self.distance_to(self.assigned_building)
        interact_dist = max(TILE_SIZE * 2.0, (self.assigned_building.width_tiles * TILE_SIZE) * 0.8)

        if dist > interact_dist:
            if not self.path and game_map:
                self.path = game_map.find_path((self.x, self.y), (self.assigned_building.x, self.assigned_building.y), self.domain)
                self._update_velocity_from_path()
            self._update_movement(delta_time, game_map)
        else:
            self.path = []
            self.vx = 0.0
            self.vy = 0.0
            if not self._has_counted_work:
                self.assigned_building.assigned_workers += 1
                self._has_counted_work = True


    def _detach_worker(self):
        if self.assigned_building and self._has_counted_work:
            if hasattr(self.assigned_building, "assigned_workers") and self.assigned_building.assigned_workers > 0:
                self.assigned_building.assigned_workers -= 1
        self._has_counted_work = False
        self.assigned_building = None
