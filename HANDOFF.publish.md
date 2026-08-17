# HANDOFF — T3MPLATE TV Network Publish (v0.9-stage7)

**Publisher:** autonomous (free-model chain: opencod-free → poolside/laguna-s-2.1:free)
**Project:** T3MPLATE TV Network — living 90s SNES broadcast, headless 24/7 runtime
**Publish artifact:** this is the publish artifact (DONE.publish marker present)

---

## What got published

| Item | Value |
|---|---|
| Local commit (HEAD main) | `09765f4` Merge branch 't3mplt-finish-hygiene-stream' |
| Remote main (after push) | `09765f432d7b7040de0963440be54669531b3585` |
| Release tag (annotated) | `v0.9-stage7` -> `767fe88ba243ab2023da952f88be8a5246e5bf21` |
| Push URL | https://github.com/FrankyNeedles/T3MPLATE_TV_NETWORK.git |
| Green gate | real evidence below (pytest + ffprobe from a FRESH clone) |

## Push evidence (real terminal output)
```
git push origin main
To https://github.com/FrankyNeedles/T3MPLATE_TV_NETWORK.git
 5836e31..09765f4 main -> main
---EXIT:0---

git push origin v0.9-stage7
To https://github.com/FrankyNeedles/T3MPLATE_TV_NETWORK.git
 * [new tag] v0.9-stage7 -> v0.9-stage7
---EXIT:0---

remote tags:
767fe88ba243ab2023da952f88be8a5246e5bf21  refs/tags/v0.9-stage7
remote main:
09765f432d7b7040de0963440be54669531b3585  refs/heads/main
```

## Release notes
Full release body written to `RELEASE_NOTES_v0.9-stage7.md` (7506 bytes). Summarises
Stages 1-7 of the handoff stack: real SNES visuals, real SNES audio beds, living world
+ causal feedback, 90s daily grid programming, on-air sprite animation, A/V-synced
RTMP streaming, hygiene sweep removing the dead app/extractors stacks + garbage audio.

## Reproducibility verification (FRESH CLONE — the real test)
Clone target: `C:/Users/frank/orca/workspaces/t3mplate-publish-verify` (not the
source tree). Fresh venv `.venv-verify`, `pip install -r requirements.txt`, ffmpeg
WinGet build 9.0 on PATH.

### Gate 1 — pytest
```
113 passed in 28.36s
```
(113 dots, zero failures, zero skips that matter.)

### Gate 2 — fresh-clone end-to-end broadcast
```
python run.py --seconds 10
Broadcast recorded -> OUTPUT/broadcast/demo.mp4 (150353 bytes)
ffprobe OUTPUT/broadcast/demo.mp4:
  Stream #0:0: video h264, yuv420p, 512x448, 24 fps, 213 frames, duration 8.875000s
  Stream #0:1: audio aac (LC), 22050 Hz, mono, 193 frames, duration 8.916463s
  A/V sync diff = 0.041 s  (< 0.2 s gate  ->  PASS)
  signalstats YAVG ~50-92 -> non-blank (real content)
```

### Reproducibility verdict
A clean machine with only `git clone` + `pip install -r requirements.txt` +
`ffmpeg` reproduces: 113 green tests, a real 512x448 h264+aac MP4, A/V sync within
tolerance. The world DB + asset catalog are regenerated at runtime from the
gitignored-but-rebuilt `data/lore/*.json` + `tvn/assets` procedural catalog
(`build_catalog()`), so nothing is shipped stale.

## What is NOT in scope / open threads (honest)
- Live Twitch `--stream` path is A/V-synced but was not exercised into a real Twitch
  ingest here (no TWITCH_STREAM_KEY in the fresh `.env`); the local MediaMTX RTMP
  gate from Stage 7 handoff remains the reproducible artifact.
- Real SPC-emulator-captured SNES music is the staged upgrade; the shipped audio is
  the syn-thec bed (honest provenance, see AUTHENTIC_ASSETS.md).
- `run.py` writes to `OUTPUT/` (gitignored) — expected; not a bug.

## Next move (foreman decision)
Published and reproducible. Tree closed. CC ingests publish evidence into
cc-docs-keeper reference + recall. No active worktree remains open for this stream.
