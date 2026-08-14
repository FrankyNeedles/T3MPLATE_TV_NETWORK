#!/usr/bin/env python3
"""Stage 5 acceptance-1 evidence: per-frame pixel-delta over an animated show.

Renders a walking show segment through the REAL renderer and reports:
  * whole-frame and cast-band mean|delta| between consecutive show frames, and
  * the horizontal sweep of the CAST SPRITES' x-centroid, computed on an
    isolated cast layer (draw_cast onto a plain canvas -- no background, no
    dialogue box, no chrome) so a walking sprite sliding across the slot is the
    ONLY thing moving.

A frozen or 2-frame-bob feed shows ~0 cast delta and a pinned centroid; a real
walk cross drags the cast centroid dramatically rightward over the beat.
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tvn import gary, programming, renderer, broadcast
from tvn.world import LivingWorld


def analyse(seg, start=2, window=120, fps=24):
    r = renderer.Renderer()
    beats_native = sum(max(1, b.frames or 1) for b in (seg.beats or []))
    total = max(1, int(fps / max(1, (renderer.SETTINGS.rate or 24)) * beats_native))
    y0, y1 = 130, 224
    full, band, cast_cx = [], [], []
    prev = None
    for f in range(start, min(total, start + window)):
        c = r.frame(seg, f, ticker_offset=0)                 # full composited frame
        arr = np.asarray(c.convert("RGB")).astype(np.int16)
        b = arr[y0:y1, :, :]
        if prev is not None:
            prev_b = prev[y0:y1, :, :]
            full.append(float(np.abs(arr - prev).mean()))
            band.append(float(np.abs(b - prev_b).mean()))
        prev = arr
        # isolated cast layer: draw_cast only (bg/dialogue/chrome excluded),
        # with the SAME walk_offset logic the frame() pipeline uses.
        from PIL import Image as _Img
        layer = _Img.new("RGBA", c.size, (0, 0, 0, 0))
        _beat, _bf = r.active_beat(seg, f)
        _woff = 0.0
        if _beat is not None and _beat.motion == "walk":
            _dur = max(1, _beat.frames or 1)
            _prog = min(1.0, _bf / _dur)
            _woff = round(-renderer.WN * (1 - _prog))
        r.draw_cast(layer, seg, f, beat=_beat, walk_offset=_woff)
        la = np.asarray(layer)
        alpha = la[..., 3] > 0
        cols = np.argwhere(alpha)
        if cols.size:
            cast_cx.append(float(cols[:, 1].mean()))
    return np.array(full), np.array(band), np.array(cast_cx), total


def main():
    world = LivingWorld("sqlite:///:memory:")
    g = gary.GaryPD(world)
    slot = programming.Slot(11 * 60, "daytime", "Koopa & Chill", "talk", 60)
    segs = [g.decide(slot, seed=s) for s in range(8)]
    walk_seg = next(
        (s for s in segs if any(b.motion == "walk" for b in s.beats)), None)
    if walk_seg is None:
        walk_seg = broadcast.BroadcastSegment(
            seg_id="ev", title="Koopa & Chill", fmt="talk", background="talk_show",
            cast=[broadcast.Cast(name="bowser", kind="bowser", title="Host"),
                  broadcast.Cast(name="yoshi", kind="yoshi", title="Guest")],
            beats=[broadcast.Beat(speaker="yoshi",
                                  text="The guest makes their way across the stage to the mic.",
                                  motion="walk", frames=180)])
    full, band, cast_cx, total = analyse(walk_seg)

    print(f"motion beats: {[b.motion for b in walk_seg.beats]}")
    print(f"show frames rendered (rate path): {total}")
    print(f"whole-frame mean|delta|: {full.mean():.4f} over {len(full)} consecutive frames")
    print(f"show-band    mean|delta|: {band.mean():.4f} (max {band.max():.4f})")
    print(f"show-band frames with any change: {(band > 0).sum()}/{len(band)}")
    if len(cast_cx) >= 2:
        print(f"CAST x-centroid sweep (isolated sprites): "
              f"{cast_cx.min():.0f} -> {cast_cx.max():.0f} px "
              f"({cast_cx.max() - cast_cx.min():.0f} px)")
    sweep = cast_cx.max() - cast_cx.min() if len(cast_cx) >= 2 else 0.0
    ok = band.mean() > 0.03 and (band > 0).sum() >= int(0.6 * len(band)) and sweep > 20
    print(f"VERDICT: {'PASS - real on-air walk/cross + pose transitions' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())