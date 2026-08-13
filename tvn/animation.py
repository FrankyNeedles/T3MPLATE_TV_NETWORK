#!/usr/bin/env python3
"""Movement Library -- Frank's key concept.

All movement information is a reusable LIBRARY: motion clips (idle, walk, talk,
happy, jump, attack...) that any scene, show, or event can invoke. A clip is a
named, loopable sequence of pose/frame keys within a character's sprite sheet.

Scenes do NOT hardcode pixels; they call `MovementLibrary.play(character, motion)`
and receive an ordered, timed list of frames. This keeps motion authentic to SNES
sprite animation and re-usable across every show/every event.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class MotionClip:
    """A reusable, loopable movement attached to a character's sprite sheet."""

    name: str                 # canonical motion id, e.g. "walk"
    poses: tuple[str, ...]    # ordered sprite-sheet pose keys, e.g. ("walk_a", "walk_b")
    fps: float = 6            # SNES-era chunky animation cadence
    loop: bool = True
    category: str = "idle"    # idle | walk | action | reaction
    emote: Optional[str] = None  # mood bias for dialogue (cheerful/angry/...)


# --- The canonical motion set every character supports -----------------------
BASE_MOTIONS: dict[str, MotionClip] = {
    "idle": MotionClip("idle", ("idle",), 4, loop=True, category="idle"),
    "think": MotionClip("think", ("idle", "think"), 2, loop=True, category="idle"),
    "talk": MotionClip("talk", ("talk_a", "talk_b"), 5, loop=True, category="reaction"),
    "wave": MotionClip("wave", ("happy", "talk_a"), 4, loop=True, category="action"),
    "walk": MotionClip("walk", ("walk_a", "walk_b"), 6, loop=True, category="walk"),
    "happy": MotionClip("happy", ("happy", "idle"), 4, loop=True, category="reaction",
                        emote="cheerful"),
    "jump": MotionClip("jump", ("jump", "idle"), 3, loop=False, category="action"),
    "attack": MotionClip("attack", ("attack", "idle"), 3, loop=False, category="action"),
}


class MovementLibrary:
    """Registry of movements per character; scenes invoke clips by name.

    Default: every character supports the base canonical motions. Per-character
    overrides can supply richer clips (e.g. Bowser's "laugh"). New moves are added
    here once and reused everywhere -- this is the movement library, first-class.
    """

    def __init__(self) -> None:
        self._clips: dict[str, dict[str, MotionClip]] = {}
        self._custom: dict[str, dict[str, MotionClip]] = {}

    # ---- registration ------------------------------------------------------
    def register(self, character: str, clips: dict[str, MotionClip]) -> None:
        """Register per-character custom clips (merged over base)."""
        self._custom.setdefault(character, {}).update(clips)

    # ---- read --------------------------------------------------------------
    def available(self, character: str) -> list[str]:
        merged = dict(BASE_MOTIONS)
        merged.update(self._custom.get(character, {}))
        return sorted(merged)

    def clip(self, character: str, motion: str) -> MotionClip:
        custom = self._custom.get(character, {}).get(motion) or BASE_MOTIONS.get(motion)
        if custom is None:
            raise KeyError(f"no motion '{motion}' for character '{character}'")
        return custom

    # ---- invoke (the scene-facing API) ------------------------------------
    def play(self, character: str, motion: str):
        """Return the ordered pose keys for a motion. Never raises for unknown
        motion -- falls back to idle (SAFE: a missing move must not kill the feed)."""
        try:
            clip = self.clip(character, motion)
        except KeyError:
            clip = BASE_MOTIONS["idle"]
        return clip.poses, clip.fps, clip.loop

    # ---- attach movement to an event --------------------------------------
    def choreograph(self, characters: list[str], motion: str) -> dict[str, tuple]:
        """Attach a single motion to a cast of characters (for an event/scene)."""
        return {c: self.play(c, motion) for c in characters}


library = MovementLibrary()

# Stock custom clips making the cast feel alive (cheap, reusable).
library.register("bowser", {
    "laugh": MotionClip("laugh", ("happy", "talk_b", "happy"), 3, loop=True,
                        category="reaction", emote="maniacal"),
    "roar": MotionClip("roar", ("attack", "happy", "idle"), 4, loop=False,
                       category="action", emote="angry"),
})
library.register("yoshi", {
    "hop": MotionClip("hop", ("jump", "idle", "jump"), 4, loop=True, category="walk"),
})
library.register("wario", {
    "cackle": MotionClip("cackle", ("happy", "idle", "happy"), 3, loop=True,
                         category="reaction", emote="greedy"),
})