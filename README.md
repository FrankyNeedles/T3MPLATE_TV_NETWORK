# T3MPLATE TV NETWORK
Autonomous SNES broadcast simulation with authentic assets.

## Setup
1. Install Poetry: `pip install poetry`
2. `poetry install`
3. `poetry run python run.py`

## Quick Start
```bash
pip install poetry
poetry install
poetry run python run.py
```

## Development
- `make dev` - Poetry shell + uvicorn reload
- `make test` - pytest -v
- `make lint` - ruff check --fix
- `make typecheck` - mypy --strict

## Deploy
- `make deploy` - Docker run local
- `make dockerfile` - Multi-arch push

## Docker
```dockerfile
# Dockerfile provided
docker build -t t3mplate-tv .
docker run -p 8000:8000 t3mplate-tv
```

## Milestone
- 50 SNES games w/TCRF data scraped/validated 95%
- Full pipeline: ROM extract → Gary LLM → broadcast → world sim