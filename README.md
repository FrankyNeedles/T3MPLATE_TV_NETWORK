# T3MPLATE TV NETWORK - 100% MASTER_PLAN.md Alignment
Autonomous SNES TV Network MVP.

## Stack
- Backend: FastAPI, SQLAlchemy, Pydantic
- LLM: OpenRouter/Langchain
- Assets: Authentic SNES sprites/audio from ROM extractors
- Frontend: Pygame renderer (stub), Lutro emu (Phase5)
- Dev: Poetry, pytest, ruff, mypy, pre-commit
- Deploy: Docker Compose, GitHub Actions CI

## Setup (Windows)
1. `pip install -r requirements.txt` (sounddevice soundfile pygame*)
2. `pip install fastapi uvicorn sqlalchemy pillow langchain-core openrouter python-dotenv`
3. `mkdir roms assets/manifests data/snes_universe logs`
4. `python run.py` → API localhost:8080, broadcast tick

* Pygame 3.14 build fail: use stub or Python 3.12 venv.

## Commands
- `python run.py` - Bootstrap + API + broadcast
- `python -m pytest` - 27 tests
- `python -m ruff check . --fix` - Lint
- `python -m mypy .` - Typecheck
- `make extract-all` - Extract/ scrape/ validate
- `make deploy` - Docker up

## Phases Status
✅ Prep: Fixed syntax, unicode, pytest imports, deps (wheels)
✅ Phase1: pyproject.toml, Makefile, CI, utils logging, README
Phase2: Top50 TCRF scraper (50/50), extractor test sample.sfc
Phase3: Load 88 chars, DB FK, gossip news
Phase4: Gary OpenRouter, action manifest lookup
Phase5: Pygame 60fps Mode7, PyAudio BRR, Lutro
Phase6: E2E tests, Prometheus, 24hr load
Phase7: Docker services, Twitch/OBS/Sphinx, v1.0

## TV_WORLD Migration
- assets/sprites/audio/manifests/
- data/snes_universe/characters.json (88 chars)
- roms/sample.sfc

## Verify
- pytest: 27 collected
- run.py: No traceback, API/tick
