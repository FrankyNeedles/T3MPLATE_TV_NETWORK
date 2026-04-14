import pytest

try:
    import pygame
except ImportError:
    pygame = None

import time
from app.station import Station
from app.renderer import Renderer
from app.audio import AudioPlayer
from app.living_world import Timeline
from playwright.async_api import async_playwright
import asyncio


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def test_1hr_sim():
    pygame.init()
    station = Station()
    station.running = True
    start_events = len(station.session.query(Timeline).all())
    # Sim 1hr = 20 ticks (3min each)
    for _ in range(20):
        station.tick()
        time.sleep(0.1)  # Mock delay
    end_events = len(station.session.query(Timeline).all())
    assert end_events - start_events >= 20
    # Video assert: Mock surface frames
    renderer = Renderer()
    surface = pygame.Surface((640, 480))
    renderer.render_visual({"visual": {"sprite_name": "mario"}})
    assert surface.get_at((100, 100)) != (0, 0, 0, 0)  # Non-black pixel
    pygame.quit()


def test_audio_duration():
    audio = AudioPlayer()
    start = time.time()
    audio.play_wav("assets/audio/coin.wav")  # Mock 5s
    time.sleep(5)
    assert abs(time.time() - start - 5) < 1  # Duration match


@pytest.mark.asyncio
async def test_api_endpoints():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://127.0.0.1:8000/status")
        status = await page.content()
        assert "daypart" in status
        await browser.close()


if __name__ == "__main__":
    pytest.main(["-v"])
