# HANDOFF — T3MPLATE TV STAGE 6 (HYGIENE) + STAGE 7 (STREAM AUDIO + A/V SYNC)

**Branch:** `t3mplt-finish-hygiene-stream` (off `7706132` = real main @ `E:\T3MPLATE_TV_NETWORK`)
**Worktree:** `C:\Users\frank\orca\workspaces\T3MPLATE_TV_NETWORK\t3mplt-finish-hygiene-stream`
**Audit basis:** `C:\Users\frank\orca\workspaces\T3MPLATE_TV_NETWORK\t3mplt-auditor\AUDIT.md`

**Commits (in order):**
1. `073f7d0` chore(hygiene): remove dead app/ + extractors/ stacks, garbage audio, broken root scripts (SLOP-1, audit F-2.4)
2. `4228c22` docs: commit research outputs + AUTHENTIC_ASSETS pointer to the correct capture route
3. `ff5e611` feat(stage7): stream audio+video (per-frame AAC) + A/V sync bound + per-airing audio novelty
4. `4c72d7f` test(stage7): A/V sync bound + per-airing audio novelty + RTMP audio+video + stderr-visibility regressions
5. `4686500` tool(stage7): RTMP gate driver (push real A/V segments to a local server for ffprobe)

**Status: DONE** — all 5 acceptance gates green.

---

## STAGE 6 — HYGIENE SWEEP (critique SLOP-1 + audit F-2.4)

### Removed (`git rm`)
- **`app/`** — the pygame/LLM "dead stack" (23 files): `station.py`, `streamer.py`,
  `broadcast_engine.py`, `snes_scene_engine.py`, `night_shift.py`, `living_world.py`,
  `gary.py`, etc.
- **`extractors/`** — the hand-rolled **noise ROM decoders** (13 files): `rom_audio_extractor.py`,
  `snes_rom_hacker.py`, `all_rom_extractor.py`, `tcrf_scraper.py`, `top_50_snes_games.py`, ...
- **Root scripts that imported the removed packages** (leftover traps): `run_bootstrap.py`,
  `bootstrap_living_world.py`, `bootstrap_tv_world.py`, `tcrf_scraper.py`, `tcrf_cache.json`,
  `data/tcrf_cache.json`.
- **Garbage audio per audit F-2.4**: `eb_fateful.wav` (128 B), `eb_katy.wav` (156 B),
  `mk_fatality.wav` (100 B), `mk_round.wav` (72 B) — all 0.00 s — plus the tiny 0.04 s
  `super_mario_world_coin.wav` / `super_mario_world_jump_sfx.wav` / `jump.wav`.
- The fake 10-byte `assets/t3mplate_tv.sfc`, `roms/`, and `ROM_SOURCE/unzipped*` were **already
  absent** (`.gitignore` ignores `*.sfc` / `roms/`); nothing to remove and none resurrected.
- The dead `bed_game_show/bed_infomercial/bed_news.wav` synth subdirs were also already gone.

Retained live path only: `assets/audio/` now holds just `manifest.json` + the four real
emulator-captured beds (`real_smw_{title,overworld,level,castle}.wav`).

### `AUTHENTIC_ASSETS.md` (new)
Short ASCII pointer to the **correct** capture route (RetroArch emulator-capture: snes9x DSP →
FFmpeg record for audio, screenshot/key-gate for visuals). Documents explicitly that the dead
`app/`/`extractors/` static-ROM stacks are **removed, not kept as a fix-me trap** — no one should
try to resurrect them, and `*.sfc` files stay untracked.

### The three `RESEARCH_*.md` committed
`RESEARCH_90S_TV.md`, `RESEARCH_ASSETS.md`, `RESEARCH_SNES.md` (untracked at main root) copied
into the worktree and committed.

### Gate 1 (Stage 6): `git status` clean ✅
Only the live `tvn/` path + `AUTHENTIC_ASSETS.md` + RESEARCH docs are tracked. Verified final:
`git status --short` shows **0 entries**.

---

## STAGE 7 — STREAM AUDIO + A/V SYNC (audit F-2.5, WEAK-3, BUG-1)

### 1. `tvn/output.py` — `stream_rtmp` is now AUDIO+VIDEO (WEAK-3)
- Accepts an iterator of locked **`(frame, pcm_chunk)` pairs** (one PCM chunk per video frame).
- Muxes real bed audio through **per-frame AAC**: `-af aresample=async=1:first_pts=0,asetnsamples=n=1024`
  then `-c:a aac`. The pushed stream carries a real `aac (LC)` track, not silent video.
- **stderr is NEVER DEVNULL'd in stream mode** (`stderr=None`, ignored `silent`): a dead push /
  dropped connection logs to stderr and a `BrokenPipeError` ends the loop loudly — the old
  `silent=True -> DEVNULL` **silent-dead-push** bug is gone (BUG-1).

### 2. `tvn/output.py` — `write_video`: A/V sync bound (F-2.5)
- Audio is **padded/trimmed to the exact video frame count** (`_pad_audio_to_frames`) and muxed
  with `-shortest`.
- Post-write assert `_av_sync_ok(...)` requires `abs(audio_dur - video_dur) < 0.2 s`, else
  `RuntimeError`.

### 3. `tvn/audio.py` — per-airing audio novelty (F-2.5)
- `Mixer.track_for` cache key is now `fmt:seconds:variant`. A per-airing `variant` rotates the
  **start phase into the real bed**, so consecutive same-slot airings carry **DIFFERENT audio** —
  still real SNES audio, just a different window of it (never fake, never byte-identical).
- Same `variant` is cached & stable within an airing.

### 4. Wiring
- `runner`: `segment_audio(..., variant=seed)`; `_record_cycle` passes the fresh per-airing seed.
- `run_forever --stream`: one producer decides the segment ONCE and yields locked `(frame, chunk)`
  pairs with a per-airing `variant`, so on-screen content and aired music are the SAME segment.
- `run_24_7.py`: "video-only MVP" note updated → real audio+video.

---

## ACCEPTANCE GATES (all green, with real evidence)

| # | Gate | Evidence |
|---|---|---|
| 1 | `git status` clean | `0` entries after final commit |
| 2 | `--stream` local RTMP shows video+audio | ffprobe `rtmp://localhost:1935/live` → `h264` + `aac`; ffmpeg log `Stream #0:1: Audio: aac (LC) 22050 Hz mono`; MediaMTX `2 tracks (H264, MPEG-4 Audio)` |
| 3 | A/V sync `abs(audio-video) < 0.2s`, no silent-fail | real MP4: `video 8.875s` vs `audio 8.916s` → **0.04s**; stderr always surfaced |
| 4 | Consecutive same-slot airings differ in AUDIO + regression | `test_same_slot_airings_differ_in_audio_with_variant` (unit) |
| 5 | pytest 91+ & run.py non-blank MP4 | **98 passed** (91 + 7 new); `run.py --seconds 12` → 222 KB non-blank MP4 (YAVG ≈ 74) |

### Gate 2 real run (this machine)
Local **MediaMTX v1.20.0** on `:1935`, push via `scripts/_stage7_rtmp_ping.py`:
```
ffprobe rtmp://localhost:1935/live
  Stream #0:0: video h264  512x448 24 fps
  Stream #0:1: audio aac  22050 Hz mono
```
`stream_rtmp` returned code **0**.

### Gate 3 real A/V sync (ffprobe on `OUTPUT/broadcast/demo.mp4`)
```
video: duration 8.875000
audio: duration 8.916463   → diff 0.041 s (< 0.2 s)
```

---

## Regression tests added (`tests_mvp/test_stage7_av.py`, 7 tests)
- `test_same_slot_airings_differ_in_audio_with_variant` — F-2.5 audio novelty
- `test_same_variant_is_cached_and_stable`
- `test_av_sync_ok_true_within_tolerance` — the 0.2 s bound
- `test_pad_audio_to_exact_frame_count` — pad/trim to frame count
- `test_write_video_av_locked` — end-to-end ffprobe `abs < 0.2 s`
- `test_stream_rtmp_muxes_audio_and_keeps_stderr_visible` — WEAK-3 + BUG-1
- `test_stream_rtmp_pair_form_writes_locked_av` — (frame, chunk) A/V lock

## Notes for the next builder
- `scripts/_stage7_rtmp_ping.py` is a bounded, self-terminating driver for reproducing the RTMP
  gate on any machine (point it at your own server or a local MediaMTX instance).
- The `tvn/audio.py` `capture_spc_via_emulator` full-SPC round-trip remains documented-future
  (no SPC player on PATH this machine); the staged real emulator-captured beds are the shipped
  audio source, per `AUTHENTIC_ASSETS.md`.
- **Parallel branch note:** `t3mplt-finish-motion` (animation) was intentionally NOT touched here;
  Stage 7 changes are confined to `tvn/{output,audio,runner}.py` + `run_24_7.py` so the two finish
  branches do not collide on `tvn/renderer.py`/`sprites.py`.