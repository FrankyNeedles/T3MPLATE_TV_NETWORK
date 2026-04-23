#!/usr/bin/env python3
"""
Gary DB Query Upgrade – Live Lore Gossip.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.gary import GaryPD
from app.living_world import living_world, LoreEntry

# Gary with DB lore
gary = GaryPD()

# Live Mario lore sample
lore_sample = living_world.session.query(LoreEntry.text).filter(
    LoreEntry.game.ilike('%mario%'), 
    LoreEntry.type == 'strings'
).limit(10).all()

ctx = f"ROM Lore Sample: {', '.join([l.text for l in lore_sample])}"
decision = gary.make_decision(
    twitch_metrics={"viewers": 1200},
    news=["AI news"],
    lore=str(ctx)
)

print("Gary Decision with Lore:")
print(decision.model_dump())

# Test render cue
if 'action' in decision.model_dump():
    print("Render Cue Ready: bank/offset to station!")
