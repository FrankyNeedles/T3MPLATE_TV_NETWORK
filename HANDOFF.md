# HANDOFF — T3MPLATE TV WORLD: Minimal Honest MVP

**Branch:** `t3mplt-build-mvp` (Orca worker worktree)
**Built:** autonomously from the research recipe (RESEARCH_90S_TV / RESEARCH_SNES /
RESEARCH_ASSETS / RESEARCH_LIVING) + analysis autopsy (ANALYSIS.md).
**Verdict followed:** *revive the idea, not the stack.*

---

## 1. What was built

A clean, **headless, 24/7** runtime for the core vision — *"the SNES world presented
as a living 90s network TV broadcast."* A new `tvn/` package replaces the dead
pygame/sounddevice stack with SQLAlchemy + Pillow + numpy + ffmpeg. The broadcast
**actually renders continuity** and records a playable MP4 (interleaved video `h264`
+ `aac` audio) via ffmpeg, and can stream to Twitch.

### Architecture (the loop, world → content → render → record)
```
living_world.tick()  (night maintenance)
  → programming.get_slot()   fixed 90s daily grid → current show/format/daypart
  → gary.decide(slot)        world-aware beat selector → BroadcastSegment
  → renderer.render_segment  SNES dialogue + chrome + movement (Pillow, headless)
  → world.on_air(...)        CAUSAL feedback: co-hosts drift, ratings move
  → ffmpeg                   record MP4 chunk and/or continuous RTMP
```

### Files
| Module | Role |
|---|---|
| `tvn/world.py` | SQLAlchemy ORM (Character/Relationship/Career/Show/RunningGag/TimelineEvent), curated 9-char SNES cast, `world_digest()`, **causal** `on_air()`, `tick()`, `morning_report()`, stale-schema migration |
| `tvn/gary.py` | **Restored `GaryDecision`** (the deleted class behind the autopsy's root cause) + world-aware **beat selector** (feud/friendship/gag/seeking-work/ratings) driving dialogue from live world-state — zero-LLM |
| `tvn/programming.py` | **Fixed 90s daily grid** (24 slots, real dayparts), pod grammar (`promo → national×N → local → PSA → station_id`), hand-off builder |
| `tvn/sprites.py` | Curated **SNES 15-bit-paletted** pixel cast + pose/animation frames (idle/talk/walk/happy/jump/attack) |
| `tvn/animation.py` | **Movement Library** (Frank's concept): reusable motion clips attachable to any scene/event; safe idle fallback |
| `tvn/assets.py` | SNES set backgrounds, **full-screen SNES promo-art** commercial/PSA cards, deterministic **noise-battery gates**, honest append-only catalog (`method:"procedural_curated"`) |
| `tvn/renderer.py` | Headless Pillow renderer: **SNES-native dialogue box** (border+portrait+typewriter), 90s chrome (lower-third, ticker, bug, rating), scanlines+vignette |
| `tvn/audio.py` | First-class audio: honest **synth bed** today + **SPC-emulator-capture hook** (`capture_spc_via_emulator`) for real SNES music later |
| `tvn/output.py` | ffmpeg: pipes RGB frames → MP4 (video+audio) or continuous RTMP |
| `tvn/runner.py` | the 24/7 loop; `run_once` / `run_forever` |
| `run.py` | one-shot demo broadcast + world digest + morning report + verify hint |
| `run_24_7.py` | `--record` (default, append-only MP4 chunks) / `--stream` (Twitch, video-only) |

## 2. Design directions folded in (from Frank)
- **SNES-native dialogue boxes** — bordered text box with character portrait + typewriter reveal (the SNES speech-box look) — `renderer.draw_dialogue`.
- **90s chrome, drawn as SNES** — chrome/bevel lower-thirds, scrolling ticker, corner bug + animated globe, TV rating; all composited on SNES sets with SNES-palette pixel art, then scanlines so it reads "broadcast."
- **SNES full-screen promo art as the commercial/PSA language** — `assets.promo_card(...)` draws the big full-screen banner/title screen used during breaks, per Frank's third directive.
- **Movement as a library** — `tvn/animation.py` `MovementLibrary`; clips are attachable to any scene/event and drive real sprite animation (talk/walk/happy bounce) on air. Unknown motion is safe (idle), so a missing move never kills the feed.
- **Audio first-class** — MVP ships a real audible chiptune bed (honest `method:"synth"`); the **honest SPC route (emulator capture → SPC player → WAV)** is designed as the pluggable next step; a real SPC-rendered WAV dropped in `assets/audio/` is auto-preferred.

## 3. How to run
```bash
# in the worktree t3mplt-build-mvp
python -m venv .venv-mvp            # Python 3.11/3.12
.venv-mvp/Scripts/python -m pip install -r requirements.txt   # + ffmpeg on PATH

# one-shot demo (records OUTPUT/broadcast/demo.mp4, prints world digest + report)
.venv-mvp/Scripts/python run.py --seconds 20

# 24/7 record mode (append-only MP4 chunks per aired segment; Ctrl+C to stop)
.venv-mvp/Scripts/python run_24_7.py

# live to Twitch (needs TWITCH_STREAM_KEY in .env) — video-only in this MVP
.venv-mvp/Scripts/python run_24_7.py --stream

# run the unit suite (44 tests)
.venv-mvp/Scripts/python -m pytest
# verify a recording is real: ffprobe OUTPUT/broadcast/demo.mp4
```

## 4. What works / doesn't (honest)
**Works & verified:**
- ✅ 44/44 unit tests pass (`tests_mvp/`).
- ✅ End-to-end single broadcast: `run.py --seconds 16` → **512×448 h264 + aac, 16.3s, non-blank** (probed via ffprobe/signalstats), interleaved audio.
- ✅ 24/7 record mode airs the current grid slot, writes MP4 chunks, advances the world.
- ✅ Content is **caused by the world**: top seed feud (Mario↔Bowser) threads dialogue through the schedule; `on_air` logs causal relationship deltas into the morning report.
- ✅ `GaryDecision` restored; Gary decides with zero LLM/API key.
- ✅ Asset gates: all cast + backgrounds pass the RESEARCH_ASSETS content gates; catalog is honest (`procedural_curated`, never claimed as ROM rips).

**Doesn't / limited (deliberate MVP scope):**
- ❌ Live Twitch stream is **video-only** in this MVP (audio-on-RTMP needs per-frame AAC sync — next step).
- ❌ **Real SNES music/SFX not captured yet** — via SPC emulator capture (`audio.capture_spc_via_emulator`), the honest route; currently synth bed only.
- ❌ Visuals are **procedurally-drawn SNES-palette placeholders, not real ROM rips** — the authentic path (run real ROMs under RetroArch into the pipeline, or drop curated ripped sprites) is the documented upgrade.
- ⚠️ The broadcast renders a beat/slide-show cadence (dialogue typewriter + sprite animation), not full 24fps gameplay — enough to prove the vision, not yet seamless video.
- ⚠️ Grid uses a broad-shape 24-slot table; the full RESEARCH_90S grid (all rotation/stunt variants) is partially implemented.
- ⚠️ Sun-Mon prime night-identity blocks & sweeps stunt rotation are stubbed (not wired into slot selection).

## 5. What's next (ranked)
1. **Real SNES audio**: script snes9x/RetroArch to save-SPC per ROM → render WAV → drop in `assets/audio/`; renderer/mixer already auto-prefers them.
2. **Authentic visuals**: run real ROMs under RetroArch into the ffmpeg pipeline (broadcast actual gameplay under the 90s overlay) OR curate ripped sprite sheets + `.pal` — replace placeholders, keep the catalog gate.
3. **Audio on live RTMP** (frame-synced AAC) so `--stream` is audio+video.
4. **Rich movements/scenes**: extend the MovementLibrary with per-scene choreography (walk-on, sit, face-off) and drive set/scene transitions.
5. **LLM Gary layer** on top of the (green) fallback: feed `world_digest()` into a model for richer authored dialogue; keep the deterministic skeleton as the safety net.
6. Full grid fidelity: night-identity blocks (Must-See/TGIF/Sunday), sweeps stunts, series lifecycle (pitch→pilot→series→syndication→cancellation→seeking-work loop — partially done in world.tick).

## 6. Verification evidence
- `python -m pytest` → **44 passed**.
- `ffprobe OUTPUT/broadcast/demo.mp4` → `Duration: 00:00:16.3, Video: h264 yuv420p 512x448 24fps, Audio: aac 22050Hz mono`.
- Frame stats (`signalstats` YAVG mean ~50–92, std ~64–74) → **non-blank** (not black/garbage).
- 24/7 record smoke: `[12:43:01] airing -> 20260813_124243_soap.mp4` (289 KB real h264).
- Morning report shows causal chain: `link & zelda co-hosted on The Rings of Hyrule (score 69, +4 delta)`.

## 7. Substance-over-slop checks done
- No hand-rolled ROM extractor (research proved that = noise). Assets are honestly `procedural_curated`, gated by content checks (dimensions, alpha coverage, used-colour ≤15, bbox ratio) — not metadata-only.
- The old broken `app/` stack is untouched; this runs fresh on `tvn/`.
- No fabricated "done" claim: this is an honest Working/Not-Working MVP, opened for the next CC workstream.