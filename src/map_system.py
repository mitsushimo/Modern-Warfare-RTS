"""
Map and Pathfinding System.
Handles terrain generation, tile querying, and domain-aware A* pathfinding.
"""
import math
import heapq
from typing import List, Tuple, Optional, Dict
from src.config import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, TerrainType, Domain

class GameMap:
    def __init__(self, width: int = MAP_WIDTH, height: int = MAP_HEIGHT, map_name: str = "Divided Sea"):
        self.width = width
        self.height = height
        self.map_name = map_name
        self.tiles: List[List[TerrainType]] = [
            [TerrainType.LAND for _ in range(width)] for _ in range(height)
        ]
        self.building_grid: Dict[Tuple[int, int], str] = {}
        self.generate_map(map_name)

    def generate_map(self, map_name: str = "Divided Sea"):
        self.map_name = map_name
        self.tiles = [[TerrainType.LAND for _ in range(self.width)] for _ in range(self.height)]
        self.building_grid.clear()

        if map_name == "Continental Front":
            self._generate_continental_front()
        elif map_name == "Shattered Isthmus":
            self._generate_shattered_isthmus()
        elif map_name == "Inland Sea":
            self._generate_inland_sea()
        else:
            self._generate_divided_sea()

        self._apply_coasts()

    def _generate_default_map(self):
        """Backward compatibility for direct callers."""
        self._generate_divided_sea()
        self._apply_coasts()

    def _generate_divided_sea(self):
        """Creates a strategic map with western & eastern landmasses separated by a sea."""
        for y in range(self.height):
            for x in range(self.width):
                left_coast = int(24 + 3.0 * math.sin(y * 0.25))
                right_coast = int(39 + 3.0 * math.cos(y * 0.25))

                if left_coast <= x <= right_coast:
                    self.tiles[y][x] = TerrainType.WATER
                elif x == left_coast - 1 or x == right_coast + 1:
                    self.tiles[y][x] = TerrainType.COAST
                else:
                    self.tiles[y][x] = TerrainType.LAND

    def _generate_continental_front(self):
        """Direct land warfare map. Continuous landmass connects Player and Enemy territories."""
        for y in range(self.height):
            for x in range(self.width):
                if (y <= 6 or y >= self.height - 7) and (20 <= x <= 44):
                    offset = int(1.5 * math.sin(x * 0.4))
                    if y <= 6 + offset or y >= (self.height - 7 + offset):
                        self.tiles[y][x] = TerrainType.WATER
                    else:
                        self.tiles[y][x] = TerrainType.LAND
                else:
                    self.tiles[y][x] = TerrainType.LAND

    def _generate_shattered_isthmus(self):
        """Player & Enemy connected across a central land bridge (y=18..29) flanked by north and south seas."""
        for y in range(self.height):
            for x in range(self.width):
                if 18 <= x <= 45:
                    bridge_top = int(18 + 2.0 * math.sin(x * 0.3))
                    bridge_bottom = int(29 + 2.0 * math.cos(x * 0.3))
                    if bridge_top <= y <= bridge_bottom:
                        self.tiles[y][x] = TerrainType.LAND
                    else:
                        self.tiles[y][x] = TerrainType.WATER
                else:
                    self.tiles[y][x] = TerrainType.LAND

    def _generate_inland_sea(self):
        """A central inland sea surrounded by northern and southern land corridors connecting both factions."""
        cx = self.width / 2.0
        cy = self.height / 2.0
        rx = 13.5
        ry = 9.0
        for y in range(self.height):
            for x in range(self.width):
                dist = (((x - cx) / rx) ** 2) + (((y - cy) / ry) ** 2)
                wave = 0.12 * math.sin(math.atan2(y - cy, x - cx) * 5.0)
                if dist + wave <= 1.0:
                    self.tiles[y][x] = TerrainType.WATER
                else:
                    self.tiles[y][x] = TerrainType.LAND

    def _apply_coasts(self):
        """Marks any land tile immediately bordering water as COAST."""
        coasts = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == TerrainType.LAND:
                    has_water_neighbor = False
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if self.is_in_bounds(nx, ny) and self.tiles[ny][nx] == TerrainType.WATER:
                                has_water_neighbor = True
                                break
                        if has_water_neighbor:
                            break
                    if has_water_neighbor:
                        coasts.append((x, y))
        for x, y in coasts:
            self.tiles[y][x] = TerrainType.COAST

    def is_in_bounds(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height

    def get_terrain(self, tx: int, ty: int) -> Optional[TerrainType]:
        if not self.is_in_bounds(tx, ty):
            return None
        return self.tiles[ty][tx]

    def is_passable(self, tx: int, ty: int, domain: Domain) -> bool:
        if not self.is_in_bounds(tx, ty):
            return False
        if (tx, ty) in self.building_grid:
            return False
        terrain = self.tiles[ty][tx]
        if domain == Domain.LAND:
            return terrain in (TerrainType.LAND, TerrainType.COAST)
        elif domain == Domain.SEA:
            return terrain == TerrainType.WATER
        return False

    def is_coastal_adjacent(self, tx: int, ty: int, width: int, height: int) -> bool:
        has_land, has_water = False, False
        for y in range(ty - 1, ty + height + 1):
            for x in range(tx - 1, tx + width + 1):
                if not self.is_in_bounds(x, y):
                    continue
                t = self.tiles[y][x]
                if t in (TerrainType.LAND, TerrainType.COAST):
                    has_land = True
                elif t == TerrainType.WATER:
                    has_water = True
        return has_land and has_water

    def can_place_building(
        self, tx: int, ty: int, width: int, height: int, coastal_required: bool = False
    ) -> bool:
        for dy in range(height):
            for dx in range(width):
                cur_x, cur_y = tx + dx, ty + dy
                if not self.is_in_bounds(cur_x, cur_y) or (cur_x, cur_y) in self.building_grid:
                    return False
                t = self.tiles[cur_y][cur_x]
                if t not in (TerrainType.LAND, TerrainType.COAST):
                    return False
        if coastal_required and not self.is_coastal_adjacent(tx, ty, width, height):
            return False
        return True

    def register_building(self, building_id: str, tx: int, ty: int, width: int, height: int):
        for dy in range(height):
            for dx in range(width):
                self.building_grid[(tx + dx, ty + dy)] = building_id

    def unregister_building(self, tx: int, ty: int, width: int, height: int):
        for dy in range(height):
            for dx in range(width):
                self.building_grid.pop((tx + dx, ty + dy), None)

    def find_spawn_tile(
        self, tx: int, ty: int, width: int, height: int, domain: Domain
    ) -> Optional[Tuple[int, int]]:
        candidates = []
        for y in range(ty - 1, ty + height + 1):
            for x in range(tx - 1, tx + width + 1):
                if tx <= x < tx + width and ty <= y < ty + height:
                    continue
                if self.is_passable(x, y, domain):
                    dist = math.hypot(x + 0.5 - (tx + width / 2.0), y + 0.5 - (ty + height / 2.0))
                    candidates.append((dist, (x, y)))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def find_path(
        self, start_pos: Tuple[float, float], goal_pos: Tuple[float, float], domain: Domain
    ) -> List[Tuple[float, float]]:
        start_tx = max(0, min(self.width - 1, int(start_pos[0] // TILE_SIZE)))
        start_ty = max(0, min(self.height - 1, int(start_pos[1] // TILE_SIZE)))
        goal_tx = max(0, min(self.width - 1, int(goal_pos[0] // TILE_SIZE)))
        goal_ty = max(0, min(self.height - 1, int(goal_pos[1] // TILE_SIZE)))

        if not self.is_passable(start_tx, start_ty, domain):
            found_start = False
            for r in range(1, 4):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        cand_x, cand_y = start_tx + dx, start_ty + dy
                        if self.is_passable(cand_x, cand_y, domain):
                            start_tx, start_ty = cand_x, cand_y
                            found_start = True
                            break
                    if found_start:
                        break
                if found_start:
                    break
            if not found_start:
                return []

        if start_tx == goal_tx and start_ty == goal_ty:
            if self.is_passable(goal_tx, goal_ty, domain):
                return [goal_pos]
            return []

        exact_goal_passable = self.is_passable(goal_tx, goal_ty, domain)
        target_goal_node = (goal_tx, goal_ty) if exact_goal_passable else None

        if target_goal_node is None:
            alt_goal = None
            best_alt_dist = float("inf")
            for r in range(1, 3):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        cand_x, cand_y = goal_tx + dx, goal_ty + dy
                        if self.is_passable(cand_x, cand_y, domain):
                            d = math.hypot(cand_x - goal_tx, cand_y - goal_ty)
                            if d < best_alt_dist:
                                best_alt_dist = d
                                alt_goal = (cand_x, cand_y)
                if alt_goal:
                    break
            target_goal_node = alt_goal

        def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
            return math.hypot(a[0] - b[0], a[1] - b[1])

        start_node = (start_tx, start_ty)
        aim_node = target_goal_node if target_goal_node else (goal_tx, goal_ty)

        closed_set = set()
        open_set = []
        heapq.heappush(open_set, (heuristic(start_node, aim_node), 0.0, start_node))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start_node: 0.0}

        best_node = start_node
        best_dist = heuristic(start_node, (goal_tx, goal_ty))

        directions = [
            (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
            (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
        ]

        max_visited = self.width * self.height * 2
        visited = 0

        while open_set and visited < max_visited:
            visited += 1
            _, cur_g, current = heapq.heappop(open_set)

            if current in closed_set:
                continue
            closed_set.add(current)

            d = heuristic(current, (goal_tx, goal_ty))
            if d < best_dist:
                best_dist = d
                best_node = current

            if target_goal_node and current == target_goal_node:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                world_path = [
                    ((tx + 0.5) * TILE_SIZE, (ty + 0.5) * TILE_SIZE) for (tx, ty) in path
                ]
                if exact_goal_passable:
                    world_path[-1] = goal_pos
                return world_path

            for dx, dy, move_cost in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if neighbor in closed_set:
                    continue
                if not self.is_passable(neighbor[0], neighbor[1], domain):
                    continue
                if dx != 0 and dy != 0:
                    if not self.is_passable(current[0] + dx, current[1], domain) or \
                       not self.is_passable(current[0], current[1] + dy, domain):
                        continue

                tentative_g = cur_g + move_cost
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + heuristic(neighbor, aim_node)
                    heapq.heappush(open_set, (f, tentative_g, neighbor))

        # Destination unreachable: stop at closest reachable passable tile (e.g. shore)
        if best_node == start_node:
            return []

        path = [best_node]
        current = best_node
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        world_path = [
            ((tx + 0.5) * TILE_SIZE, (ty + 0.5) * TILE_SIZE) for (tx, ty) in path
        ]
        return world_path
