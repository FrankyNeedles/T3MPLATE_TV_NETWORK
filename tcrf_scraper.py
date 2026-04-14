from datetime import datetime
import schedule
import time
from extractors.top_50_snes_games import TOP_50_SNES_GAMES
import json
import requests
from bs4 import BeautifulSoup


def daily_tcrf_scrape():
    pass  # bs4 imported at top
    cache = {}
    for game_id, game in TOP_50_SNES_GAMES.items():
        url = game.get("tcrf_url", "")
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            offsets = []
            for elem in soup.find_all(["code", "pre", "p", "li"]):
                text = elem.get_text()
                words = text.split()
                for word in words:
                    if "0x" in word and len(word) < 12 and word[2:].isalnum():
                        offsets.append(word)
            unique_offsets = list(set(offsets))
            # Parse to sprite/audio banks (stub: even for sprites, odd for audio)
            sprite_banks = {
                f"sprite{i}": {
                    "bank": 0x0 + i,
                    "offset": unique_offsets[i % len(unique_offsets)]
                    if unique_offsets
                    else "0x00000",
                }
                for i in range(5)
            }
            audio_offsets = {
                f"audio{i}": {
                    "type": "brr" if i % 2 == 0 else "spc",
                    "offset": unique_offsets[
                        (i + len(unique_offsets) // 2) % len(unique_offsets)
                    ]
                    if unique_offsets
                    else f"0x{i}0000",
                }
                for i in range(3)
            }
            cache[game_id] = {
                "url": url,
                "offsets": unique_offsets,
                "sprite_banks": sprite_banks,
                "audio_offsets": audio_offsets,
                "scraped_at": datetime.now().isoformat(),
            }
            # Update TOP_50_SNES_GAMES
            TOP_50_SNES_GAMES[game_id]["sprite_banks"] = sprite_banks
            TOP_50_SNES_GAMES[game_id]["audio_offsets"] = audio_offsets
            TOP_50_SNES_GAMES[game_id]["tcrf_offsets"] = unique_offsets
        except Exception as e:
            cache[game_id] = {"url": url, "offsets": [], "error": str(e)}
            print(f"Scrape error for {game_id}: {e}")
    with open("tcrf_cache.json", "w") as f:
        json.dump(cache, f, indent=2)
    print(
        f"Scraped {len(cache)} games to cache, total offsets {sum(len(c['offsets']) for c in cache.values() if 'offsets' in c)}"
    )


schedule.every().day.at("02:00").do(daily_tcrf_scrape)

if __name__ == "__main__":
    daily_tcrf_scrape()
    while True:
        schedule.run_pending()
        time.sleep(3600)
