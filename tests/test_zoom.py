"""
Unit Tests for Camera Zoom and Viewport Scaling System.
"""
import os
import pygame
import pytest
from src.config import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.renderer import Camera, Renderer
from src.game_state import GameState
from src.input_handler import InputHandler

@pytest.fixture(autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def test_camera_zoom_initial_values():
    cam = Camera(1280, 768)
    assert cam.zoom == 1.0
    assert cam.min_zoom == 0.5
    assert cam.max_zoom == 2.5


def test_camera_world_screen_round_trip():
    cam = Camera(1280, 768)
    cam.move(100.0, 50.0)

    for zoom in (0.5, 0.8, 1.0, 1.5, 2.0, 2.5):
        cam.zoom = zoom
        for wx, wy in [(0.0, 0.0), (320.0, 240.0), (1024.0, 768.0)]:
            sx, sy = cam.world_to_screen(wx, wy)
            r_wx, r_wy = cam.screen_to_world(sx, sy)
            # Int rounding on screen coordinates introduces at most 1 pixel / zoom error
            assert abs(r_wx - wx) <= 2.0 / zoom
            assert abs(r_wy - wy) <= 2.0 / zoom


def test_camera_zoom_at_anchors_cursor():
    cam = Camera(1280, 768)
    cam.move(200.0, 200.0)

    cursor_sx, cursor_sy = 640, 384
    # World point under cursor before zoom
    anchor_wx, anchor_wy = cam.screen_to_world(cursor_sx, cursor_sy)

    # Zoom in
    cam.zoom_at(cursor_sx, cursor_sy, 1.5)
    assert cam.zoom == 1.5

    # World point under cursor after zoom should be the same
    new_anchor_wx, new_anchor_wy = cam.screen_to_world(cursor_sx, cursor_sy)
    assert abs(new_anchor_wx - anchor_wx) < 1.0
    assert abs(new_anchor_wy - anchor_wy) < 1.0


def test_camera_bounds_adjust_with_zoom():
    cam = Camera(1280, 768)
    cam.update_bounds(1280, 768)
    base_max_x = cam.max_x
    base_max_y = cam.max_y

    # Zooming in means visible world is smaller, so max pan is greater
    cam.zoom = 2.0
    cam.update_bounds(1280, 768)
    assert cam.max_x > base_max_x
    assert cam.max_y > base_max_y

    # Zooming out means visible world is larger, so max pan is smaller
    cam.zoom = 0.5
    cam.update_bounds(1280, 768)
    assert cam.max_x < base_max_x
    assert cam.max_y < base_max_y


def test_mousewheel_event_triggers_zoom():
    gs = GameState()
    handler = InputHandler()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    assert renderer.camera.zoom == 1.0

    # Scroll up (zoom in) in world viewport (y=300)
    wheel_up = pygame.event.Event(pygame.MOUSEWHEEL, y=1, pos=(640, 300))
    handler.handle_events([wheel_up], gs, renderer)
    assert renderer.camera.zoom > 1.0

    # Scroll down (zoom out)
    cur_zoom = renderer.camera.zoom
    wheel_down = pygame.event.Event(pygame.MOUSEWHEEL, y=-1, pos=(640, 300))
    handler.handle_events([wheel_down], gs, renderer)
    assert renderer.camera.zoom < cur_zoom


def test_minimap_viewport_reflects_zoom():
    gs = GameState()
    screen = pygame.Surface((1280, 768))
    renderer = Renderer(screen)

    renderer.camera.zoom = 1.0
    renderer.render_minimap(gs.map, gs.buildings, gs.units)
    vw_normal = renderer.minimap_viewport_rect.width

    renderer.camera.zoom = 2.0
    renderer.render_minimap(gs.map, gs.buildings, gs.units)
    vw_zoomed_in = renderer.minimap_viewport_rect.width

    assert vw_zoomed_in < vw_normal
