"""
Base Entity class for Units and Buildings.
"""
import math
import uuid
from typing import Tuple
from src.config import Faction

class Entity:
    def __init__(
        self,
        name: str,
        faction: Faction,
        x: float,
        y: float,
        max_hp: float,
        armor: int = 0,
    ):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.faction = faction
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.max_hp = float(max_hp)
        self.hp = float(max_hp)
        self.armor = armor
        self.is_selected = False

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def position(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @property
    def velocity(self) -> Tuple[float, float]:
        return (self.vx, self.vy)

    def distance_to_point(self, px: float, py: float) -> float:
        return math.hypot(px - self.x, py - self.y)

    def take_damage(self, raw_damage: float) -> float:
        """Applies damage mitigated by armor. Returns actual damage dealt."""
        effective_damage = max(1.0, float(raw_damage - self.armor))
        self.hp = max(0.0, self.hp - effective_damage)
        return effective_damage

    def repair_or_heal(self, amount: float):
        if self.is_alive:
            self.hp = min(self.max_hp, self.hp + amount)

