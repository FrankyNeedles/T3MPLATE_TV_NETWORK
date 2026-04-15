#!/usr/bin/env python3
"""
ROM Library Scanner - Scans the 784 ROM library

Usage:
    python -m extractors.scan_rom_library [--root ROM_SOURCE]
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from extractors.snes_rom_hacker import SNESROMTools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_roms(root: Path) -> list[Path]:
    """Find all ROM files in the library structure."""
    roms = []

    for ext in ["*.sfc", "*.smc"]:
        # Direct files in root
        roms.extend(root.glob(ext))

        # Files in subdirectories (like unzipped/)
        for rom_path in root.rglob(ext):
            if rom_path.parent.name != root.name:
                roms.append(rom_path)

    return list(set(roms))


def scan_single_rom(rom_path: Path) -> dict | None:
    """Scan a single ROM file."""
    try:
        with open(rom_path, "rb") as f:
            rom_data = f.read()

        if len(rom_data) < 0x200:
            logger.warning(f"ROM too small: {rom_path}")
            return None

        header = SNESROMTools.parse_header(rom_data)
        map_mode = header.map_mode
        if map_mode == "Unknown":
            map_mode = SNESROMTools.detect_map_mode(rom_data)

        title = header.title if header.title else rom_path.stem

        parent_name = rom_path.parent.name
        if parent_name == rom_path.parent.parent.name:
            region = "USA"
        else:
            region = "USA"

        return {
            "title": title,
            "filename": rom_path.name,
            "path": str(rom_path.relative_to(rom_path.anchor)),
            "size_bytes": len(rom_data),
            "size_mb": round(len(rom_data) / (1024 * 1024), 2),
            "hash_sha256": SNESROMTools.compute_sha256(rom_data),
            "map_mode": map_mode,
            "region": region,
            "country_code": header.country,
            "rom_type": header.rom_type,
            "checksum": hex(header.checksum) if header.checksum else None,
            "validated": True,
        }

    except Exception as e:
        logger.error(f"Failed to scan {rom_path}: {e}")
        return None


def scan_library(root: Path, max_workers: int = 8, limit: int | None = None) -> dict:
    """
    Scan entire ROM library with parallel processing.

    Args:
        root: Root directory containing ROMs
        max_workers: Number of parallel workers
        limit: Optional limit for testing

    Returns:
        Manifest dict with all ROMs
    """
    logger.info(f"Scanning ROM library at: {root}")

    rom_paths = find_roms(root)
    if limit:
        rom_paths = rom_paths[:limit]

    logger.info(f"Found {len(rom_paths)} ROM files")

    manifest = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "total_roms": len(rom_paths),
        "total_size_bytes": 0,
        "total_size_mb": 0,
        "roms": [],
    }

    processed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(scan_single_rom, path): path for path in rom_paths
        }

        for future in as_completed(future_to_path):
            rom_path = future_to_path[future]
            result = future.result()

            if result:
                manifest["roms"].append(result)
                manifest["total_size_bytes"] += result["size_bytes"]
                processed += 1

                if processed % 50 == 0:
                    logger.info(f"Processed {processed}/{len(rom_paths)} ROMs...")

    manifest["total_size_mb"] = round(manifest["total_size_bytes"] / (1024 * 1024), 2)

    logger.info(
        f"Scan complete: {len(manifest['roms'])} ROMs, "
        f"{manifest['total_size_mb']} MB total"
    )

    return manifest


def save_manifest(manifest: dict, output_path: Path):
    """Save manifest to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    logger.info(f"Manifest saved to: {output_path}")


def load_manifest(input_path: Path) -> dict:
    """Load existing manifest."""
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_rom_by_hash(manifest: dict, hash_sha256: str) -> dict | None:
    """Find ROM in manifest by hash."""
    for rom in manifest.get("roms", []):
        if rom.get("hash_sha256") == hash_sha256:
            return rom
    return None


def get_top_games(manifest: dict, limit: int = 50) -> list[dict]:
    """Get top games by size (largest = most complete ROMs)."""
    roms = sorted(
        manifest.get("roms", []), key=lambda r: r.get("size_bytes", 0), reverse=True
    )
    return roms[:limit]


def get_map_mode_stats(manifest: dict) -> dict:
    """Get statistics on LoROM vs HiROM distribution."""
    stats = {"LoROM": 0, "HiROM": 0, "Unknown": 0}
    for rom in manifest.get("roms", []):
        mode = rom.get("map_mode", "Unknown")
        stats[mode] = stats.get(mode, 0) + 1
    return stats


def get_games_by_title(manifest: dict, title: str) -> list[dict]:
    """Search for games by title (case-insensitive)."""
    title_lower = title.lower()
    return [
        rom
        for rom in manifest.get("roms", [])
        if title_lower in rom.get("title", "").lower()
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan SNES ROM library")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("ROM_SOURCE/unzipped"),
        help="Root directory of ROM library",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ROM_SOURCE/roms_manifest.json"),
        help="Output manifest path",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel workers",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of ROMs to scan (for testing)",
    )

    args = parser.parse_args()

    manifest = scan_library(args.root, max_workers=args.workers, limit=args.limit)
    save_manifest(manifest, args.output)

    print("\n=== Scan Summary ===")
    print(f"Total ROMs: {manifest['total_roms']}")
    print(f"Total Size: {manifest['total_size_mb']} MB")
    print(f"Map Modes: {get_map_mode_stats(manifest)}")
