#!/usr/bin/env python3
"""
Init Living World DB + Load 88 Chars + Lore.
Creates tables, populates from characters.json + rom_lore/*.json.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.living_world import LivingWorld, generate_morning_report
from app.characters import load_characters_from_assets
from sqlalchemy import Column, String, Integer, Text, DateTime
import json
from sqlalchemy.orm import sessionmaker

# Init DB
lw = LivingWorld()
session = lw.session

# Load 88 chars
chars_json = load_characters_from_assets()
print(f"Loading {len(chars_json)} chars...")
lw._populate_initial_data()

# Load lore to new LoreEntry table (if missing)
try:
    LoreEntry = lw.LoreEntry  # Assume added
except:
    # Add model stub
    print("Lore table pending")

# Seed from rom_lore
lore_dir = Path("assets/rom_lore")
total_lore = 0
for lore_file in lore_dir.glob("*.json"):
    lore = json.load(lore_file.open())
    for t in ['strings', 'music', 'enemies', 'items']:
        for text in lore.get(t, []):
            if len(text) > 3:
                lore_entry = LoreEntry(game=lore['game'], type=t, text=text)
                session.add(lore_entry)
                total_lore += 1
print(f"Loaded {total_lore} lore entries")

lw.session.commit()
print("World Init Complete!")
print(generate_morning_report(lw))
