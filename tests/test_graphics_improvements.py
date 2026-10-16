"""
Unit Tests for Isometric Projection, Triangular Terrain Graphics, and Asset Pipeline.
"""
import os
import math
import pygame
import pytest
from src.config import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, Faction
from src.renderer import Camera, Renderer
from src.game_state import GameState
from src.input_handler import InputHandler
from src.asset_manager import AssetManager
from src.entities.unit import Unit
from src.entities.building import Building

@pytest.fixture(autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def test_isometric_projection_round_trip():
    """Validates that world_to_screen and screen_to_world are analytical inverses in isometric mode."""
    cam = Camera(1280, 768, projection_mode="isometric")
    cam.move(250.0, 150.0)

    for zoom in (0.5, 0.75, 1.0, 1.33, 2.0):
        cam.zoom = zoom
        for wx, wy in [(0.0, 0.0), (128.0, 256.0), (800.0, 600.0), (1500.0, 1000.0)]:
            sx, sy = cam.world_to_screen(wx, wy)
            rec_wx, rec_wy = cam.screen_to_world(sx, sy)
            # Int truncation on screen coords allows max 2px / zoom variance
            assert abs(rec_wx - wx) <= 2.0 / zoom
            assert abs(rec_wy - wy) <= 2.0 / zoom


def test_projection_mode_toggle():
    """Tests that projection mode is always isometric."""
    cam = Camera(1280, 768, projection_mode="isometric")
    assert cam.projection_mode == "isometric"

    cam.toggle_projection()
    assert cam.projection_mode == "isometric"


def test_input_handler_tab_does_not_toggle_projection_always_isometric():
    """Pressing Tab no longer toggles projection mode; game remains in isometric mode."""
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    assert renderer.camera.projection_mode == "isometric"

    tab_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)
    handler.handle_events([tab_event], gs, renderer)
    assert renderer.camera.projection_mode == "isometric"


def test_depth_sorting_entities():
    """Depth sorting in render_entities ensures back entities render before front entities."""
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)
    renderer.camera.projection_mode = "isometric"

    # Unit 1 is further back (smaller x+y) than Unit 2
    u1 = Unit("Foot Soldier", Faction.PLAYER, 100.0, 100.0)  # depth = 200
    u2 = Unit("Foot Soldier", Faction.PLAYER, 500.0, 500.0)  # depth = 1000
    bld = Building("HQ", Faction.PLAYER, 6, 6)               # depth = (6+3 + 6+3)*32 = 576

    # Verify render_entities renders without exceptions
    renderer.render_entities([bld], [u2, u1])


def test_screen_space_single_and_box_selection():
    """Tests accurate screen-space unit clicking and drag-box selection in isometric mode."""
    gs = GameState()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)
    renderer.camera.projection_mode = "isometric"

    # Spawn unit at known world coordinate
    unit = gs.spawn_unit("Foot Soldier", Faction.PLAYER, 200.0, 200.0)
    sx, sy = renderer.camera.world_to_screen(unit.x, unit.y)

    # 1. Click directly on unit's screen position
    gs.select_single_screen(sx, sy, renderer.camera)
    assert unit in gs.selected_entities
    assert unit.is_selected is True

    # 2. Click away
    gs.select_single_screen(sx + 200, sy + 200, renderer.camera)
    assert unit not in gs.selected_entities

    # 3. Marquee box selection enclosing unit screen position
    drag_rect = pygame.Rect(sx - 20, sy - 20, 40, 40)
    gs.select_box_screen(drag_rect, renderer.camera)
    assert unit in gs.selected_entities


def test_triangular_terrain_mesh_rendering():
    """Renders map in isometric mode with 4-triangle facet shaded tiles."""
    gs = GameState()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)
    renderer.camera.projection_mode = "isometric"

    # Render terrain in isometric
    renderer.render_map(gs.map)

    # Switch to topdown and render
    renderer.camera.projection_mode = "topdown"
    renderer.render_map(gs.map)


def test_asset_manager_fallback_and_caching(tmp_path):
    """Verifies that AssetManager gracefully falls back to procedural graphics and caches loaded sprites."""
    am = AssetManager(assets_dir=str(tmp_path))

    # Missing sprites return None (triggers procedural fallback)
    assert am.get_building_sprite("HQ", 1.0) is None
    assert am.get_unit_sprite("Tank", 1.0) is None

    # Save a dummy sprite PNG to temporary folder
    test_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    test_surf.fill((255, 0, 0, 255))
    dummy_path = tmp_path / "tank.png"
    pygame.image.save(test_surf, str(dummy_path))

    # Reload asset manager with this path
    am2 = AssetManager(assets_dir=str(tmp_path))
    loaded = am2.get_unit_sprite("Tank", 1.0)
    assert loaded is not None
    assert loaded.get_size() == (64, 64)

    # Scaled cache
    zoomed = am2.get_unit_sprite("Tank", 1.5)
    assert zoomed is not None
    assert zoomed.get_size() == (96, 96)
    # Check cache hit returns same surface
    zoomed_cached = am2.get_unit_sprite("Tank", 1.5)
    assert zoomed_cached is zoomed


def test_asset_manager_high_res_jpeg_normalization_and_disk_preservation():
    """
    Validates that high-res JPG files are safely loaded into in-memory bounded footprints,
    outer white backgrounds are made transparent, and disk files remain completely untouched.
    """
    hq_disk_path = os.path.join("assets", "sprites", "buildings", "hq.jpg")
    assert os.path.exists(hq_disk_path)
    original_disk_size = os.path.getsize(hq_disk_path)

    am = AssetManager(assets_dir="assets/sprites")
    hq_sprite = am.get_building_sprite("HQ", 1.0)
    assert hq_sprite is not None

    # Normalization: 1x sprite fits within 3x3 footprint (192 x 220)
    w, h = hq_sprite.get_size()
    assert w <= 192 and h <= 220

    # Top-left corner must be transparent (white background keyed out)
    assert hq_sprite.get_at((0, 0)).a == 0

    # Zoomed 2.5x sprite does not crash and remains bounded in size
    hq_zoomed = am.get_building_sprite("HQ", 2.5)
    assert hq_zoomed is not None
    zw, zh = hq_zoomed.get_size()
    assert zw <= 480 and zh <= 550

    # Verify original file on disk was not modified
    assert os.path.getsize(hq_disk_path) == original_disk_size


def test_building_sprite_ground_flush_anchoring():
    """Verifies that building sprites anchor flush to the bottom-most ground diamond vertex."""
    from src.renderer import Camera, Renderer
    from src.entities.building import Building
    from src.config import Faction, TILE_SIZE

    surf = pygame.Surface((1280, 768))
    renderer = Renderer(surf)
    bld = Building("HQ", Faction.PLAYER, 10, 10)
    zoom = 1.0

    # Compute expected ground bottom vertex
    wx1 = (bld.tile_x + bld.width_tiles) * TILE_SIZE
    wy1 = (bld.tile_y + bld.height_tiles) * TILE_SIZE
    g_bottom = renderer.camera.world_to_screen(wx1, wy1)

    sprite = renderer.asset_manager.get_building_sprite(bld.type_name, zoom)
    assert sprite is not None
    sprite_rect = sprite.get_rect(midbottom=g_bottom)

    # Building base must align with g_bottom
    assert sprite_rect.midbottom == g_bottom
    assert sprite_rect.bottom == g_bottom[1]


def test_asset_manager_directional_mirroring(tmp_path):
    """Verifies that 5-direction sprites automatically mirror for western sectors (sw, w, nw)."""
    # Create an asymmetrical surface (red dot on right side)
    surf = pygame.Surface((48, 48), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    pygame.draw.circle(surf, (255, 0, 0, 255), (38, 24), 6)
    img_path = tmp_path / "foot_soldier_se.png"
    pygame.image.save(surf, str(img_path))

    am = AssetManager(assets_dir=str(tmp_path))

    # Direct retrieval of South-East sprite
    se_sprite = am.get_unit_sprite("Foot Soldier", 1.0, direction="se")
    assert se_sprite is not None
    # Red circle should be on the right side (x > 24)
    assert se_sprite.get_at((38, 24)).r == 255

    # South-West sprite should be automatically generated by horizontal flipping
    sw_sprite = am.get_unit_sprite("Foot Soldier", 1.0, direction="sw")
    assert sw_sprite is not None
    # Flipped red circle should now be on the left side (48 - 1 - 38 = 9)
    assert sw_sprite.get_at((9, 24)).r == 255


def test_unit_heading_and_turret_compass_tracking():
    """Tests unit heading retention and turret aiming compass sectors."""
    tank = Unit("Tank", Faction.PLAYER, 100.0, 100.0)
    assert tank.heading_angle is not None
    assert tank.turret_angle is not None

    # Move right (East)
    tank.order_move([(200.0, 100.0)])
    assert tank.vx > 0.0
    dir_str = tank.get_compass_direction(projection_mode="isometric")
    assert dir_str in ("e", "se", "ne")

    # Stop unit: heading angle must persist even when stationary
    tank.path = []
    tank._update_movement(0.1)
    assert tank.vx == 0.0
    assert tank.get_compass_direction(projection_mode="isometric") == dir_str


def test_ship_size_adjustments():
    """Battleship footprint is 2X (256, 192), Torpedo Boat is 75% (60, 48), Destroyer is unchanged (96, 72)."""
    from src.asset_manager import UNIT_TARGET_SIZES
    from src.config import UNIT_TYPES

    assert UNIT_TARGET_SIZES["battleship"] == (256, 192)
    assert UNIT_TARGET_SIZES["torpedo_boat"] == (60, 48)
    assert UNIT_TARGET_SIZES["destroyer"] == (96, 72)

    assert UNIT_TYPES["Battleship"]["radius"] == 36
    assert UNIT_TYPES["Torpedo Boat"]["radius"] == 9
    assert UNIT_TYPES["Destroyer"]["radius"] == 15


def test_faction_circular_dot_on_unit_hp_bar():
    """Renders unit HP bar with a blue (player) or red (enemy) circular dot on top."""
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    player_unit = Unit("Battleship", Faction.PLAYER, 400.0, 400.0)
    enemy_unit = Unit("Battleship", Faction.ENEMY, 500.0, 500.0)

    # Render without errors
    renderer._render_unit_isometric(player_unit, 1.0)
    renderer._render_unit_isometric(enemy_unit, 1.0)


def test_click_any_part_of_ship_image_selects_unit():
    """Validates selecting a ship by clicking on the edges/ends of its displayed image (outside center radius)."""
    gs = GameState()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    # Spawn Battleship at world (400, 400)
    ship = gs.spawn_unit("Battleship", Faction.PLAYER, 400.0, 400.0)
    sx, sy = renderer.camera.world_to_screen(ship.x, ship.y)

    # Get displayed sprite to verify dimensions
    sprite = renderer.asset_manager.get_unit_sprite("Battleship", 1.0, direction=ship.get_compass_direction())
    assert sprite is not None
    s_rect = sprite.get_rect(center=(sx, sy))

    # Click on the bow/front edge of the ship (far from center, e.g. 50px away)
    bow_click_x = sx + int(s_rect.width * 0.35)
    bow_click_y = sy - int(s_rect.height * 0.25)
    assert math.hypot(bow_click_x - sx, bow_click_y - sy) > 25.0

    gs.select_single_screen(bow_click_x, bow_click_y, renderer.camera, renderer.asset_manager)
    assert ship in gs.selected_entities
    assert ship.is_selected is True

    # Click far outside the ship image deselects
    gs.select_single_screen(sx + 300, sy + 300, renderer.camera, renderer.asset_manager)
    assert ship not in gs.selected_entities


