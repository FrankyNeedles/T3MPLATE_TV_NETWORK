#!/usr/bin/env python3
"""
TCRF Scraper for TOP 50 SNES.
Scrapes TCRF wiki for sprite/audio hex offsets per game.
Runs daily cron (schedule/Task Scheduler).
Populates data/tcrf_cache.json → merges TOP_50_SNES_GAMES.
"""

import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
from top_50_snes_games import TOP_50_SNES_GAMES

logger = logging.getLogger(__name__)

CACHE_PATH = Path("data/tcrf_cache.json")
CACHE_PATH.parent.mkdir(exist_ok=True)


def parse_tcrf_sections(soup):
    sprite_offsets = set()
    audio_offsets = set()
    hex_re = re.compile(r"\b(\$|0x)?([0-9A-Fa-f]{2,8})\b", re.I)

    def extract_hexs(element):
        text = element.get_text()
        return hex_re.findall(text)

    sprite_keywords = ["sprite", "graphic", "gfx", "object", "tile", "palette"]
    audio_keywords = ["sound", "music", "spc", "brr", "sfx", "audio"]
    for heading in soup.find_all(["h2", "h3", "h4"]):
        title = heading.get_text().lower()
        is_sprite = any(kw in title for kw in sprite_keywords)
        is_audio = any(kw in title for kw in audio_keywords)
        if not is_sprite and not is_audio:
            continue
        sibling = heading.find_next_sibling()
        while sibling and sibling.name not in ["h1", "h2"]:
            for child_tag in sibling.find_all(
                ["p", "li", "td", "pre", "code", "th", "table"]
            ):
                hexs = extract_hexs(child_tag)
                for prefix, h in hexs:
                    full_hex = (prefix or "$") + h.upper()
                    if 2 <= len(h) <= 8:
                        if is_sprite:
                            sprite_offsets.add(full_hex)
                        if is_audio:
                            audio_offsets.add(full_hex)
            sibling = sibling.find_next_sibling()
    return list(sprite_offsets)[:10], list(audio_offsets)[:5]


def scrape_game(game_id):
    logger.info(f"Scraping TCRF for {game_id}")
    game = TOP_50_SNES_GAMES[game_id]
    url = game["tcrf_url"]
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        soups = [soup]
        ug_url = url.rstrip("/") + "/Unused_Graphics_%26_Objects"
        try:
            ug_resp = requests.get(ug_url, timeout=15)
            if ug_resp.ok:
                ug_soup = BeautifulSoup(ug_resp.text, "html.parser")
                soups.append(ug_soup)
        except:
            pass
        all_sprite = set()
        all_audio = set()
        for s in soups:
            sp, au = parse_tcrf_sections(s)
            all_sprite.update(sp)
            all_audio.update(au)
        sprite_off = list(all_sprite)[:10]
        audio_off = list(all_audio)[:5]
        sprite_banks = {
            f"sprite{i}": {
                "bank": 0x0D + i,
                "offset": off,
                "bpp": 2,
                "size": "16x16",
                "frames": 4,
            }
            for i, off in enumerate(sprite_off)
        }
        audio_offs = {
            f"audio{i}": {"offset": off, "type": "brr" if i % 2 == 0 else "spc"}
            for i, off in enumerate(audio_off)
        }
        logger.info(
            f"Scraped {game_id}: {len(sprite_banks)} sprites, {len(audio_offs)} audio"
        )
        return {game_id: {"sprite_banks": sprite_banks, "audio_offsets": audio_offs}}
    except Exception as e:
        logger.error(f"Error scraping {game_id}: {e}")
        return {}


if __name__ == "__main__":
    cache = {}
    for game_id in TOP_50_SNES_GAMES:
        scraped = scrape_game(game_id)
        cache.update(scraped)
        print(
            f"Scraped {game_id}: {len(scraped.get(game_id, {}).get('sprite_banks', []))} sprites"
        )
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"TCRF cache saved: {CACHE_PATH} ({len(cache)} games)")
    print("Reload top_50_snes_games.py to merge cache.")
