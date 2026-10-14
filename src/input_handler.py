"""
Input Handler System.
Processes keyboard and mouse events for camera, selection, orders, and UI buttons.
"""
import pygame
from typing import Optional, Tuple
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, Faction, UNIT_TYPES
)
from src.entities.building import Building

class InputHandler:
    def __init__(self):
        self.drag_start: Optional[Tuple[int, int]] = None
        self.is_dragging = False
        self.show_map_menu = False
        self.show_save_modal = False
        self.show_load_modal = False
        self.selected_load_name = ""
        self.save_name_input = "quicksave"
        self.save_status_msg = ""
        self.existing_saves = []

    def handle_events(self, events, game_state, renderer) -> bool:
        """Processes events. Returns False if user requested quit."""
        mouse_pos = pygame.mouse.get_pos()
        hud_y = renderer.screen_height - 140

        for event in events:
            if hasattr(event, "pos"):
                mouse_pos = event.pos

            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.VIDEORESIZE:
                new_screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                renderer.handle_resize(event.w, event.h, new_screen)
                hud_y = renderer.screen_height - 140
                continue

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    try:
                        cur_surface = pygame.display.get_surface()
                        is_full = bool(cur_surface and (cur_surface.get_flags() & pygame.FULLSCREEN))
                        if is_full:
                            new_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                            renderer.handle_resize(SCREEN_WIDTH, SCREEN_HEIGHT, new_screen)
                        else:
                            info = pygame.display.Info()
                            new_w = info.current_w if info.current_w > 0 else SCREEN_WIDTH
                            new_h = info.current_h if info.current_h > 0 else SCREEN_HEIGHT
                            new_screen = pygame.display.set_mode((new_w, new_h), pygame.FULLSCREEN | pygame.RESIZABLE)
                            renderer.handle_resize(new_w, new_h, new_screen)
                        hud_y = renderer.screen_height - 140
                    except Exception:
                        pass
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.show_save_modal:
                        self.show_save_modal = False
                        self.save_status_msg = ""
                        continue
                    elif self.show_load_modal:
                        self.show_load_modal = False
                        continue
                    elif getattr(game_state, "is_paused", False):
                        game_state.is_paused = False
                        continue
                    elif self.show_map_menu:
                        self.show_map_menu = False
                        continue
                    elif game_state.placement_building_type:
                        game_state.cancel_building_placement()
                        continue
                    elif game_state.selected_entities:
                        game_state.clear_selection()
                        continue
                    else:
                        game_state.is_paused = True
                        self.show_save_modal = False
                        self.show_load_modal = False
                        self.save_status_msg = ""
                        self.drag_start = None
                        self.is_dragging = False
                        continue

                # If in save modal, capture typing
                if getattr(game_state, "is_paused", False) and self.show_save_modal:
                    if event.key == pygame.K_BACKSPACE:
                        self.save_name_input = self.save_name_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        s_name = self.save_name_input.strip() if self.save_name_input.strip() else "quicksave"
                        game_state.save_game(s_name)
                        self.save_status_msg = f"Saved '{s_name}' successfully!"
                        self.existing_saves = game_state.list_saves()
                    elif event.unicode and (event.unicode.isalnum() or event.unicode in (" ", "_", "-")):
                        if len(self.save_name_input) < 24:
                            self.save_name_input += event.unicode
                    continue

                if self.show_map_menu or getattr(game_state, "is_paused", False):
                    continue

                # Hotkeys 1-5 for HUD actions
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    hk_str = str(event.key - pygame.K_0)
                    for btn in renderer.hud_buttons:
                        if btn.get("hotkey") == hk_str and btn.get("can_afford"):
                            self._trigger_hud_action(btn, game_state)
                            break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if getattr(game_state, "is_paused", False):
                        if not self.show_save_modal and not self.show_load_modal:
                            for btn in getattr(renderer, "pause_buttons", []):
                                if btn["rect"].collidepoint(mouse_pos):
                                    act = btn["action"]
                                    if act in ("resume", "Resume"):
                                        game_state.is_paused = False
                                    elif act in ("save", "Save"):
                                        self.show_save_modal = True
                                        self.show_load_modal = False
                                        self.save_status_msg = ""
                                        self.existing_saves = game_state.list_saves()
                                        if not self.save_name_input:
                                            self.save_name_input = "quicksave"
                                    elif act in ("load", "Load"):
                                        self.show_load_modal = True
                                        self.show_save_modal = False
                                        self.existing_saves = game_state.list_saves()
                                        self.selected_load_name = self.existing_saves[0] if self.existing_saves else ""
                                    elif act in ("quit", "quid", "Quit", "Quid"):
                                        return False
                                    break
                        elif self.show_save_modal:
                            for item in getattr(renderer, "save_items", []):
                                if item["rect"].collidepoint(mouse_pos):
                                    self.save_name_input = item["save_name"]
                                    self.save_status_msg = f"Selected '{self.save_name_input}' to overwrite."
                                    break
                            for btn in getattr(renderer, "save_buttons", []):
                                if btn["rect"].collidepoint(mouse_pos):
                                    act = btn["action"]
                                    if act in ("confirm_save", "save", "Save"):
                                        s_name = self.save_name_input.strip() if self.save_name_input.strip() else "quicksave"
                                        game_state.save_game(s_name)
                                        self.save_status_msg = f"Saved '{s_name}' successfully!"
                                        self.existing_saves = game_state.list_saves()
                                    elif act in ("back", "Back"):
                                        self.show_save_modal = False
                                        self.save_status_msg = ""
                                    break
                        elif self.show_load_modal:
                            for item in getattr(renderer, "load_items", []):
                                if item["rect"].collidepoint(mouse_pos):
                                    self.selected_load_name = item["save_name"]
                                    break
                            for btn in getattr(renderer, "load_buttons", []):
                                if btn["rect"].collidepoint(mouse_pos):
                                    act = btn["action"]
                                    if act in ("confirm_load", "load", "Load") and self.selected_load_name:
                                        success = game_state.load_game(self.selected_load_name)
                                        if success:
                                            self.show_load_modal = False
                                            game_state.is_paused = False
                                    elif act in ("back", "Back"):
                                        self.show_load_modal = False
                                    break
                        continue

                    if self.show_map_menu:
                        if renderer.modal_close_rect and renderer.modal_close_rect.collidepoint(mouse_pos):
                            self.show_map_menu = False
                            continue

                        clicked_map = None
                        for btn in getattr(renderer, "modal_buttons", []):
                            if btn["rect"].collidepoint(mouse_pos):
                                clicked_map = btn["map_name"]
                                break

                        if clicked_map:
                            game_state.load_map(clicked_map)
                            renderer.camera.x = 0.0
                            renderer.camera.y = 0.0
                            self.show_map_menu = False
                            continue

                        if renderer.modal_rect and not renderer.modal_rect.collidepoint(mouse_pos):
                            self.show_map_menu = False
                            continue

                        continue

                    # Minimap click -> pan camera
                    if hasattr(renderer, "minimap_rect") and renderer.minimap_rect.collidepoint(mouse_pos):
                        total_w = game_state.map.width * TILE_SIZE
                        total_h = game_state.map.height * TILE_SIZE
                        rel_x = (mouse_pos[0] - renderer.minimap_rect.x) / float(renderer.minimap_rect.width)
                        rel_y = (mouse_pos[1] - renderer.minimap_rect.y) / float(renderer.minimap_rect.height)
                        target_wx = rel_x * total_w
                        target_wy = rel_y * total_h
                        renderer.camera.x = max(0.0, min(renderer.camera.max_x, target_wx - renderer.screen_width / 2.0))
                        renderer.camera.y = max(0.0, min(renderer.camera.max_y, target_wy - (renderer.screen_height - 140) / 2.0))
                        continue

                    # Top Bar Map Button (clicking this is the only way to open map selector)
                    if hasattr(renderer, "top_bar_map_button_rect") and renderer.top_bar_map_button_rect.collidepoint(mouse_pos):
                        self.show_map_menu = True
                        self.drag_start = None
                        self.is_dragging = False
                        if game_state.placement_building_type:
                            game_state.cancel_building_placement()
                        continue

                    if mouse_pos[1] < 36:
                        continue

                    # Check HUD click
                    if mouse_pos[1] >= hud_y:
                        for btn in renderer.hud_buttons:
                            if btn["rect"].collidepoint(mouse_pos) and btn["can_afford"]:
                                self._trigger_hud_action(btn, game_state)
                                break
                    else:
                        # World click
                        if game_state.placement_building_type:
                            wx, wy = renderer.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
                            tx, ty = int(wx // TILE_SIZE), int(wy // TILE_SIZE)
                            game_state.confirm_building_placement(tx, ty)
                        else:
                            self.drag_start = mouse_pos
                            self.is_dragging = True

                elif event.button == 3:  # Right click
                    if self.show_map_menu or getattr(game_state, "is_paused", False):
                        continue
                    if game_state.placement_building_type:
                        game_state.cancel_building_placement()
                    else:
                        if 36 <= mouse_pos[1] < hud_y:
                            wx, wy = renderer.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
                            game_state.issue_right_click_order(wx, wy)

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.show_map_menu or getattr(game_state, "is_paused", False):
                    self.drag_start = None
                    self.is_dragging = False
                    continue

                if event.button == 1 and self.is_dragging:
                    if self.drag_start:
                        dx = abs(mouse_pos[0] - self.drag_start[0])
                        dy = abs(mouse_pos[1] - self.drag_start[1])
                        if dx > 8 or dy > 8:
                            w1, h1 = renderer.camera.screen_to_world(self.drag_start[0], self.drag_start[1])
                            w2, h2 = renderer.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
                            game_state.select_box(w1, h1, w2, h2)
                        else:
                            wx, wy = renderer.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
                            game_state.select_single(wx, wy)
                    self.drag_start = None
                    self.is_dragging = False

        return True

    def update_camera_controls(self, renderer, delta_time: float, game_state=None):
        if self.show_map_menu or (game_state and getattr(game_state, "is_paused", False)):
            return

        keys = pygame.key.get_pressed()
        pan_speed = 500.0 * delta_time

        dx, dy = 0.0, 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= pan_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += pan_speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= pan_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += pan_speed

        renderer.camera.move(dx, dy)

    def _trigger_hud_action(self, btn: dict, game_state):
        action = btn["action"]
        key = btn["key"]

        if action == "build":
            game_state.start_building_placement(key)

        elif action == "train":
            # Find selected building
            selected_bld = next((e for e in game_state.selected_entities if isinstance(e, Building)), None)
            if selected_bld and selected_bld.faction == Faction.PLAYER:
                econ = game_state.economies[Faction.PLAYER]
                cost = UNIT_TYPES[key]["cost"]
                if econ.can_afford(cost):
                    econ.deduct(cost)
                    selected_bld.queue_unit(key)
