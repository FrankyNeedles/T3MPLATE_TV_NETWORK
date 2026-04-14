#!/usr/bin/env python3
"""
Living World System
Manages persistent character relationships, careers, show lifecycles.
Uses SQLite with SQLAlchemy for persistence.
"""

import json
import random
from datetime import datetime, date
from typing import List, Dict
from sqlalchemy import (
    create_engine,
    func,
    String,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Text,
    Integer,
)
from sqlalchemy.orm import (
    sessionmaker,
    relationship,
    Session,
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from .config import CONFIG
from .characters import load_characters_from_assets


class Base(DeclarativeBase):
    pass


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    game: Mapped[str] = mapped_column(String(50))
    sprites: Mapped[dict] = mapped_column(JSON)
    lore: Mapped[str] = mapped_column(Text)

    relationships: Mapped[List["Relationship"]] = relationship(
        "Relationship",
        foreign_keys="Relationship.character1_id",
        primaryjoin="Character.id == Relationship.character1_id",
        back_populates="character1",
    )
    relationships_as2: Mapped[List["Relationship"]] = relationship(
        "Relationship",
        foreign_keys="Relationship.character2_id",
        primaryjoin="Character.id == Relationship.character2_id",
        back_populates="character2",
    )
    careers: Mapped[List["Career"]] = relationship("Career", back_populates="character")
    events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="character"
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character1_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    character2_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    events: Mapped[list] = mapped_column(JSON, default=list)

    character1: Mapped["Character"] = relationship(
        "Character", foreign_keys=[character1_id], back_populates="relationships"
    )
    character2: Mapped["Character"] = relationship(
        "Character", foreign_keys=[character2_id], back_populates="relationships_as2"
    )


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    show_type: Mapped[str] = mapped_column(String(50))
    show_count: Mapped[int] = mapped_column(Integer, default=1)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

    character: Mapped["Character"] = relationship("Character", back_populates="careers")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(200))
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    outcome: Mapped[str] = mapped_column(String(50))
    character_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("characters.id"), nullable=True
    )

    character: Mapped["Character"] = relationship("Character", back_populates="events")


class LivingWorld:
    def __init__(self, db_url: str = None):
        if db_url is None:
            db_path = CONFIG.data_dir / "lore" / "living_world.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_url = f"sqlite:///{db_path}"
        else:
            self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self._populate_initial_data()

    def _populate_initial_data(self):
        """Populate DB with initial characters."""
        chars_json = load_characters_from_assets()
        existing = self.session.query(Character).count()
        if existing == 0:
            for char in chars_json:
                new_char = Character(
                    name=char["name"],
                    game=char.get("game", "unknown"),
                    sprites=char.get("sprites", {}),
                    lore=char.get("lore", ""),
                )
                self.session.add(new_char)
            self.session.commit()
            print(f"Populated {len(chars_json)} initial characters")

    def create_relationship(
        self, char1_name: str, char2_name: str, initial_score: int = 0
    ):
        """Create or update relationship (use min/max id to avoid duplicate)."""
        char1 = self.session.query(Character).filter_by(name=char1_name).first()
        char2 = self.session.query(Character).filter_by(name=char2_name).first()
        if not char1 or not char2:
            return None
        id1, id2 = min(char1.id, char2.id), max(char1.id, char2.id)
        rel = (
            self.session.query(Relationship)
            .filter(
                Relationship.character1_id == id1, Relationship.character2_id == id2
            )
            .first()
        )
        if not rel:
            rel = Relationship(
                character1_id=id1, character2_id=id2, score=initial_score
            )
            self.session.add(rel)
            self.session.commit()
        return rel

    def update_relationship(
        self, char1_name: str, char2_name: str, delta: int, event: str
    ):
        """Update relationship based on show outcome."""
        rel = self.create_relationship(char1_name, char2_name)
        if rel:
            rel.score = max(-100, min(100, rel.score + delta))

            events_list = rel.events or []
            events_list.append(
                {
                    "event": event,
                    "score_delta": delta,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            rel.events = events_list

            self.session.commit()
            return rel.score
        return 0

    def generate_gossip(self, char_name: str) -> str:
        """Generate gossip based on relationships."""
        char = self.session.query(Character).filter_by(name=char_name).first()
        if not char:
            return "No gossip available."

        rels = char.relationships + char.relationships_as2
        if not rels:
            return f"{char_name} is keeping to themselves lately."

        rel = random.choice(rels)
        other_char = (
            rel.character1 if char.name == rel.character2.name else rel.character2
        )
        mood = (
            "great friends"
            if rel.score > 50
            else "on bad terms"
            if rel.score < -50
            else "neutral"
        )
        return f"{char_name} and {other_char.name} are {mood} after their recent {random.choice(['show', 'adventure', 'meeting'])}."

    def create_career_entry(self, char_name: str, show_type: str, rating: float):
        """Track career progression."""
        char = self.session.query(Character).filter_by(name=char_name).first()
        if char:
            career = (
                self.session.query(Career)
                .filter_by(character_id=char.id, show_type=show_type)
                .first()
            )
            if career:
                career.show_count += 1
                career.rating = (
                    career.rating * (career.show_count - 1) + rating
                ) / career.show_count
            else:
                career = Career(
                    character_id=char.id,
                    show_type=show_type,
                    show_count=1,
                    rating=rating,
                )
                self.session.add(career)
            self.session.commit()
            return career
        return None

    def add_timeline_event(self, event: str, outcome: str, char_name: str = None):
        """Add event to timeline."""
        char_id = (
            self.session.query(Character.id).filter_by(name=char_name).scalar()
            if char_name
            else None
        )
        ev = TimelineEvent(event=event, outcome=outcome, character_id=char_id)
        self.session.add(ev)
        self.session.commit()
        return ev

    def simulate_day(self, shows: List[Dict]) -> dict:
        """Simulate 24hr with shows, update world state."""
        report = {
            "day": date.today(),
            "shows": len(shows),
            "new_relationships": 0,
            "gossip_generated": [],
        }

        for show in shows:
            hosts = show.get("hosts", [])
            if len(hosts) >= 2:
                # Update relationships
                rating = random.uniform(1, 10)
                for i in range(len(hosts)):
                    for j in range(i + 1, len(hosts)):
                        delta = (
                            random.randint(-20, 20)
                            if rating > 5
                            else random.randint(-40, 10)
                        )
                        event_str = f"Hosted {show.get('type', 'show')} together"
                        score = self.update_relationship(
                            hosts[i], hosts[j], delta, event_str
                        )
                        if score != 0:
                            report["new_relationships"] += 1

                # Career update
                for host in hosts:
                    self.create_career_entry(host, show.get("type", "show"), rating)
                    self.add_timeline_event(
                        f"{host} on {show.get('type', 'show')}",
                        f"Rating {rating:.2f}",
                        host,
                    )

            # Generate gossip
            if hosts:
                host = random.choice(hosts)
                gossip = self.generate_gossip(host)
                report["gossip_generated"].append(gossip)

        # Morning report
        total_rels = self.session.query(Relationship).count()
        report["total_relationships"] = total_rels
        report["top_gossip"] = (
            random.choice(report["gossip_generated"])
            if report["gossip_generated"]
            else "Quiet day."
        )

        return report

    def generate_morning_report(self) -> dict:
        """Generate daily report as JSON."""
        # Query stats
        total_chars = self.session.query(Character).count()
        total_rels = self.session.query(Relationship).count()
        avg_score = self.session.query(func.avg(Relationship.score)).scalar() or 0

        positive_rels = (
            self.session.query(Relationship).filter(Relationship.score > 50).count()
        )
        negative_rels = (
            self.session.query(Relationship).filter(Relationship.score < -50).count()
        )

        recent_events = (
            self.session.query(TimelineEvent)
            .order_by(TimelineEvent.date.desc())
            .limit(5)
            .all()
        )

        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_characters": total_chars,
            "total_relationships": total_rels,
            "average_affinity": round(avg_score, 1),
            "strong_bonds": positive_rels,
            "conflicts": negative_rels,
            "recent_events": [
                {"event": e.event, "outcome": e.outcome, "date": e.date.isoformat()}
                for e in recent_events
            ],
            "gossip": self.generate_gossip("Mario")
            if self.session.query(Character).filter_by(name="Mario").first()
            else "No gossip.",
        }

        # Save to file
        report_path = (
            CONFIG.data_dir
            / "lore"
            / f"morning_report_{datetime.now().strftime('%Y%m%d')}.json"
        )
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report


# Global instance
living_world = LivingWorld()


def morning_report():
    return living_world.generate_morning_report()


__all__ = [
    "LivingWorld",
    "morning_report",
    "Session",
    "Character",
    "Relationship",
    "Career",
    "TimelineEvent",
]
