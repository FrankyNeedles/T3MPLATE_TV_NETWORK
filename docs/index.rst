T3MPLATE TV Network Documentation
=============================

Overview
--------
SNES asset extraction to AI-driven TV broadcast.

Setup
-----
1. Install deps: pip install -r requirements.txt
2. Env: .env OPENROUTER_API_KEY=...
3. ROMs: Place in roms/
4. Run: python run.py

API
---
- /status: Daypart/energy
- /schedule: History
- /broadcast: WS stream JSON actions

Asset Pipeline
--------------
1. Extract ROM → PNG/WAV/manifest (95% TCRF)
2. Bootstrap DB chars/rels
3. Gary decisions w/assets
4. Station tick → render/audio/broadcast
5. Docker compose up (8080 API, 8765 emu)