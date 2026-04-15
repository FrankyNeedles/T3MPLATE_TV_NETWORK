# Makefile - MASTER_PLAN.md Phases
.PHONY: install dev test lint typecheck format extract-all docker-build deploy clean

dev:
	python -m poetry run uvicorn app.station_api:app --host 127.0.0.1 --port 8080 --reload

test:
	python -m poetry run pytest -v --cov=app --cov-report=term-missing

lint:
	python -m poetry run ruff check . --fix

typecheck:
	python -m poetry run mypy .

format:
	python -m poetry run ruff format .

extract-all:
	python -m poetry run python -m extractors.authentic_snes_extractor
	python -m poetry run python -m extractors.tcrf_scraper scrape_all
	python -m poetry run python -m extractors.validate_assets

docker-build:
	docker compose build

deploy:
	docker compose up -d --build

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache data/living_world.db .venv