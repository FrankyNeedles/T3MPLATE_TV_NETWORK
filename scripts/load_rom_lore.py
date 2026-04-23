#!/usr/bin/env python3
"""
Load ROM Lore to Living World DB.
Strings/music/enemies → LoreEntry table for Gary gossip.
"""

import json
from pathlib import Path
from app.living_world import living_world, Base
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import sessionmaker

LORE_DIR = Path("assets/rom_lore")
DB_URL = living_world.db_url  # From living_world

# New table (append to living_world.py models)
class LoreEntry(Base):
    __tablename__ = "lore_entries"
    id = Column(Integer, primary_key=True)
    game = Column(String(100))
    type = Column(String(20))  # string/music/enemy/item
    text = Column(Text)
    created_at = Column(DateTime)

Base.metadata.create_all(living_world.engine)
Session = sessionmaker(bind=living_world.engine)
session = Session()

total_loaded = 0
for lore_file in LORE_DIR.glob("*.json"):
    lore = json.load(lore_file.open())
    for entry_type in ["strings", "music", "enemies", "items"]:
        for text in lore.get(entry_type, []):
            if len(text) > 3:
                db_entry = LoreEntry(game=lore["game"], type=entry_type, text=text)
                session.merge(db_entry)  # Dedup
                total_loaded += 1
    print(f"Loaded {lore['game']}: {total_loaded}")

session.commit()
print(f"World Lore Loaded: {total_loaded} entries")

# Gary query example
print("\nMario Gossip Sample:")
mario_lore = session.query(LoreEntry).filter(LoreEntry.game.ilike('%mario%'), LoreEntry.type=='strings').limit(5).all()
for l in mario_lore:
    print(f"- {l.text}")
