Asset Pipeline
===============

1. ROM Extract: python extractors/authentic_snes_extractor.py
2. Validate TCRF: python extractors/validate_assets.py (95% match)
3. Bootstrap DB: python bootstrap_living_world.py
4. Run full: python run.py (Gary/Station/API)

Daily: python tcrf_scraper.py for offsets cache.