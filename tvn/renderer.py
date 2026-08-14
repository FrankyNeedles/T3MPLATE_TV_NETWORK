#!/usr/bin/env python3
"""Headless Pillow renderer -- draws the 90s SNES broadcast.

Frank's on-air styling directive is folded in:
  * SNES-native dialogue boxes (bordered box + character portrait + typewriter)
  * 90s station chrome (lower-third, ticker, corner bug, rating) drawn as SNES art
  * full-screen SNES promo/banner art as the commercial & PSA card language
  * authentic SNES sprite animation driven by the MovementLibrary
plus a scanline + vignette treatment so it reads as "broadcast" not "broken capture".

Renders at native 256x224 then integer-upscales with scanlines (SNES-faithful).
"""
from __future__ import annotations

from typing import Iterator, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import assets, broadcast
from .animation import library as movement_library
from .sprites import SpriteBank
from .config import SETTINGS

NATIVE = SETTINGS.res_native
SCALE = SETTINGS.scale
WN, HN = NATIVE


# --- fonts (drawn at native res, upscaled whole -> chunky pixel text) --------
def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _draw_text(d, xy, text, font, fill=(255, 255, 255), center=False,
               stroke=0, stroke_fill=(0, 0, 0)):
    if center:
        bbox = d.textbbox((0, 0), text, font=font)
        x = xy[0] - (bbox[2] - bbox[0]) // 2
        y = xy[1]
    else:
        x, y = xy
    d.text((x, y), text, font=font, fill=fill,
           stroke_width=stroke, stroke_fill=stroke_fill)
    return d.textbbox((x, y), text, font=font)


def _image(im: Image.Image, px_scale: int = SCALE) -> Image.Image:
    if px_scale != 1:
        im = im.resize((im.width * px_scale, im.height * px_scale), Image.NEAREST)
    return im


class Renderer:
    def __init__(self, bank: Optional[SpriteBank] = None, scale: int = SCALE):
        self.bank = bank or SpriteBank(2)   # on-screen sprites 2x native
        self.scale = scale
        self._catalog = assets.ready_assets()

    # ---- elemental drawing --------------------------------------------------
    def draw_background(self, canvas: Image.Image, set_name: str):
        bg = assets.background(set_name)
        canvas.alpha_composite(bg, (0, 0))

    @staticmethod
    def active_beat(segment: broadcast.BroadcastSegment, frame: int):
        """Return (beat, beat_local_frame) for a global segment frame.

        The active beat is chosen by CUMULATIVE beat duration (Stage 5, F-1.1):
        each beat holds the screen for `beat.frames` frames, not the static
        `frame//90` slide, so animation cadence is driven by the beat's own
        length. Falls back to the last beat for any out-of-range frame.
        """
        beats = segment.beats or []
        if not beats:
            return None, 0
        total = sum(max(1, b.frames or 1) for b in beats)
        local = frame % total
        acc = 0
        for b in beats:
            dur = max(1, b.frames or 1)
            if local < acc + dur:
                return b, local - acc
            acc += dur
        last = beats[-1]
        return last, acc

    @staticmethod
    def _motion_for(c: broadcast.Cast, beat: Optional[broadcast.Beat]) -> str:
        """Per-cast motion for a frame: the ACTIVE beat's speaker animates with
        the beat's motion (talk/happy/walk/wave -- F-1.1); everyone else stays
        in the library's idle clip. `Cast.motion` is no longer authoritative
        (Gary built every cast as 'idle')."""
        if beat is not None and c.name == beat.speaker:
            return beat.motion or "idle"
        return "idle"

    def draw_cast(self, canvas: Image.Image, segment: broadcast.BroadcastSegment,
                  frame: int, beat: Optional[broadcast.Beat] = None,
                  walk_offset: float = 0.0):
        """Place + animate cast (movement library drives pose selection).

        Stage 5 (F-1.1): pose comes from the ACTIVE beat's motion for the
        speaker (feed Beat.motion through), not the frozen Cast.motion. A
        `walk` motion also slides the cast member horizontally across the slot
        so movement is a real cross, not a 2-frame bob.
        """
        n = len(segment.cast)
        base_w = 16 * 2           # 2x native sprite width
        spacing = WN // max(1, n + 1)   # (n1) was `(WN - base_w * 0)` -- dead multiply
        for i, c in enumerate(segment.cast):
            motion = self._motion_for(c, beat)
            poses, fps, loop = movement_library.play(c.name, motion)
            pose = poses[int(frame // max(1, round(6 / fps))) % len(poses)]
            img = self.bank.image(c.kind, pose)
            x = spacing * (i + 1) + base_w // 4
            y = HN - 46            # feet near dialogue box
            # walk motion: a real cross-slot slide (F-1.1, acceptance-1)
            if motion == "walk":
                x = int(x + walk_offset)
            canvas.alpha_composite(img, (int(x), int(y)))

    # Frank's first directive: SNES-native dialogue box
    def draw_dialogue(self, canvas: Image.Image, speaker: str, text: str,
                      char_count: int, cast_map: dict[str, str]):
        """Bordered SNES text box + portrait + typewriter reveal."""
        kind = cast_map.get(speaker, speaker)
        d = ImageDraw.Draw(canvas)
        box = (6, 138, WN - 6, HN - 8)
        # outer chrome border, inner black field
        d.rectangle(box, outline=(255, 255, 255), width=2)
        d.rectangle((box[0] + 2, box[1] + 2, box[2] - 2, box[3] - 2), fill=(8, 8, 24, 255))
        # portrait (head of speaking character) in the box corner
        try:
            port = self.bank.image(kind, "talk_a")
            canvas.alpha_composite(port, (box[0] + 6, box[1] + 6))
        except Exception:
            pass
        # typewriter reveal
        shown = text[:max(1, char_count)]
        font = _font(10)
        _draw_text(d, (box[0] + 40, box[1] + 12), shown, font, fill=(235, 235, 255))
        _draw_text(d, (box[0] + 40, box[1] + 28), speaker.upper(), font,
                   fill=(255, 210, 90), stroke=1)

    # ---- 90s chrome ---------------------------------------------------------
    def draw_bug(self, canvas: Image.Image, frame: int):
        d = ImageDraw.Draw(canvas)
        d.rectangle([WN - 34, 3, WN - 3, 15], outline=(0, 0, 0))
        _draw_text(d, (WN - 33, 4), "T3TV", _font(8), fill=(255, 255, 255), stroke=1)
        # tiny animated globe (90s CGI-logo vibe)
        cx = WN - 6
        cy = 9
        hue = (frame // 8) % 3
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3),
                  fill=(255, 200, 0) if hue == 0 else (0, 140, 255))

    def draw_rating(self, canvas: Image.Image, rating: str):
        d = ImageDraw.Draw(canvas)
        bbox = (WN - 40, 20, WN - 4, 32)
        d.rectangle(bbox, outline=(255, 255, 255))
        d.rectangle((bbox[0] + 1, bbox[1] + 1, bbox[2] - 1, bbox[3] - 1),
                    fill=(0, 0, 0, 200))
        _draw_text(d, (bbox[0] + 4, bbox[1] + 2), rating, _font(7),
                   fill=(255, 255, 255))

    def draw_lower_third(self, canvas: Image.Image, name: str, title: str, frame: int):
        """Beveled 90s lower-third (name + title box, bottom-left)."""
        d = ImageDraw.Draw(canvas)
        x0, y1 = 4, HN - 8
        x1 = x0 + (WN // 2) + 8
        y0 = y1 - 22
        d.rectangle([x0, y0, x1, y1], fill=(40, 40, 70, 255), outline=(255, 255, 255), width=1)
        # bevel edges (chrome) -- skip when ticker occupies bottom
        _draw_text(d, (x0 + 5, y0 + 2), (name or "").upper(), _font(9),
                   fill=(255, 215, 90), stroke=1)
        _draw_text(d, (x0 + 5, y0 + 14), (title or "").upper(), _font(7),
                   fill=(230, 230, 255))

    def draw_ticker(self, canvas: Image.Image, headlines: list[str], frame: int):
        if not headlines:
            return
        d = ImageDraw.Draw(canvas)
        strip = (0, HN - 8, WN, HN)
        d.rectangle(strip, fill=(0, 0, 0, 255))
        d.rectangle((strip[0], strip[1], strip[2], strip[1] + 1), fill=(255, 255, 255))
        joined = "  •  ".join((h or "").upper() for h in headlines)
        font = _font(8)
        w = d.textlength(joined, font=font)
        offset = frame % (int(w) + WN)
        _draw_text(d, (WN - offset, strip[1]), joined, font, fill=(255, 255, 255))

    # ---- bumper / promo / commercial (SNES full-screen art) ----------------
    def draw_bumper(self, canvas: Image.Image, title: str, frame: int):
        art = assets.promo_card("promo", title, "T3MPLATE TELEVISION NETWORK")
        canvas.alpha_composite(art, (0, 0))
        # animated chrome logo sweep
        d = ImageDraw.Draw(canvas)
        x = (frame * 3) % (WN + 40) - 40
        d.line([(x, 0), (x + 20, HN)], fill=(255, 255, 255, 60))

    def draw_full(self, elem: str, text: str = "", sub: str = ""):
        """Full-screen element (color bars / commercial / PSA / station id)."""
        if elem == "color_bars":
            img = Image.new("RGBA", NATIVE, (30, 30, 30, 255))
            ImageDraw.Draw(img)
            return img
        art = assets.promo_card(elem, text, sub)
        return art

    # ---- the frame pipeline --------------------------------------------------
    def frame(self, segment: broadcast.BroadcastSegment, frame: int,
              ticker_offset: int = 0) -> Image.Image:
        """Render one broadcast frame (native 256x224, pre-scanlines)."""
        canvas = Image.new("RGBA", NATIVE, (0, 0, 0, 255))
        self.draw_background(canvas, segment.background)
        # Stage 5 (F-1.1): the ACTIVE beat drives cast motion + dialogue cadence.
        beat, beat_frame = self.active_beat(segment, frame)
        walk_offset = (frame % 60 - 30) if (beat and beat.motion == "walk") else 0.0
        self.draw_cast(canvas, segment, beat_frame, beat=beat, walk_offset=walk_offset)

        # dialogue from the active beat (typewriter paced by beat-local frame)
        if beat is not None:
            cast_map = {c.name: c.kind for c in segment.cast}
            chars = (beat_frame % 90) * 2
            self.draw_dialogue(canvas, beat.speaker, beat.text, chars, cast_map)

        self.draw_rating(canvas, segment.rating)
        if segment.ticker:
            self.draw_ticker(canvas, segment.ticker, ticker_offset)
        else:
            self.draw_bug(canvas, frame)
        return canvas

    def _scanlines(self, img: Image.Image) -> Image.Image:
        """Upscale + apply CRT scanlines + subtle vignette."""
        img = _image(img, self.scale)
        w, h = img.size
        arr = np.asarray(img.convert("RGB")).astype(np.float32)
        # scanlines: darken odd rows every 2px (CRT shadow mask feel)
        mask = np.ones((h, 1, 1), dtype=np.float32)
        mask[1::2] = 0.82
        arr *= mask
        # subtle vignette
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt(((xx - cx) / (w / 2)) ** 2 + ((yy - cy) / (h / 2)) ** 2)
        arr *= (1.0 - 0.18 * np.clip(dist, 0, 1)[..., None])
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def render_segment(segment: broadcast.BroadcastSegment,
                   final=True, renderer: Optional[Renderer] = None,
                   fps: int = 0) -> Iterator[np.ndarray]:
    """Yield broadcast frames for a segment as RGB uint8 arrays (streamable).

    Renders bumper -> show beats (with commercials/promos interleaved) ->
    hand-off. Each yielded array is a full final-resolution frame for ffmpeg.

    Stage 5 (F-1.1): the show pass length is driven by the SUM of the beats'
    own `frames` durations (scaled by fps), not a rate-based `1 beat/sec` guess,
    so each beat's animation actually plays out.
    """
    r = renderer or Renderer()
    rate = fps or SETTINGS.rate
    beat_frames = sum(max(1, b.frames or 1) for b in (segment.beats or []))
    frames_total = max(1, int(rate / max(1, (SETTINGS.rate or 24)) * beat_frames))
    # bumper lead-in
    for f in range(20):
        if not segment.bumper:
            break
        c = Image.new("RGBA", NATIVE, (0, 0, 0, 255))
        r.draw_bumper(c, segment.title, f)
        img = r._scanlines(c) if final else c
        yield np.asarray(img)
    # show beats
    tick_off = 0
    for f in range(frames_total):
        tick_off = f * 4 % 300
        c = r.frame(segment, f, ticker_offset=tick_off)
        img = r._scanlines(c) if final else c
        yield np.asarray(img)
    # hand-off / coming-up promo
    for f in range(24):
        c = Image.new("RGBA", NATIVE, (0, 0, 0, 255))
        sub = segment.hand_off or "COMING UP NEXT"
        art = assets.promo_card("promo", segment.hand_off.replace(" is NEXT!", "") if segment.hand_off else "STAY TUNED", sub)
        c.alpha_composite(art, (0, 0))
        img = r._scanlines(c) if final else c
        yield np.asarray(img)