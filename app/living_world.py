#!/usr/bin/env python3
"""Living World System - MASTER_PLAN Phase 3."""

from datetime import datetime
from typing import List
from sqlalchemy import (
    and_,
    or_,
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
        "Character",
        foreign_keys="Relationship.character1_id",
        back_populates="relationships",
    )
    character2: Mapped["Character"] = relationship(
        "Character",
        foreign_keys="Relationship.character2_id",
        back_populates="relationships_as2",
    )


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    show_type: Mapped[str] = mapped_column(String(50))
    show_count: Mapped[int] = mapped_column(Integer, default=1)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    career_level: Mapped[str] = mapped_column(String(20), default="intern")

    character: Mapped["Character"] = relationship("Character", back_populates="careers")


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pitch")
    genre: Mapped[str] = mapped_column(String(50))
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    budget: Mapped[int] = mapped_column(Integer, default=100000)
    hosts: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    VALID_STATUSES = {
        "pitch",
        "pilot",
        "series",
        "syndication",
        "cancellation",
        "revival",
    }


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


class RunningGag(Base):
    __tablename__ = "running_gags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gag_text: Mapped[str] = mapped_column(String(200))
    occurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    associated_characters: Mapped[list] = mapped_column(JSON, default=list)

class LoreEntry(Base):
    __tablename__ = "lore_entries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20))  # string/music/enemy/item
    text: Mapped[str] = mapped_column(Text)


class LivingWorld:
    def __init__(self, db_url: str = None):
        if db_url is None:
            db_path = CONFIG.data_dir / "lore" / "living_world.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self._populate_initial_data()

    def _populate_initial_data(self):
        chars_json = load_characters_from_assets()
        existing = self.session.query(Character).count()
        if existing == 0:
            chars_ids = []
            for char in chars_json:
                new_char = Character(
                    name=char["name"],
                    game=char.get("game", "unknown"),
                    sprites=char.get("sprites", {}),
                    lore=char.get("lore", ""),
                )
                self.session.add(new_char)
                self.session.flush()  # ID assign
                chars_ids.append(new_char.id)
            self.session.commit()
            print(f"Populated {len(chars_json)} initial characters")

            # Bootstrap 20 rels
            import random

            for _ in range(20):
                c1 = random.choice(chars_ids)
                c2 = random.choice([cid for cid in chars_ids if cid != c1])
                rel = Relationship(
                    character1_id=c1, character2_id=c2, score=random.randint(-50, 50)
                )
                self.session.add(rel)
            self.session.commit()
            print("Bootstrapped 20 relationships + gossip ready")
            chars = self.session.query(Character).all()
            import random

            genres = ["news", "comedy", "game show", "talk", "sports"]
            for i in range(5):
                hosts = [random.choice(chars).name for _ in range(2)]
                show = Show(
                    name=f"SNES Show {i + 1}",
                    genre=random.choice(genres),
                    status="pitch",
                    hosts=hosts,
                    rating=0.0,
                )
                self.session.add(show)
            for char in random.sample(chars, 10):
                career = Career(
                    character_id=char.id,
                    show_type=random.choice(genres),
                    show_count=random.randint(1, 5),
                    rating=round(random.uniform(4.0, 8.0), 1),
                    career_level="intern",
                )
                self.session.add(career)
            sample_gags = [
                "Mario yelling 'Yahoo!'",
                "Luigi is afraid of ghosts",
                "Bowser destroys the castle",
            ]
            for gag_text in sample_gags:
                rg = RunningGag(
                    gag_text=gag_text, occurrence_count=random.randint(0, 3)
                )
                self.session.add(rg)
            self.session.commit()
            print("Added sample shows, careers, running gags")

    def update_relationship(
        self, char1_name: str, char2_name: str, score_delta: int, event: str
    ):
        c1 = self.session.query(Character).filter_by(name=char1_name).first()
        c2 = self.session.query(Character).filter_by(name=char2_name).first()
        if not c1 or not c2:
            return
        rel = (
            self.session.query(Relationship)
            .filter(
                or_(
                    and_(
                        Relationship.character1_id == c1.id,
                        Relationship.character2_id == c2.id,
                    ),
                    and_(
                        Relationship.character1_id == c2.id,
                        Relationship.character2_id == c1.id,
                    ),
                )
            )
            .first()
        )
        if rel:
            rel.score = min(100, max(-100, rel.score + score_delta))
            rel.events.append(
                {
                    "event": event,
                    "delta": score_delta,
                    "date": datetime.now().isoformat(),
                }
            )
        else:
            new_rel = Relationship(
                character1_id=min(c1.id, c2.id),
                character2_id=max(c1.id, c2.id),
                score=score_delta,
                events=[
                    {
                        "event": event,
                        "delta": score_delta,
                        "date": datetime.now().isoformat(),
                    }
                ],
            )
            self.session.add(new_rel)
        self.session.commit()

    def tick(self):
        """Evolve world one day: relationships, shows, careers, gags."""
        self.evolve_relationships()
        self.advance_shows()
        self.update_careers()
        self.track_running_gags()
        self.session.commit()

    def evolve_relationships(self):
        """Evolve friendships/rivalries with random events."""
        rels = self.session.query(Relationship).all()
        import random

        for rel in rels:
            delta = random.randint(-10, 10)
            event_str = f"Daily interaction (delta: {delta})"
            rel.score = min(100, max(-100, rel.score + delta))
            rel.events.append(
                {"event": event_str, "delta": delta, "date": datetime.now().isoformat()}
            )

    def advance_shows(self):
        """pitch->pilot->series->syndication->cancellation."""
        shows = self.session.query(Show).all()
        import random

        for show in shows:
            if show.status == "pitch":
                show.status = "pilot"
                show.rating = round(random.uniform(2.0, 9.0), 1)
            elif show.status == "pilot":
                if show.rating >= 6.5:
                    show.status = "series"
                else:
                    show.status = "cancellation"
                    show.cancelled_at = datetime.now()
            elif show.status == "series":
                if random.random() < 0.05 or show.rating < 4.0:
                    show.status = "cancellation"
                    show.cancelled_at = datetime.now()
                elif show.rating > 8.5 and random.random() < 0.2:
                    show.status = "syndication"
            show.budget = max(50000, show.budget + int(random.uniform(-20000, 50000)))

    def update_careers(self):
        """Intern -> regular -> star -> legend."""
        careers = self.session.query(Career).join(Character).all()
        import random

        for career in careers:
            career.show_count += random.randint(0, 3)
            career.rating = max(
                1.0, min(10.0, career.rating + random.uniform(-1.0, 2.0))
            )
            total_shows = career.show_count
            if total_shows >= 100:
                career.career_level = "legend"
            elif total_shows >= 50:
                career.career_level = "star"
            elif total_shows >= 10:
                career.career_level = "regular"
            else:
                career.career_level = "intern"

    def track_running_gags(self):
        """Increment or add running gags."""
        import random

        gag_texts = [
            "Mario slips on banana peel",
            "Luigi screams at ghost",
            "Bowser roars loudly",
            "Peach waves hello",
            "Yoshi eats fruit",
        ]
        gag_text = random.choice(gag_texts)
        rg = self.session.query(RunningGag).filter_by(gag_text=gag_text).first()
        if rg:
            rg.occurrence_count += 1
            rg.last_used = datetime.now()
        else:
            new_rg = RunningGag(gag_text=gag_text)
            self.session.add(new_rg)

    def generate_morning_report(self) -> dict:
        total_chars = self.session.query(Character).count()
        total_rels = self.session.query(Relationship).count()
        avg_score = self.session.query(func.avg(Relationship.score)).scalar() or 0
        top_rels = (
            self.session.query(Relationship)
            .order_by(Relationship.score.desc())
            .limit(5)
            .all()
        )
        top_gags = (
            self.session.query(RunningGag)
            .order_by(RunningGag.occurrence_count.desc())
            .limit(5)
            .all()
        )
        shows = self.session.query(Show).all()
        shows_status = {
            show.name: {"status": show.status, "rating": getattr(show, "rating", 0)}
            for show in shows
        }
        top_careers = (
            self.session.query(Career)
            .join(Character)
            .order_by(Career.show_count.desc())
            .limit(5)
            .all()
        )
        careers_summary = {
            c.character.name: {
                "level": c.career_level,
                "shows": c.show_count,
                "rating": c.rating,
            }
            for c in top_careers
        }
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "stats": {
                "characters": total_chars,
                "relationships": total_rels,
                "avg_affinity": round(float(avg_score), 1),
            },
            "top_friendships": [
                f"{r.character1.name} & {r.character2.name}: {r.score}"
                for r in top_rels[:3]
            ],
            "top_rivalries": [
                f"{r.character1.name} & {r.character2.name}: {r.score}"
                for r in sorted(top_rels, key=lambda r: r.score)[:3]
            ],
            "top_gags": [f"{g.gag_text} ({g.occurrence_count}x)" for g in top_gags],
            "show_lifecycles": shows_status,
            "career_trajectories": careers_summary,
        }
        return report


living_world = LivingWorld()

Session = living_world.Session


def update_relationship(char1_name: str, char2_name: str, score_delta: int, event: str):
    living_world.update_relationship(char1_name, char2_name, score_delta, event)


def generate_morning_report(lw=None):
    lw = lw or living_world
    return lw.generate_morning_report()


def generate_gossip(character: str) -> list[str]:
    return [f"{character} had a great day gossip."]
