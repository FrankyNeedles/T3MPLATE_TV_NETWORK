# T3MPLATE TV Network — MVP v0.9-stage7

**Tag:** `v0.9-stage7` @ `09765f4` (Merge branch `t3mplt-finish-hygiene-stream`)
**Published:** https://github.com/FrankyNeedles/T3MPLATE_TV_NETWORK/releases/tag/v0.9-stage7
**What it is:** A headless, 24/7 runtime for *“the SNES world presented as a living 90s network TV broadcast.”* A new `tvn/` package (SQLAlchemy + Pillow + numpy + ffmpeg) renders the broadcast as a living broadcast — content is **caused by the world**, not random slot-machine picks — and records a playable MP4 (`h264` video + `aac` audio, 512×448) or streams A/V-synced RTMP.

> Honesty: this is an MVP. It ships **real SNES audio**, **real SNES pixels**, and **on-air motion** — but visuals are curated emulator captures (not ROM rips run live), and the full live gameplay feed under 90s chrome is the documented next step.

---

## 🟢 Green gates (this commit)

| Gate | Evidence |
|---|---|
| pytest | **113 passed** |
| run.py demo | `--seconds 12` → non-blank **512×448 h264 + aac** MP4 (~148 KB), `ffprobe` confirmed |
| A/V sync | audio/video duration diff **< 0.04 s** (`abs(audio_dur - video_dur) < 0.2 s` asserted in `write_video`) |
| Stream | `--stream` pushes **real audio + video** to RTMP (per-frame AAC, `aac (LC)` track) |

---

## Stacked handoff: Stages 1–7

### Stage 1 — Real SNES Visuals
- **Curated SMW sprites** (Mario, Bowser, Yoshi) from Spriters Resource, provenance-tracked (`method:curated_rip`, SHA256 in manifest).
- **Emulator-captured SMW backgrounds** (8 real sets: news_studio, talk_show, game_show, studio, cartoon_house, diner, city, sports_arena) via RetroArch + snes9x, gated and honestly cataloged.
- Procedural painter + synth bed remain as **graceful fallbacks** — a missing frame never kills the feed.

### Stage 2 — Real SNES Audio
- **4 real emulator-captured SMW beds** (`real_smw_{title,overworld,level,castle}.wav`, ~794 KB each, mono 22050 Hz) replace the synth bed as defaults.
- `ensure_bed()` maps each format/show to a real bed (news→title, morning→overworld, etc.).
- `capture_spc_via_emulator` auto-runs the full `.spc → WAV` round-trip when a real SPC player is on PATH; otherwise returns a staged real bed or `None` (never a fake file).

### Stage 3 — Make 24/7 LIVING
- **Seeded novelty**: every airing mints a fresh seed; consecutive airings are never byte-identical (9/10 byte-identical → **0/18 identical**).
- **Format-coherent beats**: infomercial/PSA slots never carry feud/friendship content (locked to promo/ratings/ticker).
- **Causal world mutations**: every `on_air()` change carries a real `reason` tied to an in-world event and chains via `caused_by_event_id` (a causal DAG, not a flat log).

### Stage 4 — Balance the World (BUG-2)
- **Mean-reverting drift**: relationships no longer ratchet to ±100; they oscillate around a signed baseline (~±65) instead of saturating.
- **Hour-independent tick**: `world.tick()` fires on a monotonic schedule regardless of wall-clock start time (fixes multi-day stalls for 9 AM starts).
- Popularity reverts per-character toward a celebrity baseline (no shared-delta clamping bug).

### Stage 5 — Finish Motion (F-1.1, F-3.1/F-3.2, F-1.2/1.3/1.4)
- **On-air animation**: `Beat.motion` flows through `draw_cast` — the speaker animates (real frame-to-frame deltas, 242 distinct frames of 287), others idle.
- **Episode continuity**: `on_air("Super Playhouse")` now upserts a `Show` from the grid-slot title so `episode_count`/`episode_title` actually advance in the live loop.
- **Arc backfill**: directed relationship arcs auto-backfilled on every DB open (idempotent); 6/6 seeded bonds populated (previously 0/10 on live DB).
- **Sprite re-keying**: Yoshi/Bowser transparency corrected; `real_art` gate tightened (rejects opaque-box leaks).

### Stage 6 — Hygiene Sweep (SLOP-1, audit F-2.4)
- **Removed dead stacks**: `app/` (pygame/LLM dead code, 23 files), `extractors/` (hand-rolled noise ROM decoders, 13 files), broken root scripts (`run_bootstrap.py`, `bootstrap_*.py`, `tcrf_scraper.py`).
- **Removed garbage audio**: all 0-byte/silent/fake `.wav` files and the fake 10-byte `.sfc`.
- `git status` clean after the sweep. `AUTHENTIC_ASSETS.md` points to the correct RetroArch capture route.

### Stage 7 — Stream Audio + A/V Sync (F-2.5, WEAK-3, BUG-1)
- **`stream_rtmp` is now audio+video**: muxes real bed audio via per-frame AAC (`-af aresample=async=1:first_pts=0,asetnsamples=n=1024 -c:a aac`), not silent video.
- **stderr always surfaced**: the `silent=True → DEVNULL` silent-dead-push bug is fixed; a dead stream logs loudly.
- **Per-airing audio novelty**: `Mixer.track_for` cache key includes `variant`; consecutive same-slot airings carry **different real audio** (same SNES bed, different phase window — never fake, never byte-identical).
- **A/V sync bound**: `_pad_audio_to_frames` locks audio to the exact video frame count; `write_video` asserts `abs(audio_dur - video_dur) < 0.2 s` (measured 0.041 s).

---

## What works (verified)

- ✅ 113 unit tests pass (`tests_mvp/`).
- ✅ End-to-end broadcast: `python run.py --seconds 12` → `OUTPUT/broadcast/demo.mp4` (non-blank 512×448, h264 video + aac audio, real SMW content visible).
- ✅ 24/7 record mode (`run_24_7.py`) airs the current grid slot, writes MP4 chunks, advances the living world.
- ✅ Headless — no display, no pygame, no window. Runs anywhere with ffmpeg on PATH + Python 3.11+.
- ✅ Content is world-caused: top-seed feuds (Mario↔Bowser) thread dialogue through the schedule; relationship scores drift and revert realistically.
- ✅ Real SNES audio: 4 emulator-captured SMW beds, non-silent, format-mapped.
- ✅ On-air sprite animation (talk/walk/happy cycles), not static idle.
- ✅ A/V-synced recording (0.04 s diff) and A/V streaming to RTMP.
- ✅ Clean reproducibility: fresh clone → venv → install → 113 tests pass → `run.py` regenerates a non-blank MP4.

## What's next (ranked)

1. **Full 24/7 living**: wire sweeps stunts, night-identity blocks (Must-See/TGIF/Sunday), and series lifecycle (pitch→pilot→series→syndication→cancellation→seeking-work).
2. **Authentic live gameplay**: run real ROMs under RetroArch into the ffmpeg pipeline (actual gameplay under the 90s overlay) OR curate additional ripped sprite sheets — replacing procedural placeholders.
3. **SPC player render**: the `.spc → WAV` round-trip is toolchain-blocked on this machine (no C compiler / no installable SPC player); it auto-activates `capture_spc_via_emulator` when a real player appears.
4. **Rich movement choreography**: extend the MovementLibrary with per-scene walk-ons, sit, face-offs, and set/scene transitions.
5. **LLM Gary layer**: feed `world_digest()` into a model for richer authored dialogue; keep the deterministic skeleton as the safety net.
6. **Full grid fidelity**: complete all rotation/stunt variants from `RESEARCH_90S_TV.md`.

---

## Reproducing this release

```bash
git clone https://github.com/FrankyNeedles/T3MPLATE_TV_NETWORK.git
cd T3MPLATE_TV_NETWORK
python -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest            # 113 passed
.venv/bin/python run.py --seconds 12   # OUTPUT/broadcast/demo.mp4 — ffprobe: h264 512x448 + aac
ffprobe OUTPUT/broadcast/demo.mp4     # verify non-blank, real audio
```

> ffmpeg/ffprobe must be on PATH (the MVP shell can install via WinGet: `Gyan.FFmpeg` on Windows, or `brew install ffmpeg` on macOS).
