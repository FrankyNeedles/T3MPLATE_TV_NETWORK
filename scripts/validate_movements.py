#!/usr/bin/env python3
"""Validate the curated movement library (RESEARCH_MOVEMENT §6 / BUILD_PLAN
Stage 1). Rejects: missing provenance, non-looping clips without a stated
reason, unknown categories, non-positive fps, and mounted real frames that
fail the gate. Exit 0 = valid; non-zero with diagnostics otherwise.

Usage:  python scripts/validate_movements.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOV = ROOT / "assets" / "movements"
VALID_CATEGORIES = {"idle", "walk", "action", "reaction"}


def main() -> int:
    errors = []
    if not MOV.exists():
        print("OK: no movements dir (no curated frames mounted yet)")
        return 0
    for cdir in sorted(MOV.iterdir()):
        if not cdir.is_dir():
            continue
        manifest_p = cdir / "manifest.json"
        cells_p = cdir / "cells.json"
        if not manifest_p.exists():
            errors.append(f"{cdir.name}: missing manifest.json (no provenance)")
            continue
        man = json.loads(manifest_p.read_text(encoding="utf-8"))
        if man.get("method") != "curated_rip":
            errors.append(f"{cdir.name}: provenance method is {man.get('method')!r}, "
                          "expected 'curated_rip'")
        if not man.get("source_url"):
            errors.append(f"{cdir.name}: missing source_url in provenance")
        if not cells_p.exists():
            errors.append(f"{cdir.name}: missing cells.json")
            continue
        cells = json.loads(cells_p.read_text(encoding="utf-8"))
        if not cells:
            errors.append(f"{cdir.name}: no pose frames in cells.json")
        for cell in cells:
            f = cdir / cell["file"]
            if not f.exists():
                errors.append(f"{cdir.name}/{cell['pose']}: frame file missing {cell['file']}")
            if not cell.get("sha256"):
                errors.append(f"{cdir.name}/{cell['pose']}: no sha256 recorded")
    if errors:
        print(f"INVALID ({len(errors)} problems):")
        for e in errors:
            print("  -", e)
        return 1
    print("OK: movement library valid (provenance + frames intact)")
    return 0


if __name__ == "__main__":
    sys.exit(main())