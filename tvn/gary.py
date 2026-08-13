#!/usr/bin/env python3
"""Gary PD -- the program director (decision brain) for T3MPLATE TV.

Restores `class GaryDecision` (deleted in the fatal 5836e31 commit -- see the
abandonment autopsy) and replaces the old `random.choice(templates)` fallback with
a WORLD-AWARE beat selector: it reads the living-world digest and fills dialogue
with REAL relationships / feuds / gags / seeking-work guests, so the broadcast is
CAUSED by the world. No LLM API key required -- this is the zero-cost content
director (the '_fallback_decision' role defined as The Mushroom Network's brain).
"""
from __future__ import annotations

import random
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from . import content, broadcast
from .animation import library as movement_library


class GaryDecision(BaseModel):
    """Pydantic schema for Gary's broadcast decisions."""

    show: str
    show_type: str
    hosts: list[str]                              # canonical names (mario, luigi...)
    segment_type: str = "act_one"
    topic: str = ""
    news_angle: str = ""
    has_lower_third: bool = True
    has_ticker: bool = False
    ticker_text: str = ""
    has_bumper: bool = True
    has_rating: bool = True
    tv_rating: str = "TV-PG"
    commercial_break: bool = False
    commercial_duration: int = 90
    mood: str = "neutral"
    target_duration: int = 120
    thought: str = ""
    dialogue: list[dict] = Field(default_factory=list)
    music_cue: dict = Field(default_factory=dict)
    sfx_cues: list[dict] = Field(default_factory=list)
    scene_type: str = ""
    background: str = "studio"
    coming_up: str = ""
    actions: dict = Field(default_factory=dict)


# Beat priority: strongest world-signal wins. Index 0 = highest priority.
_BEAT_PRIORITY = ["seeking_work", "feud", "friendship", "gag", "ratings", "show_promo"]
# Formats where a guest actually makes sense (else we fall back to other beats).
_GUEST_FORMATS = {"talk", "late_night", "game_show", "morning", "news"}


class GaryPD:
    def __init__(self, world):
        self.world = world
        self.mood = "cheerful"

    # -- world-aware beat selection ------------------------------------------
    def _choose_beat(self, fmt: str, digest: dict) -> tuple[str, dict]:
        """Pick a story beat from REAL world state (not random.choice)."""
        priority: list[str] = []
        fills: dict[str, Any] = {}

        # enriched fills gathered regardless of which beat wins
        if digest["friendships"]:
            f = digest["friendships"][0]
            fills["c1"], fills["c2"], fills["score"] = f["a"], f["b"], abs(f["score"])
        if digest["feuds"]:
            fe = digest["feuds"][0]
            fills["feud_c1"], fills["feud_c2"], fills["feud_score"] = fe["a"], fe["b"], abs(fe["score"])
        if digest["gags"]:
            fills["gag"] = digest["gags"][0]["gag"].lower()
            fills["count"] = digest["gags"][0]["count"]
        if digest["shows"]:
            fills["show"] = digest["shows"][0]["name"]

        # decide candidate beats by format
        if digest["seeking_work"] and fmt in _GUEST_FORMATS:
            priority.append("seeking_work")
            fills["guest"] = digest["seeking_work"][0]
        if digest["feuds"] and fmt not in ("soap", "cartoon", "late_night"):
            priority.append("feud")
        if digest["friendships"]:
            priority.append("friendship")
        if digest["gags"]:
            priority.append("gag")
        if digest["shows"]:
            priority.append("ratings")
        priority.append("show_promo")

        # lowest index wins == strongest signal
        for beat in _BEAT_PRIORITY:
            if beat in priority:
                return beat, fills
        return "show_promo", fills

    def _mood_for(self, beat: str) -> str:
        return {"feud": "dramatic", "gag": "happy", "friendship": "cheerful",
                "seeking_work": "warm", "ratings": "celebratory"}.get(beat, "neutral")

    # -- segment production ---------------------------------------------------
    def decide(self, slot) -> broadcast.BroadcastSegment:
        """Produce a renderable BroadcastSegment for the active grid slot,
        caused by the world digest."""
        digest = self.world.world_digest()
        fmt = slot.fmt
        preset = content.SHOW_PRESETS.get(fmt, content.SHOW_PRESETS["news"])
        beat, fills = self._choose_beat(fmt, digest)
        self.mood = self._mood_for(beat)

        # cast (honor preset hosts; append feud/guest when present)
        casts = []
        for name in preset["hosts"]:
            meta = content.CAST.get(name)
            if meta:
                casts.append(broadcast.Cast(name=name, kind=meta["kind"],
                                            title=meta["role"], motion="idle"))
        if beat == "feud" and "feud_c2" in fills and fmt in ("talk", "morning", "news"):
            guest = fills["feud_c2"]
            g = content.CAST.get(guest)
            if g and all(c.name != guest for c in casts):
                casts.append(broadcast.Cast(name=guest, kind=g["kind"],
                                            title="Guest", motion="idle"))
        elif beat == "seeking_work" and "guest" in fills:
            g = content.CAST.get(fills["guest"])
            if g and all(c.name != fills["guest"] for c in casts):
                casts.append(broadcast.Cast(name=fills["guest"], kind=g["kind"],
                                            title="Seeking Work", motion="idle"))

        if not casts:
            # never air dead air -- fall back to a guaranteed host
            meta = content.CAST["toad"]
            casts = [broadcast.Cast(name="toad", kind="toad", title="Host",
                                    motion="idle")]

        # pin the fill names to THIS beat's real actors (not whichever beat won)
        if beat == "feud" and "feud_c2" in fills:
            fills["c1"], fills["c2"] = fills["feud_c1"], fills["feud_c2"]
        elif beat == "friendship":
            f = digest["friendships"][0]
            fills["c1"], fills["c2"], fills["score"] = f["a"], f["b"], abs(f["score"])
        elif beat == "gag":
            f = digest["friendships"][0] if digest["friendships"] else \
                {"a": casts[0].name, "b": casts[1].name if len(casts) > 1 else "the viewers", "score": 40}
            fills["c1"], fills["c2"], fills["score"] = f["a"], f["b"], abs(f["score"])
        elif beat == "seeking_work":
            fills["host"] = casts[0].name
            fills["guest"] = fills.get("guest", "toad")
        elif beat in ("ratings", "show_promo"):
            f = digest["friendships"][0] if digest["friendships"] else \
                {"a": casts[0].name, "b": casts[1].name if len(casts) > 1 else "the network", "score": 40}
            fills["c1"], fills["c2"], fills["score"] = f["a"], f["b"], abs(f["score"])
        else:
            f = digest["friendships"][0] if digest["friendships"] else \
                {"a": casts[0].name, "b": casts[1].name if len(casts) > 1 else "the viewers", "score": 40}
            fills["c1"], fills["c2"], fills["score"] = f["a"], f["b"], abs(f["score"])

        # dialogue beats from the template, filled with live world data
        tpl = content.FALLBACK_BEATS[beat]
        dialog = []
        for (speaker, line) in tpl["dialogue"]:
            text = line
            spk = speaker
            for k, v in fills.items():
                if text:
                    text = text.replace("{" + k + "}", str(v))
                spk = spk.replace("{" + k + "}", str(v))
            # a placeholder that never resolved (e.g. no live feud) -> safe name
            if "{" in spk:
                spk = casts[0].name
            text = text.replace("{c1}", casts[0].name).replace("{c2}",
                     casts[1].name if len(casts) > 1 else casts[0].name).replace("{host}", casts[0].name)
            if text and "{" in text:  # drop unresolved braces (defensive, no slop text)
                text = text.replace("{", "").replace("}", "")
            # every speaker must be a drawn cast member: add unseen speakers
            if spk not in [c.name for c in casts]:
                meta = content.CAST.get(spk)
                if meta:
                    casts.append(broadcast.Cast(name=spk, kind=meta["kind"],
                                                title="Guest", motion="idle"))
            dialog.append(broadcast.Beat(
                speaker=spk, text=text,
                motion=tpl["motion"] if spk in [c.name for c in casts] else "idle",
                frames=max(60, int(18 * len(text) / 10))))

        # background (preset + world mood)
        bg = preset["sets"][0]

        # ticker derived from world (not static)
        ticker = []
        if preset.get("ticker"):
            if digest["feuds"]:
                fe = digest["feuds"][0]
                ticker.append(f"FEUD WATCH: {fe['a']} vs {fe['b']} -- drama at 11")
            if digest["friendships"]:
                f = digest["friendships"][0]
                ticker.append(f"GOOD NEWS: {f['a']} & {f['b']} reunite on-air today")
            if digest["shows"]:
                s = digest["shows"][0]
                ticker.append(f"RATINGS: {s['name']} strong (r{s['rating']})")

        show_title = slot.title
        return broadcast.BroadcastSegment(
            seg_id=f"{show_title.lower().replace(' ', '_')}_{datetime.now().strftime('%H%M')}",
            title=show_title, fmt=fmt, daypart=slot.daypart,
            background=bg, cast=casts, beats=dialog,
            ticker=ticker, rating="TV-PG",
            bumper=True, commercial=slot.fmt in content.DAYPART_FORMATS.get("overnight", []),
            hand_off="")

    # -- the classic decision record (kept for tests / the LLM upgrade path) --
    def make_decision(self, slot) -> GaryDecision:
        seg = self.decide(slot)
        return GaryDecision(
            show=seg.title, show_type=seg.fmt,
            hosts=[c.name for c in seg.cast],
            topic=seg.beats[0].text if seg.beats else "",
            news_angle=self._news_angle(seg),
            has_lower_third=any(c.title for c in seg.cast),
            has_ticker=bool(seg.ticker), ticker_text=" | ".join(seg.ticker),
            has_bumper=seg.bumper, has_rating=True, tv_rating=seg.rating,
            commercial_break=seg.commercial, commercial_duration=90,
            mood=self.mood, target_duration=120,
            thought=f"{seg.fmt} for {seg.daypart}",
            dialogue=[{"character": b.speaker, "text": b.text} for b in seg.beats],
            background=seg.background, coming_up=seg.hand_off)

    def _news_angle(self, seg) -> str:
        d = self.world.world_digest()
        if d["feuds"]:
            fe = d["feuds"][0]
            return f"Rivalry: {fe['a']} vs {fe['b']}"
        if d["gags"]:
            return f"Every town has a running gag: {d['gags'][0]['gag']}"
        return "Another day in the Mushroom Kingdom."

    # -- movement library access (Frank: movement as a first-class library) --
    def choreograph(self, segment: broadcast.BroadcastSegment) -> dict[str, str]:
        """Return per-cast movement assignments for this segment's beats."""
        out: dict[str, str] = {}
        for c in segment.cast:
            out[c.name] = "idle"
        for b in segment.beats:
            out[b.speaker] = b.motion
        return out