#!/usr/bin/env python3
"""
All ROMs Asset Extractor - Extract key data from ALL 784 SNES ROMs.
Focus: Palettes, tilemaps, sprites, BRR audio samples for TV project.
Parallel extraction for speed.
"""

import asyncio
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import struct

from extractors.snes_rom_hacker import AuthenticAssetExtractor, SNESROMTools
from extractors.rom_library_scanner import ROMLibraryScanner

OUTPUT_ROOT = Path("assets/all_roms")
MANIFEST_PATH = Path("ROM_SOURCE/roms_manifest.json")

async def extract_rom_data(rom_info: dict):
    """Extract key assets from single ROM."""
    rom_path = Path(rom_info["path"])
    title = rom_info["title"].replace("/", "_").replace("\\", "_")[:50]
    output_dir = OUTPUT_ROOT / title
    output_dir.mkdir(exist_ok=True, parents=True)
    
    results = {"rom": rom_info["path"], "extracted": {}}
    
    try:
        extractor = AuthenticAssetExtractor(rom_path)
        
        # 1. Header JSON
        header = {
            "title": extractor.header.title,
            "map_mode": extractor.map_mode,
            "region": extractor.header.region,
            "checksum": extractor.header.checksum
        }
        with open(output_dir / "header.json", "w") as f:
            json.dump(header, f, indent=2)
        results["extracted"]["header"] = True
        
        # 2. CGRAM Palette PNG
        palette = SNESROMTools.extract_cgram(extractor.rom_data, 0x21200, extractor.map_mode)
        pal_img = Image.new('RGB', (16, 16))
        for i, color in enumerate(palette.colors[:256]):
            x, y = i % 16, i // 16
            pal_img.putpixel((x, y), color)
        pal_img.save(output_dir / "palette.png")
        results["extracted"]["palette"] = True
        
        # 3. BG1 Tilemap sample (first 32x32)
        bg1 = SNESROMTools.extract_tilemap(extractor.rom_data, 0x3D800, extractor.map_mode)
        with open(output_dir / "bg1_tilemap.bin", "wb") as f:
            for tile in bg1.tile_data[:1024]:  # 32x32
                f.write(struct.pack(">H", tile))
        results["extracted"]["bg1"] = True
        
        # 4. Sprite bank sample (bank 2, offset 0x8000 - common player)
        try:
            sprite_sample = extractor.extract_sprite(0x028000, (32, 32))
            sprite_sample.save(output_dir / "sprite_sample.png")
            results["extracted"]["sprite_sample"] = True
        except:
            results["extracted"]["sprite_sample"] = False
        
        # 5. BRR audio sample (first BRR block found)
        try:
            brr_pcm = SNESROMTools.decode_brr_stream(extractor.rom_data, 0x100000)  # Typical BRR area
            if brr_pcm:
                import wave
                wav_path = output_dir / "brr_sample.wav"
                with wave.open(wav_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(32000)
                    wf.writeframes(b''.join(struct.pack("<h", s) for s in brr_pcm[:32000]))
                results["extracted"]["brr_sample"] = True
        except:
            results["extracted"]["brr_sample"] = False
            
    except Exception as e:
        results["error"] = str(e)
    
    return results

async def extract_all_roms():
    """Extract from all 784 ROMs."""
    manifest_path = Path("ROM_SOURCE/roms_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    roms = manifest["roms"]  # ALL 834 ROMs
    
    print(f"Extracting from {len(roms)} ROMs...")
    
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, extract_rom_data, rom) for rom in roms]
        results = await asyncio.gather(*tasks)
    
    summary_path = OUTPUT_ROOT / "extraction_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    
    success = sum(1 for r in results if "error" not in r)
    print(f"Complete: {success}/{len(roms)} ROMs extracted")
    print(f"Summary: {summary_path}")

if __name__ == "__main__":
    asyncio.run(extract_all_roms())
