"""
Tests for Building Faction Flags and Engineer HQ Construction.
"""
import os
import pygame
import pytest

from src.config import (
    Faction, ResourceType, BUILDING_TYPES, UNIT_TYPES, TILE_SIZE,
    COLOR_PLAYER, COLOR_ENEMY, SCREEN_WIDTH, SCREEN_HEIGHT
)
from src.entities.building import Building
from src.entities.unit import Unit, UnitState
from src.game_state import GameState
from src.renderer import Renderer
from src.input_handler import InputHandler


def test_hq_cost_higher_than_all_other_buildings():
    """HQ cost should be higher than every other building currently available."""
    hq_cost = BUILDING_TYPES["HQ"]["cost"]
    hq_total = sum(hq_cost.values())

    for bld_name, data in BUILDING_TYPES.items():
        if bld_name == "HQ":
            continue
        other_cost = data["cost"]
        other_total = sum(other_cost.values())
        assert hq_total > other_total, (
            f"HQ total cost ({hq_total}) must be higher than {bld_name} total ({other_total})"
        )
        assert hq_cost[ResourceType.FOOD] >= other_cost[ResourceType.FOOD]
        assert hq_cost[ResourceType.STEEL] > other_cost[ResourceType.STEEL]
        assert hq_cost[ResourceType.FUEL] >= other_cost[ResourceType.FUEL]


def test_engineer_hud_includes_hq_build_button():
    """Selecting an Engineer should show HQ in the bottom HUD build row with hotkey 6."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()

    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer = Renderer(surf)
    game_state = GameState()

    engineer = next(u for u in game_state.units if u.type_name == "Engineer" and u.faction == Faction.PLAYER)
    game_state.clear_selection()
    engineer.is_selected = True
    game_state.selected_entities.append(engineer)

    renderer.render_bottom_hud(game_state.selected_entities, game_state.economies[Faction.PLAYER], (0, 0))

    btn_keys = [btn["key"] for btn in renderer.hud_buttons]
    assert "HQ" in btn_keys
    hq_btn = next(btn for btn in renderer.hud_buttons if btn["key"] == "HQ")
    assert hq_btn["hotkey"] == "6"
    assert hq_btn["action"] == "build"

    minimap_x = SCREEN_WIDTH - 160 - 12
    for btn in renderer.hud_buttons:
        assert btn["rect"].right < minimap_x, f"Button {btn['key']} overlaps minimap!"


def test_engineer_hotkey_6_starts_hq_placement_and_constructs():
    """Pressing hotkey 6 with Engineer selected should start HQ placement and allow construction."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()

    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer = Renderer(surf)
    game_state = GameState()
    handler = InputHandler()

    player_econ = game_state.economies[Faction.PLAYER]
    player_econ.add(ResourceType.FOOD, 100)
    player_econ.add(ResourceType.STEEL, 100)
    player_econ.add(ResourceType.FUEL, 100)

    engineer = next(u for u in game_state.units if u.type_name == "Engineer" and u.faction == Faction.PLAYER)
    game_state.clear_selection()
    engineer.is_selected = True
    game_state.selected_entities.append(engineer)

    renderer.render_bottom_hud(game_state.selected_entities, player_econ, (0, 0))

    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_6)
    handler.handle_events([event], game_state, renderer)

    assert game_state.placement_building_type == "HQ"

    initial_steel = player_econ.get_amount(ResourceType.STEEL)
    placed = game_state.confirm_building_placement(8, 14)
    assert placed is True
    assert game_state.placement_building_type is None
    assert player_econ.get_amount(ResourceType.STEEL) == initial_steel - BUILDING_TYPES["HQ"]["cost"][ResourceType.STEEL]

    new_hq = next(b for b in game_state.buildings if b.type_name == "HQ" and b.tile_x == 8 and b.tile_y == 14)
    assert new_hq.under_construction is True
    assert new_hq.faction == Faction.PLAYER

    for _ in range(150):
        game_state.update(0.2)

    assert new_hq.under_construction is False
    assert new_hq.is_operational is True
    assert new_hq.hp == new_hq.max_hp


def test_building_flag_rendering_player_and_enemy():
    """Verifies that building flags render in player (blue) and enemy (red) colors without error."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()

    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer = Renderer(surf)

    player_bld = Building("HQ", Faction.PLAYER, 10, 10)
    enemy_bld = Building("HQ", Faction.ENEMY, 25, 25)

    # Isometric mode (sprite building)
    renderer.camera.projection_mode = "isometric"
    renderer._render_building_isometric(player_bld, 1.0)
    renderer._render_building_isometric(enemy_bld, 1.0)

    # Top-down mode
    renderer.camera.projection_mode = "topdown"
    renderer._render_building_topdown(player_bld, 1.0)
    renderer._render_building_topdown(enemy_bld, 1.0)

    # Procedural isometric building
    farm_player = Building("Farm", Faction.PLAYER, 15, 15)
    farm_enemy = Building("Farm", Faction.ENEMY, 20, 20)
    renderer.camera.projection_mode = "isometric"
    renderer._render_building_isometric(farm_player, 1.0)
    renderer._render_building_isometric(farm_enemy, 1.0)
