#!/usr/bin/env python3
"""
Level1: Player Characters (bank 0x02).
Extract ~80 TV-ready chars for Gary.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from PIL import Image
from extractors.world_asset_extractor import WorldAssetExtractor

extractor = WorldAssetExtractor()
player_sprites = {k: v for k, v in CHARACTER_SPRITES.items() if v['bank'] == 0x02 or 'idle' in k.lower()}
manifest = []

for key in player_sprites:
    path = extractor.extract_character_sprite(key)
    if path:
        manifest.append({'key': key, 'path': str(path), 'size': path.stat().st_size})

with open('assets/sprites/level1_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"Level1 Complete: {len(manifest)} player chars extracted")
