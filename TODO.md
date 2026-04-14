# T3MPLATE_TV_NETWORK Error Fixes TODO
Status: 0/16 complete [In Progress]

## Phase 1: Dependencies & Config (4 steps)
- [ ] 1.1 Update requirements.txt with all missing deps
- [ ] 1.2 Read/verify app/config.py, add missing CONFIG mocks/fallbacks
- [ ] 1.3 pip install -r requirements.txt
- [ ] 1.4 pytest tests/ -v (Phase 1 validation)

## Phase 2: Runtime Fixes (4 steps)
- [ ] 2.1 Fix extractors/authentic_snes_extractor.py (ROM checks, excepts)
- [ ] 2.2 Fix run.py (ROM path, bootstrap wrap)
- [ ] 2.3 Fix tests/test_full_pipeline.py (fixtures, asserts)
- [ ] 2.4 pytest (Phase 2)

## Phase 3: Code Quality (8 steps)
- [ ] 3.1 Fix extractors/validate_assets.py (thresholds, scrape)
- [ ] 3.2 Fix app/gary.py (LLM excepts, logging)
- [ ] 3.3 Replace prints → logging.info in run.py, bootstrap_*.py, app/*.py (multi-file)
- [ ] 3.4 Fix tcrf_scraper.py (excepts/prints)
- [ ] 3.5 docker-compose up --build test
- [ ] 3.6 python run.py (full run, no crashes)
- [ ] 3.7 Final pytest + coverage
- [ ] 3.8 ✅ Complete - attempt_completion

Next: Phase 1 Step 1.1 (requirements.txt)

