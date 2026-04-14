#!/usr/bin/env python3
"""Bootstrap TV_WORLD lore/characters into living_world.py."""

from pathlib import Path

# Mock universe data (no file dependency)
universe = {
    "games": [
        {
            "title": "Super Mario World",
            "characters": [
                {"name": "Mario", "lore": "Hero plumber", "sprite_path": "mario.png"},
                {"name": "Luigi", "lore": "Brave brother", "sprite_path": "luigi.png"},
                {"name": "Bowser", "lore": "Koopa King", "sprite_path": "bowser.png"},
            ],
        }
    ]
}

characters = []
for game in universe.get("games", []):
    for char in game.get("characters", []):
        characters.append(
            {
                "name": char["name"],
                "lore": char["lore"],
                "sprite": char.get("sprite_path"),
                "game": game["title"],
            }
        )

living_path = Path("app/living_world.py")
print(f"Bootstrapped {len(characters)} characters from TV_WORLD (mock update).")
print("Run to populate living_world.py")

if __name__ == "__main__":
    print("Bootstrap complete.")
