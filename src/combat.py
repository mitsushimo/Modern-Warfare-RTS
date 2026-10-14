"""
Combat Effects and Projectiles.
Supports traveling projectiles with weapon-specific velocities and delayed damage.
"""
import math
from typing import List, Tuple, Optional, Any
from src.config import (
    COLOR_TRACER_BULLET, COLOR_TRACER_CANNON, COLOR_TRACER_TORPEDO,
    COLOR_TRACER_ARTILLERY, TILE_SIZE
)
from src.audio import SoundManager

class CombatEffect:
    def __init__(
        self,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        duration: float = 0.2,
        color: Tuple[int, int, int] = COLOR_TRACER_BULLET,
        width: int = 2,
    ):
        self.start_pos = (float(start_pos[0]), float(start_pos[1]))
        self.end_pos = (float(end_pos[0]), float(end_pos[1]))
        self.current_pos = [self.start_pos[0], self.start_pos[1]]
        self.duration = duration
        self.time_alive = 0.0
        self.color = color
        self.width = width
        self.has_impacted = False

    @property
    def is_finished(self) -> bool:
        return self.time_alive >= self.duration

    def update(self, delta_time: float):
        self.time_alive += delta_time


def check_segment_circle_hit(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    center: Tuple[float, float],
    radius: float,
) -> Optional[float]:
    """
    Checks if line segment p1 -> p2 intersects a circle at center with radius.
    Returns the distance along the segment [0, length] of the first intersection point,
    or None if no intersection occurs.
    """
    x1, y1 = p1
    x2, y2 = p2
    cx, cy = center
    dx = x2 - x1
    dy = y2 - y1
    seg_len = math.hypot(dx, dy)
    if seg_len < 1e-6:
        if math.hypot(x1 - cx, y1 - cy) <= radius:
            return 0.0
        return None

    ux = dx / seg_len
    uy = dy / seg_len
    fx = cx - x1
    fy = cy - y1
    proj = fx * ux + fy * uy
    dist_perp_sq = (fx * fx + fy * fy) - (proj * proj)
    rad_sq = radius * radius

    if dist_perp_sq > rad_sq:
        return None

    half_chord = math.sqrt(max(0.0, rad_sq - dist_perp_sq))
    t_entry = proj - half_chord
    t_exit = proj + half_chord

    if t_exit < 0.0 or t_entry > seg_len:
        return None

    return max(0.0, t_entry)


def check_segment_aabb_hit(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    rect: Tuple[float, float, float, float],
    padding: float = 0.0,
) -> Optional[float]:
    """
    Checks if segment p1 -> p2 intersects an axis-aligned box (left, top, w, h).
    Returns distance along segment [0, length] of first intersection, or None.
    """
    left = rect[0] - padding
    right = rect[0] + rect[2] + padding
    top = rect[1] - padding
    bottom = rect[1] + rect[3] + padding

    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    seg_len = math.hypot(dx, dy)

    if seg_len < 1e-6:
        if left <= x1 <= right and top <= y1 <= bottom:
            return 0.0
        return None

    t_min = 0.0
    t_max = 1.0

    if abs(dx) < 1e-6:
        if x1 < left or x1 > right:
            return None
    else:
        u1 = (left - x1) / dx
        u2 = (right - x1) / dx
        if u1 > u2:
            u1, u2 = u2, u1
        t_min = max(t_min, u1)
        t_max = min(t_max, u2)
        if t_min > t_max:
            return None

    if abs(dy) < 1e-6:
        if y1 < top or y1 > bottom:
            return None
    else:
        u1 = (top - y1) / dy
        u2 = (bottom - y1) / dy
        if u1 > u2:
            u1, u2 = u2, u1
        t_min = max(t_min, u1)
        t_max = min(t_max, u2)
        if t_min > t_max:
            return None

    return t_min * seg_len


class Projectile(CombatEffect):
    def __init__(
        self,
        start_pos: Tuple[float, float],
        target_pos: Tuple[float, float],
        speed: float,
        damage: float = 0.0,
        target: Optional[Any] = None,
        attacker: Optional[Any] = None,
        weapon_type: str = "bullet",
        color: Tuple[int, int, int] = COLOR_TRACER_BULLET,
        width: int = 2,
        head_radius: float = 2.5,
        max_range: Optional[float] = None,
    ):
        super().__init__(start_pos, target_pos, duration=15.0, color=color, width=width)
        self.target_pos = (float(target_pos[0]), float(target_pos[1]))
        self.speed = float(speed)
        self.damage = float(damage)
        self.target = target
        self.attacker = attacker
        self.weapon_type = weapon_type
        self.head_radius = head_radius

        dx = self.target_pos[0] - self.start_pos[0]
        dy = self.target_pos[1] - self.start_pos[1]
        dist = math.hypot(dx, dy)
        if dist > 0.0001:
            self.dir_x = dx / dist
            self.dir_y = dy / dist
        else:
            self.dir_x = 1.0
            self.dir_y = 0.0

        if max_range is not None:
            self.max_range = float(max_range)
        elif attacker and hasattr(attacker, "attack_range"):
            self.max_range = max(float(attacker.attack_range), dist)
        elif dist > 0:
            self.max_range = dist
        else:
            self.max_range = 1000.0

        self.distance_traveled = 0.0
        self.end_pos = (
            self.start_pos[0] + self.dir_x * self.max_range,
            self.start_pos[1] + self.dir_y * self.max_range,
        )
        self.trail: List[Tuple[float, float]] = [(self.start_pos[0], self.start_pos[1])]
        self.impact_timer = 0.0
        self.impact_duration = 0.12
        self.impact_radius = max(3.0, head_radius * 1.8)
        self.hit_entity: Optional[Any] = None

    @property
    def is_finished(self) -> bool:
        if not self.has_impacted:
            return self.time_alive >= self.duration
        return self.impact_timer >= self.impact_duration

    def update(self, delta_time: float, entities: Optional[List[Any]] = None):
        self.time_alive += delta_time
        if self.has_impacted:
            self.impact_timer += delta_time
            return

        remaining_range = self.max_range - self.distance_traveled
        if remaining_range <= 0.001:
            self.has_impacted = True
            self.impact_timer = 0.0
            return

        step = min(self.speed * delta_time, remaining_range)
        p_prev = (self.current_pos[0], self.current_pos[1])
        p_next = (
            p_prev[0] + self.dir_x * step,
            p_prev[1] + self.dir_y * step,
        )

        candidate_entities = []
        if entities is not None:
            candidate_entities = entities
        elif self.target and getattr(self.target, "is_alive", False):
            candidate_entities = [self.target]

        attacker_faction = getattr(self.attacker, "faction", None)

        best_hit_dist = None
        best_hit_entity = None

        for ent in candidate_entities:
            if not getattr(ent, "is_alive", False):
                continue
            if ent is self.attacker:
                continue
            if attacker_faction is not None and getattr(ent, "faction", None) == attacker_faction:
                continue

            hit_dist = None
            if hasattr(ent, "get_world_rect"):
                rect = ent.get_world_rect()
                hit_dist = check_segment_aabb_hit(p_prev, p_next, rect, padding=self.head_radius)
            else:
                rad = float(getattr(ent, "radius", 10.0)) + self.head_radius
                hit_dist = check_segment_circle_hit(p_prev, p_next, (ent.x, ent.y), rad)

            if hit_dist is not None:
                if best_hit_dist is None or hit_dist < best_hit_dist:
                    best_hit_dist = hit_dist
                    best_hit_entity = ent

        if best_hit_entity is not None:
            impact_x = p_prev[0] + self.dir_x * best_hit_dist
            impact_y = p_prev[1] + self.dir_y * best_hit_dist
            self.current_pos = [impact_x, impact_y]
            self.has_impacted = True
            self.impact_timer = 0.0
            self.hit_entity = best_hit_entity
            self.distance_traveled += best_hit_dist
            self.trail.append((impact_x, impact_y))
            if self.damage > 0:
                best_hit_entity.take_damage(self.damage)
        else:
            self.current_pos = [p_next[0], p_next[1]]
            self.distance_traveled += step
            self.trail.append((p_next[0], p_next[1]))
            max_t = 7 if self.weapon_type == "torpedo" else 4
            if len(self.trail) > max_t:
                self.trail.pop(0)

            if self.distance_traveled >= self.max_range - 0.001:
                self.has_impacted = True
                self.impact_timer = 0.0


class CombatManager:
    def __init__(self, sound_manager: Optional[SoundManager] = None):
        self.effects: List[CombatEffect] = []
        self.sound_manager = sound_manager if sound_manager is not None else SoundManager()

    @property
    def projectiles(self) -> List[Projectile]:
        return [e for e in self.effects if isinstance(e, Projectile)]

    def add_combat_event(self, event: dict):
        attacker = event.get("attacker")
        target = event.get("target")
        damage = float(event.get("damage", 0.0))
        origin = event.get("origin", (0, 0))
        target_pos = event.get("target_pos", (0, 0))
        unit_type = getattr(attacker, "type_name", "") if attacker else ""

        if self.sound_manager:
            self.sound_manager.play_attack_sound(unit_type)

        w_type = event.get("weapon_type")
        if not w_type:
            if "Torpedo" in unit_type:
                w_type = "torpedo"
            elif "Cannon" in unit_type or "Battleship" in unit_type:
                w_type = "artillery_shell"
            elif "Tank" in unit_type:
                w_type = "tank_shell"
            elif "Destroyer" in unit_type:
                w_type = "naval_shell"
            else:
                w_type = "bullet"

        if w_type == "torpedo":
            col, width, h_rad, def_spd = COLOR_TRACER_TORPEDO, 3, 4.0, 5.0 * TILE_SIZE
        elif w_type == "artillery_shell":
            col, width, h_rad, def_spd = COLOR_TRACER_ARTILLERY, 3, 4.5, 8.0 * TILE_SIZE
        elif w_type == "tank_shell":
            col, width, h_rad, def_spd = COLOR_TRACER_CANNON, 3, 3.5, 14.0 * TILE_SIZE
        elif w_type == "naval_shell":
            col, width, h_rad, def_spd = (255, 205, 90), 3, 3.5, 15.0 * TILE_SIZE
        else:
            col, width, h_rad, def_spd = COLOR_TRACER_BULLET, 2, 2.0, 22.0 * TILE_SIZE

        speed = float(event.get("projectile_speed", def_spd))
        max_range = event.get("max_range")
        self.effects.append(Projectile(
            start_pos=origin, target_pos=target_pos, speed=speed, damage=damage,
            target=target, attacker=attacker, weapon_type=w_type, color=col,
            width=width, head_radius=h_rad, max_range=max_range
        ))

    def update(self, delta_time: float, entities: Optional[List[Any]] = None):
        for effect in self.effects:
            if isinstance(effect, Projectile):
                effect.update(delta_time, entities=entities)
            else:
                effect.update(delta_time)
        self.effects = [e for e in self.effects if not e.is_finished]

