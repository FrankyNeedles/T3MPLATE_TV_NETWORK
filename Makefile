# Makefile - MASTER_PLAN.md Phases
.PHONY: install dev test lint typecheck format clean

dev:
	python -m pytest

test:
	python -m pytest -v

lint:
	python -m ruff check tvn tests_mvp --fix

typecheck:
	python -m mypy .

format:
	python -m ruff format .

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache data/living_world.db .venv