from unittest.mock import Mock
from tcrf_scraper import daily_tcrf_scrape
import json
from pathlib import Path


def test_scrape_mock(mock_get):
    # Mock responses with 50+ offsets
    mock_resp = Mock()
    mock_resp.text = (
        "<pre>Sprite bank: 0x0AC000 Audio: 0x1DF380 0xF60000 Other: 0x123456</pre><p>More offsets: 0x080000 0xC00000 ...</p>"
        * 10
    )  # 50+ hex
    mock_get.return_value = mock_resp

    daily_tcrf_scrape()
    cache_path = Path("tcrf_cache.json")
    assert cache_path.exists()
    cache = json.load(open(cache_path))
    total_offsets = sum(len(c["offsets"]) for c in cache.values())
    assert total_offsets >= 50  # Mock 50 offsets
    # Check parsed banks/audio
    for game in cache.values():
        assert "sprite_banks" in game and len(game["sprite_banks"]) >= 5
        assert "audio_offsets" in game and len(game["audio_offsets"]) >= 3
