"""
Asset Manager for Unit and Building Sprites.
Supports transparent PNG and high-resolution JPG sprites with in-memory downscaling,
corner-connected white background keying, bounding-box cropping, zoom caching,
8-way directional movement, split hull/turret layers, and procedural fallback.
Original image files on disk are never modified.
"""
import math
import os
import pygame
from typing import Optional, Tuple, Dict, List

# Target 1x footprint bounding box sizes in pixels (matching in-game isometric tile grids)
BUILDING_TARGET_SIZES: Dict[str, Tuple[int, int]] = {
    "hq": (192, 220),       # 3x3 footprint (ground width = 192), height accommodates tall rooftop antennas
    "farm": (128, 128),     # 2x2 footprint
    "factory": (160, 160),  # 2.5x2.5 footprint
    "refinery": (128, 140), # 2x2 footprint
    "barracks": (192, 160), # 3x3 footprint
    "shipyard": (192, 160), # 3x3 footprint
}

UNIT_TARGET_SIZES: Dict[str, Tuple[int, int]] = {
    "engineer": (48, 48),
    "foot_soldier": (48, 48),
    "tank": (64, 64),
    "cannon": (64, 64),
    "torpedo_boat": (60, 48),
    "destroyer": (96, 72),
    "battleship": (256, 192),
}

SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
MIRROR_MAP = {"sw": "se", "w": "e", "nw": "ne"}
MAX_CACHE_ENTRIES = 300


class AssetManager:
    def __init__(self, assets_dir: str = "assets/sprites"):
        self.assets_dir = assets_dir
        self.raw_images: Dict[str, pygame.Surface] = {}
        self.base_scales: Dict[str, float] = {}
        self.scaled_cache: Dict[Tuple[str, float], pygame.Surface] = {}
        self._load_available_sprites()

    def _load_available_sprites(self):
        """Discovers and loads image files. Pre-normalizes in memory without altering disk files."""
        if not os.path.exists(self.assets_dir):
            return

        candidates: Dict[str, str] = {}
        for root, _, files in os.walk(self.assets_dir):
            for file in sorted(files):
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXTS:
                    key = os.path.splitext(file)[0].lower()
                    rel_path = os.path.join(root, file)
                    if key in candidates:
                        prev_ext = os.path.splitext(candidates[key])[1].lower()
                        if ext == ".png" and prev_ext != ".png":
                            candidates[key] = rel_path
                    else:
                        candidates[key] = rel_path

        for key, rel_path in candidates.items():
            try:
                raw = pygame.image.load(rel_path)
                if pygame.display.get_surface() is not None:
                    try:
                        raw = raw.convert_alpha()
                    except Exception:
                        pass
                target_box = self._get_target_box_for_key(key)
                master, base_scale = self._normalize_image_in_memory(raw, target_box)
                self.raw_images[key] = master
                self.base_scales[key] = base_scale
            except Exception:
                pass

    def _get_target_box_for_key(self, key: str) -> Optional[Tuple[int, int]]:
        """Maps an image key to its expected 1x in-game screen footprint."""
        for b_name, size in BUILDING_TARGET_SIZES.items():
            if key == b_name or key.startswith(f"{b_name}_"):
                return size

        for u_name, size in UNIT_TARGET_SIZES.items():
            if key == u_name or key.startswith(f"{u_name}_"):
                return size

        return None

    def _normalize_image_in_memory(
        self,
        raw: pygame.Surface,
        target_size: Optional[Tuple[int, int]]
    ) -> Tuple[pygame.Surface, float]:
        """
        Processes a raw image in memory:
        1. Downscales oversized images to a safe working resolution immediately.
        2. Keys out solid white / light backgrounds from corners (for JPGs) preserving internal white details.
        3. Auto-crops transparent borders.
        4. Sizes into a Hi-DPI 2x master buffer with base_scale = 0.5 (or preserves original size if already small).
        """
        w, h = raw.get_size()
        # Step 1: Pre-downscale huge multi-megapixel images to working buffer (max 768px)
        if max(w, h) > 768:
            s = 768.0 / float(max(w, h))
            work = pygame.transform.smoothscale(raw, (max(8, int(w * s)), max(8, int(h * s))))
        else:
            work = raw.copy()

        # Step 2: Key out solid white backgrounds if all 4 corners are near-white
        mw, mh = work.get_size()
        rgba = pygame.Surface((mw, mh), pygame.SRCALPHA)
        rgba.blit(work, (0, 0))

        corners = [
            rgba.get_at((0, 0)),
            rgba.get_at((mw - 1, 0)),
            rgba.get_at((0, mh - 1)),
            rgba.get_at((mw - 1, mh - 1)),
        ]
        is_near_white_corners = all(
            c.r >= 230 and c.g >= 230 and c.b >= 230 and (len(c) < 4 or c.a >= 200)
            for c in corners
        )

        if is_near_white_corners:
            try:
                bg_candidates = pygame.mask.from_threshold(rgba, (255, 255, 255, 255), (28, 28, 28, 255))
                outer_bg = pygame.Mask((mw, mh))
                # Seed from all borders of the image
                for x in range(0, mw, 4):
                    if bg_candidates.get_at((x, 0)):
                        outer_bg.draw(bg_candidates.connected_component((x, 0)), (0, 0))
                    if bg_candidates.get_at((x, mh - 1)):
                        outer_bg.draw(bg_candidates.connected_component((x, mh - 1)), (0, 0))
                for y in range(0, mh, 4):
                    if bg_candidates.get_at((0, y)):
                        outer_bg.draw(bg_candidates.connected_component((0, y)), (0, 0))
                    if bg_candidates.get_at((mw - 1, y)):
                        outer_bg.draw(bg_candidates.connected_component((mw - 1, y)), (0, 0))

                # Clear enclosed sky pockets trapped between antennas/wires in upper 40% of sprite
                rem = bg_candidates.copy()
                rem.erase(outer_bg, (0, 0))
                for r in rem.get_bounding_rects():
                    if r.centery < mh * 0.4 and (r.w < mw * 0.3 and r.h < mh * 0.35):
                        outer_bg.draw(rem.connected_component((r.centerx, r.centery)), (0, 0))

                fg = outer_bg.copy()
                fg.invert()
                clean = fg.to_surface(setsurface=rgba, unsetcolor=(0, 0, 0, 0))
                rects = fg.get_bounding_rects()
                if rects:
                    union_r = rects[0].unionall(rects[1:])
                    work = clean.subsurface(union_r).copy()
                else:
                    work = clean
            except Exception:
                pass

        # Step 3: Determine footprint scale
        cw, ch = work.get_size()
        if target_size is not None:
            tw, th = target_size
            if cw > tw or ch > th:
                # High-res image: scale to 2x Hi-DPI master buffer for crisp close-up zooming
                scale_1x = min(tw / float(cw), th / float(ch))
                base_w = max(8, int(cw * scale_1x))
                base_h = max(8, int(ch * scale_1x))
                master = pygame.transform.smoothscale(work, (base_w * 2, base_h * 2))
                return master, 0.5
            else:
                # Already within 1x target size
                return work, 1.0

        # General fallback if no explicit target size
        if max(cw, ch) > 256:
            s_gen = 256.0 / float(max(cw, ch))
            gen_w = max(8, int(cw * s_gen))
            gen_h = max(8, int(ch * s_gen))
            return pygame.transform.smoothscale(work, (gen_w, gen_h)), 1.0

        return work, 1.0


    def get_building_sprite(self, type_name: str, zoom: float) -> Optional[pygame.Surface]:
        """Returns scaled sprite for a building, or None if no image exists."""
        key = type_name.lower().replace(" ", "_")
        return self._get_scaled(key, zoom)

    def get_unit_sprite(
        self,
        type_name: str,
        zoom: float,
        direction: Optional[str] = None
    ) -> Optional[pygame.Surface]:
        """
        Returns scaled sprite for a unit.
        If direction is given, looks for '<unit>_<dir>' first with automatic
        horizontal mirror flipping (e.g. 'sw' flipped from 'se') before falling
        back to base '<unit>'.
        """
        base_key = type_name.lower().replace(" ", "_")

        if direction:
            dir_key = f"{base_key}_{direction.lower()}"
            sprite = self._get_scaled_with_mirror(dir_key, base_key, direction.lower(), zoom)
            if sprite is not None:
                return sprite

        return self._get_scaled(base_key, zoom)

    def get_unit_parts(
        self,
        type_name: str,
        zoom: float,
        hull_dir: Optional[str] = None,
        turret_dir: Optional[str] = None
    ) -> Tuple[Optional[pygame.Surface], Optional[pygame.Surface]]:
        """
        Returns a tuple of (hull_sprite, turret_sprite) for split turret units.
        Returns (None, None) if neither part exists.
        """
        base_key = type_name.lower().replace(" ", "_")

        hull_sprite: Optional[pygame.Surface] = None
        if hull_dir:
            hull_key = f"{base_key}_hull_{hull_dir.lower()}"
            hull_sprite = self._get_scaled_with_mirror(hull_key, f"{base_key}_hull", hull_dir.lower(), zoom)
        if hull_sprite is None:
            hull_sprite = self._get_scaled(f"{base_key}_hull", zoom)

        turret_sprite: Optional[pygame.Surface] = None
        if turret_dir:
            turret_key = f"{base_key}_turret_{turret_dir.lower()}"
            turret_sprite = self._get_scaled_with_mirror(turret_key, f"{base_key}_turret", turret_dir.lower(), zoom)
        if turret_sprite is None:
            turret_sprite = self._get_scaled(f"{base_key}_turret", zoom)

        return hull_sprite, turret_sprite

    def _get_scaled_with_mirror(
        self,
        full_key: str,
        prefix_key: str,
        direction: str,
        zoom: float
    ) -> Optional[pygame.Surface]:
        """Checks for direct key, then tries mirroring counterpart direction before failing."""
        if full_key in self.raw_images:
            return self._get_scaled(full_key, zoom)

        if direction in MIRROR_MAP:
            src_dir = MIRROR_MAP[direction]
            src_key = f"{prefix_key}_{src_dir}"
            if src_key in self.raw_images:
                src_surf = self.raw_images[src_key]
                flipped = pygame.transform.flip(src_surf, True, False)
                self.raw_images[full_key] = flipped
                self.base_scales[full_key] = self.base_scales.get(src_key, 1.0)
                return self._get_scaled(full_key, zoom)

        return None

    def _get_scaled(self, key: str, zoom: float) -> Optional[pygame.Surface]:
        if key not in self.raw_images:
            return None

        # Quantize zoom to 2 decimal places for cache hits
        q_zoom = round(zoom, 2)
        cache_key = (key, q_zoom)
        if cache_key in self.scaled_cache:
            return self.scaled_cache[cache_key]

        raw = self.raw_images[key]
        b_scale = self.base_scales.get(key, 1.0)
        eff_scale = b_scale * q_zoom
        nw = max(8, int(raw.get_width() * eff_scale))
        nh = max(8, int(raw.get_height() * eff_scale))
        scaled = pygame.transform.smoothscale(raw, (nw, nh))

        # Cap cache size to avoid unbounded memory usage
        if len(self.scaled_cache) >= MAX_CACHE_ENTRIES:
            self.scaled_cache.clear()

        self.scaled_cache[cache_key] = scaled
        return scaled

