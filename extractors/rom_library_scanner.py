#!/usr/bin/env python3
"""
ROM Library Scanner - Scans 784 ROM library for games by title.
Supports .sfc/.smc in ROM_SOURCE/unzipped/
"""

from pathlib import Path
from typing import Dict, Optional, List
import hashlib
from dataclasses import dataclass

@dataclass
class ROMInfo:
    path: Path
    title: str
    hash_sha256: str
    map_mode: str
    region: str

class ROMLibraryScanner:
    ROM_ROOTS = [
    Path("ROM_SOURCE/unzipped"),
    Path("ROM_SOURCE/unzipped_snes_new"),
    Path("I:/Roms"),
]
    
    # Known games and title match patterns
    GAME_PATTERNS = {
        "SUPER MARIOWORLD": ["super mario world", "mario world", "mario"],
        "THE LEGEND OF ZELDA": ["legend of zelda", "link to the past", "zelda"],
        "DONKEY KONG COUNTRY": ["donkey kong country", "dkc"],
        "EARTHBOUND": ["earthbound", "earth bound"],
        "CHRONO TRIGGER": ["chrono trigger"],
        "MEGAMAN X": ["mega man x", "megaman x"],
        "STAR FOX": ["star fox"],
        "CONTRA3": ["contra iii", "contra 3", "contra3"],
        "STREET FIGHTER 2": ["street fighter ii", "street fighter 2", "sf2"],
        "MORTAL KOMBAT": ["mortal kombat", "mk"],
        "THE SIMPSONS": ["simpsons"],
        "KIRBY SUPER STAR": ["kirby super star", "kirby"],
        "FINAL FIGHT": ["final fight"],
        "TMNT": ["ninja turtles", "tmnt", "turtles"],
        "ADDAMS FAMILY": ["addams family"],
        "BATMAN FOREVER": ["batman forever", "batman"],
        "SPIDER-MAN": ["spider-man", "spiderman"],
        "POWER RANGERS": ["power rangers", "mighty morphin", "power rangers zeo"],
        "WHEEL OF FORTUNE": ["wheel of fortune"],
        "JEOPARDY": ["jeopardy"],
        "DUCK TALES": ["duck tales", "duck tales", "ducktales"],
        "LOONEY TUNES": ["looney tunes"],
        "TOM AND JERRY": ["tom and jerry"],
        "REN AND STIMPY": ["ren & stimpy", "ren stimpy"],
        "ANIMANIACS": ["animaniacs"],
        "THE FLINTSTONES": ["flintstones"],
        "THE JETSONS": ["jetsons"],
        "ROCCO'S MODERN LIFE": ["rocko", "rocko's modern life"],
        "WARIO'S WOODS": ["wario"],
        "ACTRAISER": ["actraiser"],
        "LEGEND OF THE MYSTICAL NINJA": ["mystical ninja"],
        "ART OF FIGHTING": ["art of fighting"],
        "SUPER MARIO RPG": ["super mario rpg"],
        "BEAVIS AND BUTT-HEAD": ["beavis", "butt-head"],
    }
    
    def __init__(self):
        self.available_roms: Dict[str, List[ROMInfo]] = {}
        self._scan_roms()
    
    def _scan_roms(self):
        """Scan all ROMs and build lookup table."""
        for rom_root in self.ROM_ROOTS:
            if rom_root.exists():
                for rom_path in rom_root.rglob("*.sfc"):
                    info = self._parse_rom(rom_path)
                    if info:
                        self._add_to_lookup(info)
                for rom_path in rom_root.rglob("*.smc"):
                    info = self._parse_rom(rom_path)
                    if info:
                        self._add_to_lookup(info)
        
        # ZIP handling (extract temp)
        import tempfile, zipfile
        for rom_root in self.ROM_ROOTS:
            for zip_path in rom_root.glob("*.zip"):
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(temp_dir)
                    for rom_path in Path(temp_dir).rglob("*.sfc"):
                        info = self._parse_rom(rom_path)
                        if info:
                            info.path = zip_path  # Mark as from ZIP
                            self._add_to_lookup(info)
    
    def _parse_rom(self, rom_path: Path) -> Optional[ROMInfo]:
        """Parse ROM header using SNESROMTools."""
        try:
            with open(rom_path, "rb") as f:
                data = f.read()
            
            from .snes_rom_hacker import SNESROMTools
            header = SNESROMTools.parse_header(data)
            
            title = header.title or rom_path.stem
            map_mode = header.map_mode if header.map_mode != "Unknown" else SNESROMTools.detect_map_mode(data)
            
            regions = {1: "USA", 0: "Japan", 2: "Europe"}
            region = regions.get(header.country, "Unknown")
            
            h = hashlib.sha256(data).hexdigest()
            
            return ROMInfo(path=rom_path, title=title, hash_sha256=h, 
                          map_mode=map_mode, region=region)
        except:
            return None
    
    def _add_to_lookup(self, info: ROMInfo):
        """Add ROM to game lookup."""
        title_lower = info.title.lower()
        for game_key, patterns in self.GAME_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in title_lower:
                    if game_key not in self.available_roms:
                        self.available_roms[game_key] = []
                    self.available_roms[game_key].append(info)
                    return
        
        # Fallback: add to 'unknown'
        if 'unknown' not in self.available_roms:
            self.available_roms['unknown'] = []
        self.available_roms['unknown'].append(info)
    
    def find_game_rom(self, game_title: str) -> Optional[Path]:
        """Find first matching ROM for game."""
        game_key = game_title.upper()
        roms = self.available_roms.get(game_key)
        return roms[0].path if roms else None
    
    def list_available_games(self) -> Dict[str, List[str]]:
        """List games with ROM paths."""
        return {k: [str(r.path) for r in v] for k, v in self.available_roms.items()}
    
    def generate_manifest(self, output_path: Path = Path("ROM_SOURCE/roms_manifest.json")):
        """Generate full ROM manifest."""
        manifest = {
            "total_roms": len([r for roms in self.available_roms.values() for r in roms]),
            "games": self.list_available_games(),
            "generated_at": "2026-04-22"
        }
        with open(output_path, "w") as f:
            import json
            json.dump(manifest, f, indent=2)
        print(f"Manifest saved: {output_path} ({manifest['total_roms']} ROMs)")
        return manifest
if __name__ == "__main__":
    scanner = ROMLibraryScanner()
    print("Available games:")
    print(scanner.list_available_games())
    scanner.generate_manifest()
    print("Scan complete.")
