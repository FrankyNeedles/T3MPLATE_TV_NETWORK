#!/usr/bin/env python3
"""Stage 5 F-3.1/F-3.2 evidence: live-style run on a REAL persistent DB.

Airs several real grid-slot titles through the production path
(gary.decide + world.on_air(show=seg.title, genre=seg.fmt)) -- exactly what
runner._record_cycle does, minus the ffmpeg encode -- and proves:
  * episode_count/title/rating ADVANCE for real grid titles (not just seeded
    'X of T3TV' names), and
  * relationship arcs are populated on the persistent DB after reopen.
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tvn import gary, programming
from tvn.world import open_world, Show, Relationship, Character


def main():
    db = Path("data/lore/living_world_ev.db")
    if db.exists():
        db.unlink()
    w = open_world(f"sqlite:///{db}")
    g = gary.GaryPD(w)

    # air a spread of REAL grid slots multiple times each (live-style)
    slots = [programming.GRID[11],      # Super Playhouse (cartoon)
             programming.GRID[0],       # Late Night with Wario
             programming.GRID[6],       # T3TV Morning Update (news)
             programming.GRID[13],      # The Rings of Hyrule (soap)
             programming.GRID[7]]       # Mushroom Morning (morning)
    for rep in range(2):
        for slot in slots:
            seg = g.decide(slot, seed=rep)
            w.on_air([c.name for c in seg.cast], show=seg.title,
                     tension=2 if slot.daypart in ("prime", "access") else 0,
                     genre=slot.fmt)

    print("=== F-3.1 episode continuity on real grid titles ===")
    for slot in slots:
        s = w.session.query(Show).filter_by(name=slot.title).first()
        status = "OK" if s and s.episode_count >= 2 and s.episode_title else "MISSING"
        print(f"  {slot.title!r:34s} genre={slot.fmt:12s} ep={s.episode_count if s else 0}"
              f" title={s.episode_title if s else ''!r} rating={s.rating if s else 0} -> {status}")

    ok31 = all(
        (w.session.query(Show).filter_by(name=s.title).first()
         and w.session.query(Show).filter_by(name=s.title).first().episode_count >= 2)
        for s in slots)

    print("=== F-3.2 arcs backfilled on persistent DB ===")
    rels = w.session.query(Relationship).all()
    filled = sum(1 for r in rels if r.arc_label)
    print(f"  relationship arcs: {filled}/{len(rels)} populated")
    for r in rels:
        print(f"    {r.character1.name:6s} ~ {r.character2.name:6s} -> {r.arc_label!r}")
    ok32 = filled >= 6 and all(
        r.arc_label for r in rels
        if (r.character1.name, r.character2.name) in {
            ("mario", "luigi"), ("mario", "bowser"), ("wario", "luigi"),
            ("link", "zelda"), ("peach", "mario"), ("yoshi", "mario")})

    # reopen to prove the DB AND the backfill survive a real restart
    w.session.close(); w.engine.dispose()
    w2 = open_world(f"sqlite:///{db}")
    rel2 = w2._find_rel(w2.get_character("mario").id, w2.get_character("bowser").id)
    persist = rel2 is not None and rel2.arc_label == "The Eternal Rivalry"
    print(f"  after reopen, mario~bowser arc preserved: {persist}")

    verdict = "PASS" if (ok31 and ok32 and persist) else "FAIL"
    print(f"VERDICT: {verdict} (episodes advance + arcs persist on real DB)")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())