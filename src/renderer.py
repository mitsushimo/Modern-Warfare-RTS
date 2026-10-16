"""
Renderer and Camera System.
Draws terrain, units, buildings, health bars, combat FX, and HUD.
"""
import math
import pygame
from typing import Tuple, List, Optional
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    COLOR_WHITE, COLOR_GRAY, COLOR_PANEL_BG, COLOR_PANEL_BORDER,
    COLOR_GRASS, COLOR_COAST, COLOR_WATER, COLOR_PLAYER, COLOR_PLAYER_ACCENT,
    COLOR_ENEMY, COLOR_ENEMY_ACCENT, COLOR_SELECTION_BOX, COLOR_HEALTH_GOOD,
    COLOR_HEALTH_MED, COLOR_HEALTH_LOW, COLOR_BUTTON_NORMAL,
    COLOR_BUTTON_HOVER, COLOR_BUTTON_DISABLED, COLOR_BUTTON_TEXT,
    COLOR_BUTTON_TEXT_MUTED, Domain, Faction, TerrainType,
    BUILDING_TYPES, UNIT_TYPES, ResourceType, MAP_PRESETS
)
from src.entities.unit import Unit, UnitState
from src.entities.building import Building
from src.asset_manager import AssetManager

class Camera:
    def __init__(self, screen_width: int, screen_height: int, projection_mode: str = "isometric", map_width: int = MAP_WIDTH, map_height: int = MAP_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.projection_mode = projection_mode
        self.map_width = map_width
        self.map_height = map_height
        self.x: float = 0.0
        self.y: float = 0.0
        self.zoom: float = 1.0
        self.min_zoom: float = 0.5
        self.max_zoom: float = 2.5
        self.update_bounds(screen_width, screen_height)

    def set_map_dimensions(self, width: int, height: int):
        self.map_width = width
        self.map_height = height
        self.update_bounds(self.screen_width, self.screen_height)

    def toggle_projection(self):
        """Projection mode is always isometric."""
        self.projection_mode = "isometric"
        self.update_bounds(self.screen_width, self.screen_height)

    def update_bounds(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        vis_w = screen_width / self.zoom
        vis_h = screen_height / self.zoom
        total_u = (self.map_width + self.map_height) * TILE_SIZE
        total_v = (self.map_width + self.map_height) * TILE_SIZE * 0.5
        self.max_x = max(0.0, total_u - vis_w)
        self.max_y = max(0.0, total_v - vis_h)
        self.x = max(0.0, min(self.max_x, self.x))
        self.y = max(0.0, min(self.max_y, self.y))

    def move(self, dx: float, dy: float):
        self.x = max(0.0, min(self.max_x, self.x + dx))
        self.y = max(0.0, min(self.max_y, self.y + dy))

    def zoom_at(self, screen_x: float, screen_y: float, factor: float):
        """Zooms centered at the screen cursor (screen_x, screen_y)."""
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-4:
            return

        # Projected coordinate (u, v) under cursor before zoom
        anchor_u = screen_x / old_zoom + self.x
        anchor_v = screen_y / old_zoom + self.y

        self.zoom = new_zoom
        self.update_bounds(self.screen_width, self.screen_height)

        # Place camera such that anchor_u, anchor_v remains under screen_x, screen_y
        new_x = anchor_u - screen_x / new_zoom
        new_y = anchor_v - screen_y / new_zoom
        self.x = max(0.0, min(self.max_x, new_x))
        self.y = max(0.0, min(self.max_y, new_y))

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        if self.projection_mode == "isometric":
            u = (wx - wy) + self.map_height * TILE_SIZE
            v = (wx + wy) * 0.5
            return int((u - self.x) * self.zoom), int((v - self.y) * self.zoom)
        else:
            return int((wx - self.x) * self.zoom), int((wy - self.y) * self.zoom)

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        if self.projection_mode == "isometric":
            u = sx / self.zoom + self.x
            v = sy / self.zoom + self.y
            du = u - self.map_height * TILE_SIZE
            wx = v + du * 0.5
            wy = v - du * 0.5
            return float(wx), float(wy)
        else:
            return float(sx / self.zoom + self.x), float(sy / self.zoom + self.y)

class Renderer:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.screen_width = surface.get_width()
        self.screen_height = surface.get_height()
        self.camera = Camera(self.screen_width, self.screen_height)
        self.asset_manager = AssetManager()
        self.font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 11)
        self.font_large = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 16, bold=True)
        self.hud_buttons: List[dict] = []
        self.top_bar_map_button_rect = pygame.Rect(490, 5, 210, 26)
        self.modal_buttons: List[dict] = []
        self.modal_page_buttons: List[dict] = []
        self.map_modal_page: int = 0
        self.modal_rect: Optional[pygame.Rect] = None
        self.modal_close_rect: Optional[pygame.Rect] = None
        self.pause_buttons: List[dict] = []
        self.save_buttons: List[dict] = []
        self.save_items: List[dict] = []
        self.load_buttons: List[dict] = []
        self.load_items: List[dict] = []

        self.save_input_rect: Optional[pygame.Rect] = None
        self.minimap_rect: pygame.Rect = pygame.Rect(0, 0, 160, 120)
        self.minimap_viewport_rect: pygame.Rect = pygame.Rect(0, 0, 10, 10)
        self.minimap_terrain_surf: Optional[pygame.Surface] = None
        self.cached_minimap_map_name: Optional[str] = None


    def handle_resize(self, width: int, height: int, surface: Optional[pygame.Surface] = None):
        self.screen_width = width
        self.screen_height = height
        if surface is not None:
            self.surface = surface
        self.camera.update_bounds(width, height)

    def render_map(self, game_map):
        self.surface.fill((14, 16, 20))
        if self.camera.map_width != game_map.width or self.camera.map_height != game_map.height:
            self.camera.set_map_dimensions(game_map.width, game_map.height)

        if getattr(self.camera, "projection_mode", "isometric") == "topdown":
            vis_w = self.screen_width / self.camera.zoom
            vis_h = self.screen_height / self.camera.zoom
            start_tx = max(0, int(self.camera.x // TILE_SIZE))
            end_tx = min(game_map.width, int((self.camera.x + vis_w) // TILE_SIZE) + 2)
            start_ty = max(0, int(self.camera.y // TILE_SIZE))
            end_ty = min(game_map.height, int((self.camera.y + vis_h) // TILE_SIZE) + 2)

            for ty in range(start_ty, end_ty):
                for tx in range(start_tx, end_tx):
                    t = game_map.get_terrain(tx, ty)
                    col = COLOR_WATER if t == TerrainType.WATER else (COLOR_COAST if t == TerrainType.COAST else COLOR_GRASS)
                    sx, sy = self.camera.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
                    next_sx, next_sy = self.camera.world_to_screen((tx + 1) * TILE_SIZE, (ty + 1) * TILE_SIZE)
                    rect = pygame.Rect(sx, sy, max(1, next_sx - sx), max(1, next_sy - sy))
                    pygame.draw.rect(self.surface, col, rect)
                    pygame.draw.rect(self.surface, (max(0, col[0] - 12), max(0, col[1] - 12), max(0, col[2] - 12)), rect, 1)
            return

        # Isometric Triangular Terrain Mesh
        tl_wx, tl_wy = self.camera.screen_to_world(0, 0)
        tr_wx, tr_wy = self.camera.screen_to_world(self.screen_width, 0)
        br_wx, br_wy = self.camera.screen_to_world(self.screen_width, self.screen_height)
        bl_wx, bl_wy = self.camera.screen_to_world(0, self.screen_height)

        min_wx = min(tl_wx, tr_wx, br_wx, bl_wx)
        max_wx = max(tl_wx, tr_wx, br_wx, bl_wx)
        min_wy = min(tl_wy, tr_wy, br_wy, bl_wy)
        max_wy = max(tl_wy, tr_wy, br_wy, bl_wy)

        start_tx = max(0, int(min_wx // TILE_SIZE) - 1)
        end_tx = min(game_map.width, int(max_wx // TILE_SIZE) + 2)
        start_ty = max(0, int(min_wy // TILE_SIZE) - 1)
        end_ty = min(game_map.height, int(max_wy // TILE_SIZE) + 2)

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                t = game_map.get_terrain(tx, ty)

                p_top = self.camera.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
                p_right = self.camera.world_to_screen((tx + 1) * TILE_SIZE, ty * TILE_SIZE)
                p_bottom = self.camera.world_to_screen((tx + 1) * TILE_SIZE, (ty + 1) * TILE_SIZE)
                p_left = self.camera.world_to_screen(tx * TILE_SIZE, (ty + 1) * TILE_SIZE)
                p_center = (
                    (p_left[0] + p_right[0]) // 2,
                    (p_top[1] + p_bottom[1]) // 2
                )

                if t == TerrainType.WATER:
                    col_w = (46, 105, 175)
                    col_n = (42, 98, 168)
                    col_s = (36, 90, 158)
                    col_e = (30, 82, 148)
                elif t == TerrainType.COAST:
                    n_up = game_map.get_terrain(tx, ty - 1)
                    n_rt = game_map.get_terrain(tx + 1, ty)
                    n_dn = game_map.get_terrain(tx, ty + 1)
                    n_lt = game_map.get_terrain(tx - 1, ty)

                    col_w = (145, 185, 175) if n_lt == TerrainType.WATER else (205, 190, 138)
                    col_n = (140, 180, 170) if n_up == TerrainType.WATER else (196, 180, 130)
                    col_s = (135, 175, 165) if n_dn == TerrainType.WATER else (185, 170, 120)
                    col_e = (130, 170, 160) if n_rt == TerrainType.WATER else (175, 160, 110)
                else:
                    col_w = (68, 140, 78)
                    col_n = (62, 130, 72)
                    col_s = (54, 118, 64)
                    col_e = (48, 108, 58)

                # Render 4 triangular graphics units per tile with directional light
                pygame.draw.polygon(self.surface, col_w, [p_left, p_top, p_center])
                pygame.draw.polygon(self.surface, col_n, [p_top, p_right, p_center])
                pygame.draw.polygon(self.surface, col_s, [p_bottom, p_left, p_center])
                pygame.draw.polygon(self.surface, col_e, [p_right, p_bottom, p_center])
                pygame.draw.polygon(self.surface, (max(0, col_e[0] - 12), max(0, col_e[1] - 12), max(0, col_e[2] - 12)), [p_top, p_right, p_bottom, p_left], 1)

    def _render_health_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        hp: float,
        max_hp: float,
        faction: Optional[Faction] = None
    ):
        ratio = max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0
        pygame.draw.rect(self.surface, (20, 20, 20), pygame.Rect(x, y, width, height))
        col = COLOR_HEALTH_GOOD if ratio > 0.5 else (COLOR_HEALTH_MED if ratio > 0.25 else COLOR_HEALTH_LOW)
        pygame.draw.rect(self.surface, col, pygame.Rect(x, y, int(width * ratio), height))

        if faction is not None:
            # Blue (player) or red (enemy) circular dot on top of the HP gauge bar
            dot_rad = max(3, int(height * 0.8))
            dot_cx = x + width // 2
            dot_cy = y - dot_rad - 2
            dot_col = COLOR_PLAYER if faction == Faction.PLAYER else COLOR_ENEMY
            pygame.draw.circle(self.surface, (15, 15, 20), (dot_cx, dot_cy), dot_rad + 1)
            pygame.draw.circle(self.surface, dot_col, (dot_cx, dot_cy), dot_rad)

    def _render_building_flag(self, faction: Faction, corner_x: int, corner_y: int, zoom: float):
        """Draws a faction-colored flag (blue for player, red for enemy) on the right-hand corner of a building."""
        is_player = (faction == Faction.PLAYER)
        flag_fill = COLOR_PLAYER if is_player else COLOR_ENEMY
        flag_accent = COLOR_PLAYER_ACCENT if is_player else COLOR_ENEMY_ACCENT
        outline_col = (20, 24, 32) if is_player else (36, 16, 16)

        pole_h = max(22, int(30 * zoom))
        pole_top_y = corner_y - pole_h
        pole_w = max(2, int(2 * zoom))

        # 1. Pole shadow / line
        pygame.draw.line(self.surface, (40, 44, 48), (corner_x, corner_y), (corner_x, pole_top_y), pole_w + 1)
        # 2. Metallic pole
        pygame.draw.line(self.surface, (185, 190, 200), (corner_x, corner_y), (corner_x, pole_top_y), pole_w)

        # 3. Gold finial ball on top of the pole
        finial_r = max(2, int(3 * zoom))
        pygame.draw.circle(self.surface, (235, 195, 55), (corner_x, pole_top_y), finial_r)
        pygame.draw.circle(self.surface, (60, 50, 20), (corner_x, pole_top_y), finial_r, 1)

        # 4. Flag banner (waving towards the right)
        flag_w = max(16, int(22 * zoom))
        flag_h = max(11, int(15 * zoom))
        fy0 = pole_top_y + max(2, int(3 * zoom))
        fy1 = fy0 + flag_h
        fx0 = corner_x + 1
        fx1 = fx0 + flag_w

        # Swallowtail flag shape
        notch_depth = max(4, int(5 * zoom))
        pts = [
            (fx0, fy0),
            (fx1, fy0),
            (fx1 - notch_depth, (fy0 + fy1) // 2),
            (fx1, fy1),
            (fx0, fy1),
        ]
        pygame.draw.polygon(self.surface, flag_fill, pts)
        pygame.draw.polygon(self.surface, outline_col, pts, 1)

        # Inner accent stripe along the hoist
        stripe_w = max(2, int(3 * zoom))
        pygame.draw.rect(self.surface, flag_accent, pygame.Rect(fx0 + 1, fy0 + 1, stripe_w, flag_h - 2))

    def _render_building_isometric(self, bld: Building, zoom: float):
        w_tiles, h_tiles = bld.width_tiles, bld.height_tiles
        wx0, wy0 = bld.tile_x * TILE_SIZE, bld.tile_y * TILE_SIZE
        wx1, wy1 = (bld.tile_x + w_tiles) * TILE_SIZE, (bld.tile_y + h_tiles) * TILE_SIZE

        g_top = self.camera.world_to_screen(wx0, wy0)
        g_right = self.camera.world_to_screen(wx1, wy0)
        g_bottom = self.camera.world_to_screen(wx1, wy1)
        g_left = self.camera.world_to_screen(wx0, wy1)

        base_cx = (g_left[0] + g_right[0]) // 2
        base_cy = (g_top[1] + g_bottom[1]) // 2

        sprite = self.asset_manager.get_building_sprite(bld.type_name, zoom)
        if sprite:
            # 1. Ground selection diamond under the building foundation
            if bld.is_selected:
                pygame.draw.polygon(self.surface, COLOR_SELECTION_BOX, [g_top, g_right, g_bottom, g_left], max(2, int(2 * zoom)))
                if getattr(bld, "rally_point", None):
                    r_sx, r_sy = self.camera.world_to_screen(bld.rally_point[0], bld.rally_point[1])
                    pygame.draw.line(self.surface, (255, 220, 80), (base_cx, base_cy), (r_sx, r_sy), 1)
                    arm = max(4, int(8 * zoom))
                    pygame.draw.line(self.surface, (255, 230, 40), (r_sx - arm, r_sy - arm), (r_sx + arm, r_sy + arm), max(1, int(3 * zoom)))
                    pygame.draw.line(self.surface, (255, 230, 40), (r_sx - arm, r_sy + arm), (r_sx + arm, r_sy - arm), max(1, int(3 * zoom)))
                    pygame.draw.circle(self.surface, (255, 230, 40), (r_sx, r_sy), arm + max(2, int(4 * zoom)), 1)

            # 2. Building Sprite anchored flush to the bottom ground diamond vertex (g_bottom)
            sprite_rect = sprite.get_rect(midbottom=g_bottom)
            self.surface.blit(sprite, sprite_rect)

            # 3. Ground selection outline hugging the front foundation edges
            if bld.is_selected:
                pygame.draw.lines(self.surface, COLOR_SELECTION_BOX, False, [g_left, g_bottom, g_right], max(2, int(2 * zoom)))

            # 4. Faction Flag on the right-hand corner of the building
            flag_x = g_right[0] - int(4 * zoom)
            flag_y = g_right[1] - int(14 * zoom)
            self._render_building_flag(bld.faction, flag_x, flag_y, zoom)

            # 5. Health bar
            hb_w = max(24, int(w_tiles * 18 * zoom))
            hb_h = max(3, int(5 * zoom))
            self._render_health_bar(sprite_rect.centerx - hb_w // 2, sprite_rect.top - max(8, int(10 * zoom)), hb_w, hb_h, bld.hp, bld.max_hp)

            # 6. Construction progress bar
            if bld.under_construction:
                prog = bld.build_progress / bld.build_time
                bar_y = sprite_rect.top - max(4, int(5 * zoom))
                pygame.draw.rect(self.surface, (30, 30, 30), pygame.Rect(sprite_rect.centerx - hb_w // 2, bar_y, hb_w, max(2, int(4 * zoom))))
                pygame.draw.rect(self.surface, (230, 180, 40), pygame.Rect(sprite_rect.centerx - hb_w // 2, bar_y, max(1, int(hb_w * prog)), max(2, int(4 * zoom))))
            return

        ext_h = int((w_tiles + h_tiles) * 10 * zoom)
        if bld.under_construction:
            prog = bld.build_progress / bld.build_time
            ext_h = max(4, int(ext_h * prog))

        r_top = (g_top[0], g_top[1] - ext_h)
        r_right = (g_right[0], g_right[1] - ext_h)
        r_bottom = (g_bottom[0], g_bottom[1] - ext_h)
        r_left = (g_left[0], g_left[1] - ext_h)

        is_player = (bld.faction == Faction.PLAYER)
        wall_l_col = (52, 75, 95) if is_player else (95, 52, 52)
        wall_r_col = (38, 55, 72) if is_player else (72, 38, 38)
        roof_col = (68, 98, 124) if is_player else (124, 68, 68)
        accent_col = COLOR_PLAYER if is_player else COLOR_ENEMY

        pygame.draw.polygon(self.surface, wall_l_col, [g_left, g_bottom, r_bottom, r_left])
        pygame.draw.polygon(self.surface, (30, 42, 54), [g_left, g_bottom, r_bottom, r_left], 1)
        pygame.draw.polygon(self.surface, wall_r_col, [g_bottom, g_right, r_right, r_bottom])
        pygame.draw.polygon(self.surface, (25, 35, 45), [g_bottom, g_right, r_right, r_bottom], 1)

        pygame.draw.polygon(self.surface, roof_col, [r_top, r_right, r_bottom, r_left])
        pygame.draw.polygon(self.surface, accent_col, [r_top, r_right, r_bottom, r_left], max(1, int(2 * zoom)))

        roof_cx = (r_left[0] + r_right[0]) // 2
        roof_cy = (r_top[1] + r_bottom[1]) // 2
        font_to_use = self.font if zoom >= 0.8 else self.font_small
        text = font_to_use.render(bld.symbol, True, COLOR_WHITE)
        self.surface.blit(text, text.get_rect(center=(roof_cx, roof_cy)))

        if bld.is_selected:
            pygame.draw.polygon(self.surface, COLOR_SELECTION_BOX, [g_top, g_right, g_bottom, g_left], max(2, int(2 * zoom)))
            if getattr(bld, "rally_point", None):
                r_sx, r_sy = self.camera.world_to_screen(bld.rally_point[0], bld.rally_point[1])
                pygame.draw.line(self.surface, (255, 220, 80), (roof_cx, roof_cy), (r_sx, r_sy), 1)
                arm = max(4, int(8 * zoom))
                pygame.draw.line(self.surface, (255, 230, 40), (r_sx - arm, r_sy - arm), (r_sx + arm, r_sy + arm), max(1, int(3 * zoom)))
                pygame.draw.line(self.surface, (255, 230, 40), (r_sx - arm, r_sy + arm), (r_sx + arm, r_sy - arm), max(1, int(3 * zoom)))
                pygame.draw.circle(self.surface, (255, 230, 40), (r_sx, r_sy), arm + max(2, int(4 * zoom)), 1)

        hb_w = max(24, int(w_tiles * 18 * zoom))
        hb_h = max(3, int(5 * zoom))
        self._render_health_bar(roof_cx - hb_w // 2, r_top[1] - max(8, int(12 * zoom)), hb_w, hb_h, bld.hp, bld.max_hp)

        if bld.under_construction:
            prog = bld.build_progress / bld.build_time
            bar_y = r_top[1] - max(5, int(6 * zoom))
            pygame.draw.rect(self.surface, (30, 30, 30), pygame.Rect(roof_cx - hb_w // 2, bar_y, hb_w, max(2, int(4 * zoom))))
            pygame.draw.rect(self.surface, (230, 180, 40), pygame.Rect(roof_cx - hb_w // 2, bar_y, max(1, int(hb_w * prog)), max(2, int(4 * zoom))))

        # Faction Flag on the right-hand corner of the building roof
        self._render_building_flag(bld.faction, r_right[0], r_right[1], zoom)

    def _render_building_topdown(self, bld: Building, zoom: float):
        wx, wy, w, h = bld.get_world_rect()
        sx, sy = self.camera.world_to_screen(wx, wy)
        next_sx, next_sy = self.camera.world_to_screen(wx + w, wy + h)
        sw = max(2, next_sx - sx)
        sh = max(2, next_sy - sy)
        rect = pygame.Rect(sx, sy, sw, sh)
        bg_col = (45, 55, 65) if bld.faction == Faction.PLAYER else (65, 45, 45)
        pygame.draw.rect(self.surface, bg_col, rect, border_radius=max(1, int(4 * zoom)))
        border_col = COLOR_PLAYER if bld.faction == Faction.PLAYER else COLOR_ENEMY
        pygame.draw.rect(self.surface, border_col, rect, max(1, int(2 * zoom)), border_radius=max(1, int(4 * zoom)))

        font_to_use = self.font if zoom >= 0.8 else self.font_small
        text = font_to_use.render(bld.symbol, True, COLOR_WHITE)
        self.surface.blit(text, text.get_rect(center=rect.center))

        # Faction Flag on the top-right corner of the building
        flag_x = rect.right - max(3, int(4 * zoom))
        flag_y = rect.top + max(3, int(4 * zoom))
        self._render_building_flag(bld.faction, flag_x, flag_y, zoom)

        if bld.is_selected:
            pad = max(2, int(6 * zoom))
            pygame.draw.rect(self.surface, COLOR_SELECTION_BOX, rect.inflate(pad, pad), max(1, int(2 * zoom)), border_radius=max(2, int(6 * zoom)))
            if getattr(bld, "rally_point", None):
                r_sx, r_sy = self.camera.world_to_screen(bld.rally_point[0], bld.rally_point[1])
                b_cx, b_cy = rect.center
                pygame.draw.line(self.surface, (255, 220, 80), (b_cx, b_cy), (r_sx, r_sy), 1)
                arm = max(4, int(8 * zoom))
                pygame.draw.line(self.surface, (255, 230, 40), (r_sx - arm, r_sy - arm), (r_sx + arm, r_sy + arm), max(1, int(3 * zoom)))
                pygame.draw.line(self.surface, (255, 230, 40), (r_sx - arm, r_sy + arm), (r_sx + arm, r_sy - arm), max(1, int(3 * zoom)))
                pygame.draw.circle(self.surface, (255, 230, 40), (r_sx, r_sy), arm + max(2, int(4 * zoom)), 1)
        self._render_health_bar(sx, sy - max(6, int(12 * zoom)), sw, max(3, int(5 * zoom)), bld.hp, bld.max_hp)

        if bld.under_construction:
            prog = bld.build_progress / bld.build_time
            bar_h = max(2, int(4 * zoom))
            pygame.draw.rect(self.surface, (30, 30, 30), pygame.Rect(sx, sy - max(4, int(6 * zoom)), sw, bar_h))
            pygame.draw.rect(self.surface, (230, 180, 40), pygame.Rect(sx, sy - max(4, int(6 * zoom)), max(1, int(sw * prog)), bar_h))

    def render_buildings(self, buildings: List[Building]):
        zoom = self.camera.zoom
        is_iso = (getattr(self.camera, "projection_mode", "isometric") == "isometric")
        for bld in buildings:
            if is_iso:
                self._render_building_isometric(bld, zoom)
            else:
                self._render_building_topdown(bld, zoom)
    def _render_unit_isometric(self, unit: Unit, zoom: float):
        sx, sy = self.camera.world_to_screen(unit.x, unit.y)
        r = max(4, int(unit.radius * zoom))

        proj_mode = getattr(self.camera, "projection_mode", "isometric")
        hull_dir = unit.get_compass_direction(projection_mode=proj_mode)
        turret_dir = unit.get_turret_compass_direction(projection_mode=proj_mode)

        hull_sprite, turret_sprite = self.asset_manager.get_unit_parts(unit.type_name, zoom, hull_dir, turret_dir)
        if not hull_sprite and not turret_sprite:
            hull_sprite = self.asset_manager.get_unit_sprite(unit.type_name, zoom, direction=hull_dir)

        if hull_sprite or turret_sprite:
            # 1. Ground shadow ellipse
            h_rect = hull_sprite.get_rect(center=(sx, sy)) if hull_sprite else None
            turret_rect = turret_sprite.get_rect(center=(sx, sy - int(3 * zoom))) if turret_sprite else None

            # Calculate shadow footprint based on sprite dimensions
            ref_w = h_rect.width if h_rect else (turret_rect.width if turret_rect else r * 2)
            ref_h = h_rect.height if h_rect else (turret_rect.height if turret_rect else r)
            shadow_w = max(int(r * 2.2), int(ref_w * 0.45))
            shadow_h = max(int(r * 1.1), int(ref_h * 0.25))

            # 1. Ground shadow ellipse
            shadow_surf = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 75), (shadow_w // 2, shadow_h // 2, shadow_w, shadow_h))
            self.surface.blit(shadow_surf, (sx - shadow_w, sy - shadow_h // 2 + int(3 * zoom)))

            # 2. Selection ring (beneath hull, scaled to unit size)
            if unit.is_selected:
                sel_w = max(r + 4, int(ref_w * 0.45))
                sel_h = max(r // 2 + 2, int(ref_h * 0.25))
                pygame.draw.ellipse(self.surface, COLOR_SELECTION_BOX, (sx - sel_w, sy - sel_h, sel_w * 2, sel_h * 2), max(1, int(2 * zoom)))

            # 3. Hull sprite
            if hull_sprite and h_rect:
                self.surface.blit(hull_sprite, h_rect)

            # 4. Turret sprite (centered on mount)
            if turret_sprite and turret_rect:
                self.surface.blit(turret_sprite, turret_rect)

            # 5. Health bar with circular faction dot on top
            hb_w = max(18, int(unit.radius * 2 * zoom))
            hb_h = max(2, int(4 * zoom))
            sprite_top = h_rect.top if h_rect else (turret_rect.top if turret_rect else sy - r)
            bar_y = min(sy - r - max(8, int(12 * zoom)), sprite_top - max(6, int(8 * zoom)))
            self._render_health_bar(sx - hb_w // 2, bar_y, hb_w, hb_h, unit.hp, unit.max_hp, faction=unit.faction)
            return

        base_col = COLOR_PLAYER if unit.faction == Faction.PLAYER else COLOR_ENEMY
        accent_col = COLOR_PLAYER_ACCENT if unit.faction == Faction.PLAYER else COLOR_ENEMY_ACCENT

        # Ground shadow ellipse
        shadow_w = int(r * 2.2)
        shadow_h = int(r * 1.1)
        shadow_surf = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 75), (shadow_w // 2, shadow_h // 2, shadow_w, shadow_h))
        self.surface.blit(shadow_surf, (sx - shadow_w, sy - shadow_h // 2 + int(3 * zoom)))

        # Heading vector
        vx, vy = unit.vx, unit.vy
        v_len = (vx * vx + vy * vy) ** 0.5
        h_dx, h_dy = (vx / v_len, vy / v_len) if v_len > 0.01 else (1.0, 0.0)

        # Turret / weapon aiming vector
        if unit.state == UnitState.ATTACKING and getattr(unit, "target_entity", None):
            t_angle = getattr(unit, "turret_angle", unit.heading_angle)
            tsvx = math.cos(t_angle) - math.sin(t_angle)
            tsvy = (math.cos(t_angle) + math.sin(t_angle)) * 0.5
            t_len = math.hypot(tsvx, tsvy)
            t_dx, t_dy = (tsvx / t_len, tsvy / t_len) if t_len > 0.001 else (1.0, 0.0)
        else:
            t_dx, t_dy = h_dx, h_dy

        if unit.domain == Domain.SEA:
            hull_len = max(8, int(r * 2.4))
            hull_w = max(4, int(r * 1.2))
            hull_h = max(3, int(5 * zoom))
            pygame.draw.ellipse(self.surface, (30, 42, 54), (sx - hull_len // 2, sy - hull_w // 2, hull_len, hull_w))
            pygame.draw.ellipse(self.surface, base_col, (sx - hull_len // 2, sy - hull_w // 2 - hull_h, hull_len, hull_w))
            tip_x = int(sx + t_dx * hull_len * 0.45)
            tip_y = int(sy - hull_h + t_dy * hull_w * 0.45)
            pygame.draw.line(self.surface, (240, 240, 240), (sx, sy - hull_h), (tip_x, tip_y), max(2, int(2 * zoom)))
        elif "Tank" in unit.type_name:
            box_w = max(6, int(r * 1.8))
            box_h = max(5, int(r * 1.2))
            ext_h = max(3, int(4 * zoom))
            pygame.draw.rect(self.surface, (25, 28, 34), (sx - box_w // 2, sy - box_h // 2, box_w, box_h), border_radius=2)
            pygame.draw.rect(self.surface, base_col, (sx - box_w // 2, sy - box_h // 2 - ext_h, box_w, box_h), border_radius=2)
            tip_x = int(sx + t_dx * box_w * 0.6)
            tip_y = int(sy - ext_h + t_dy * box_h * 0.6)
            pygame.draw.line(self.surface, (230, 230, 240), (sx, sy - ext_h), (tip_x, tip_y), max(2, int(3 * zoom)))
        else:
            body_h = max(4, int(r * 1.4))
            pygame.draw.circle(self.surface, (35, 40, 48), (sx, sy), r)
            pygame.draw.circle(self.surface, base_col, (sx, sy - body_h // 2), r)
            pygame.draw.circle(self.surface, accent_col, (sx, sy - body_h // 2), max(2, r // 2))

        if zoom >= 0.75:
            sym_txt = self.font_small.render(unit.symbol, True, (255, 255, 255))
            self.surface.blit(sym_txt, sym_txt.get_rect(center=(sx, sy - max(4, int(6 * zoom)))))

        if unit.is_selected:
            pygame.draw.ellipse(self.surface, COLOR_SELECTION_BOX, (sx - r - 4, sy - r // 2 - 2, (r + 4) * 2, r + 4), 1)

        hb_w = max(18, int(unit.radius * 2 * zoom))
        hb_h = max(2, int(4 * zoom))
        self._render_health_bar(sx - hb_w // 2, sy - r - max(8, int(12 * zoom)), hb_w, hb_h, unit.hp, unit.max_hp, faction=unit.faction)

    def _render_unit_topdown(self, unit: Unit, zoom: float):
        sx, sy = self.camera.world_to_screen(unit.x, unit.y)
        base_col = COLOR_PLAYER if unit.faction == Faction.PLAYER else COLOR_ENEMY
        accent_col = COLOR_PLAYER_ACCENT if unit.faction == Faction.PLAYER else COLOR_ENEMY_ACCENT
        scaled_radius = max(3, int(unit.radius * zoom))

        if unit.domain == Domain.SEA:
            length = max(4, int(unit.radius * 2.2 * zoom))
            width = max(3, int(unit.radius * 1.2 * zoom))
            ship_rect = pygame.Rect(sx - length // 2, sy - width // 2, length, width)
            pygame.draw.ellipse(self.surface, (30, 40, 50), ship_rect)
            pygame.draw.ellipse(self.surface, base_col, ship_rect, max(1, int(2 * zoom)))
        else:
            pygame.draw.circle(self.surface, (40, 45, 50), (sx, sy), scaled_radius)
            pygame.draw.circle(self.surface, base_col, (sx, sy), scaled_radius, max(1, int(2 * zoom)))

        if zoom >= 0.75:
            sym_txt = self.font_small.render(unit.symbol, True, accent_col)
            self.surface.blit(sym_txt, sym_txt.get_rect(center=(sx, sy)))

        if unit.is_selected:
            pygame.draw.circle(self.surface, COLOR_SELECTION_BOX, (sx, sy), scaled_radius + max(2, int(4 * zoom)), 1)

        hb_w = max(18, int(unit.radius * 2 * zoom))
        hb_h = max(2, int(4 * zoom))
        self._render_health_bar(sx - hb_w // 2, sy - scaled_radius - max(4, int(8 * zoom)), hb_w, hb_h, unit.hp, unit.max_hp, faction=unit.faction)

    def render_units(self, units: List[Unit]):
        zoom = self.camera.zoom
        is_iso = (getattr(self.camera, "projection_mode", "isometric") == "isometric")
        for unit in units:
            if is_iso:
                self._render_unit_isometric(unit, zoom)
            else:
                self._render_unit_topdown(unit, zoom)

    def render_entities(self, buildings: List[Building], units: List[Unit]):
        """Renders buildings and units unified with back-to-front depth sorting."""
        zoom = self.camera.zoom
        if getattr(self.camera, "projection_mode", "isometric") == "topdown":
            self.render_buildings(buildings)
            self.render_units(units)
            return

        items = []
        for bld in buildings:
            if not bld.is_alive:
                continue
            depth = (bld.tile_x + bld.width_tiles + bld.tile_y + bld.height_tiles) * TILE_SIZE
            items.append((depth, "bld", bld))

        for u in units:
            if not u.is_alive:
                continue
            depth = u.x + u.y
            items.append((depth, "unit", u))

        items.sort(key=lambda it: it[0])

        for _, kind, ent in items:
            if kind == "bld":
                self._render_building_isometric(ent, zoom)
            else:
                self._render_unit_isometric(ent, zoom)

    def render_combat_effects(self, effects):
        zoom = self.camera.zoom
        for eff in effects:
            if getattr(eff, "has_impacted", False):
                cx, cy = eff.current_pos
                sx, sy = self.camera.world_to_screen(cx, cy)
                imp_rad = max(2, int(getattr(eff, "impact_radius", 4.0) * zoom))
                pygame.draw.circle(self.surface, eff.color, (sx, sy), imp_rad)
                pygame.draw.circle(self.surface, (255, 255, 255), (sx, sy), max(1, imp_rad - 2))
                continue

            trail = getattr(eff, "trail", None)
            eff_w = max(1, int(eff.width * zoom))
            if trail and len(trail) >= 2:
                for idx in range(len(trail) - 1):
                    p1 = trail[idx]
                    p2 = trail[idx + 1]
                    s1 = self.camera.world_to_screen(p1[0], p1[1])
                    s2 = self.camera.world_to_screen(p2[0], p2[1])
                    pygame.draw.line(self.surface, eff.color, s1, s2, eff_w)
            else:
                cur_pos = getattr(eff, "current_pos", eff.end_pos)
                s1 = self.camera.world_to_screen(eff.start_pos[0], eff.start_pos[1])
                s2 = self.camera.world_to_screen(cur_pos[0], cur_pos[1])
                pygame.draw.line(self.surface, eff.color, s1, s2, eff_w)

            cur_p = getattr(eff, "current_pos", None)
            if cur_p:
                sx, sy = self.camera.world_to_screen(cur_p[0], cur_p[1])
                rad = max(2, int(getattr(eff, "head_radius", 2.5) * zoom))
                pygame.draw.circle(self.surface, (255, 255, 255), (sx, sy), rad)
                pygame.draw.circle(self.surface, eff.color, (sx, sy), rad, 1)

    def render_top_bar(
        self,
        economy,
        units,
        current_map_name: str = "Divided Sea",
        mouse_pos: Optional[Tuple[int, int]] = None
    ):
        bar_rect = pygame.Rect(0, 0, self.screen_width, 36)
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, bar_rect)
        pygame.draw.line(self.surface, COLOR_PANEL_BORDER, (0, 36), (self.screen_width, 36), 2)

        food_val = int(economy.get_amount(ResourceType.FOOD))
        steel_val = int(economy.get_amount(ResourceType.STEEL))
        fuel_val = int(economy.get_amount(ResourceType.FUEL))
        army_cnt = sum(1 for u in units if u.faction == Faction.PLAYER and u.domain == Domain.LAND)
        navy_cnt = sum(1 for u in units if u.faction == Faction.PLAYER and u.domain == Domain.SEA)

        texts = [f"Food: {food_val}", f"Steel: {steel_val}", f"Fuel: {fuel_val}", f"Army: {army_cnt}", f"Navy: {navy_cnt}"]
        x_off = 20
        for t in texts:
            img = self.font.render(t, True, COLOR_WHITE)
            self.surface.blit(img, (x_off, 10))
            x_off += img.get_width() + 24

        # Clickable Map Selection Button on Top Bar
        map_btn_w = 210
        map_btn_h = 26
        map_btn_x = max(x_off + 12, min(self.screen_width - 550, 490))
        map_btn_y = 5
        self.top_bar_map_button_rect = pygame.Rect(map_btn_x, map_btn_y, map_btn_w, map_btn_h)

        is_hover = bool(mouse_pos and self.top_bar_map_button_rect.collidepoint(mouse_pos))
        btn_bg = COLOR_BUTTON_HOVER if is_hover else COLOR_BUTTON_NORMAL
        border_col = COLOR_PLAYER_ACCENT if is_hover else COLOR_PANEL_BORDER

        pygame.draw.rect(self.surface, btn_bg, self.top_bar_map_button_rect, border_radius=4)
        pygame.draw.rect(self.surface, border_col, self.top_bar_map_button_rect, 1, border_radius=4)

        map_label = f"Map: {current_map_name} ▼"
        map_text_surf = self.font.render(map_label, True, COLOR_BUTTON_TEXT)
        self.surface.blit(map_text_surf, map_text_surf.get_rect(center=self.top_bar_map_button_rect.center))

        view_mode_name = "Isometric" if getattr(self.camera, "projection_mode", "isometric") == "isometric" else "Top-Down"
        hint = f"[Tab] {view_mode_name} | Wheel: Zoom ({int(self.camera.zoom * 100)}%) | WASD: Pan"
        hint_img = self.font_small.render(hint, True, COLOR_GRAY)
        self.surface.blit(hint_img, (self.screen_width - hint_img.get_width() - 20, 11))

    def render_bottom_hud(self, selected_entities, economy, mouse_pos: Tuple[int, int]):
        hud_h = 140
        hud_y = self.screen_height - hud_h
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, pygame.Rect(0, hud_y, self.screen_width, hud_h))
        pygame.draw.line(self.surface, COLOR_PANEL_BORDER, (0, hud_y), (self.screen_width, hud_y), 2)

        self.hud_buttons.clear()
        if not selected_entities:
            self.surface.blit(self.font.render("No unit or building selected.", True, COLOR_GRAY), (30, hud_y + 55))
            return

        first = selected_entities[0]
        info_x = 20
        title = self.font_large.render(f"{first.name} ({first.faction.value})", True, COLOR_WHITE)
        self.surface.blit(title, (info_x, hud_y + 12))

        hp_str = f"HP: {int(first.hp)} / {int(first.max_hp)}   Armor: {first.armor}"
        hp_img = self.font.render(hp_str, True, COLOR_HEALTH_GOOD if first.hp > first.max_hp * 0.5 else COLOR_HEALTH_MED)
        self.surface.blit(hp_img, (info_x, hud_y + 36))

        if isinstance(first, Unit):
            u_info = f"Atk: {int(first.attack_damage)}  Rng: {first.attack_range / TILE_SIZE:.1f}t  Spd: {first.speed / TILE_SIZE:.1f}"
            self.surface.blit(self.font.render(u_info, True, COLOR_WHITE), (info_x, hud_y + 58))
            st_str = f"Status: {first.state.name}   Domain: {first.domain.value}"
            self.surface.blit(self.font_small.render(st_str, True, COLOR_GRAY), (info_x, hud_y + 80))
        elif isinstance(first, Building):
            b_state = "Under Construction" if first.under_construction else "Operational"
            if first.under_construction:
                prog_pct = int((first.build_progress / first.build_time) * 100)
                b_state += f" ({prog_pct}%)"
            elif first.worker_yield:
                b_state += f" (Workers: {first.assigned_workers})"
            self.surface.blit(self.font_small.render(b_state, True, COLOR_GRAY), (info_x, hud_y + 56))

            if first.producible_units:
                if first.production_queue:
                    curr_u = first.production_queue[0]
                    req_t = UNIT_TYPES[curr_u]["build_time"]
                    pct = min(100, int((first.production_progress / req_t) * 100))
                    status_str = f"Creating: {curr_u} ({pct}%)"
                    self.surface.blit(self.font.render(status_str, True, (245, 210, 80)), (info_x, hud_y + 74))

                    bar_w = 180
                    bar_h = 6
                    bar_rect = pygame.Rect(info_x, hud_y + 94, bar_w, bar_h)
                    pygame.draw.rect(self.surface, (40, 44, 52), bar_rect, border_radius=2)
                    fill_w = max(0, int(bar_w * (first.production_progress / req_t)))
                    if fill_w > 0:
                        pygame.draw.rect(self.surface, (50, 200, 100), (info_x, hud_y + 94, fill_w, bar_h), border_radius=2)
                    pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, bar_rect, 1, border_radius=2)

                    q_str = f"Queue ({len(first.production_queue)}/5): {', '.join(first.production_queue)}"
                    self.surface.blit(self.font_small.render(q_str, True, COLOR_GRAY), (info_x, hud_y + 104))
                else:
                    self.surface.blit(self.font.render("Production: Idle", True, (160, 170, 180)), (info_x, hud_y + 74))
                    self.surface.blit(self.font_small.render("Queue: Empty (0/5)", True, COLOR_GRAY), (info_x, hud_y + 94))

        btn_start_x = 330
        btn_y = hud_y + 16

        if isinstance(first, Unit) and first.type_name == "Engineer" and first.faction == Faction.PLAYER:
            buildables = [
                ("Farm", "Farm\n20F 40S", "1"),
                ("Factory", "Factory\n30F 90S", "2"),
                ("Refinery", "Refinery\n20F 80S", "3"),
                ("Barracks", "Barracks\n30F 120S 20U", "4"),
                ("Shipyard", "Shipyard\n40F 170S 30U", "5"),
                ("HQ", "HQ\n60F 250S 50U", "6"),
            ]
            self._render_button_row(btn_start_x, btn_y, buildables, economy, mouse_pos, action_type="build")
        elif isinstance(first, Building) and first.faction == Faction.PLAYER and first.is_operational:
            trainables = []
            hotkeys = ["1", "2", "3", "4", "5", "6"]
            for idx, u_name in enumerate(first.producible_units):
                cost = UNIT_TYPES[u_name]["cost"]
                c_str = f"{cost[ResourceType.FOOD]}F {cost[ResourceType.STEEL]}S {cost[ResourceType.FUEL]}U"
                trainables.append((u_name, f"{u_name}\n{c_str}", hotkeys[idx] if idx < len(hotkeys) else ""))
            self._render_button_row(btn_start_x, btn_y, trainables, economy, mouse_pos, action_type="train")

    def _render_button_row(self, start_x: int, y: int, items, economy, mouse_pos, action_type: str):
        bx = start_x
        btn_w, btn_h = 110, 68
        for item_key, label, hotkey in items:
            rect = pygame.Rect(bx, y, btn_w, btn_h)
            cost = BUILDING_TYPES[item_key]["cost"] if action_type == "build" else UNIT_TYPES[item_key]["cost"]
            can_afford = economy.can_afford(cost)
            is_hover = rect.collidepoint(mouse_pos)
            bg_col = COLOR_BUTTON_HOVER if (is_hover and can_afford) else (COLOR_BUTTON_NORMAL if can_afford else COLOR_BUTTON_DISABLED)
            pygame.draw.rect(self.surface, bg_col, rect, border_radius=5)
            pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, rect, 1, border_radius=5)

            lines = label.split("\n")
            top_t = self.font.render(f"[{hotkey}] {lines[0]}", True, COLOR_BUTTON_TEXT if can_afford else COLOR_BUTTON_TEXT_MUTED)
            self.surface.blit(top_t, (bx + 6, y + 8))
            if len(lines) > 1:
                bot_t = self.font_small.render(lines[1], True, (200, 210, 100) if can_afford else COLOR_BUTTON_TEXT_MUTED)
                self.surface.blit(bot_t, (bx + 6, y + 36))

            self.hud_buttons.append({"rect": rect, "key": item_key, "action": action_type, "can_afford": can_afford, "hotkey": hotkey})
            bx += btn_w + 10

    def render_placement_ghost(self, building_type: Optional[str], game_map, mouse_pos: Tuple[int, int]):
        if not building_type:
            return
        b_data = BUILDING_TYPES[building_type]
        w, h = b_data["width_tiles"], b_data["height_tiles"]
        coastal = b_data.get("coastal_required", False)

        wx, wy = self.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        tx, ty = int(wx // TILE_SIZE), int(wy // TILE_SIZE)

        valid = game_map.can_place_building(tx, ty, w, h, coastal)
        ghost_color = (60, 220, 100, 120) if valid else (220, 60, 60, 120)
        border_color = (100, 255, 120) if valid else (255, 100, 100)

        if getattr(self.camera, "projection_mode", "isometric") == "topdown":
            sx, sy = self.camera.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
            next_sx, next_sy = self.camera.world_to_screen((tx + w) * TILE_SIZE, (ty + h) * TILE_SIZE)
            gw = max(2, next_sx - sx)
            gh = max(2, next_sy - sy)
            ghost_surface = pygame.Surface((gw, gh), pygame.SRCALPHA)
            ghost_surface.fill(ghost_color)
            self.surface.blit(ghost_surface, (sx, sy))
            pygame.draw.rect(self.surface, border_color, pygame.Rect(sx, sy, gw, gh), 1)
        else:
            p_top = self.camera.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
            p_right = self.camera.world_to_screen((tx + w) * TILE_SIZE, ty * TILE_SIZE)
            p_bottom = self.camera.world_to_screen((tx + w) * TILE_SIZE, (ty + h) * TILE_SIZE)
            p_left = self.camera.world_to_screen(tx * TILE_SIZE, (ty + h) * TILE_SIZE)
            poly = [p_top, p_right, p_bottom, p_left]

            min_x = min(p[0] for p in poly)
            max_x = max(p[0] for p in poly)
            min_y = min(p[1] for p in poly)
            max_y = max(p[1] for p in poly)
            gw = max(4, max_x - min_x + 1)
            gh = max(4, max_y - min_y + 1)
            ghost_surface = pygame.Surface((gw, gh), pygame.SRCALPHA)
            rel_poly = [(p[0] - min_x, p[1] - min_y) for p in poly]
            pygame.draw.polygon(ghost_surface, ghost_color, rel_poly)
            self.surface.blit(ghost_surface, (min_x, min_y))
            pygame.draw.polygon(self.surface, border_color, poly, 2)

    def render_selection_box(self, drag_start: Optional[Tuple[int, int]], current_pos: Tuple[int, int]):
        if not drag_start:
            return
        x1, y1 = drag_start
        x2, y2 = current_pos
        rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        fill_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill_surf.fill((50, 220, 80, 40))
        self.surface.blit(fill_surf, (rect.x, rect.y))
        pygame.draw.rect(self.surface, COLOR_SELECTION_BOX, rect, 1)
    def render_map_selection_modal(self, current_map_name: str, mouse_pos: Tuple[int, int]):
        """Renders an overlay modal to select and load named maps."""
        # Dim background
        dim_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 185))
        self.surface.blit(dim_surf, (0, 0))

        modal_w, modal_h = 680, 480
        modal_x = (self.screen_width - modal_w) // 2
        modal_y = (self.screen_height - modal_h) // 2
        self.modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        # Modal Window Frame
        pygame.draw.rect(self.surface, (28, 32, 40), self.modal_rect, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, self.modal_rect, 2, border_radius=8)

        # Header Title
        title_surf = self.font_large.render("SELECT THEATER OF WAR (MAP)", True, COLOR_WHITE)
        self.surface.blit(title_surf, (modal_x + 24, modal_y + 18))

        # Close [X] Button in top-right
        close_btn_rect = pygame.Rect(modal_x + modal_w - 38, modal_y + 16, 24, 24)
        is_close_hover = close_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(self.surface, (90, 40, 40) if is_close_hover else (50, 32, 36), close_btn_rect, border_radius=4)
        close_txt = self.font.render("X", True, COLOR_WHITE)
        self.surface.blit(close_txt, close_txt.get_rect(center=close_btn_rect.center))
        self.modal_close_rect = close_btn_rect

        # Subtitle
        sub_surf = self.font_small.render(
            "Select a map to load a new battle. Current simulation progress will reset.",
            True, COLOR_GRAY
        )
        self.surface.blit(sub_surf, (modal_x + 24, modal_y + 44))

        pygame.draw.line(self.surface, COLOR_PANEL_BORDER, (modal_x + 20, modal_y + 68), (modal_x + modal_w - 20, modal_y + 68), 1)

        # Map Cards with Pagination
        self.modal_buttons = []
        self.modal_page_buttons = []
        card_w = modal_w - 48
        card_h = 76
        PAGE_SIZE = 4

        map_list = list(MAP_PRESETS.items())
        total_pages = (len(map_list) + PAGE_SIZE - 1) // PAGE_SIZE

        if not hasattr(self, "map_modal_page") or self.map_modal_page >= total_pages or self.map_modal_page < 0:
            cur_idx = next((i for i, (k, _) in enumerate(map_list) if k == current_map_name), 0)
            self.map_modal_page = cur_idx // PAGE_SIZE

        start_idx = self.map_modal_page * PAGE_SIZE
        end_idx = min(len(map_list), start_idx + PAGE_SIZE)
        page_items = map_list[start_idx:end_idx]

        card_y = modal_y + 80
        for map_key, map_info in page_items:
            card_rect = pygame.Rect(modal_x + 24, card_y, card_w, card_h)
            is_active = (map_key == current_map_name)
            is_hover = card_rect.collidepoint(mouse_pos)

            if is_hover:
                bg_col = (48, 56, 70)
                border_col = COLOR_PLAYER_ACCENT
            elif is_active:
                bg_col = (34, 46, 60)
                border_col = COLOR_PLAYER
            else:
                bg_col = (34, 38, 46)
                border_col = (58, 64, 76)

            pygame.draw.rect(self.surface, bg_col, card_rect, border_radius=6)
            pygame.draw.rect(self.surface, border_col, card_rect, 2 if (is_hover or is_active) else 1, border_radius=6)

            # Map Name & Tag Badge
            name_surf = self.font_large.render(map_info["name"], True, COLOR_WHITE)
            self.surface.blit(name_surf, (card_rect.x + 14, card_rect.y + 10))

            tag_str = map_info.get("tag", "")
            tag_surf = self.font_small.render(f"[{tag_str}]", True, (240, 205, 90))
            self.surface.blit(tag_surf, (card_rect.x + 20 + name_surf.get_width(), card_rect.y + 13))

            if is_active:
                active_badge = self.font_small.render("ACTIVE MAP", True, COLOR_HEALTH_GOOD)
                self.surface.blit(active_badge, (card_rect.right - active_badge.get_width() - 14, card_rect.y + 13))

            # Description
            desc_str = map_info.get("description", "")
            desc_surf = self.font_small.render(desc_str, True, (190, 195, 205))
            self.surface.blit(desc_surf, (card_rect.x + 14, card_rect.y + 35))

            # Land Connection status
            if map_info.get("land_connected", False):
                land_ind = self.font_small.render("Direct Land Connection: YES (Land Weapons Testable)", True, (100, 220, 140))
            else:
                land_ind = self.font_small.render("Direct Land Connection: NO (Water Channel)", True, (140, 180, 230))
            self.surface.blit(land_ind, (card_rect.x + 14, card_rect.y + 54))

            self.modal_buttons.append({"rect": card_rect, "map_name": map_key})
            card_y += card_h + 10

        # Pagination controls
        if total_pages > 1:
            nav_y = modal_y + modal_h - 44
            btn_prev_rect = pygame.Rect(modal_x + 24, nav_y, 110, 26)
            btn_next_rect = pygame.Rect(modal_x + modal_w - 134, nav_y, 110, 26)

            has_prev = self.map_modal_page > 0
            has_next = self.map_modal_page < total_pages - 1

            is_prev_h = has_prev and btn_prev_rect.collidepoint(mouse_pos)
            is_next_h = has_next and btn_next_rect.collidepoint(mouse_pos)

            prev_bg = COLOR_BUTTON_HOVER if is_prev_h else (COLOR_BUTTON_NORMAL if has_prev else COLOR_BUTTON_DISABLED)
            next_bg = COLOR_BUTTON_HOVER if is_next_h else (COLOR_BUTTON_NORMAL if has_next else COLOR_BUTTON_DISABLED)

            pygame.draw.rect(self.surface, prev_bg, btn_prev_rect, border_radius=4)
            pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, btn_prev_rect, 1, border_radius=4)
            prev_txt = self.font_small.render("< Previous", True, COLOR_BUTTON_TEXT if has_prev else COLOR_BUTTON_TEXT_MUTED)
            self.surface.blit(prev_txt, prev_txt.get_rect(center=btn_prev_rect.center))

            pygame.draw.rect(self.surface, next_bg, btn_next_rect, border_radius=4)
            pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, btn_next_rect, 1, border_radius=4)
            next_txt = self.font_small.render("Next Page >", True, COLOR_BUTTON_TEXT if has_next else COLOR_BUTTON_TEXT_MUTED)
            self.surface.blit(next_txt, next_txt.get_rect(center=btn_next_rect.center))

            page_info = f"Page {self.map_modal_page + 1} of {total_pages}"
            page_surf = self.font_small.render(page_info, True, COLOR_WHITE)
            self.surface.blit(page_surf, page_surf.get_rect(center=(modal_x + modal_w // 2, nav_y + 13)))

            if has_prev:
                self.modal_page_buttons.append({"rect": btn_prev_rect, "page_delta": -1})
            if has_next:
                self.modal_page_buttons.append({"rect": btn_next_rect, "page_delta": 1})

        # Footer Notice
        footer_txt = self.font_small.render("Click a map card to load | Click outside or press [ESC] to cancel", True, COLOR_GRAY)
        self.surface.blit(footer_txt, (modal_x + 24, modal_y + modal_h - (62 if total_pages > 1 else 26)))

    def render_minimap(self, game_map, buildings, units):
        mm_w = 160
        mm_h = 120
        mm_x = self.screen_width - mm_w - 12
        mm_y = self.screen_height - mm_h - 10
        self.minimap_rect = pygame.Rect(mm_x, mm_y, mm_w, mm_h)

        map_name = getattr(game_map, "map_name", "")
        if (
            self.minimap_terrain_surf is None
            or self.cached_minimap_map_name != map_name
            or self.minimap_terrain_surf.get_size() != (mm_w, mm_h)
        ):
            self.cached_minimap_map_name = map_name
            self.minimap_terrain_surf = pygame.Surface((mm_w, mm_h))
            self.minimap_terrain_surf.fill((20, 20, 24))
            for ty in range(game_map.height):
                for tx in range(game_map.width):
                    tile = game_map.tiles[ty][tx]
                    if tile == TerrainType.WATER:
                        col = COLOR_WATER
                    elif tile == TerrainType.COAST:
                        col = COLOR_COAST
                    else:
                        col = COLOR_GRASS
                    px = int(tx * mm_w / game_map.width)
                    py = int(ty * mm_h / game_map.height)
                    pw = max(1, int((tx + 1) * mm_w / game_map.width) - px)
                    ph = max(1, int((ty + 1) * mm_h / game_map.height) - py)
                    pygame.draw.rect(self.minimap_terrain_surf, col, (px, py, pw, ph))

        self.surface.blit(self.minimap_terrain_surf, (mm_x, mm_y))

        # Buildings
        for bld in buildings:
            if not bld.is_alive:
                continue
            bx = mm_x + int((bld.tile_x / game_map.width) * mm_w)
            by = mm_y + int((bld.tile_y / game_map.height) * mm_h)
            bw = max(2, int((bld.width_tiles / game_map.width) * mm_w))
            bh = max(2, int((bld.height_tiles / game_map.height) * mm_h))
            b_col = COLOR_PLAYER_ACCENT if bld.faction == Faction.PLAYER else COLOR_ENEMY_ACCENT
            pygame.draw.rect(self.surface, b_col, (bx, by, bw, bh))

        # Units
        total_world_w = game_map.width * TILE_SIZE
        total_world_h = game_map.height * TILE_SIZE
        for unit in units:
            if not unit.is_alive:
                continue
            ux = mm_x + int((unit.x / total_world_w) * mm_w)
            uy = mm_y + int((unit.y / total_world_h) * mm_h)
            if unit.is_selected:
                u_col = (255, 255, 255)
            elif unit.faction == Faction.PLAYER:
                u_col = COLOR_PLAYER
            else:
                u_col = COLOR_ENEMY
            pygame.draw.circle(self.surface, u_col, (ux, uy), 2)

        # Main viewport rectangle
        cam_w = min(self.screen_width / self.camera.zoom, total_world_w)
        cam_h = min(max(100, (self.screen_height - 140) / self.camera.zoom), total_world_h)

        if getattr(self.camera, "projection_mode", "isometric") == "isometric":
            total_proj_w = (game_map.width + game_map.height) * TILE_SIZE
            total_proj_h = (game_map.width + game_map.height) * TILE_SIZE * 0.5
            vx = mm_x + int((self.camera.x / total_proj_w) * mm_w)
            vy = mm_y + int((self.camera.y / total_proj_h) * mm_h)
        else:
            vx = mm_x + int((self.camera.x / total_world_w) * mm_w)
            vy = mm_y + int((self.camera.y / total_world_h) * mm_h)

        vw = max(4, int((cam_w / total_world_w) * mm_w))
        vh = max(4, int((cam_h / total_world_h) * mm_h))

        vx = max(mm_x, min(mm_x + mm_w - 4, vx))
        vy = max(mm_y, min(mm_y + mm_h - 4, vy))
        vw = min(mm_x + mm_w - vx, vw)
        vh = min(mm_y + mm_h - vy, vh)

        self.minimap_viewport_rect = pygame.Rect(vx, vy, vw, vh)
        pygame.draw.rect(self.surface, (255, 255, 255), self.minimap_viewport_rect, 1)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, self.minimap_rect, 1, border_radius=2)

    def render_pause_modal(
        self,
        mouse_pos: Tuple[int, int],
        show_save: bool = False,
        show_load: bool = False,
        save_name_input: str = "",
        selected_load_name: str = "",
        existing_saves: Optional[List[str]] = None,
        status_msg: str = "",
    ):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 12, 16, 190))
        self.surface.blit(overlay, (0, 0))

        self.pause_buttons.clear()
        self.save_buttons.clear()
        self.save_items.clear()
        self.load_buttons.clear()
        self.load_items.clear()

        if show_save:
            self._render_save_dialog(mouse_pos, save_name_input, existing_saves, status_msg)
        elif show_load:
            self._render_load_dialog(mouse_pos, selected_load_name, existing_saves, status_msg)
        else:
            self._render_pause_main(mouse_pos)

    def _render_pause_main(self, mouse_pos: Tuple[int, int]):
        modal_w = 340
        modal_h = 330
        modal_x = (self.screen_width - modal_w) // 2
        modal_y = (self.screen_height - modal_h) // 2
        panel_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        pygame.draw.rect(self.surface, COLOR_PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, panel_rect, 2, border_radius=8)

        title_surf = self.font_large.render("GAME PAUSED", True, COLOR_WHITE)
        self.surface.blit(title_surf, title_surf.get_rect(center=(modal_x + modal_w // 2, modal_y + 32)))

        sub_surf = self.font_small.render("Simulation is frozen", True, COLOR_GRAY)
        self.surface.blit(sub_surf, sub_surf.get_rect(center=(modal_x + modal_w // 2, modal_y + 54)))

        pygame.draw.line(self.surface, COLOR_PANEL_BORDER, (modal_x + 20, modal_y + 70), (modal_x + modal_w - 20, modal_y + 70), 1)

        btn_w = 230
        btn_h = 40
        btn_x = modal_x + (modal_w - btn_w) // 2
        start_btn_y = modal_y + 86
        gap = 12

        buttons_meta = [
            ("Resume", "resume", "resume"),
            ("Save", "save", "save"),
            ("Load a saved game", "load", "load"),
            ("Quit", "quit", "quit"),
        ]

        for idx, (label, action, key) in enumerate(buttons_meta):
            by = start_btn_y + idx * (btn_h + gap)
            rect = pygame.Rect(btn_x, by, btn_w, btn_h)
            is_hover = rect.collidepoint(mouse_pos)
            bg_col = COLOR_BUTTON_HOVER if is_hover else COLOR_BUTTON_NORMAL
            border_col = COLOR_PLAYER_ACCENT if is_hover else COLOR_PANEL_BORDER

            pygame.draw.rect(self.surface, bg_col, rect, border_radius=6)
            pygame.draw.rect(self.surface, border_col, rect, 2 if is_hover else 1, border_radius=6)

            txt_surf = self.font.render(label, True, COLOR_WHITE if is_hover else COLOR_BUTTON_TEXT)
            self.surface.blit(txt_surf, txt_surf.get_rect(center=rect.center))

            self.pause_buttons.append({
                "rect": rect,
                "action": action,
                "label": label,
                "text": label,
                "key": key,
            })

    def _render_save_dialog(
        self,
        mouse_pos: Tuple[int, int],
        save_name_input: str,
        existing_saves: Optional[List[str]],
        status_msg: str,
    ):
        modal_w = 480
        modal_h = 420
        modal_x = (self.screen_width - modal_w) // 2
        modal_y = (self.screen_height - modal_h) // 2
        panel_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        pygame.draw.rect(self.surface, COLOR_PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, panel_rect, 2, border_radius=8)

        title_surf = self.font_large.render("SAVE GAME PROGRESS", True, COLOR_WHITE)
        self.surface.blit(title_surf, title_surf.get_rect(center=(modal_x + modal_w // 2, modal_y + 30)))

        sub_surf = self.font_small.render("Type a save name or select an existing save file to overwrite", True, COLOR_GRAY)
        self.surface.blit(sub_surf, sub_surf.get_rect(center=(modal_x + modal_w // 2, modal_y + 54)))

        pygame.draw.line(self.surface, COLOR_PANEL_BORDER, (modal_x + 20, modal_y + 70), (modal_x + modal_w - 20, modal_y + 70), 1)

        input_label = self.font_small.render("Save File Name:", True, COLOR_WHITE)
        self.surface.blit(input_label, (modal_x + 30, modal_y + 82))

        input_rect = pygame.Rect(modal_x + 30, modal_y + 102, modal_w - 60, 36)
        self.save_input_rect = input_rect
        pygame.draw.rect(self.surface, (20, 24, 30), input_rect, border_radius=4)
        pygame.draw.rect(self.surface, COLOR_PLAYER_ACCENT, input_rect, 2, border_radius=4)

        display_input = save_name_input if save_name_input else "quicksave"
        in_color = COLOR_WHITE if save_name_input else COLOR_GRAY
        in_surf = self.font.render(display_input, True, in_color)
        self.surface.blit(in_surf, (input_rect.x + 10, input_rect.y + 8))

        list_title = self.font_small.render("Existing Saves (Click to select/overwrite):", True, COLOR_GRAY)
        self.surface.blit(list_title, (modal_x + 30, modal_y + 148))

        list_y = modal_y + 170
        saves_to_show = (existing_saves or [])[:4]
        if not saves_to_show:
            no_save_txt = self.font_small.render("No existing saves found.", True, (100, 105, 115))
            self.surface.blit(no_save_txt, (modal_x + 35, list_y + 10))
        else:
            for save_fn in saves_to_show:
                item_rect = pygame.Rect(modal_x + 30, list_y, modal_w - 60, 30)
                is_h = item_rect.collidepoint(mouse_pos)
                is_cur = (save_fn == save_name_input)
                bg = (45, 55, 70) if is_h else ((35, 45, 60) if is_cur else (25, 29, 36))
                border = COLOR_PLAYER if is_cur else ((70, 80, 95) if is_h else (45, 50, 60))
                pygame.draw.rect(self.surface, bg, item_rect, border_radius=4)
                pygame.draw.rect(self.surface, border, item_rect, 1, border_radius=4)

                fn_surf = self.font.render(save_fn, True, COLOR_WHITE)
                self.surface.blit(fn_surf, (item_rect.x + 10, item_rect.y + 6))
                tag_surf = self.font_small.render(".json", True, COLOR_GRAY)
                self.surface.blit(tag_surf, (item_rect.x + 10 + fn_surf.get_width() + 4, item_rect.y + 8))

                self.save_items.append({"rect": item_rect, "save_name": save_fn})
                list_y += 34

        if status_msg:
            stat_surf = self.font_small.render(status_msg, True, COLOR_HEALTH_GOOD)
            self.surface.blit(stat_surf, (modal_x + 30, modal_y + 320))

        btn_save_rect = pygame.Rect(modal_x + 30, modal_y + 355, 195, 40)
        btn_back_rect = pygame.Rect(modal_x + modal_w - 225, modal_y + 355, 195, 40)

        is_save_h = btn_save_rect.collidepoint(mouse_pos)
        is_back_h = btn_back_rect.collidepoint(mouse_pos)

        pygame.draw.rect(self.surface, (40, 100, 50) if is_save_h else (30, 75, 40), btn_save_rect, border_radius=5)
        pygame.draw.rect(self.surface, COLOR_HEALTH_GOOD if is_save_h else (50, 140, 70), btn_save_rect, 1, border_radius=5)
        save_lbl = self.font.render("Save / Overwrite", True, COLOR_WHITE)
        self.surface.blit(save_lbl, save_lbl.get_rect(center=btn_save_rect.center))

        pygame.draw.rect(self.surface, COLOR_BUTTON_HOVER if is_back_h else COLOR_BUTTON_NORMAL, btn_back_rect, border_radius=5)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, btn_back_rect, 1, border_radius=5)
        back_lbl = self.font.render("Back to Menu", True, COLOR_BUTTON_TEXT)
        self.surface.blit(back_lbl, back_lbl.get_rect(center=btn_back_rect.center))

        self.save_buttons.append({"rect": btn_save_rect, "action": "confirm_save", "label": "Save", "text": "Save"})
        self.save_buttons.append({"rect": btn_back_rect, "action": "back", "label": "Back", "text": "Back"})

    def _render_load_dialog(
        self,
        mouse_pos: Tuple[int, int],
        selected_load_name: str,
        existing_saves: Optional[List[str]],
        status_msg: str,
    ):
        modal_w = 480
        modal_h = 420
        modal_x = (self.screen_width - modal_w) // 2
        modal_y = (self.screen_height - modal_h) // 2
        panel_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        pygame.draw.rect(self.surface, COLOR_PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, panel_rect, 2, border_radius=8)

        title_surf = self.font_large.render("LOAD A SAVED GAME", True, COLOR_WHITE)
        self.surface.blit(title_surf, title_surf.get_rect(center=(modal_x + modal_w // 2, modal_y + 30)))

        sub_surf = self.font_small.render("Select a saved game file to resume progress", True, COLOR_GRAY)
        self.surface.blit(sub_surf, sub_surf.get_rect(center=(modal_x + modal_w // 2, modal_y + 54)))

        pygame.draw.line(self.surface, COLOR_PANEL_BORDER, (modal_x + 20, modal_y + 70), (modal_x + modal_w - 20, modal_y + 70), 1)

        list_title = self.font_small.render("Available Saves (Click to select):", True, COLOR_WHITE)
        self.surface.blit(list_title, (modal_x + 30, modal_y + 84))

        list_y = modal_y + 108
        saves_to_show = (existing_saves or [])[:5]
        if not saves_to_show:
            no_save_txt = self.font_small.render("No existing save files found in saves/ folder.", True, (120, 125, 135))
            self.surface.blit(no_save_txt, (modal_x + 35, list_y + 20))
        else:
            for save_fn in saves_to_show:
                item_rect = pygame.Rect(modal_x + 30, list_y, modal_w - 60, 32)
                is_h = item_rect.collidepoint(mouse_pos)
                is_cur = (save_fn == selected_load_name)
                bg = (45, 55, 70) if is_h else ((35, 45, 60) if is_cur else (25, 29, 36))
                border = COLOR_PLAYER if is_cur else ((70, 80, 95) if is_h else (45, 50, 60))
                pygame.draw.rect(self.surface, bg, item_rect, border_radius=4)
                pygame.draw.rect(self.surface, border, item_rect, 2 if is_cur else 1, border_radius=4)

                fn_surf = self.font.render(save_fn, True, COLOR_WHITE)
                self.surface.blit(fn_surf, (item_rect.x + 12, item_rect.y + 7))
                tag_surf = self.font_small.render(".json", True, COLOR_GRAY)
                self.surface.blit(tag_surf, (item_rect.x + 12 + fn_surf.get_width() + 4, item_rect.y + 9))

                if is_cur:
                    sel_badge = self.font_small.render("SELECTED", True, COLOR_HEALTH_GOOD)
                    self.surface.blit(sel_badge, (item_rect.right - sel_badge.get_width() - 12, item_rect.y + 9))

                self.load_items.append({"rect": item_rect, "save_name": save_fn})
                list_y += 36

        if status_msg:
            stat_surf = self.font_small.render(status_msg, True, COLOR_HEALTH_GOOD)
            self.surface.blit(stat_surf, (modal_x + 30, modal_y + 326))

        # Bottom Action Buttons
        btn_load_rect = pygame.Rect(modal_x + 30, modal_y + 355, 195, 40)
        btn_back_rect = pygame.Rect(modal_x + modal_w - 225, modal_y + 355, 195, 40)

        can_load = bool(selected_load_name)
        is_load_h = btn_load_rect.collidepoint(mouse_pos) and can_load
        is_back_h = btn_back_rect.collidepoint(mouse_pos)

        load_bg = (40, 100, 50) if is_load_h else ((30, 75, 40) if can_load else (35, 38, 44))
        load_border = COLOR_HEALTH_GOOD if is_load_h else ((50, 140, 70) if can_load else (50, 52, 58))
        load_text_col = COLOR_WHITE if can_load else COLOR_BUTTON_TEXT_MUTED

        pygame.draw.rect(self.surface, load_bg, btn_load_rect, border_radius=5)
        pygame.draw.rect(self.surface, load_border, btn_load_rect, 1, border_radius=5)
        load_lbl = self.font.render("Load Game", True, load_text_col)
        self.surface.blit(load_lbl, load_lbl.get_rect(center=btn_load_rect.center))

        pygame.draw.rect(self.surface, COLOR_BUTTON_HOVER if is_back_h else COLOR_BUTTON_NORMAL, btn_back_rect, border_radius=5)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, btn_back_rect, 1, border_radius=5)
        back_lbl = self.font.render("Back to Menu", True, COLOR_BUTTON_TEXT)
        self.surface.blit(back_lbl, back_lbl.get_rect(center=btn_back_rect.center))

        self.load_buttons.append({"rect": btn_load_rect, "action": "confirm_load", "label": "Load Game", "can_load": can_load})
        self.load_buttons.append({"rect": btn_back_rect, "action": "back", "label": "Back"})


