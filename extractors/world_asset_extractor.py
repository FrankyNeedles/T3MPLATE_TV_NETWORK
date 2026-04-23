#!/usr/bin/env python3
"""
World Asset Extractor v2 – Scanner-Integrated, No Old Code.
Extract sprites/backgrounds from catalog + ROMs.
"""

import json
import logging
from pathlib import Path
from PIL import Image
from typing import Dict, Optional

from extractors.rom_library_scanner import ROMLibraryScanner
from extractors.snes_rom_hacker import AuthenticAssetExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATALOG_PATH = Path("assets/world_assets_catalog.json")
SPRITES_DIR = Path("assets/sprites")
SPRITES_DIR.mkdir(exist_ok=True, parents=True)

class RomAssetExtractor:
    def __init__(self):
        self.scanner = ROMLibraryScanner()
    
    def extract_from_catalog(self):
        """Extract all catalog sprites."""
        with open(CATALOG_PATH, 'r') as f:
            catalog = json.load(f)
        
        results = {"extracted": 0, "failed": 0}
        for sprite in catalog.get("sprites", []):
            if self._extract_single(sprite):
                results["extracted"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Catalog Extract: {results['extracted']}/{len(catalog.get('sprites', []))}")
        return results
    
    def _extract_single(self, sprite: dict) -> bool:
        """Extract one sprite."""
        rom_path_str = sprite["rom_path"].replace("\\\\", "/")
        rom_path = Path(rom_path_str)
        if not rom_path.exists():
            logger.warning(f"ROM missing: {rom_path}")
            return False
        
        bank = sprite.get("bank")
        offset = sprite["offset"]
        addr = (bank * 0x10000) + offset if bank else offset
        
        try:
            extractor = AuthenticAssetExtractor(rom_path)
            img = extractor.extract_sprite(addr, (32, 32))
            output_path = SPRITES_DIR / sprite["name"]
            img.save(output_path)
            logger.info(f"V {sprite['name']} ({img.size}px) from {rom_path.name}")
            sprite["extracted"] = True
            sprite["size_kb"] = output_path.stat().st_size / 1024
            return True
        except Exception as e:
            logger.error(f"X {sprite['name']}: {e}")
            sprite["extracted"] = False
            return False
    
    def save_catalog(self):
        """Save updated catalog."""
        with open(CATALOG_PATH, 'w') as f:
            json.dump(catalog, f, indent=2)  # Assume catalog global or param

if __name__ == "__main__":
    extractor = RomAssetExtractor()
    extractor.extract_from_catalog()
