#!/usr/bin/env python3
"""
Asset Extraction Pipeline - Connects scanner to real ROM extraction.
Extracts all catalog sprites from real 784 ROM library.
"""

import json
from pathlib import Path
from extractors.rom_library_scanner import ROMLibraryScanner
from extractors.snes_rom_hacker import AuthenticAssetExtractor

CATALOG_PATH = Path("assets/world_assets_catalog.json")
SPRITES_DIR = Path("assets/sprites")
SPRITES_DIR.mkdir(exist_ok=True, parents=True)

class AssetPipeline:
    def __init__(self):
        self.scanner = ROMLibraryScanner()
    
    def run(self):
        """Extract all sprites from catalog."""
        with open(CATALOG_PATH, 'r') as f:
            catalog = json.load(f)
        
        results = {"extracted": [], "failed": [], "total": len(catalog["sprites"])}
        
        for sprite in catalog["sprites"]:
            success = self._extract_sprite(sprite)
            if success:
                results["extracted"].append(sprite["name"])
            else:
                results["failed"].append(sprite["name"])
        
        # Update catalog with results
        for sprite in catalog["sprites"]:
            sprite["extracted"] = sprite["name"] in results["extracted"]
        
        with open(CATALOG_PATH, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        print(f"Pipeline complete: {len(results['extracted'])}/{results['total']} extracted")
        return results
    
    def _extract_sprite(self, sprite: dict) -> bool:
        """Extract single sprite."""
        rom_path_str = sprite["rom_path"].replace("ROM_SOURCE\\\\unzipped\\\\", "ROM_SOURCE/unzipped/").replace("\\\\", "/")
        rom_path = Path(rom_path_str)
        if not rom_path.exists():
            print(f"X ROM missing: {rom_path}")
            return False
        
        try:
            bank = sprite.get("bank")
            offset = sprite["offset"]
            addr = (bank * 0x10000) + offset if bank else offset
            
            extractor = AuthenticAssetExtractor(rom_path)
            img = extractor.extract_sprite(addr, (32, 32))
            
            output_path = SPRITES_DIR / sprite["name"]
            img.save(output_path)
            
            print(f"V {sprite['name']} from {rom_path.name} ({img.size}px)")
            return True
        except Exception as e:
            print(f"❌ {sprite['name']}: {e}")
            return False

if __name__ == "__main__":
    pipeline = AssetPipeline()
    pipeline.run()
