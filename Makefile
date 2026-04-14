# Makefile for development
.PHONY: dev test install clean

install:
	poetry install

dev:
	poetry run python run.py

test:
	poetry run pytest

lint:
	poetry run ruff check .

clean:
	rm -rf __pycache__ .pytest_cache