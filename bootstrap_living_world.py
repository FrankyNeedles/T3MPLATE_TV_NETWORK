#!/usr/bin/env python3
"""
Bootstrap TV_WORLD DATA/lore/JSONs to DB.
"""

import json
from app.living_world import Character, Relationship, Career, Timeline, Session
from datetime import datetime, timedelta

# Mock TV_WORLD JSONs (relationships/timeline/careers)
tv_data = {
    "characters": [
        {
            "name": f"TV_Char{i}",
            "game": "TV_Show",
            "lore": f"TV lore {i}",
            "sprites": "tv_sprite.png",
        }
        for i in range(50)
    ],
    "relationships": [
        {"char1": "TV_Char1", "char2": "TV_Char2", "score": 50} for _ in range(10)
    ],
    "careers": [{"char": "TV_Char1", "show_count": 5, "rating": 4.2}],
    "timeline": [
        {
            "event": "TV Event",
            "date": (datetime.now() - timedelta(days=i)).isoformat(),
            "outcome": "Positive",
        }
        for i in range(10)
    ],
}

with open("bootstrap_tv_data.json", "w") as f:
    json.dump(tv_data, f)

session = Session()
for char in tv_data["characters"]:
    c = Character(
        name=char["name"], game=char["game"], sprites=char["sprites"], lore=char["lore"]
    )
    session.add(c)
    career = Career(
        char_id=c.id,
        show_count=char.get("show_count", 0),
        rating=char.get("rating", 0.0),
    )
    session.add(career)

for rel in tv_data["relationships"]:
    c1 = session.query(Character).filter_by(name=rel["char1"]).first()
    c2 = session.query(Character).filter_by(name=rel["char2"]).first()
    if c1 and c2:
        r = Relationship(
            char1_id=min(c1.id, c2.id), char2_id=max(c1.id, c2.id), score=rel["score"]
        )
        session.add(r)

for ev in tv_data["timeline"]:
    t = Timeline(
        event=ev["event"],
        date=datetime.fromisoformat(ev["date"]),
        outcome=ev["outcome"],
    )
    session.add(t)

session.commit()
print(
    f"Bootstrapped {len(tv_data['characters'])} chars, {len(tv_data['relationships'])} rels, {len(tv_data['timeline'])} events"
)

if __name__ == "__main__":
    print("Bootstrap complete. Run to populate DB.")
