"""
Age of Modernity - Main Entry Point.
"""
import sys
import os
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, Faction
from src.game_state import GameState
from src.renderer import Renderer
from src.input_handler import InputHandler

def run_game(headless_frames: int = 0):
    if headless_frames > 0:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()
    pygame.font.init()
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            pass
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Age of Modernity - Modern Warfare RTS")
    clock = pygame.time.Clock()

    game_state = GameState()
    renderer = Renderer(screen)
    input_handler = InputHandler()

    running = True
    frame_count = 0

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.1)  # Clamp against extreme delta spikes

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                renderer.handle_resize(event.w, event.h, screen)

        cur_w, cur_h = screen.get_size()
        if (cur_w, cur_h) != (renderer.screen_width, renderer.screen_height):
            renderer.handle_resize(cur_w, cur_h, screen)

        if not input_handler.handle_events(events, game_state, renderer):
            running = False
            break

        input_handler.update_camera_controls(renderer, dt, game_state)
        game_state.update(dt)

        mouse_pos = pygame.mouse.get_pos()

        # Rendering pipeline
        renderer.render_map(game_state.map)
        renderer.render_entities(game_state.buildings, game_state.units)
        renderer.render_combat_effects(game_state.combat_manager.effects)

        # UI Overlays
        renderer.render_top_bar(
            game_state.economies[Faction.PLAYER],
            game_state.units,
            game_state.current_map_name,
            mouse_pos
        )
        renderer.render_bottom_hud(game_state.selected_entities, game_state.economies[Faction.PLAYER], mouse_pos)
        renderer.render_minimap(game_state.map, game_state.buildings, game_state.units)
        renderer.render_placement_ghost(game_state.placement_building_type, game_state.map, mouse_pos)

        if input_handler.is_dragging:
            renderer.render_selection_box(input_handler.drag_start, mouse_pos)

        if input_handler.show_map_menu:
            renderer.render_map_selection_modal(game_state.current_map_name, mouse_pos)

        if getattr(game_state, "is_paused", False):
            renderer.render_pause_modal(
                mouse_pos,
                show_save=input_handler.show_save_modal,
                show_load=input_handler.show_load_modal,
                save_name_input=input_handler.save_name_input,
                selected_load_name=input_handler.selected_load_name,
                existing_saves=input_handler.existing_saves,
                status_msg=input_handler.save_status_msg,
            )

        pygame.display.flip()

        frame_count += 1
        if 0 < headless_frames <= frame_count:
            break

    pygame.quit()
    return True

if __name__ == "__main__":
    test_mode = "--test-run" in sys.argv
    frames = 120 if test_mode else 0
    run_game(headless_frames=frames)
