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
    def _enrich_fills(self, digest: dict, rng) -> dict:
        """Gather candidate fills and ROTATE which world item wins (GAP-3)."""
        fills: dict[str, Any] = {}
        if digest["friendships"]:
            f = rng.choice(digest["friendships"])
            fills["friendships"] = digest["friendships"]
            fills["_top_friendship"] = f
        if digest["feuds"]:
            fills["feuds"] = digest["feuds"]
            fills["_top_feud"] = rng.choice(digest["feuds"])
        if digest["gags"]:
            g = rng.choice(digest["gags"])
            fills["gag"] = g["gag"].lower()
            fills["count"] = g["count"]
        if digest["shows"]:
            fills["shows"] = digest["shows"]
            fills["_top_show"] = rng.choice(digest["shows"])
        return fills

    def _on_set_relation(self, digest: dict, rel_kind: str, on_set: set[str],
                         allow_guest: bool) -> list[dict]:
        """Return ALL real relationships at least one of whose members is ON SET.

        A feud or friendship beat may ONLY air when the actual participants carry
        it in the world (WEAK-1b): at least one member under the mic, and the
        other either already over it or able to join as a guest. Returning the
        full candidate list (instead of the first) lets the per-airing RNG rotate
        WHICH pair airs (GAP-3) instead of always broadcasting the top bond.
        """
        rows = digest["feuds"] if rel_kind == "feud" else digest["friendships"]
        out = []
        for r in rows:
            a, b = r["a"], r["b"]
            if (a in on_set or b in on_set) and a in content.CAST and b in content.CAST:
                out.append(r)
        return out

    def _choose_beat(self, fmt: str, digest: dict, rng, hosts: list[str]) -> tuple[str, dict]:
        """Pick a story beat from REAL world state, respecting the format's
        allowed beats (WEAK-1a) and verifying any relational beat against the
        actual on-set cast (WEAK-1b). Not random.choice."""
        allowed = set(content.FORMAT_ALLOWED_BEATS.get(fmt, content.FORMAT_ALLOWED_BEATS["news"]))
        fills = self._enrich_fills(digest, rng)
        on_set = set(hosts)

        # relational beats first -- but only if the format permits them AND the
        # cast actually carries the relationship (re-key guest for the partner).
        # Among ALL candidate bonds, the seed rotates which pair airs (GAP-3).
        for rel_kind, beat_name in (("feud", "feud"), ("friendship", "friendship")):
            if beat_name not in allowed:
                continue
            rels = self._on_set_relation(digest, rel_kind, on_set, allow_guest=True)
            if rels:
                rel = rng.choice(rels)
                fills["a"], fills["b"] = rel["a"], rel["b"]
                fills["score"] = abs(rel["score"])
                fills["_rel_kind"] = rel_kind
                fills["_rel_missing_guest"] = self._missing_member(rel, on_set)
                return beat_name, fills

        # seeking-work guest (only on formats that welcome a guest)
        if digest["seeking_work"] and fmt in _GUEST_FORMATS and "seeking_work" in allowed:
            guest = rng.choice(digest["seeking_work"])
            fills["guest"] = guest
            return "seeking_work", fills

        # gag is narration, fine on most family/scripted formats
        if "gag" in allowed and digest["gags"]:
            return "gag", fills

        # ratings wins when a strong show exists
        if "ratings" in allowed and digest["shows"]:
            fills["show"] = fills["_top_show"]["name"]
            fills["rating"] = fills["_top_show"]["rating"]
            return "ratings", fills

        # show promo is always a safe, format-neutral close
        if digest["shows"]:
            fills["show"] = fills["_top_show"]["name"]
        return "show_promo", fills

    def _missing_member(self, rel: dict, on_set: set[str]) -> Optional[str]:
        """The participant not currently over the mic (becomes the guest)."""
        a, b = rel["a"], rel["b"]
        if a not in on_set:
            return a
        if b not in on_set:
            return b
        return None

    def _mood_for(self, beat: str) -> str:
        return {"feud": "dramatic", "gag": "happy", "friendship": "cheerful",
                "seeking_work": "warm", "ratings": "celebratory"}.get(beat, "neutral")

    # -- segment production ---------------------------------------------------
    def decide(self, slot, seed: Optional[int] = None) -> broadcast.BroadcastSegment:
        """Produce a renderable BroadcastSegment for the active grid slot,
        caused by the world digest. `seed` seeds per-airing novelty (GAP-3): a
        different seed per pass -> different world pair / dialogue variant, so
        consecutive airings of a slot DIFFER instead of looping byte-identical.
        """
        digest = self.world.world_digest()
        fmt = slot.fmt
        preset = content.SHOW_PRESETS.get(fmt, content.SHOW_PRESETS["news"])
        rng = random.Random(seed)

        beat, fills = self._choose_beat(fmt, digest, rng,
                                        [n for n in preset["hosts"] if n in content.CAST])
        self.mood = self._mood_for(beat)

        # cast (honor preset hosts; append the re-keyed relational guest / work guest)
        casts = []
        for name in preset["hosts"]:
            meta = content.CAST.get(name)
            if meta:
                casts.append(broadcast.Cast(name=name, kind=meta["kind"],
                                            title=meta["role"], motion="idle"))

        # WEAK-1b: if the relational partner isn't a host, re-key cast to bring
        # the REAL feud/friendship actor over the mic (not a random host).
        missing = fills.get("_rel_missing_guest")
        if missing and missing in content.CAST:
            m = content.CAST[missing]
            if all(c.name != missing for c in casts):
                casts.append(broadcast.Cast(name=missing, kind=m["kind"],
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

        # Keep the SHOW'S OWN presenters as the dialogue speakers; the relational
        # pair {a}/{b} is filled with the REAL feud/friendship actors regardless.
        if len(casts) >= 2:
            fills["c1"], fills["c2"] = casts[0].name, casts[1].name
        else:
            fills["c1"] = casts[0].name
            fills["c2"] = casts[1].name if len(casts) > 1 else "the viewers"
        fills["host"] = casts[0].name
        fills.setdefault("a", fills.get("c1"))
        fills.setdefault("b", fills.get("c2"))
        fills.setdefault("show", fills.get("_top_show", {}).get("name", "T3TV Tonight"))

        # dialogue beats from the beat template, FORMAT-voiced and variant-rotated
        tpl = content.FALLBACK_BEATS[beat]
        variants = []
        if fmt in tpl.get("formats", {}):
            variants = tpl["formats"][fmt]
        else:
            variants = tpl["variants"]
        # rotation per airing (GAP-3): a fresh seed -> a fresh dialogue variant
        chosen = rng.choice(variants)

        dialog = []
        for (speaker, line) in chosen:
            text = line
            spk = speaker
            for k, v in fills.items():
                if k.startswith("_"):
                    continue
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

        # ticker derived from world (not static); only formats that allow the
        # topic get the corresponding ticker line (format coherence, WEAK-1a).
        ticker = []
        allowed = set(content.FORMAT_ALLOWED_BEATS.get(fmt, content.FORMAT_ALLOWED_BEATS["news"]))
        if preset.get("ticker"):
            if digest["feuds"] and "feud" in allowed:
                fe = digest["feuds"][0]
                ticker.append(f"FEUD WATCH: {fe['a']} vs {fe['b']} -- drama at 11")
            if digest["friendships"] and "friendship" in allowed:
                f = digest["friendships"][0]
                ticker.append(f"GOOD NEWS: {f['a']} & {f['b']} reunite on-air today")
            if digest["shows"]:
                s = digest["shows"][0]
                ticker.append(f"RATINGS: {s['name']} strong (r{s['rating']})")

        show_title = slot.title
        return broadcast.BroadcastSegment(
            seg_id=f"{show_title.lower().replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}",
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