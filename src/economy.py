"""
Economy System.
Tracks stockpiles of Food, Steel, and Fuel for each faction.
"""
from typing import Dict
from src.config import ResourceType, STARTING_RESOURCES, Faction

class FactionEconomy:
    def __init__(self, faction: Faction):
        self.faction = faction
        self.resources: Dict[ResourceType, float] = {
            res: float(val) for res, val in STARTING_RESOURCES.items()
        }

    def get_amount(self, resource: ResourceType) -> float:
        return self.resources.get(resource, 0.0)

    def can_afford(self, cost: Dict[ResourceType, int]) -> bool:
        for res, amount in cost.items():
            if self.resources.get(res, 0.0) < amount:
                return False
        return True

    def deduct(self, cost: Dict[ResourceType, int]) -> bool:
        if not self.can_afford(cost):
            return False
        for res, amount in cost.items():
            self.resources[res] -= amount
        return True

    def add(self, resource: ResourceType, amount: float):
        self.resources[resource] = self.resources.get(resource, 0.0) + amount

    def refund(self, cost: Dict[ResourceType, int]):
        for res, amount in cost.items():
            self.resources[res] = self.resources.get(res, 0.0) + amount
