#!/usr/bin/env python3
"""
Gary Control Upgrade – DB Query/Actions/Scene.
Level2.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.gary import GaryPD
from app.living_world import living_world

gary = GaryPD()

# DB query live lore
lore_sample = living_world.session.query(LoreEntry.text).filter(
    living_world.session.query(LoreEntry.game).ilike('%mario%')
).limit(10).all()
ctx = f"Lore Live: { [l.text for l in lore_sample] }"

# Decision with actions
decision = gary.make_decision(
    viewers=1500,  # Sweeps
    news="Mario crossover",
    lore=ctx
)

# Simulate render cue
if decision.actions:
    for action in decision.actions.values():
        if 'bank' in action:
            print(f"Station Cue: decode bank{action['bank']} offset{action['offset']}")

print(decision.model_dump())
print("Level2 Gary Control Complete")
