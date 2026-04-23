#!/usr/bin/env python3
"""
Visual Exact Upgrade – Full Decode/Mode7/Anim.
Level1.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from PIL import Image
from app.station import Station  # decode_snes_sprite
from extractors.world_asset_extractor import RomAssetExtractor

# Fix decode + anim
extractor = RomAssetExtractor()
station = Station()  # For decode

for sprite in ['mario_idle', 'fox_idle']:  # Sample
    path = extractor.extract_from_catalog(sprite)  # Full pixels
    if path:
        # Anim frames (delta)
        for frame in range(8):
            delta_addr = sprite_addr + frame * 0x100
            frame_img = station.decode_snes_sprite(bank, delta_addr)  # Full
            frame_img.save(f"assets/sprites/{sprite}_f{frame}.png")
        print(f"Exact anim: {sprite} 8 frames")

# Mode7 tilemap (SMW 0x3D800)
tilemap_bin = Path("assets/backgrounds/forest_zelda.bin").read_bytes()
mode7_surf = station._render_mode7(tilemap_bin)  # Rotate/scale
mode7_surf.save("assets/backgrounds/mode7_forest.png")
print("Mode7 ready")

print("Level1 Visual Exact Complete")
