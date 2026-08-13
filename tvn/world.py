#!/usr/bin/env python3
"""Living World engine -- the continuity brain of the broadcast.

Self-contained SQLAlchemy ORM adapted from the salvageable app/living_world.py
(kept logic; dropped the random fake-88 seeding and the fragile imports). Holds
characters, relationships, careers, shows, running gags, and a causal event log.

The critical bridge per RESEARCH_LIVING: world_digest() exposes the ACTUAL world
state (top friendships/feuds, active shows, gags, seeking-work guests) so that
Gary's decisions and the broadcast can be CAUSED by the world -- not random.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, func, or_, and_,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase, sessionmaker, relationship, Mapped, mapped_column,
)

from . import content
from .config import SETTINGS


class Base(DeclarativeBase):
    pass


class Character(Base):
    __tablename__ = "characters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    game: Mapped[str] = mapped_column(String(50))
    kind: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(80), default="")
    mood: Mapped[str] = mapped_column(String(30), default="neutral")
    lore: Mapped[str] = mapped_column(Text, default="")
    popularity: Mapped[float] = mapped_column(Float, default=50.0)

    def relationships_all(self):
        return list(self._rels1) + list(self._rels2)

    _rels1 = relationship("Relationship", foreign_keys="Relationship.character1_id",
                          back_populates="character1")
    _rels2 = relationship("Relationship", foreign_keys="Relationship.character2_id",
                          back_populates="character2")
    careers = relationship("Career", back_populates="character")


class Relationship(Base):
    __tablename__ = "relationships"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character1_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    character2_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    events: Mapped[list] = mapped_column(JSON, default=list)
    character1 = relationship("Character", foreign_keys=[character1_id],
                              back_populates="_rels1")
    character2 = relationship("Character", foreign_keys=[character2_id],
                              back_populates="_rels2")


class Career(Base):
    __tablename__ = "careers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"))
    show_type: Mapped[str] = mapped_column(String(50))
    show_count: Mapped[int] = mapped_column(Integer, default=1)
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    career_level: Mapped[str] = mapped_column(String(20), default="intern")
    employer: Mapped[str] = mapped_column(String(80), default="")
    seeking_work: Mapped[bool] = mapped_column(Boolean, default=False)
    character = relationship("Character", back_populates="careers")


class Show(Base):
    __tablename__ = "shows"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pitch")
    genre: Mapped[str] = mapped_column(String(50))
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    airings: Mapped[int] = mapped_column(Integer, default=0)
    hosts: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class RunningGag(Base):
    __tablename__ = "running_gags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gag_text: Mapped[str] = mapped_column(String(200))
    associated_characters: Mapped[list] = mapped_column(JSON, default=list)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(300))
    reason: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str] = mapped_column(String(50), default="")
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    character_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("characters.id"), nullable=True)


class LivingWorld:
    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            SETTINGS.lore_dir.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{SETTINGS.db_path}"
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self._migrate_if_stale()
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self._seed()

    def _migrate_if_stale(self):
        """Rebuild the schema if an old-schema DB (missing columns) is present."""
        from sqlalchemy import inspect
        try:
            insp = inspect(self.engine)
            if "characters" in insp.get_table_names():
                cols = {c["name"] for c in insp.get_columns("characters")}
                if "kind" not in cols:   # old project schema (sprites/lore, no kind)
                    Base.metadata.drop_all(self.engine)
        except Exception:
            pass

    # -- seeding (curated, not random 88) -------------------------------------
    def _seed(self):
        if self.session.query(Character).count() > 0:
            return
        names = {}
        for name, meta in content.CAST.items():
            ch = Character(name=name, game=meta["game"], kind=meta["kind"],
                           role=meta["role"], mood=meta["mood"], lore=meta["bio"])
            self.session.add(ch)
            self.session.flush()
            names[name] = ch.id
        for a, b, s in content.SEED_FRIENDSHIPS:
            self._add_rel(names[a], names[b], s)
        for a, b, s in content.SEED_FEUDS:
            self._add_rel(names[a], names[b], s)
        for name in names:
            self.session.add(Career(character_id=names[name],
                                    show_type="news", show_count=1,
                                    rating=6.0, career_level="regular",
                                    employer="T3TV"))
        for gag, chars in [("Mario yells 'Yahoo!'", ["mario", "luigi"]),
                           ("Luigi is afraid of ghosts", ["luigi"]),
                           ("Yoshi eats everything", ["yoshi", "toad"]),
                           ("Bowser's castle keeps getting rebuilt", ["bowser"])]:
            self.session.add(RunningGag(gag_text=gag, associated_characters=chars,
                                        occurrence_count=0))
        for fmt, preset in [("news", ["mario"]), ("morning", ["peach"]),
                            ("talk", ["bowser"]), ("game_show", ["toad"]),
                            ("late_night", ["wario"]), ("action", ["link"])]:
            self.session.add(Show(name=f"{fmt.title()} of T3TV", status="series",
                                  genre=fmt, rating=7.0, hosts=preset))
        self.session.commit()

    def _add_rel(self, a, b, score):
        self.session.add(Relationship(character1_id=min(a, b),
                                      character2_id=max(a, b), score=score))

    # -- read helpers ---------------------------------------------------------
    def get_character(self, name):
        return self.session.query(Character).filter_by(name=name).first()

    def top_relationships(self, limit=4):
        return (self.session.query(Relationship)
                .order_by(Relationship.score.desc()).limit(limit).all())

    def top_feuds(self, limit=3):
        return (self.session.query(Relationship)
                .order_by(Relationship.score.asc()).limit(limit).all())

    def active_shows(self, limit=6):
        return (self.session.query(Show)
                .filter(Show.status.in_(["series", "syndication", "pilot"]))
                .order_by(Show.rating.desc()).limit(limit).all())

    def top_gags(self, limit=3):
        return (self.session.query(RunningGag)
                .order_by(RunningGag.occurrence_count.desc()).limit(limit).all())

    def seeking_work(self):
        rows = (self.session.query(Career)
                .filter(Career.seeking_work.is_(True)).all())
        return [c.character.name for c in rows]

    # -- world digest (the bridge, per RESEARCH_LIVING 2.2) --------------------
    def world_digest(self) -> dict:
        fr = [{"a": r.character1.name, "b": r.character2.name, "score": r.score}
              for r in self.top_relationships() if r.score > 0]
        fe = [{"a": r.character1.name, "b": r.character2.name, "score": r.score}
              for r in self.top_feuds() if r.score < 0]
        shows = [{"name": s.name, "status": s.status, "rating": s.rating}
                 for s in self.active_shows()]
        gags = [{"gag": g.gag_text, "count": g.occurrence_count}
                for g in self.top_gags()]
        seeking = self.seeking_work()
        return {
            "friendships": fr,
            "feuds": fe,
            "shows": shows,
            "gags": gags,
            "seeking_work": seeking,
        }

    def describe_world(self) -> str:
        """Compact human-readable digest (fed to Gary / morning report)."""
        d = self.world_digest()
        lines = []
        lines.append("TOP FRIENDSHIPS: " + ", ".join(
            f"{f['a']}~{f['b']}({f['score']})" for f in d["friendships"]))
        lines.append("TOP FEUDS: " + ", ".join(
            f"{f['a']}~{f['b']}({f['score']})" for f in d["feuds"]))
        lines.append("ACTIVE SHOWS: " + ", ".join(
            f"{s['name']}[{s['status']}/r{s['rating']}]" for s in d["shows"]))
        lines.append("RUNNING GAGS: " + ", ".join(
            f"{g['gag']}x{g['count']}" for g in d["gags"]))
        if d["seeking_work"]:
            lines.append("SEEKING WORK: " + ", ".join(d["seeking_work"]))
        return "\n".join(lines)

    # -- causal evolution -----------------------------------------------------
    def on_air(self, cast: list[str], show: Optional[str] = None,
               tension: int = 0, outcome: str = "aired"):
        """Record that a beat/show aired; apply CAUSAL relationship/career deltas.

        Co-hosts who work together gently drift according to how the segment went
        (positive chemistry if they're already friendly, spiky if feuding). The
        reason is logged on the event -- every mutation has a cause.
        """
        for a in cast:
            for b in cast:
                if a >= b:
                    continue
                ca, cb = self.get_character(a), self.get_character(b)
                if not ca or not cb:
                    continue
                rel = self._find_rel(ca.id, cb.id)
                if rel is None:
                    rel = Relationship(character1_id=min(ca.id, cb.id),
                                       character2_id=max(ca.id, cb.id), score=0,
                                       events=[])
                    self.session.add(rel)
                rel.events = rel.events or []
                delta = 4 if rel.score >= 0 else -4
                if tension:
                    delta += tension
                rel.score = max(-100, min(100, rel.score + delta))
                cause = f"co-hosted on {show}" if show else "aired together"
                rel.events.append({"event": cause, "delta": delta,
                                   "date": datetime.now().isoformat()})
                self._note(f"{a} & {b} {cause} (score {rel.score}, +{delta} delta)",
                           reason=f"chemistry on {'/'.join(cast)}", outcome=outcome)
                ca.popularity = min(100, ca.popularity + 1)
                cb.popularity = min(100, cb.popularity + 1)
        # bump the show rating gently (performance, not dice)
        if show:
            s = self.session.query(Show).filter_by(name=show).first()
            if s and s.rating > 0:
                s.rating = round(0.9 * s.rating + 0.1 * (7.0 + max(-2, min(2, tension))), 1)
                s.airings += 1
        self.session.commit()

    def _find_rel(self, a, b):
        return (self.session.query(Relationship)
                .filter(or_(
                    and_(Relationship.character1_id == a, Relationship.character2_id == b),
                    and_(Relationship.character1_id == b, Relationship.character2_id == a)))
                .first())

    def _note(self, event, reason="", outcome="", character=None):
        self.session.add(TimelineEvent(event=event[:300], reason=reason,
                                       outcome=outcome))

    def bump_gag(self, gag_text: str):
        g = self.session.query(RunningGag).filter_by(gag_text=gag_text).first()
        if g:
            g.occurrence_count += 1
            g.last_used = datetime.now()
            self._note(f"running gag: '{gag_text}' (now x{g.occurrence_count})",
                       reason="aired on air")
            self.session.commit()

    # -- daily / weekly maintenance -------------------------------------------
    def tick(self, days: int = 1):
        """Evening maintenance: decay stale scores, occasionally set someone
        seeking work if their show wrapped, evolve. Runs off-peak."""
        for rel in self.session.query(Relationship).all():
            rel.score = max(-100, min(100, int(rel.score * 0.98)))  # gentle decay
        # a cancelled/pitch-only show drops to 'wraps'; cast seeks work
        for show in self.session.query(Show).filter_by(status="pitch").all():
            show.status = "cancellation"
        cancelled = self.session.query(Show).filter_by(status="cancellation").all()
        for show in cancelled:
            for host in (show.hosts or []):
                career = (self.session.query(Career).join(Character)
                          .filter(Character.name == host).first())
                if career:
                    career.seeking_work = True
                    career.employer = ""
            self.session.query(Show).filter_by(id=show.id).update({"status": "syndication",
                                                                   "rating": show.rating})
        for gag in self.session.query(RunningGag).all():
            if (datetime.now() - gag.last_used) > timedelta(days=4):
                gag.occurrence_count = max(0, int(gag.occurrence_count * 0.8))
        self.session.commit()

    # -- morning report --------------------------------------------------------
    def morning_report(self) -> dict:
        d = self.world_digest()
        evs = (self.session.query(TimelineEvent)
               .order_by(TimelineEvent.date.desc()).limit(6).all())
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "stats": {"characters": self.session.query(Character).count(),
                      "relationships": self.session.query(Relationship).count(),
                      "shows": self.session.query(Show).count()},
            "friendships": d["friendships"],
            "feuds": d["feuds"],
            "shows": d["shows"],
            "gags": d["gags"],
            "seeking_work": d["seeking_work"],
            "recent_events": [e.event for e in evs],
        }


def open_world(db_url: Optional[str] = None) -> LivingWorld:
    return LivingWorld(db_url)