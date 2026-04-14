import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.station import station
from app.gary import gary
from app.living_world import living_world
from app.action_trigger import action_trigger
from app.station_api import app as api_app
from extractors.authentic_snes_extractor import AuthenticSNESExtractor
from extractors.top_50_snes_games import TOP_50_SNES_GAMES
from app.config import CONFIG
import uvicorn
import threading
import time


def bootstrap_pipeline():
    """Bootstrap: Extract + Validate + DB Load."""
    print("🔧 Starting extraction...")
    rom_path = CONFIG.roms_dir / "chrono_trigger.sfc"  # Example from TV_WORLD
    if rom_path.exists():
        extractor = AuthenticSNESExtractor(rom_path)
        game_id = "chrono_trigger"
        sprites = extractor.extract_sprites(game_id, TOP_50_SNES_GAMES[game_id])
        audio = extractor.extract_audio(game_id, TOP_50_SNES_GAMES[game_id])
        extractor.save_manifest()
        val = extractor.validate_extraction()
        print(
            f"Extraction: {len(sprites)} sprites, {len(audio)} audio. Validation: {val['valid']}"
        )

    print("📊 Bootstrapping living world...")
    living_world._populate_initial_data()  # From JSONs

    print("✅ Pipeline ready!")


def run_broadcast():
    """Station tick loop."""
    print("📺 Starting 24/7 broadcast...")
    tick = 0
    while True:
        tick += 1
        status = station.tick()
        print(f"Tick {tick}: {status}")

        # Simulate 3min decisions faster
        if tick % 10 == 0:  # Every 10 ticks
            decision = gary.make_decision()
            action_trigger.execute_decision(decision.model_dump())

        time.sleep(0.1)  # 10fps demo


def run_api():
    """FastAPI server."""
    uvicorn.run(
        api_app, host=CONFIG.api_host, port=CONFIG.api_port, reload=CONFIG.api_reload
    )


if __name__ == "__main__":
    bootstrap_pipeline()

    # Threads: API + Broadcast
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    broadcast_thread = threading.Thread(target=run_broadcast, daemon=True)
    broadcast_thread.start()

    # Wait for threads
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutdown...")
