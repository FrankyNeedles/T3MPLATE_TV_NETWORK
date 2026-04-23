#!/usr/bin/env python3
"""
Level1: Animation Frames (idle/walk deltas, 8-frame sets).
Uses ANIMATION_POSES pattern from codebase.
Sample 5 ROMs.
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from PIL import Image
from extractors.world_asset_extractor import RomAssetExtractor as WorldAssetExtractor
from app.snes_scene_engine import ANIMATION_POSES  # Pose deltas

extractor = WorldAssetExtractor()
rom_ids = ['super_mario_world', 'zelda_lttp', 'chrono_trigger', 'donkey_kong_country', 'star_fox']
manifest = []
ANIM_POSES = ANIMATION_POSES  # From codebase

for rom_id in rom_ids:
    rom = extractor.scanner.find_game_rom(rom_id)
    if not rom:
        print(f"ROM skip: {rom_id}")
        continue
    for char_key in ['mario_idle', 'link_idle', 'crono_idle']:  # Sample chars
        poses = ANIM_POSES
        base_addr = CHARACTER_SPRITES.get(char_key, {}).get('offset', 0)
        for pose in ['idle', 'walk']:
            delta = poses[pose]['offset_delta']
            addr = base_addr + delta
            for frame in range(poses[pose]['frames']):  # 2-4 frames
                f_addr = addr + frame * 0x100  # Frame stride
                img = extractor._extractor.extract_sprite(f_addr, (32, 32))
                out_path = Path("assets/sprites") / f"{char_key}_{pose}_f{frame}.png"
                img.save(out_path)
                manifest.append({
                    'asset_id': f'{char_key}_{pose}_f{frame}_{rom_id}',
                    'rom': rom_id,
                    'addr': hex(f_addr),
                    'size': (32, 32),
                    'path': str(out_path)
                })
                print(f"Anim: {out_path}")

with open('assets/manifests/anim_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"Level1 Anim: {len(manifest)} frames extracted")
