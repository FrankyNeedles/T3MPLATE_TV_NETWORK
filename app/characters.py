#!/usr/bin/env python3
"""
Characters Management
Loads and manages SNES characters from assets.
Integrates with living world for relationships/careers.
"""

import json
from typing import List, Dict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .config import CONFIG


class Base(DeclarativeBase):
    pass


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    game_id: Mapped[str] = mapped_column(String(50), index=True)
    sprite_bank: Mapped[int] = mapped_column(Integer)
    sprite_offset: Mapped[str] = mapped_column(String(20))  # e.g., '$8000'
    relationships: Mapped[List["Relationship"]] = relationship(
        back_populates="characters"
    )
    careers: Mapped[List["Career"]] = relationship(back_populates="character")

    def __repr__(self) -> str:
        return f"<Character(name='{self.name}', game_id='{self.game_id}')>"


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character1_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    character2_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)  # -100 to 100
    events: Mapped[str] = mapped_column(String(500), default="")  # JSON events
    character1: Mapped[Character] = relationship(back_populates="relationships")
    character2: Mapped[Character] = relationship(back_populates="relationships")

    def __repr__(self) -> str:
        return f"<Relationship(c1={self.character1_id}, c2={self.character2_id}, score={self.score})>"


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    show_type: Mapped[str] = mapped_column(String(50))  # news, comedy, etc.
    show_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Integer, default=5.0)  # 1-10
    character: Mapped[Character] = relationship(back_populates="careers")

    def __repr__(self) -> str:
        return f"<Career(character={self.character_id}, type='{self.show_type}', count={self.show_count})>"


def load_characters_from_assets() -> List[Dict]:
    """Load characters from JSON assets."""
    char_path = CONFIG.assets_dir / "universe" / "characters.json"
    if not char_path.exists():
        # Create sample
        sample_chars = [
            {
                "name": "Mario",
                "game_id": "super_mario_world",
                "sprite_bank": 0x1D,
                "sprite_offset": "$8000",
            },
            {
                "name": "Luigi",
                "game_id": "super_mario_world",
                "sprite_bank": 0x1D,
                "sprite_offset": "$A000",
            },
            {
                "name": "Bowser",
                "game_id": "super_mario_world",
                "sprite_bank": 0x1F,
                "sprite_offset": "$2000",
            },
            # Add 85 more...
        ]
        char_path.parent.mkdir(parents=True, exist_ok=True)
        with open(char_path, "w") as f:
            json.dump(sample_chars, f, indent=2)
        return sample_chars

    with open(char_path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    chars = load_characters_from_assets()
    print(f"Loaded {len(chars)} characters")
