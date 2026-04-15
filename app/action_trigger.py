#!/usr/bin/env python3
"""
Action Trigger System
Executes Gary decisions using authentic assets (60fps sync).
Validates against manifests before execution.
"""

import json
import time
from app.config import CONFIG
import random
import sounddevice as sd
import soundfile as sf


class ActionTrigger:
    def __init__(self):
        self.manifests_dir = CONFIG.assets_dir / "manifests"
        self.sprites_dir = CONFIG.assets_dir / "authentic_sprites"
        self.audio_dir = CONFIG.assets_dir / "audio"
        self.manifest_cache = self._load_manifest_cache()

    def _load_manifest_cache(self) -> dict:
        """Load all manifests."""
        cache = {}
        for manifest_file in self.manifests_dir.glob("*.json"):
            game_id = manifest_file.stem
            with open(manifest_file) as f:
                cache[game_id] = json.load(f)
        return cache

    def validate_actions(self, actions: dict[str, any]) -> dict[str, bool]:
        """Validate actions exist in assets."""
        validation = {"visual": False, "audio": False}
        if "visual" in actions:
            game_id = actions["visual"].get("game_id", "")
            sprite_name = actions["visual"].get("character", "")
            if game_id in self.manifest_cache:
                sprites = self.manifest_cache[game_id].get("sprites", {})
                validation["visual"] = sprite_name in sprites

        if "audio" in actions:
            game_id = actions["audio"].get("game_id", "")
            track = actions["audio"].get("track", "")
            if game_id in self.manifest_cache:
                audio = self.manifest_cache[game_id].get("audio", {})
                validation["audio"] = track in audio

        return validation

    def execute_actions(self, actions: dict[str, any]):
        """Execute validated actions."""
        validation = self.validate_actions(actions)

        if not all(validation.values()):
            print("Warning: Using fallbacks for invalid actions")

        # Visual execution (60fps sync)
        if "visual" in actions:
            self._execute_visual(actions["visual"])

        # Audio sync (100ms delay)
        if "audio" in actions:
            time.sleep(0.1)
            self._execute_audio(actions["audio"])

    def _execute_visual(self, visual: dict):
        """Render sprite from ROM data (placeholder)."""
        character = visual.get("character", "mario")
        game_id = visual.get("game_id", "super_mario_world")
        bank = visual.get("bank", 0)
        offset = visual.get("offset", "$8000")
        duration = visual.get("duration", 60)

        print(
            f"Visual: {character} from {game_id} (bank {bank}, offset {offset}) for {duration} frames @60fps"
        )
        # In prod: renderer.load_sprite(game_id, bank, offset); renderer.animate(duration)

    def _execute_audio(self, audio: dict):
        """Play BRR/SPC."""
        track = audio.get("track", "intro")
        game_id = audio.get("game_id", "super_mario_world")
        brr_offset = audio.get("brr_offset", "$1DF380")
        loop = audio.get("loop", False)

        # Placeholder playback
        coin_wav = self.audio_dir / "super_mario_world_coin.wav"
        jump_wav = self.audio_dir / "super_mario_world_jump_sfx.wav"
        wav_path = coin_wav if "coin" in track.lower() else jump_wav if "jump" in track.lower() else coin_wav
        if wav_path.exists():
            data, fs = sf.read(str(wav_path))
            sd.play(data, fs)
            sd.wait()
            print(f"Played {wav_path.name}")
        else:
            duration = 1000 if loop else 500
            import winsound
            winsound.Beep(440 + random.randint(0, 200), duration)
            print(f"Fallback beep for {track}")
        print(f"Audio: {track} from {game_id} (BRR {brr_offset}, loop={loop})")

    def execute_decision(self, decision: dict):
        """Execute full Gary decision."""
        actions = decision.get("actions", {})
        self.execute_actions(actions)
        print(f"Executed decision for '{decision.get('show', 'unknown')}'")


# Global trigger
action_trigger = ActionTrigger()

if __name__ == "__main__":
    sample_decision = {
        "show": "Mario News",
        "actions": {
            "visual": {
                "character": "mario",
                "game_id": "super_mario_world",
                "bank": 29,
                "offset": "$8000",
                "duration": 60,
            },
            "audio": {
                "track": "intro",
                "game_id": "super_mario_world",
                "brr_offset": "$1DF380",
                "loop": False,
            },
        },
    }
    action_trigger.execute_decision(sample_decision)
