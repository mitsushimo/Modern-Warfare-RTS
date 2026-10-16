"""
Unit Tests for Grand Archipelago Large Showcase Theater.
"""
import os
import pygame
import pytest
from src.config import MAP_PRESETS, TILE_SIZE, Domain, Faction, TerrainType
from src.map_system import GameMap
from src.game_state import GameState
from src.renderer import Renderer, Camera
from src.input_handler import InputHandler

@pytest.fixture(autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def test_grand_archipelago_dimensions_and_metadata():
    """Validates Grand Archipelago configuration, 96x64 sizing, and preset info."""
    assert "Grand Archipelago" in MAP_PRESETS
    preset = MAP_PRESETS["Grand Archipelago"]
    assert preset["width"] == 96
    assert preset["height"] == 64
    assert preset["land_connected"] is True

    gmap = GameMap(width=96, height=64, map_name="Grand Archipelago")
    assert gmap.width == 96
    assert gmap.height == 64
    assert len(gmap.tiles) == 64
    assert len(gmap.tiles[0]) == 96


def test_grand_archipelago_natural_coastline_features():
    """Verifies organic coastal generation, realistic land/water distribution, and coast tile presence."""
    gmap = GameMap(width=96, height=64, map_name="Grand Archipelago")
    land_count = sum(row.count(TerrainType.LAND) for row in gmap.tiles)
    coast_count = sum(row.count(TerrainType.COAST) for row in gmap.tiles)
    water_count = sum(row.count(TerrainType.WATER) for row in gmap.tiles)

    total = 96 * 64
    assert land_count + coast_count + water_count == total
    assert coast_count > 150, "Natural coastline must have substantial coastal transition tiles"
    assert water_count > 2500, "Vast archipelagic channels must occupy substantial water area"

    land_ratio = (land_count + coast_count) / total
    assert 0.20 <= land_ratio <= 0.40, f"Archipelago land ratio {land_ratio:.2%} should be between 20% and 40%"


def test_grand_archipelago_land_connectivity_and_pathfinding():
    """Verifies that an unbroken strategic land route connects Player base to Enemy base across the archipelago."""
    gmap = GameMap(width=96, height=64, map_name="Grand Archipelago")
    start_pos = (10.0 * TILE_SIZE, 42.0 * TILE_SIZE)
    goal_pos = (80.0 * TILE_SIZE, 16.0 * TILE_SIZE)

    path = gmap.find_path(start_pos, goal_pos, Domain.LAND)
    assert len(path) > 40, "Path spanning across the 96x64 archipelago should traverse multiple strategic stepping isles"

    # Verify no waypoint walks on water
    for wx, wy in path:
        tx = int(wx // TILE_SIZE)
        ty = int(wy // TILE_SIZE)
        assert gmap.tiles[ty][tx] != TerrainType.WATER, f"Waypoint ({tx}, {ty}) must not be in water"


def test_grand_archipelago_starter_bases_and_shipyards():
    """Tests that all player and enemy structures and units spawn cleanly on Grand Archipelago."""
    gs = GameState(map_name="Grand Archipelago")
    assert gs.map.width == 96
    assert gs.map.height == 64
    assert gs.current_map_name == "Grand Archipelago"

    player_blds = {b.type_name: b for b in gs.buildings if b.faction == Faction.PLAYER}
    for b_type in ["HQ", "Farm", "Factory", "Barracks", "Refinery", "Shipyard"]:
        assert b_type in player_blds, f"Player {b_type} must be placed"
        assert player_blds[b_type].is_operational

    shipyard = player_blds["Shipyard"]
    assert gs.map.is_coastal_adjacent(shipyard.tile_x, shipyard.tile_y, 3, 3)

    enemy_blds = {b.type_name: b for b in gs.buildings if b.faction == Faction.ENEMY}
    for b_type in ["HQ", "Farm", "Factory", "Barracks", "Refinery", "Shipyard"]:
        assert b_type in enemy_blds, f"Enemy {b_type} must be placed"
        assert enemy_blds[b_type].is_operational

    player_units = [u for u in gs.units if u.faction == Faction.PLAYER]
    enemy_units = [u for u in gs.units if u.faction == Faction.ENEMY]
    assert len(player_units) >= 10
    assert len(enemy_units) >= 6

    for u in gs.units:
        assert u.is_alive
        tx = int(u.x // TILE_SIZE)
        ty = int(u.y // TILE_SIZE)
        t = gs.map.tiles[ty][tx]
        if u.domain == Domain.LAND:
            assert t in (TerrainType.LAND, TerrainType.COAST), f"Land unit {u.name} at ({tx}, {ty}) on water"
        elif u.domain == Domain.SEA:
            assert t == TerrainType.WATER, f"Sea vessel {u.name} at ({tx}, {ty}) on land"

def test_grand_archipelago_camera_bounds_and_zoom():
    """Validates camera bounds adaptation and coordinate conversion on the 96x64 map."""
    cam = Camera(1280, 768, projection_mode="isometric", map_width=96, map_height=64)
    assert cam.map_width == 96
    assert cam.map_height == 64

    total_u = (96 + 64) * TILE_SIZE
    total_v = (96 + 64) * TILE_SIZE * 0.5
    assert cam.max_x == total_u - 1280
    assert cam.max_y == total_v - 768

    cam.zoom = 0.5
    cam.update_bounds(1280, 768)
    for wx, wy in [(0.0, 0.0), (96.0 * 32, 0.0), (0.0, 64.0 * 32), (96.0 * 32, 64.0 * 32)]:
        sx, sy = cam.world_to_screen(wx, wy)
        r_wx, r_wy = cam.screen_to_world(sx, sy)
        assert abs(r_wx - wx) <= 4.0
        assert abs(r_wy - wy) <= 4.0


def test_grand_archipelago_modal_pagination_and_selection():
    """Tests navigating the modal to page 2 and deploying to Grand Archipelago."""
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    handler.show_map_menu = True
    renderer.render_map_selection_modal(gs.current_map_name, (0, 0))
    assert renderer.map_modal_page == 0
    assert len(renderer.modal_buttons) == 4

    next_btn = next(b for b in renderer.modal_page_buttons if b["page_delta"] == 1)
    click_next = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=next_btn["rect"].center)
    handler.handle_events([click_next], gs, renderer)
    assert renderer.map_modal_page == 1

    renderer.render_map_selection_modal(gs.current_map_name, (0, 0))
    ga_btn = next(b for b in renderer.modal_buttons if b["map_name"] == "Grand Archipelago")
    assert ga_btn is not None

    click_ga = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=ga_btn["rect"].center)
    handler.handle_events([click_ga], gs, renderer)

    assert handler.show_map_menu is False
    assert gs.current_map_name == "Grand Archipelago"
    assert gs.map.width == 96
    assert gs.map.height == 64
    assert renderer.camera.map_width == 96
    assert renderer.camera.map_height == 64


def test_grand_archipelago_save_and_load(tmp_path):
    """Verifies saving and loading progress preserves Grand Archipelago 96x64 map dimensions."""
    save_dir = str(tmp_path / "archipelago_saves")
    gs = GameState(map_name="Grand Archipelago")
    assert gs.map.width == 96
    assert gs.map.height == 64
    gs.save_game("archipelago_progress", save_dir=save_dir)

    gs2 = GameState(map_name="Divided Sea")
    assert gs2.map.width == 64
    loaded = gs2.load_game("archipelago_progress", save_dir=save_dir)
    assert loaded is True
    assert gs2.current_map_name == "Grand Archipelago"
    assert gs2.map.width == 96
    assert gs2.map.height == 64

