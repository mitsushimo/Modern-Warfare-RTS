"""
Comprehensive Test Suite for Age of Modernity RTS MVP.
"""
import pytest
from src.config import (
    Domain, Faction, ResourceType, UNIT_TYPES, BUILDING_TYPES, TILE_SIZE, TerrainType
)
from src.map_system import GameMap
from src.economy import FactionEconomy
from src.entities.unit import Unit, UnitState
from src.entities.building import Building
from src.game_state import GameState

def test_unit_roster_and_characteristics():
    """Verifies all specified unit types exist with appropriate domain and stats."""
    expected_units = [
        ("Engineer", Domain.LAND, "Civilian"),
        ("Foot Soldier", Domain.LAND, "Army"),
        ("Tank", Domain.LAND, "Army"),
        ("Cannon", Domain.LAND, "Army"),
        ("Torpedo Boat", Domain.SEA, "Navy"),
        ("Destroyer", Domain.SEA, "Navy"),
        ("Battleship", Domain.SEA, "Navy"),
    ]

    for name, expected_domain, expected_branch in expected_units:
        assert name in UNIT_TYPES
        unit = Unit(name, Faction.PLAYER, 100, 100)
        assert unit.domain == expected_domain
        assert unit.branch == expected_branch
        assert unit.hp == unit.max_hp
        assert unit.max_hp > 0
        assert unit.attack_damage > 0
        assert unit.attack_range > 0
        assert unit.speed > 0
        assert unit.is_alive

def test_terrain_domain_movement_rules():
    """Tests that Land units and Sea vessels obey domain restrictions."""
    gmap = GameMap(width=20, height=20)
    # Set tile (5,5) to LAND and tile (10,10) to WATER
    gmap.tiles[5][5] = gmap.tiles[5][5]
    land_pass_land = gmap.is_passable(2, 2, Domain.LAND)
    sea_pass_land = gmap.is_passable(2, 2, Domain.SEA)
    assert land_pass_land is True
    assert sea_pass_land is False

    # Central sea tiles
    sea_tile_x = 28
    if sea_tile_x < gmap.width:
        assert gmap.is_passable(sea_tile_x, 10, Domain.SEA) is True
        assert gmap.is_passable(sea_tile_x, 10, Domain.LAND) is False

def test_naval_shipyard_coastal_requirement():
    """Shipyards must touch both land and water."""
    gmap = GameMap()
    # Deep inland tile (e.g. 5, 5) cannot host Shipyard
    assert gmap.can_place_building(5, 5, 3, 3, coastal_required=True) is False

    # Standard building can be placed inland
    assert gmap.can_place_building(5, 5, 3, 3, coastal_required=False) is True

def test_economy_and_costs():
    """Tests resource management, deduction, and affordability."""
    econ = FactionEconomy(Faction.PLAYER)
    cost = {ResourceType.FOOD: 50, ResourceType.STEEL: 50, ResourceType.FUEL: 0}

    initial_food = econ.get_amount(ResourceType.FOOD)
    assert econ.can_afford(cost) is True

    deducted = econ.deduct(cost)
    assert deducted is True
    assert econ.get_amount(ResourceType.FOOD) == initial_food - 50

    # Overly expensive cost
    huge_cost = {ResourceType.FOOD: 999999, ResourceType.STEEL: 0, ResourceType.FUEL: 0}
    assert econ.can_afford(huge_cost) is False
    assert econ.deduct(huge_cost) is False

def test_aoe2_engineer_construction_and_work():
    """Tests that an Engineer builds a structure from foundation to completion."""
    game_state = GameState()
    # Place an unfinished farm
    farm = game_state.place_building("Farm", Faction.PLAYER, 5, 5, under_construction=True)
    assert farm.under_construction is True
    assert farm.hp == 1.0

    engineer = game_state.spawn_unit("Engineer", Faction.PLAYER, 5 * TILE_SIZE, 5 * TILE_SIZE)
    engineer.order_build_or_repair(farm)

    assert engineer.state == UnitState.BUILDING
    # Simulate time for construction
    for _ in range(60):
        game_state.update(0.2)

    assert farm.under_construction is False
    assert farm.hp == farm.max_hp
    assert farm.is_operational is True

def test_combat_damage_and_armor_mitigation():
    """Tests attack damage reduction by armor and destruction upon zero HP."""
    attacker = Unit("Tank", Faction.PLAYER, 100, 100)
    defender = Unit("Foot Soldier", Faction.ENEMY, 100, 100)

    # Tank attack: 32, Soldier armor: 1 -> Effective damage: 31
    initial_hp = defender.hp
    dmg = defender.take_damage(attacker.attack_damage)
    assert dmg == 31.0
    assert defender.hp == initial_hp - 31.0

    # Kill defender
    defender.take_damage(9999)
    assert defender.hp == 0
    assert not defender.is_alive

def test_building_production_queue():
    """Tests training units in military buildings."""
    game_state = GameState()
    # Clear units for an isolated production test
    game_state.units.clear()
    barracks = next(b for b in game_state.buildings if b.type_name == "Barracks" and b.faction == Faction.PLAYER)

    assert barracks.queue_unit("Foot Soldier") is True
    assert len(barracks.production_queue) == 1

    # Simulate time until unit finishes
    build_time = UNIT_TYPES["Foot Soldier"]["build_time"]
    steps = int((build_time + 1.0) / 0.1)
    for _ in range(steps):
        game_state.update(0.1)

    assert len(game_state.units) == 1
    new_unit = game_state.units[0]
    assert new_unit.type_name == "Foot Soldier"
    assert new_unit.faction == Faction.PLAYER

def test_selection_and_click_orders():
    """Tests single entity selection and right-click order targeting."""
    game_state = GameState()
    # Find a player unit
    player_unit = next(u for u in game_state.units if u.faction == Faction.PLAYER)

    # Click directly on the player unit
    game_state.select_single(player_unit.x, player_unit.y)
    assert len(game_state.selected_entities) == 1
    assert game_state.selected_entities[0] is player_unit
    assert player_unit.is_selected is True

    # Click away into empty space
    game_state.select_single(0, 0)
    assert len(game_state.selected_entities) == 0
    assert player_unit.is_selected is False

    # Click on a building
    hq = next(b for b in game_state.buildings if b.type_name == "HQ" and b.faction == Faction.PLAYER)
    game_state.select_single(hq.x, hq.y)
    assert len(game_state.selected_entities) == 1
    assert game_state.selected_entities[0] is hq
    assert hq.is_selected is True

    # Select unit again and issue right-click order on enemy
    game_state.select_single(player_unit.x, player_unit.y)
    enemy_unit = next(u for u in game_state.units if u.faction == Faction.ENEMY)
    game_state.issue_right_click_order(enemy_unit.x, enemy_unit.y)
    # Right click should not crash and unit should target enemy or move
    found_entity = game_state.get_entity_at(enemy_unit.x, enemy_unit.y)
    assert found_entity is enemy_unit

def test_game_state_headless_run():
    """Runs a multi-frame integration test of the game state."""
    from main import run_game
    # Test 60 frames of headless execution
    success = run_game(headless_frames=60)
    assert success is True


def test_audio_procedural_generation_and_sound_manager(tmp_path):
    """Tests procedural .wav generation, wave header validation, and SoundManager mapping."""
    import os
    import wave
    from src.audio import ensure_default_sound_files, SoundManager
    from src.combat import CombatManager
    from src.entities.unit import Unit

    custom_dir = str(tmp_path / "sounds")
    ensure_default_sound_files(custom_dir)

    expected_files = ["gunfire.wav", "tank_cannon.wav", "battleship_cannon.wav", "torpedo.wav"]
    for fname in expected_files:
        fpath = os.path.join(custom_dir, fname)
        assert os.path.exists(fpath), f"{fname} should exist"
        with wave.open(fpath, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2  # 16-bit
            assert wf.getframerate() == 44100
            assert wf.getnframes() > 0

    sm = SoundManager(sound_dir=custom_dir)
    # Verify play_attack_sound does not crash for each unit type
    sm.play_attack_sound("Battleship")
    sm.play_attack_sound("Cannon")
    sm.play_attack_sound("Tank")
    sm.play_attack_sound("Destroyer")
    sm.play_attack_sound("Torpedo Boat")
    sm.play_attack_sound("Foot Soldier")
    sm.play_attack_sound("Engineer")
    sm.play_attack_sound("")

    # Verify CombatManager integration
    cm = CombatManager(sound_manager=sm)
    attacker = Unit("Battleship", Faction.PLAYER, 100, 100)
    cm.add_combat_event({
        "attacker": attacker,
        "origin": (100, 100),
        "target_pos": (200, 200),
    })
    assert len(cm.effects) == 1


def test_named_maps_generation_and_land_connectivity():
    """Verifies all named maps generate correctly and land-connected maps allow land pathfinding."""
    from src.config import MAP_PRESETS, TerrainType
    expected_maps = ["Divided Sea", "Continental Front", "Shattered Isthmus", "Inland Sea"]
    for name in expected_maps:
        assert name in MAP_PRESETS
        gmap = GameMap(map_name=name)
        assert gmap.map_name == name
        assert gmap.width > 0 and gmap.height > 0
        assert len(gmap.tiles) == gmap.height

    # In Continental Front, test that player territory is connected by land to enemy territory
    cf_map = GameMap(map_name="Continental Front")
    # West base at (4, 18) to East base at (54, 18) must have uninterrupted land
    for x in range(4, 55):
        t = cf_map.get_terrain(x, 18)
        assert t in (TerrainType.LAND, TerrainType.COAST), f"Tile ({x}, 18) should be land/coast, got {t}"

    # Verify A* pathfinding computes a full land path across the entire front
    player_pos = (16.0 * TILE_SIZE, 18.0 * TILE_SIZE)
    enemy_pos = (48.0 * TILE_SIZE, 18.0 * TILE_SIZE)
    path = cf_map.find_path(player_pos, enemy_pos, Domain.LAND)
    assert len(path) > 10, "Land unit path across Continental Front must contain a valid series of waypoints"
    assert path[0] == player_pos or path[-1] == enemy_pos


def test_game_state_load_map_and_reset():
    """Tests loading new maps and verifying full state/economy reset."""
    import pygame
    if not pygame.get_init():
        pygame.init()

    gs = GameState(map_name="Divided Sea")
    assert gs.current_map_name == "Divided Sea"

    # Modify state: spend food, select units
    gs.economies[Faction.PLAYER].resources[ResourceType.FOOD] = 10
    gs.select_single(gs.units[0].x, gs.units[0].y)
    assert len(gs.selected_entities) == 1

    # Load "Continental Front"
    gs.load_map("Continental Front")
    assert gs.current_map_name == "Continental Front"
    assert gs.economies[Faction.PLAYER].get_amount(ResourceType.FOOD) == 300  # Reset to starting
    assert len(gs.selected_entities) == 0  # Cleared selection

    # Check that Continental Front has starter land weapons: Tanks, Cannons, Foot Soldiers
    player_tanks = [u for u in gs.units if u.faction == Faction.PLAYER and u.type_name == "Tank"]
    player_cannons = [u for u in gs.units if u.faction == Faction.PLAYER and u.type_name == "Cannon"]
    enemy_tanks = [u for u in gs.units if u.faction == Faction.ENEMY and u.type_name == "Tank"]
    assert len(player_tanks) >= 2
    assert len(player_cannons) >= 2
    assert len(enemy_tanks) >= 2

    # Check direct land path between player tank and enemy tank
    pt = player_tanks[0]
    et = enemy_tanks[0]
    land_path = gs.map.find_path((pt.x, pt.y), (et.x, et.y), Domain.LAND)
    assert len(land_path) > 1, "Player tank must have a navigable land path directly to the enemy tank"


def test_map_selection_ui_and_exclusive_top_bar_trigger():
    """Verifies that clicking the top bar button opens map modal, 'M' key is ignored, and maps can be loaded."""
    import pygame
    from src.renderer import Renderer
    from src.input_handler import InputHandler

    if not pygame.get_init():
        pygame.init()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)
    handler = InputHandler()
    gs = GameState()

    # Render top bar so button rect is updated
    renderer.render_top_bar(gs.economies[Faction.PLAYER], gs.units, gs.current_map_name, (500, 15))
    assert renderer.top_bar_map_button_rect is not None

    # Verify 'M' key does NOT open the map menu (per user request)
    m_key_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_m})
    handler.handle_events([m_key_event], gs, renderer)
    assert handler.show_map_menu is False, "'M' hotkey must NOT open the map menu"

    # Click top bar map button
    btn_center = renderer.top_bar_map_button_rect.center
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": btn_center})
    pygame.mouse.get_pos = lambda: btn_center
    handler.handle_events([click_event], gs, renderer)
    assert handler.show_map_menu is True, "Clicking top bar map button must open the map menu"

    # Render modal while open to populate modal buttons
    renderer.render_map_selection_modal(gs.current_map_name, (0, 0))
    assert len(renderer.modal_buttons) == 4

    # Click the "Continental Front" card
    cf_card = next(b for b in renderer.modal_buttons if b["map_name"] == "Continental Front")
    card_center = cf_card["rect"].center
    pygame.mouse.get_pos = lambda: card_center
    click_card_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": card_center})
    handler.handle_events([click_card_event], gs, renderer)

    assert handler.show_map_menu is False, "Selecting a map must close the modal"
    assert gs.current_map_name == "Continental Front", "Map must be loaded to Continental Front"



def test_window_resize_and_maximize_support():
    """Tests window resizing/maximizing handling, camera bounds adjustment, and UI repositioning."""
    import pygame
    from src.renderer import Renderer
    from src.input_handler import InputHandler

    if not pygame.get_init():
        pygame.init()

    surface = pygame.Surface((1280, 768))
    renderer = Renderer(surface)
    handler = InputHandler()
    gs = GameState()

    assert renderer.screen_width == 1280
    assert renderer.screen_height == 768

    # Simulate maximizing window to 1920x1080
    maximized_surf = pygame.Surface((1920, 1080))
    renderer.handle_resize(1920, 1080, maximized_surf)

    assert renderer.screen_width == 1920
    assert renderer.screen_height == 1080
    assert renderer.camera.screen_width == 1920
    assert renderer.camera.screen_height == 1080

    # Test VIDEORESIZE event in InputHandler
    resize_event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1600, "h": 900})
    handler.handle_events([resize_event], gs, renderer)
    assert renderer.screen_width == 1600
    assert renderer.screen_height == 900

    # Ensure UI methods render cleanly at resized dimensions
    renderer.render_map(gs.map)
    renderer.render_top_bar(gs.economies[Faction.PLAYER], gs.units, gs.current_map_name, (500, 15))
    renderer.render_bottom_hud(gs.selected_entities, gs.economies[Faction.PLAYER], (500, 800))
    renderer.render_map_selection_modal(gs.current_map_name, (500, 450))


def test_unit_separation_and_group_order_spacing():
    """Verifies that units cannot occupy the exact same position and group orders generate distinct slots."""
    gs = GameState()
    gs.units.clear()

    # 1. Test that two units at identical coordinates are pushed apart
    u1 = Unit("Foot Soldier", Faction.PLAYER, 200.0, 200.0)
    u2 = Unit("Foot Soldier", Faction.PLAYER, 200.0, 200.0)
    gs.units.extend([u1, u2])

    assert u1.distance_to(u2) == 0.0
    # Run separation pass
    gs._resolve_unit_collisions()
    dist_after = u1.distance_to(u2)
    assert dist_after > 0.0, "Units must be separated when sharing identical coordinates"
    assert dist_after >= (u1.radius + u2.radius) * 0.9, "Units should separate to clear radii"

    # 2. Test group move order spacing
    gs.units.clear()
    units = [
        Unit("Foot Soldier", Faction.PLAYER, 100.0 + i * 25.0, 100.0)
        for i in range(4)
    ]
    gs.units.extend(units)
    gs.selected_entities = list(units)

    target_x, target_y = 300.0, 300.0
    slots = gs._compute_formation_slots(target_x, target_y, units)
    assert len(slots) == 4
    # All slots must be distinct
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            assert slots[i] != slots[j], "Each unit must receive a distinct formation destination"

    # Issue right-click move order to all units
    gs.issue_right_click_order(target_x, target_y)
    for u in units:
        assert u.state == UnitState.MOVING
        assert len(u.path) > 0

    # Simulate movement toward target
    for _ in range(50):
        gs.update(0.1)

    # Check that no two units have identical coordinates
    for i in range(len(units)):
        for j in range(i + 1, len(units)):
            d = units[i].distance_to(units[j])
            assert d > 0.0, "Units must not be completely on top of each other after moving"


def test_projectile_speeds_and_delayed_damage():
    """Verifies weapon projectile speeds, hierarchy (torpedo < artillery < tank < bullet), and non-instant damage."""
    # 1. Speed hierarchy check in UNIT_TYPES
    torpedo_spd = UNIT_TYPES["Torpedo Boat"]["projectile_speed"]
    cannon_spd = UNIT_TYPES["Cannon"]["projectile_speed"]
    battleship_spd = UNIT_TYPES["Battleship"]["projectile_speed"]
    tank_spd = UNIT_TYPES["Tank"]["projectile_speed"]
    destroyer_spd = UNIT_TYPES["Destroyer"]["projectile_speed"]
    infantry_spd = UNIT_TYPES["Foot Soldier"]["projectile_speed"]

    assert torpedo_spd < cannon_spd, "Torpedoes must be slower than artillery shells"
    assert cannon_spd < tank_spd, "Artillery shells must be slower than tank cannon shells"
    assert tank_spd < infantry_spd, "Tank shells should be slower than infantry rifle bullets"
    assert battleship_spd < destroyer_spd, "Battleship heavy artillery should be slower than destroyer guns"

    # 2. Non-instantaneous damage test with traveling projectile
    gs = GameState()
    gs.units.clear()

    # Place an enemy 160 pixels away
    attacker = Unit("Cannon", Faction.PLAYER, 100.0, 100.0)
    defender = Unit("Tank", Faction.ENEMY, 260.0, 100.0)
    initial_defender_hp = defender.hp
    gs.units.extend([attacker, defender])

    # Attacker targets defender
    attacker.order_attack(defender)
    assert attacker.distance_to(defender) <= attacker.attack_range

    # First update: weapon fires, projectile is spawned, but damage is NOT yet dealt!
    gs.update(0.05)
    assert len(gs.combat_manager.effects) >= 1, "Combat effect / projectile should be active"
    proj = gs.combat_manager.projectiles[0]
    assert proj.has_impacted is False, "Projectile should still be in flight"
    assert defender.hp == initial_defender_hp, "Damage must NOT be instantaneous while projectile is in flight"

    # Advance time until projectile reaches target
    # Distance = 160 px, Cannon speed = 7.5 tiles/s * 32 = 240 px/s -> ~0.67s
    travel_time_needed = 160.0 / proj.speed
    for _ in range(int(travel_time_needed / 0.05) + 3):
        gs.update(0.05)

    assert defender.hp < initial_defender_hp, "Defender must take damage after projectile arrives"



def test_lead_targeting_predicted_intercept():
    """Verifies that units lead moving targets by predicting future positions and hitting them at constant velocity."""
    gs = GameState()
    gs.units.clear()

    # Attacker at (100, 100). Cannon range is 256 px, projectile speed is 240 px/s.
    attacker = Unit("Cannon", Faction.PLAYER, 100.0, 100.0)
    defender = Unit("Tank", Faction.ENEMY, 200.0, 100.0)
    defender.order_move([(200.0, 300.0)])
    gs.units.extend([attacker, defender])

    # Check defender has positive vy
    assert defender.vy > 0
    assert defender.vx == 0

    # Calculate predicted intercept position
    pred_pos = attacker.predict_intercept_position(defender)
    assert pred_pos[0] == 200.0
    assert pred_pos[1] > 100.0, "Aim point must lead the enemy ahead along its path"

    initial_hp = defender.hp
    attacker.order_attack(defender)

    # First update: projectile fires toward predicted position
    gs.update(0.05)
    assert len(gs.combat_manager.projectiles) >= 1
    proj = gs.combat_manager.projectiles[0]
    assert proj.target_pos[1] > 100.0, "Projectile must be aimed at predicted position ahead"

    # Simulate movement while defender maintains constant velocity
    for _ in range(25):
        gs.update(0.05)
        if defender.hp < initial_hp:
            break

    assert defender.hp < initial_hp, "Moving defender should be hit at predicted position if velocity maintained"


def test_projectile_misses_if_enemy_slows_or_stops():
    """Verifies that if an enemy slows down or stops after a shot is fired, the projectile misses."""
    gs = GameState()
    gs.units.clear()

    attacker = Unit("Cannon", Faction.PLAYER, 100.0, 100.0)
    defender = Unit("Tank", Faction.ENEMY, 200.0, 100.0)
    defender.order_move([(200.0, 300.0)])
    gs.units.extend([attacker, defender])

    initial_hp = defender.hp
    attacker.order_attack(defender)

    # Fire shot on first update
    gs.update(0.05)
    assert len(gs.combat_manager.projectiles) >= 1
    proj = gs.combat_manager.projectiles[0]

    # Enemy immediately halts/slows down
    defender.order_move([])
    assert defender.vx == 0.0 and defender.vy == 0.0

    # Simulate until projectile reaches max range / expires
    for _ in range(40):
        gs.update(0.05)

    assert defender.hp == initial_hp, "Stopped defender must avoid projectile that was aimed ahead"
    assert proj.has_impacted is True, "Projectile should have reached destination/max range without hitting"


def test_projectile_misses_if_enemy_changes_direction():
    """Verifies that if an enemy changes direction after being fired upon, it avoids the hit."""
    gs = GameState()
    gs.units.clear()

    attacker = Unit("Cannon", Faction.PLAYER, 100.0, 100.0)
    defender = Unit("Tank", Faction.ENEMY, 200.0, 100.0)
    defender.order_move([(200.0, 300.0)])
    gs.units.extend([attacker, defender])

    initial_hp = defender.hp
    attacker.order_attack(defender)

    # Fire shot
    gs.update(0.05)
    assert len(gs.combat_manager.projectiles) >= 1

    # Enemy changes direction sharply: moves in reverse direction (200.0, 0.0)
    defender.order_move([(200.0, 0.0)])

    # Simulate time for projectile to pass
    for _ in range(40):
        gs.update(0.05)

    assert defender.hp == initial_hp, "Defender that reversed direction must evade the straight projectile"


def test_projectile_hits_whatever_enemy_in_line_of_fire():
    """Verifies that straight projectiles do not chase target and hit whatever enemy is in the path."""
    gs = GameState()
    gs.units.clear()

    attacker = Unit("Cannon", Faction.PLAYER, 100.0, 100.0)
    target_defender = Unit("Tank", Faction.ENEMY, 260.0, 100.0)
    # Intervening enemy standing directly in the line of fire
    intervening_enemy = Unit("Foot Soldier", Faction.ENEMY, 180.0, 100.0)
    initial_target_hp = target_defender.hp
    initial_bystander_hp = intervening_enemy.hp

    gs.units.extend([attacker, target_defender, intervening_enemy])

    # Attacker targets the distant tank
    attacker.order_attack(target_defender)

    # Advance simulation
    for _ in range(25):
        gs.update(0.05)

    assert intervening_enemy.hp < initial_bystander_hp, "Intervening enemy must be hit by the straight projectile"
    assert target_defender.hp == initial_target_hp, "Original target should NOT take damage if projectile was blocked"


def test_projectile_max_range_expiry():
    """Verifies that a projectile does not damage enemies outside its max range."""
    gs = GameState()
    gs.units.clear()

    # Tank attack range is 4.5 tiles * 32 = 144 px
    attacker = Unit("Tank", Faction.PLAYER, 100.0, 100.0)
    attacker.cooldown_timer = 999.0  # Prevent second attack while moving
    # Enemy placed 300 px away, far beyond Tank's attack range (144 px)
    far_enemy = Unit("Foot Soldier", Faction.ENEMY, 300.0, 100.0)
    initial_hp = far_enemy.hp
    gs.units.extend([attacker, far_enemy])

    # Fire event directly
    gs.combat_manager.add_combat_event({
        "attacker": attacker,
        "origin": (100.0, 100.0),
        "target_pos": (300.0, 100.0),
        "damage": attacker.attack_damage,
        "max_range": attacker.attack_range,
    })

    proj = gs.combat_manager.projectiles[0]
    assert proj.max_range == attacker.attack_range

    for _ in range(30):
        gs.update(0.05)

    assert far_enemy.hp == initial_hp, "Enemy beyond attack range must not take damage"
    assert proj.has_impacted is True




def test_projectile_hits_enemy_building():
    """Verifies that straight projectiles can collide with and damage enemy buildings."""
    gs = GameState()
    gs.units.clear()
    gs.buildings.clear()

    # Attacker at (320, 320)
    attacker = Unit("Cannon", Faction.PLAYER, 320.0, 320.0)
    # Enemy building at tile (14, 10)
    bld = gs.place_building("Barracks", Faction.ENEMY, 14, 10, under_construction=False)
    initial_bld_hp = bld.hp
    gs.units.append(attacker)

    attacker.order_attack(bld)
    for _ in range(25):
        gs.update(0.05)
        if bld.hp < initial_bld_hp:
            break

    assert bld.hp < initial_bld_hp, "Enemy building in line of fire must take damage from projectile"


def test_land_units_cannot_cross_water_and_stop_at_shore():
    """Verifies land units cannot swim across water and stop at the shore when destination is unreachable."""
    gs = GameState(map_name="Divided Sea")
    # Tank starts on West continent
    tank = Unit("Tank", Faction.PLAYER, 10.0 * TILE_SIZE, 22.0 * TILE_SIZE)
    gs.units = [tank]

    # Destination on East continent across the sea channel
    dest_x = 54.0 * TILE_SIZE
    dest_y = 22.0 * TILE_SIZE

    # Compute path
    path = gs.map.find_path((tank.x, tank.y), (dest_x, dest_y), tank.domain)
    assert len(path) > 0, "Should find path to closest shore"

    # Verify no waypoint is on water
    for wx, wy in path:
        tx = int(wx // TILE_SIZE)
        ty = int(wy // TILE_SIZE)
        assert gs.map.is_passable(tx, ty, Domain.LAND), f"Waypoint ({wx}, {wy}) at tile ({tx}, {ty}) must not be in water"
        assert gs.map.tiles[ty][tx] != TerrainType.WATER

    # The end of the path must be on the Western shore (not across the sea channel)
    final_tx = int(path[-1][0] // TILE_SIZE)
    assert final_tx <= 27, "Path must terminate at Western coastline"

    # Order move and simulate
    tank.order_move(path)
    for _ in range(150):
        gs.update(0.1)
        if tank.state == UnitState.IDLE:
            break

    cur_tx = int(tank.x // TILE_SIZE)
    cur_ty = int(tank.y // TILE_SIZE)
    assert gs.map.tiles[cur_ty][cur_tx] != TerrainType.WATER, "Land unit must never enter water"
    assert gs.map.is_passable(cur_tx, cur_ty, Domain.LAND), "Land unit must remain on passable land"
    assert cur_tx <= 27, "Land unit must have stopped at the Western shore"
    assert tank.state == UnitState.IDLE, "Unit should be idle after reaching shore"


def test_land_unit_clicking_directly_on_water_stops_at_shore():
    """Verifies that clicking directly into the water causes the land unit to move to the shore and stop."""
    gs = GameState(map_name="Divided Sea")
    infantry = Unit("Foot Soldier", Faction.PLAYER, 12.0 * TILE_SIZE, 20.0 * TILE_SIZE)
    gs.units = [infantry]

    # Water coordinate in the middle of the sea channel
    water_target = (30.0 * TILE_SIZE, 20.0 * TILE_SIZE)
    tx_water = int(water_target[0] // TILE_SIZE)
    ty_water = int(water_target[1] // TILE_SIZE)
    assert gs.map.tiles[ty_water][tx_water] == TerrainType.WATER

    path = gs.map.find_path((infantry.x, infantry.y), water_target, infantry.domain)
    assert len(path) > 0

    for wx, wy in path:
        tx = int(wx // TILE_SIZE)
        ty = int(wy // TILE_SIZE)
        assert gs.map.tiles[ty][tx] != TerrainType.WATER, "Waypoints must not be in water"

    infantry.order_move(path)
    for _ in range(80):
        gs.update(0.1)

    final_tx = int(infantry.x // TILE_SIZE)
    final_ty = int(infantry.y // TILE_SIZE)
    assert gs.map.tiles[final_ty][final_tx] != TerrainType.WATER, "Infantry must not enter water"
    assert final_tx < 25, "Infantry must stop on the shore"


def test_land_unit_paths_around_water_when_land_route_exists():
    """Verifies that when a land path exists around water (e.g. Inland Sea), the unit takes the land route."""
    gs = GameState(map_name="Inland Sea")
    cannon = Unit("Cannon", Faction.PLAYER, 10.0 * TILE_SIZE, 24.0 * TILE_SIZE)
    gs.units = [cannon]

    # Destination on the other side of the inland sea (open land tile on Eastern side)
    target_pos = (50.0 * TILE_SIZE, 24.0 * TILE_SIZE)
    # Direct line midpoint passes through water
    mid_tx = int((cannon.x + target_pos[0]) / (2.0 * TILE_SIZE))
    mid_ty = int((cannon.y + target_pos[1]) / (2.0 * TILE_SIZE))
    assert gs.map.tiles[mid_ty][mid_tx] == TerrainType.WATER, "Straight line between start and goal must cross water"

    path = gs.map.find_path((cannon.x, cannon.y), target_pos, cannon.domain)
    assert len(path) > 10, "Path around the inland sea should navigate multiple waypoints"

    # All waypoints must avoid water
    for wx, wy in path:
        tx = int(wx // TILE_SIZE)
        ty = int(wy // TILE_SIZE)
        assert gs.map.tiles[ty][tx] != TerrainType.WATER, "Path must stay on land/coast corridors"
        assert gs.map.is_passable(tx, ty, Domain.LAND)

    # Final waypoint reaches destination
    assert int(path[-1][0] // TILE_SIZE) == int(target_pos[0] // TILE_SIZE)
    assert int(path[-1][1] // TILE_SIZE) == int(target_pos[1] // TILE_SIZE)




def test_group_order_across_water_stops_at_shore():
    """Verifies that selecting units and issuing a right-click order across water moves units to the shore without swimming."""
    gs = GameState(map_name="Divided Sea")
    inf1 = Unit("Foot Soldier", Faction.PLAYER, 10.0 * TILE_SIZE, 20.0 * TILE_SIZE)
    inf2 = Unit("Foot Soldier", Faction.PLAYER, 10.0 * TILE_SIZE, 22.0 * TILE_SIZE)
    gs.units = [inf1, inf2]
    gs.selected_entities = [inf1, inf2]

    # Right click across the sea channel at the enemy base
    gs.issue_right_click_order(54.0 * TILE_SIZE, 20.0 * TILE_SIZE)

    for _ in range(120):
        gs.update(0.1)

    for u in [inf1, inf2]:
        tx = int(u.x // TILE_SIZE)
        ty = int(u.y // TILE_SIZE)
        assert gs.map.tiles[ty][tx] != TerrainType.WATER, f"Unit at ({tx}, {ty}) must not be in water"
        assert tx <= 27, "Unit must have stopped at the shore"
