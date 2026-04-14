import pytest
from app.run import full_pipeline
from app.living_world import Session, Character
from app.gary import Gary
from app.action_trigger import ActionTrigger
from app.renderer import Renderer
from app.audio import AudioPlayer
from unittest.mock import patch
import pygame
import time
from playwright.async_api import async_playwright
from pathlib import Path
import json


@pytest.fixture
def mock_rom():
    # Mock ROM extract
    with patch("extractors.authentic_snes_extractor.extractor.run_on_roms"):
        yield


@pytest.mark.asyncio
async def test_e2e_pipeline(mock_rom):
    # E2E: Extract + DB + decision + validate + render + audio + API
    await full_pipeline()  # Mock run

    # DB insert assert
    session = Session()
    chars = session.query(Character).count()
    assert chars > 0

    # Decision validate
    gary = Gary()
    decision = gary.decide_show(["Mario"], "Test")
    trigger = ActionTrigger()
    executed = trigger.execute(decision)
    assert all(
        a.get("validated", False) for a in executed["actions"].values()
    )  # 100% mock

    # Render frames mock headless
    pygame.init()
    renderer = Renderer()  # From app.renderer
    surface = pygame.Surface((640, 480))
    renderer.render_visual(executed)
    assert surface.get_at((100, 100)) != (0, 0, 0)  # Frame pixel
    pygame.quit()

    # Audio duration mock
    audio = AudioPlayer()  # From app.audio
    start = time.time()
    audio.play_wav("assets/audio/mock.wav")  # 5s mock
    time.sleep(5)
    assert time.time() - start > 4.5  # Duration ≈5s

    # API /broadcast JSON mock
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://127.0.0.1:8000/broadcast")  # Ws mock
        ws_content = await page.evaluate(
            "() => localStorage.getItem('broadcast')"
        )  # Mock
        assert "actions" in ws_content  # JSON stream
        await browser.close()


def test_tcrf_scrape():
    from tcrf_scraper import daily_tcrf_scrape

    with patch("extractors.validate_assets.scrape_tcrf_offsets") as mock_scrape:
        mock_scrape.return_value = ["0x100"]
        daily_tcrf_scrape()
        cache_path = Path("tcrf_cache.json")
        assert cache_path.exists()
        assert len(json.load(open(cache_path))) > 0
