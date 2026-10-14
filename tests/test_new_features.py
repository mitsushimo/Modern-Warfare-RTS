"""
Tests for Pause Menu, Game Save, Minimap, Building Unit Creation Status, and Building Rally Point.
"""
import os
import pygame
import pytest
from src.config import (
    Domain, Faction, ResourceType, UNIT_TYPES, BUILDING_TYPES, TILE_SIZE, TerrainType
)
from src.entities.building import Building
from src.entities.unit import Unit, UnitState
from src.game_state import GameState
from src.renderer import Renderer
from src.input_handler import InputHandler

@pytest.fixture(autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def test_pause_toggle_via_esc():
    """ESC pauses when no unit is selected, clears selection if units selected."""
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    # 1. When a unit is selected, pressing ESC clears selection and does NOT pause
    unit = gs.units[0]
    gs.selected_entities = [unit]
    unit.is_selected = True

    esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    handler.handle_events([esc_event], gs, renderer)

    assert not gs.selected_entities
    assert not gs.is_paused

    # 2. When no unit is selected, pressing ESC pauses the game
    handler.handle_events([esc_event], gs, renderer)
    assert gs.is_paused is True

    # 3. Pressing ESC again while paused unpauses the game
    handler.handle_events([esc_event], gs, renderer)
    assert gs.is_paused is False


def test_pause_freezes_simulation():
    """When paused, game_state.update(dt) does not advance simulation."""
    gs = GameState()
    unit = gs.units[0]
    initial_pos = (unit.x, unit.y)
    unit.order_move([(unit.x + 100, unit.y)])

    gs.is_paused = True
    for _ in range(10):
        gs.update(0.1)

    assert (unit.x, unit.y) == initial_pos


def test_pause_menu_buttons_and_actions():
    """Pause modal displays Resume, Save, Load a saved game, and Quit buttons with corresponding actions."""
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    gs.is_paused = True
    renderer.render_pause_modal((0, 0), show_save=False, show_load=False)

    button_labels = [b["label"] for b in renderer.pause_buttons]
    assert "Resume" in button_labels
    assert "Save" in button_labels
    assert "Load a saved game" in button_labels
    assert "Quit" in button_labels

    # Test Resume button click
    resume_btn = next(b for b in renderer.pause_buttons if b["action"] == "resume")
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=resume_btn["rect"].center)
    handler.handle_events([click_event], gs, renderer)
    assert gs.is_paused is False

    # Test Quit button click
    gs.is_paused = True
    renderer.render_pause_modal((0, 0), show_save=False, show_load=False)
    quit_btn = next(b for b in renderer.pause_buttons if b["action"] == "quit")
    click_quit = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=quit_btn["rect"].center)
    ret = handler.handle_events([click_quit], gs, renderer)
    assert ret is False  # Quit requested



def test_save_and_load_game(tmp_path):
    """Saves game progress to a file, overwrites it, and restores state on load."""
    save_dir = str(tmp_path / "test_saves")
    gs = GameState()
    gs.economies[Faction.PLAYER].resources[ResourceType.FOOD] = 777.0
    gs.economies[Faction.PLAYER].resources[ResourceType.STEEL] = 888.0

    hq = next(b for b in gs.buildings if b.type_name == "HQ" and b.faction == Faction.PLAYER)
    hq.rally_point = (100.0, 200.0)
    hq.queue_unit("Engineer")

    # 1. Save game
    save_path = gs.save_game("my_test_save", save_dir=save_dir)
    assert os.path.exists(save_path)
    assert "my_test_save" in gs.list_saves(save_dir=save_dir)

    # 2. Overwrite existing save
    gs.economies[Faction.PLAYER].resources[ResourceType.FOOD] = 999.0
    gs.save_game("my_test_save", save_dir=save_dir)

    # 3. Load game into a new state
    new_gs = GameState()
    loaded = new_gs.load_game("my_test_save", save_dir=save_dir)
    assert loaded is True
    assert new_gs.economies[Faction.PLAYER].resources[ResourceType.FOOD] == 999.0
    assert new_gs.economies[Faction.PLAYER].resources[ResourceType.STEEL] == 888.0

    loaded_hq = next(b for b in new_gs.buildings if b.type_name == "HQ" and b.faction == Faction.PLAYER)
    assert loaded_hq.rally_point == (100.0, 200.0)
    assert "Engineer" in loaded_hq.production_queue


def test_minimap_rendering_and_viewport():
    """Minimap is placed in lower-right corner and viewport rectangle reflects camera view."""
    screen_w, screen_h = 1280, 768
    screen = pygame.Surface((screen_w, screen_h))
    renderer = Renderer(screen)
    gs = GameState()

    renderer.render_minimap(gs.map, gs.buildings, gs.units)

    # Lower right corner check
    assert renderer.minimap_rect.right <= screen_w
    assert renderer.minimap_rect.bottom <= screen_h
    assert renderer.minimap_rect.left > screen_w // 2
    assert renderer.minimap_rect.top > screen_h // 2

    # Viewport rectangle initial position (camera at 0, 0)
    assert renderer.minimap_viewport_rect.left >= renderer.minimap_rect.left

    # Move camera and verify viewport rectangle updates
    renderer.camera.move(200.0, 200.0)
    renderer.render_minimap(gs.map, gs.buildings, gs.units)
    assert renderer.minimap_viewport_rect.left > renderer.minimap_rect.left


def test_building_unit_creation_status_display():
    """Unit creation status, queue, and progress bar are rendered in HUD for producing buildings."""
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)
    gs = GameState()

    hq = next(b for b in gs.buildings if b.type_name == "HQ" and b.faction == Faction.PLAYER)
    hq.is_selected = True

    # 1. Idle status when queue is empty
    renderer.render_bottom_hud([hq], gs.economies[Faction.PLAYER], (0, 0))

    # 2. Status when training
    hq.queue_unit("Engineer")
    hq.production_progress = 3.0  # 50% of 6.0s
    renderer.render_bottom_hud([hq], gs.economies[Faction.PLAYER], (0, 0))

    # Shipyard test
    shipyard = next(b for b in gs.buildings if b.type_name == "Shipyard" and b.faction == Faction.PLAYER)
    shipyard.is_selected = True
    shipyard.queue_unit("Torpedo Boat")
    renderer.render_bottom_hud([shipyard], gs.economies[Faction.PLAYER], (0, 0))


def test_building_rally_point_and_x_marker():
    """Right-clicking valid position sets rally point and X marker; clicking building clears it."""
    gs = GameState()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    hq = next(b for b in gs.buildings if b.type_name == "HQ" and b.faction == Faction.PLAYER)
    gs.selected_entities = [hq]
    hq.is_selected = True

    # Initially no rally point
    assert hq.rally_point is None

    # Right click valid land coordinate (open grass tile at 8, 10)
    target_x = 8.0 * TILE_SIZE
    target_y = 10.0 * TILE_SIZE
    gs.issue_right_click_order(target_x, target_y)

    assert hq.rally_point == (target_x, target_y)

    # Render buildings with selected HQ -> draws X marker
    renderer.render_buildings(gs.buildings)

    # Right click the building itself -> reverts to default (None)
    bld_center_x, bld_center_y = hq.x, hq.y
    gs.issue_right_click_order(bld_center_x, bld_center_y)
    assert hq.rally_point is None


def test_new_units_move_to_rally_point():
    """Units created at a building with a rally point automatically move toward it."""
    gs = GameState()
    barracks = next(b for b in gs.buildings if b.type_name == "Barracks" and b.faction == Faction.PLAYER)

    # Set rally point for barracks (open land at 12, 26)
    rally_x = 12.0 * TILE_SIZE
    rally_y = 26.0 * TILE_SIZE
    barracks.rally_point = (rally_x, rally_y)
    barracks.queue_unit("Foot Soldier")

    # Complete production
    barracks.production_progress = UNIT_TYPES["Foot Soldier"]["build_time"]
    initial_unit_count = len(gs.units)
    gs.update(0.1)

    assert len(gs.units) == initial_unit_count + 1
    new_unit = gs.units[-1]
    assert new_unit.type_name == "Foot Soldier"
    assert new_unit.state == UnitState.MOVING
    assert len(new_unit.path) > 0


def test_save_modal_interactions_and_typing(tmp_path):
    """Tests save dialog navigation, typing input, and overwriting existing saves."""
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)
    save_dir = str(tmp_path / "ui_saves")

    # Pause game and click Save button
    gs.is_paused = True
    renderer.render_pause_modal((0, 0), show_save=False)
    save_btn = next(b for b in renderer.pause_buttons if b["action"] == "save")
    click_save = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=save_btn["rect"].center)
    handler.handle_events([click_save], gs, renderer)
    assert handler.show_save_modal is True

    # Type a new save name: backspace old text, type "alpha"
    handler.save_name_input = "test"
    bs_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE)
    handler.handle_events([bs_event], gs, renderer)
    assert handler.save_name_input == "tes"

    char_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t, unicode="t")
    handler.handle_events([char_event], gs, renderer)
    assert handler.save_name_input == "test"

    # Save via method
    gs.save_game("test_slot_1", save_dir=save_dir)
    gs.save_game("test_slot_2", save_dir=save_dir)

    # Render save modal with existing saves
    existing = gs.list_saves(save_dir=save_dir)
    renderer.render_pause_modal((0, 0), show_save=True, save_name_input="new_slot", existing_saves=existing)

    # Click existing save item to overwrite
    target_item = next(item for item in renderer.save_items if item["save_name"] == "test_slot_1")
    click_item = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=target_item["rect"].center)
    handler.handle_events([click_item], gs, renderer)
    assert handler.save_name_input == "test_slot_1"

    # ESC in save modal goes back to pause menu
    esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    handler.handle_events([esc_event], gs, renderer)
    assert handler.show_save_modal is False
    assert gs.is_paused is True


def test_minimap_click_pans_camera():
    """Clicking on the minimap centers the camera around the clicked world area."""
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    renderer.render_minimap(gs.map, gs.buildings, gs.units)
    assert renderer.camera.x == 0.0

    # Click near the right side of the minimap (e.g. 80% across)
    mm_click_x = renderer.minimap_rect.left + int(renderer.minimap_rect.width * 0.8)
    mm_click_y = renderer.minimap_rect.top + int(renderer.minimap_rect.height * 0.5)
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(mm_click_x, mm_click_y))
    handler.handle_events([click_event], gs, renderer)

    assert renderer.camera.x > 0.0


def test_shipyard_naval_rally_point():
    """Shipyard rally point must be in water and newly built ships navigate to it."""
    gs = GameState()
    shipyard = next(b for b in gs.buildings if b.type_name == "Shipyard" and b.faction == Faction.PLAYER)
    gs.selected_entities = [shipyard]
    shipyard.is_selected = True

    # Try setting rally point on deep land (e.g. 5, 5) -> should be rejected because shipyard produces sea units
    land_x, land_y = 5.0 * TILE_SIZE, 5.0 * TILE_SIZE
    gs.issue_right_click_order(land_x, land_y)
    assert shipyard.rally_point is None

    # Set rally point on water (e.g. tile 26, 20 is central water channel)
    water_x, water_y = 26.0 * TILE_SIZE, 20.0 * TILE_SIZE
    assert gs.map.tiles[20][26] == TerrainType.WATER
    gs.issue_right_click_order(water_x, water_y)
    assert shipyard.rally_point == (water_x, water_y)

    # Queue torpedo boat and complete production
    shipyard.queue_unit("Torpedo Boat")
    shipyard.production_progress = UNIT_TYPES["Torpedo Boat"]["build_time"]
    initial_count = len(gs.units)
    gs.update(0.1)

    assert len(gs.units) == initial_count + 1
    new_boat = gs.units[-1]
    assert new_boat.type_name == "Torpedo Boat"
    assert new_boat.domain == Domain.SEA
    assert new_boat.state == UnitState.MOVING
    assert len(new_boat.path) > 0



def test_non_producing_building_right_click_does_not_crash():
    """Right-clicking the ground when a non-producing building (Farm, Factory, Refinery) is selected does not crash."""
    gs = GameState()
    farm = next(b for b in gs.buildings if b.type_name == "Farm" and b.faction == Faction.PLAYER)
    gs.selected_entities = [farm]
    farm.is_selected = True

    # Right click the ground
    ground_x = 10.0 * TILE_SIZE
    ground_y = 10.0 * TILE_SIZE
    gs.issue_right_click_order(ground_x, ground_y)

    assert farm.rally_point is None



def test_load_modal_interactions(tmp_path):
    """Tests opening Load modal, selecting a save file, and loading progress."""
    save_dir = str(tmp_path / "load_test_saves")
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    # 1. Create a saved game with unique resources
    gs.economies[Faction.PLAYER].resources[ResourceType.FOOD] = 1234.0
    gs.save_game("test_progress", save_dir=save_dir)
    gs.save_game("test_progress")

    # 2. Reset game state
    gs.load_map("Divided Sea")
    assert gs.economies[Faction.PLAYER].resources[ResourceType.FOOD] != 1234.0

    # 3. Pause and open pause menu
    gs.is_paused = True
    renderer.render_pause_modal((0, 0), show_save=False, show_load=False)

    # 4. Click 'Load a saved game' button
    load_btn = next(b for b in renderer.pause_buttons if b["action"] == "load")
    click_load = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=load_btn["rect"].center)
    handler.handle_events([click_load], gs, renderer)
    assert handler.show_load_modal is True

    # 5. Render load modal with available saves
    existing = gs.list_saves(save_dir=save_dir)
    handler.existing_saves = existing
    handler.selected_load_name = "test_progress"
    renderer.render_pause_modal(
        (0, 0),
        show_load=True,
        selected_load_name=handler.selected_load_name,
        existing_saves=existing
    )

    # 6. Click load item
    load_item = next(item for item in renderer.load_items if item["save_name"] == "test_progress")
    click_item = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=load_item["rect"].center)
    handler.handle_events([click_item], gs, renderer)
    assert handler.selected_load_name == "test_progress"

    # 7. Confirm load
    confirm_btn = next(b for b in renderer.load_buttons if b["action"] == "confirm_load")
    click_confirm = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=confirm_btn["rect"].center)
    handler.handle_events([click_confirm], gs, renderer)

    assert handler.show_load_modal is False
    assert gs.is_paused is False
    assert gs.economies[Faction.PLAYER].resources[ResourceType.FOOD] == 1234.0

