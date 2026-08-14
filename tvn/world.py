#!/usr/bin/env python3
"""Living World engine -- the continuity brain of the broadcast.

Self-contained SQLAlchemy ORM adapted from the salvageable app/living_world.py
(kept logic; dropped the random fake-88 seeding and the fragile imports). Holds
characters, relationships, careers, shows, running gags, and a causal event log.

The critical bridge per RESEARCH_LIVING: world_digest() exposes the ACTUAL world
state (top friendships/feuds, active shows, gags, seeking-work guests) so that
Gary's decisions and the broadcast can be CAUSED by the world -- not random.

Stage 3 (make 24/7 LIVING): directed relationship arcs (arc_label), episode
counts/titles driven by the real calendar, a persisted SeasonState, and every
on_air() mutation carrying a REAL `reason` tied to an in-world event and chained
via `caused_by_event_id` -- canon discipline: no slot-machine decisions.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, or_, and_,
    create_engine,
)
from sqlalchemy import inspect as _inspect
from sqlalchemy import text as _text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    DeclarativeBase, sessionmaker, relationship, Mapped, mapped_column,
)

from . import content
from .config import SETTINGS


# Stage 4 (BALANCE THE WORLD, BUG-2): mean-reverting drift, not a one-way
# ratchet. A co-hosting pair is pulled toward a SIGNED baseline (friends settle
# near +BASELINE, feuds near -BASELINE) with a reversion that fights ±100:
#   delta = K*(baseline - score)  -> positive below baseline, NEGATIVE beyond it,
#   so scores oscillate around the baseline instead of saturating at the cap.
BASELINE = 65.0      # a mature aired bond rests near ±65, not ±100
_REVERSION_K = 0.12  # pull-to-baseline strength per airing
_TENSION_K = 0.30    # per-unit tension push along the relationship axis
_POP_BASELINE = 60.0 # celebrity floor/trend every co-host drifts toward
_POP_K = 0.15        # popularity reversion strength per airing


# New columns added against a pre-existing on-disk DB (Stage 3 world widening).
# create_all() won't add columns to an existing table, so we ALTER here instead.
_ADD_COLUMNS = {
    "relationships": [("arc_label", "VARCHAR(80) NOT NULL DEFAULT ''")],
    "shows": [("episode_count", "INTEGER NOT NULL DEFAULT 0"),
              ("episode_title", "VARCHAR(120) NOT NULL DEFAULT ''"),
              ("arc_label", "VARCHAR(80) NOT NULL DEFAULT ''"),
              ("season", "VARCHAR(50) NOT NULL DEFAULT 'Season 1'")],
    "timeline_events": [("caused_by_event_id", "INTEGER")],
}



# Directed relationship story arcs (Stage 3/F-3.2). A shared source of truth so
# fresh-seed (_seed_now) and the live-DB backfill (_backfill_relationship_arcs)
# apply the SAME arcs to the SAME bonds.
RELATIONSHIP_ARCS = {
    ("mario", "luigi"): "Brothers Reunited",
    ("peach", "mario"): "Royal Alliance",
    ("yoshi", "mario"): "Steadfast Sidekick",
    ("link", "zelda"): "Hyrule Trust",
    ("mario", "bowser"): "The Eternal Rivalry",
    ("wario", "luigi"): "Rivalry Brewing",
}
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
    arc_label: Mapped[str] = mapped_column(String(80), default="")   # directed story arc (Stage 3)
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
    episode_count: Mapped[int] = mapped_column(Integer, default=0)
    episode_title: Mapped[str] = mapped_column(String(120), default="")
    hosts: Mapped[list] = mapped_column(JSON, default=list)
    arc_label: Mapped[str] = mapped_column(String(80), default="")   # season arc label
    season: Mapped[str] = mapped_column(String(50), default="Season 1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SeasonState(Base):
    """The broadcast's current in-world season/holiday (RESEARCH I3). Driven by
    the real calendar so promotions/series feel timely, never static."""
    __tablename__ = "season_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[str] = mapped_column(String(30))
    holiday: Mapped[str] = mapped_column(String(80), default="")
    month: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


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
    # consequence-chaining (Stage 3): every mutation points at the world event
    # that CAUSED it, so the log is a causal DAG, not a flat list.
    caused_by_event_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("timeline_events.id"), nullable=True)


class LivingWorld:
    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            SETTINGS.lore_dir.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{SETTINGS.db_path}"
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self._migrate_if_stale()
        self._add_new_columns()
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self._seed()
        self._seed_season_state()
        self._backfill_relationship_arcs()

    def _migrate_if_stale(self):
        """Rebuild the schema if an old-schema DB (missing columns) is present."""
        try:
            insp = _inspect(self.engine)
            if "characters" in insp.get_table_names():
                cols = {c["name"] for c in insp.get_columns("characters")}
                if "kind" not in cols:   # old project schema (sprites/lore, no kind)
                    Base.metadata.drop_all(self.engine)
        except Exception:
            pass

    def _add_new_columns(self):
        """ALTER existing tables that lack Stage-3 columns (safe no-op on fresh)."""
        try:
            insp = _inspect(self.engine)
            for table, cols in _ADD_COLUMNS.items():
                if table not in insp.get_table_names():
                    continue
                existing = {c["name"] for c in insp.get_columns(table)}
                with self.engine.begin() as conn:
                    for name, ddl in cols:
                        if name not in existing:
                            conn.execute(_text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
        except Exception:
            pass   # fresh DB / migration already handled; never crash open

    def _seed_season_state(self):
        """Persist the calendar-driven SeasonState row the broadcast reads."""
        try:
            month = datetime.now().month
            season, holiday = content.SEASONS.get(month, ("Summer", "Harvest Kickoff"))
            row = (self.session.query(SeasonState)
                   .filter_by(active=True).order_by(SeasonState.id.desc()).first())
            if row is None:
                self.session.add(SeasonState(season=season, holiday=holiday, month=month))
                self.session.commit()
        except Exception:
            self.session.rollback()

    # -- calendar-driven season (RESEARCH I3) ---------------------------------
    def _season_for_month(self, month: int) -> tuple[str, str]:
        return content.SEASONS.get(month, ("Summer", "Harvest Kickoff"))

    def current_season(self) -> dict:
        """Derive the live in-world season/holiday from the REAL calendar, and
        persist it in SeasonState so promotions/series read it (never static)."""
        month = datetime.now().month
        season, holiday = content.SEASONS.get(month, ("Summer", "Harvest Kickoff"))
        row = (self.session.query(SeasonState)
               .filter_by(active=True).order_by(SeasonState.id.desc()).first())
        if row is None:
            row = SeasonState(season=season, holiday=holiday, month=month)
            self.session.add(row)
        else:
            row.season, row.holiday, row.month = season, holiday, month
            row.updated_at = datetime.now()
        # opportunistically bump missing series arcs to the season sweep run so
        # series feel timely.
        for show in self.session.query(Show).all():
            if not show.arc_label:
                show.arc_label = f"{season} Sweeps Run"
                if show.episode_title == "":
                    show.episode_title = "Series Premiere"
        self.session.commit()
        return {"season": season, "holiday": holiday, "month": month}

    # -- seeding (curated, not random 88) -------------------------------------
    def _seed(self):
        """Insert curated cast/relationships if the DB is empty.

        Concurrency-safe (m5): if two processes race to first-seed, the loser
        hits an IntegrityError on commit and simply rolls back -- the winner's
        rows are retained, no crash, no duplicate seed.
        """
        if self.session.query(Character).count() > 0:
            return
        try:
            self._seed_now()
            self.session.commit()
        except IntegrityError:
            self.session.rollback()   # another worker seeded first; ours is moot

    def _seed_now(self):
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
        # directed relationship arcs (Stage 3, F-3.2): each seeded bond carries a
        # story arc so feuds/friendships read as evolving, not flat scores. Uses
        # the same source of truth as the migration backfill.
        arcs = RELATIONSHIP_ARCS
        for (a, b), label in arcs.items():
            target = self._find_rel(names[a], names[b])
            if target is None:
                self._add_rel(names[a], names[b], 0)
                target = self._find_rel(names[a], names[b])
            target.arc_label = label
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
            title_pool = content.EPISODE_TITLES.get(fmt, ["Series Premiere"])
            self.session.add(Show(name=f"{fmt.title()} of T3TV", status="series",
                                  genre=fmt, rating=7.0, hosts=preset,
                                  episode_count=1,
                                  episode_title=title_pool[0],
                                  arc_label="Series Premiere"))


    def _backfill_relationship_arcs(self):
        """Idempotently backfill empty relationship arc labels (F-3.2).

        Runs on EVERY open, not only on a fresh DB. A persistent DB that got the
        `arc_label` column via _add_new_columns but was never re-seeded now gets
        its real arcs filled in -- and re-running is a safe no-op for ones that
        already carry a label.
        """
        names = {c.name: c.id for c in self.session.query(Character).all()}
        for (a, b), label in RELATIONSHIP_ARCS.items():
            if a not in names or b not in names:
                continue
            rel = self._find_rel(names[a], names[b])
            if rel is None:
                rel = Relationship(character1_id=min(names[a], names[b]),
                                   character2_id=max(names[a], names[b]),
                                   score=0, events=[])
                self.session.add(rel)
            # idempotent: never overwrite an existing arc label
            if not rel.arc_label:
                rel.arc_label = label
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
        fr = [{"a": r.character1.name, "b": r.character2.name, "score": r.score,
               "arc_label": r.arc_label}
              for r in self.top_relationships() if r.score > 0]
        fe = [{"a": r.character1.name, "b": r.character2.name, "score": r.score,
               "arc_label": r.arc_label}
              for r in self.top_feuds() if r.score < 0]
        shows = [{"name": s.name, "status": s.status, "rating": s.rating,
                  "episode_title": s.episode_title, "episode_count": s.episode_count,
                  "arc_label": s.arc_label, "season": s.season}
                 for s in self.active_shows()]
        gags = [{"gag": g.gag_text, "count": g.occurrence_count}
                for g in self.top_gags()]
        seeking = self.seeking_work()
        season = self.current_season()
        return {
            "friendships": fr,
            "feuds": fe,
            "shows": shows,
            "gags": gags,
            "seeking_work": seeking,
            "season": season,
        }

    def describe_world(self) -> str:
        """Compact human-readable digest (fed to Gary / morning report)."""
        d = self.world_digest()
        lines = []
        lines.append(f"SEASON: {d['season']['season']} "
                     f"({d['season']['holiday']})")
        lines.append("TOP FRIENDSHIPS: " + ", ".join(
            f"{f['a']}~{f['b']}({f['score']})" for f in d["friendships"]))
        lines.append("TOP FEUDS: " + ", ".join(
            f"{f['a']}~{f['b']}({f['score']})" for f in d["feuds"]))
        lines.append("ACTIVE SHOWS: " + ", ".join(
            f"{s['name']}[{s['status']}/r{s['rating']}/ep{s['episode_count']}]"
            for s in d["shows"]))
        lines.append("RUNNING GAGS: " + ", ".join(
            f"{g['gag']}x{g['count']}" for g in d["gags"]))
        if d["seeking_work"]:
            lines.append("SEEKING WORK: " + ", ".join(d["seeking_work"]))
        return "\n".join(lines)

    def _note(self, event, reason="", outcome="", character=None,
              caused_by_event_id: Optional[int] = None) -> Optional[int]:
        ev = TimelineEvent(event=event[:300], reason=reason, outcome=outcome,
                           caused_by_event_id=caused_by_event_id)
        self.session.add(ev)
        self.session.flush()
        return ev.id

    def _find_rel(self, a, b):
        return (self.session.query(Relationship)
                .filter(or_(
                    and_(Relationship.character1_id == a, Relationship.character2_id == b),
                    and_(Relationship.character1_id == b, Relationship.character2_id == a)))
                .first())

    # -- causal evolution -----------------------------------------------------
    @staticmethod
    def _airing_delta(score: int, tension: int = 0) -> int:
        """Mean-reverting co-host delta (Stage 4 / BUG-2).

        Pulls the relationship toward its SIGNED baseline (+BASELINE for friends,
        -BASELINE for feuds); beyond the baseline the pull turns NEGATIVE, so a
        pair never ratchets to ±100 but oscillates around its resting level.
        Tension (a heated/high-stakes segment) pushes a hair further along the
        relationship's own axis. A zero net pull is nudged by one point so an
        aired pair always registers, keeping the world from freezing exactly on
        baseline (drift, not a dead equilibrium).
        """
        direc = 1.0 if score >= 0 else -1.0
        baseline = direc * BASELINE
        pull = _REVERSION_K * (baseline - score)
        if tension:
            pull += tension * _TENSION_K * direc
        d = int(round(pull))
        return d if d != 0 else int(direc)

    @staticmethod
    def _pop_delta(score: int, popularity: float) -> int:
        """Mean-reverting popularity delta (Stage 4): fame drifts toward the
        celebrity baseline on every airing; a friend glows a little extra, a
        feud loses a little face, but nobody pins at 100/0 forever."""
        direc = 1.0 if score >= 0 else -1.0
        pull = _POP_K * (_POP_BASELINE - popularity) + (1.5 if direc > 0 else -1.5)
        return int(round(pull))

    def on_air(self, cast: list[str], show: Optional[str] = None,
               tension: int = 0, outcome: str = "aired",
               caused_by_event_id: Optional[int] = None,
               genre: Optional[str] = None):
        """Record that a beat/show aired; apply CAUSAL relationship/career deltas.

        Co-hosts who work together gently drift according to how the segment went
        (positive chemistry if they're already friendly, spiky if feuding). Every
        mutation carries a REAL `reason` tied to an in-world event, and each
        mutation's timeline event is consequence-chained via `caused_by_event_id`
        to the ROOT airing event (the >0 head that kicked off this pass), so the
        log reads as a causal DAG, not a flat list (RESEARCH I3 / canon rule).
        """
        season = self.current_season()
        # ROOT event: the airing itself. Every per-pair mutation below points here
        # via caused_by_event_id (or at an explicitly supplied upstream cause).
        root = self._note(
            f"'{show}' aired: {', '.join(cast)}",
            reason=f"programming slot during the {season['season']} "
                   f"{season['holiday']}".strip(),
            outcome=outcome, caused_by_event_id=caused_by_event_id)

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
                delta = self._airing_delta(rel.score, tension)
                rel.score = max(-100, min(100, rel.score + delta))
                # popularity mean-reverts EACH co-host toward the celebrity
                # baseline from their OWN value (plays the whole world's fame,
                # not a single shared delta; nobody pins at 100/0 forever).
                pop_delta_a = self._pop_delta(rel.score, ca.popularity)
                pop_delta_b = self._pop_delta(rel.score, cb.popularity)
                cause = f"co-hosted on {show}" if show else "aired together"
                # every mutation carries a reason + the causal chain link
                rel.events.append({"event": cause, "delta": delta,
                                   "score": rel.score,
                                   "reason": f"{a} & {b} {cause} during "
                                             f"{season['season']}",
                                   "caused_by_event_id": root,
                                   "date": datetime.now().isoformat()})
                self._note(f"{a} & {b} {cause} (score {rel.score}, "
                           f"{(pop_delta_a + pop_delta_b) / 2:+.0f} pop)",
                           reason=f"{a} & {b} {cause} during {season['season']} "
                                  f"{season['holiday']}".strip(),
                           outcome=outcome, caused_by_event_id=root)
                ca.popularity = min(100, max(0, ca.popularity + pop_delta_a))
                cb.popularity = min(100, max(0, cb.popularity + pop_delta_b))
        # bump the show rating gently (performance, not dice)
        if show:
            s = self.session.query(Show).filter_by(name=show).first()
            if s is None:
                # F-3.1: production passes GRID-SLOT titles (e.g. "Super
                # Playhouse") that never match a seeded "X of T3TV" show, so
                # episode_count/title/rating never advanced in the real 24/7
                # loop. Upsert a real Show from the slot title + genre so
                # continuity actually moves on-air.
                s = Show(name=show, status="series", genre=genre or "news",
                         rating=7.0, hosts=cast, episode_count=0,
                         episode_title="Series Premiere",
                         arc_label=f"{self.current_season()['season']} Sweeps Run")
                self.session.add(s)
                self.session.flush()
            if s.rating > 0:
                s.rating = round(0.9 * s.rating + 0.1 * (7.0 + max(-2, min(2, tension))), 1)
                s.airings += 1
                # episode continuity (Stage 3): every airing advances the episode
                # count and rotates a fresh episode title from the genre pool.
                s.episode_count = (s.episode_count or 0) + 1
                pool = content.EPISODE_TITLES.get(s.genre, ["Series Premiere"])
                s.episode_title = pool[(s.episode_count - 1) % len(pool)]
                if not s.arc_label:
                    s.arc_label = f"{season['season']} Sweeps Run"
                self.session.query(Show).filter_by(id=s.id).update(
                    {"arc_label": s.arc_label}, synchronize_session=False)
        self.session.commit()

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
            "season": d["season"],
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
