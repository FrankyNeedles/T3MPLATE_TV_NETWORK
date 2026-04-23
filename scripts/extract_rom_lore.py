#!/usr/bin/env python3
"""
Extract ROM Lore – Strings/Music/Enemies for Gary World-Building.
Lightweight JSON/ROM (~1KB).
"""

import re
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from typing import Dict, List
import struct
from extractors.snes_rom_hacker import SNESROMTools

ROM_DIR = Path("ROM_SOURCE/unzipped")
LORE_DIR = Path("assets/rom_lore")
LORE_DIR.mkdir(exist_ok=True, parents=True)

def extract_lore(rom_path: Path) -> Dict:
    """Extract strings/music/enemies."""
    title = rom_path.stem.replace(" (USA)", "").replace(" ", "_")[:50]
    data = rom_path.read_bytes()
    
    lore = {"game": title, "strings": [], "music": [], "enemies": [], "items": []}
    
    # 1. Strings (ASCII 4+ chars, filter relevant)
    strings_raw = re.findall(b'[A-Za-z0-9 !?-]{4,50}', data)
    strings = []
    for s in strings_raw:
        text = s.decode('ascii', errors='ignore').strip()
        if len(text) > 3 and not re.match(r'^[0-9A-F]+$', text):  # Skip hex
            strings.append(text)
    lore["strings"] = list(set(strings))[:1000]  # Dedup top 1k
    
    # 2. Music (SPC700 tables ~ROM end, heuristic)
    spc_size = 0x10000
    if len(data) > spc_size:
        spc_data = data[-spc_size:]
        # SPC track names often ASCII near $F0F0
        music_strings = re.findall(b'[A-Za-z ]{4,20}', spc_data)
        lore["music"] = [s.decode('ascii', errors='ignore') for s in music_strings[:50]]
    
    # 3. Enemies/Items (keywords near GFX banks)
    gfx_keywords = ['enemy', 'boss', 'monster', 'goomba', 'koopa', 'slime']
    enemies = [s.decode('ascii', errors='ignore') for s in strings_raw if any(k.encode() in s.lower() for k in gfx_keywords)]
    lore["enemies"] = list(set(enemies))[:200]
    
    # 4. Items (common keywords)
    item_keywords = ['coin', 'fire', 'star', 'mushroom', 'sword', 'shield']
    items = [s.decode('ascii', errors='ignore') for s in strings_raw if any(k.encode() in s.lower() for k in item_keywords)]
    lore["items"] = list(set(items))[:100]
    
    return lore

total_entries = 0
for rom_path in ROM_DIR.rglob("*.sfc"):
    lore = extract_lore(rom_path)
    out_path = LORE_DIR / f"{lore['game']}.json"
    with open(out_path, "w") as f:
        json.dump(lore, f, indent=2)
    
    entries = len(lore['strings']) + len(lore['music']) + len(lore['enemies']) + len(lore['items'])
    total_entries += entries
    print(f"{lore['game']}: {entries} entries -> {out_path}")

print(f"\nWorld Lore Complete: {total_entries} entries from {len(list(ROM_DIR.rglob('*.sfc')))} ROMs")
print("Gary ready for SNES gossip/show scripts!")
