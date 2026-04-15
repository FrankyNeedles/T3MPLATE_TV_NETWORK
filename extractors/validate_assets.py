#!/usr/bin/env python3
"""
Asset Validation Script
Cross-checks extractions against TCRF and verifies integrity.
Enhanced with BeautifulSoup scraping for TCRF offsets.
"""

import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from top_50_snes_games import TOP_50_SNES_GAMES

logger = logging.getLogger(__name__)


def load_manifest(manifest_path: Path) -> dict:
    """Load extraction manifest."""
    with open(manifest_path, "r") as f:
        return json.load(f)


def scrape_tcrf_offsets(url: str) -> list[str]:
    """Scrape TCRF URL for hex offsets."""
    logger.info(f"Scraping TCRF offsets from {url}")
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        hex_offsets = []
        text = soup.get_text()
        for word in text.split():
            if word.startswith("0x") and len(word) < 12 and word[2:].isalnum():
                hex_offsets.append(word)
        logger.info(f"Found {len(hex_offsets)} offsets")
        return list(set(hex_offsets))
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        return []


def validate_sprites(manifest: dict) -> dict:
    """Validate sprite data with TCRF cross-check (10+ assets)."""
    issues = []
    total = 0
    valid = 0

    for game, data in manifest.get("games", {}).items():
        sprites = data.get("sprites", {})
        total += len(sprites)
        if len(sprites) < 10:
            issues.append(f"Insufficient sprites ({len(sprites)}) for {game}")
        url = TOP_50_SNES_GAMES.get(game, {}).get("tcrf_url")
        hex_offsets = scrape_tcrf_offsets(url) if url else []
        for name, sprite in sprites.items():
            offset = sprite.get("offset")
            if offset and offset.startswith("0x"):
                try:
                    int(offset, 16)
                    valid += 1
                    # TCRF verify
                    if not any(offset.lower() in o.lower() for o in hex_offsets):
                        issues.append(
                            f"TCRF unverified offset {offset} for {game}/{name}"
                        )
                except ValueError:
                    issues.append(f"Invalid offset {offset} in {game}/{name}")
            else:
                issues.append(f"Missing/invalid offset for {game}/{name}")

    return {"valid": valid, "total": total, "issues": issues}


def validate_audio(manifest: dict) -> dict:
    """Validate audio data with TCRF cross-check (5+ assets)."""
    issues = []
    total = 0
    valid = 0

    for game, data in manifest.get("games", {}).items():
        audio = data.get("audio", {})
        total += len(audio)
        if len(audio) < 5:
            issues.append(f"Insufficient audio ({len(audio)}) for {game}")
        url = TOP_50_SNES_GAMES.get(game, {}).get("tcrf_url")
        hex_offsets = scrape_tcrf_offsets(url) if url else []
        for name, track in audio.items():
            offset = track.get("offset")
            typ = track.get("type")
            if offset and typ in ["brr", "spc"]:
                try:
                    if offset.startswith("0x"):
                        int(offset, 16)
                    else:
                        int(offset)
                    valid += 1
                    # TCRF verify
                    if not any(offset.lower() in o.lower() for o in hex_offsets):
                        issues.append(
                            f"TCRF unverified offset {offset} for {game}/{name}"
                        )
                except ValueError:
                    issues.append(f"Invalid offset {offset} for {game}/{name}")
            else:
                issues.append(f"Invalid audio {name} (type {typ}) in {game}")

    return {"valid": valid, "total": total, "issues": issues}


if __name__ == "__main__":
    manifest_path = Path("assets/manifests/extraction_manifest.json")
    if manifest_path.exists():
        manifest = load_manifest(manifest_path)
        sprite_val = validate_sprites(manifest)
        audio_val = validate_audio(manifest)
        print(
            f"Sprite Validation: {sprite_val['valid']}/{sprite_val['total']}, Issues: {len(sprite_val['issues'])}"
        )
        print(
            f"Audio Validation: {audio_val['valid']}/{audio_val['total']}, Issues: {len(audio_val['issues'])}"
        )
        if sprite_val["issues"]:
            print("Sprite issues:", sprite_val["issues"][:5])
        if audio_val["issues"]:
            print("Audio issues:", audio_val["issues"][:5])
        valid = (
            sprite_val["valid"] == sprite_val["total"]
            and audio_val["valid"] == audio_val["total"]
        )
        print(f"Overall valid: {valid}")
    else:
        print("No manifest found - run extraction first")
