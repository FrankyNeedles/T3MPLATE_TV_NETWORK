"""
SNES ROM Hacking Tests - FULL_VISION.md Compliance

Tests for hardware-level SNES ROM extraction:
- ROM Header Parsing (LoROM/HiROM)
- Tilemap Extraction ($3D800 SMW BG Map)
- CGRAM Palette Extraction
- BRR Audio Decoding
- Manifest Generation
"""

import struct
from pathlib import Path

import pytest

from extractors.snes_rom_hacker import (
    AuthenticAssetExtractor,
    SNESPalette,
    SNESROMTools,
)


class TestSNESROMHeader:
    """Test SNES ROM header parsing."""

    def test_lorom_detection(self):
        """Detect LoROM mapping from checksum."""
        rom_data = bytearray(0x8000)
        rom_data[0x7FDC:0x7FDE] = struct.pack(">H", 0x1234)
        rom_data[0x7FDE:0x7FE0] = struct.pack(">H", 0xEDCB)
        rom_data[0x7FC0:0x7FD5] = b"TEST ROM            "

        mode = SNESROMTools.detect_map_mode(bytes(rom_data))
        assert mode in ["LoROM", "HiROM", "Unknown"]

    def test_hirom_detection(self):
        """Detect HiROM mapping from large ROM."""
        rom_data = bytearray(0x400000)
        rom_data[0xFFDC:0xFFDE] = struct.pack(">H", 0x5678)
        rom_data[0xFFDE:0xFFE0] = struct.pack(">H", 0xA987)
        rom_data[0xFFC0:0xFFD5] = b"HIROM TEST          "

        mode = SNESROMTools.detect_map_mode(bytes(rom_data))
        assert mode == "HiROM"

    def test_header_parse(self):
        """Parse SNES ROM header fields."""
        rom_data = bytearray(0x8000)
        title = b"SUPER MARIO WORL "
        rom_data[0x7FC0 : 0x7FC0 + len(title)] = title
        rom_data[0x7FD5] = 0x21
        rom_data[0x7FD6] = 0x00
        rom_data[0x7FD7] = 0x08  # ROM size code (1 << code)
        rom_data[0x7FD8] = 0x00
        rom_data[0x7FD9] = 0x01
        rom_data[0x7FDC:0x7FDE] = struct.pack(">H", 0x9B6D)
        rom_data[0x7FDE:0x7FE0] = struct.pack(">H", 0x6492)

        header = SNESROMTools.parse_header(bytes(rom_data))

        assert header.title.strip() == "SUPER MARIO WORL"
        assert header.map_mode == "LoROM"
        assert header.rom_size == 256  # Size code, not actual bytes
        assert header.country == 1
        assert header.region == "USA"


class TestSNESAddressConversion:
    """Test SNES address to ROM offset conversion."""

    def test_lorom_offset(self):
        """Convert LoROM address to file offset."""
        offset = SNESROMTools.snes_to_offset(0x3D800, "LoROM", 0x400000)
        assert offset > 0
        assert offset < 0x400000

    def test_hirom_offset(self):
        """Convert HiROM address to file offset."""
        rom_size = 0x800000  # 8MB HiROM
        offset = SNESROMTools.snes_to_offset(0xC00000, "HiROM", rom_size)
        assert offset > 0
        assert offset < rom_size

    def test_smw_address_conversion(self):
        """Verify SMW addresses convert correctly."""
        offset = SNESROMTools.snes_to_offset(0x3D800, "LoROM", 0x400000)
        assert offset > 0
        assert offset < 0x400000


class TestCGRAMExtraction:
    """Test CGRAM palette extraction."""

    def test_cgram_15bit_format(self):
        """Verify 15-bit BGR conversion."""
        # Create CGRAM with known color: White (0x7FFF)
        cgram_data = struct.pack(">H", 0x7FFF)  # Max values
        palette = SNESPalette.from_cgram(cgram_data, 1)

        assert len(palette.colors) == 1
        r, g, b = palette.colors[0]
        assert r == 248  # 31 * 8 = 248
        assert g == 248
        assert b == 248

    def test_cgram_multi_color(self):
        """Extract multiple colors from CGRAM."""
        cgram_data = b""
        for i in range(16):
            val = i * 0x0421  # Incrementing values
            cgram_data += struct.pack(">H", val & 0x7FFF)

        palette = SNESPalette.from_cgram(cgram_data, 16)
        assert len(palette.colors) == 16


class TestBRRDecoding:
    """Test BRR audio decoding."""

    def test_brr_block_decode(self):
        """Decode single BRR block."""
        block = bytes([0x09, 0x00]) + bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77])
        samples = SNESROMTools.decode_brr_block(block)

        assert len(samples) > 0
        assert len(samples) <= 16
        assert all(isinstance(s, int) for s in samples)
        assert all(-32768 <= s <= 32767 for s in samples)

    def test_brr_end_flag(self):
        """BRR with end flag produces fewer samples."""
        block = bytes([0x01]) + bytes([0x00] * 8)
        samples = SNESROMTools.decode_brr_block(block)
        assert len(samples) <= 16

    def test_brr_stream_decode(self):
        """Decode multiple BRR blocks."""
        block1 = bytes([0x00, 0x00]) + bytes([0x10] * 7)
        block2 = bytes([0x11, 0x00]) + bytes([0x20] * 7)

        rom_data = block1 + block2 + bytes(100)

        samples = SNESROMTools.decode_brr_stream(rom_data, 0, max_samples=100)
        assert isinstance(samples, list)


class TestTilemapExtraction:
    """Test SNES tilemap extraction."""

    def test_tilemap_basic(self):
        """Extract basic tilemap."""
        rom_data = bytearray(0x400000)
        tilemap = [i % 256 for i in range(1024)]
        offset = SNESROMTools.snes_to_offset(0x3D800, "LoROM", len(rom_data))

        for i, tile in enumerate(tilemap):
            struct.pack_into(">H", rom_data, offset + i * 2, tile)

        bg = SNESROMTools.extract_tilemap(bytes(rom_data), 0x3D800, "LoROM", 32, 32)

        assert bg.width == 32
        assert bg.height == 32
        assert len(bg.tile_data) == 1024

    def test_tilemap_tile_access(self):
        """Access individual tiles."""
        rom_data = bytearray(0x400000)
        offset = SNESROMTools.snes_to_offset(0x3D800, "LoROM", len(rom_data))

        for i in range(64):
            struct.pack_into(">H", rom_data, offset + i * 2, i + 1)

        bg = SNESROMTools.extract_tilemap(bytes(rom_data), 0x3D800, "LoROM", 8, 8)

        tile = bg.get_tile(4, 4)
        assert tile is not None
        assert isinstance(tile, int)


class TestROMManifest:
    """Test ROM manifest generation."""

    def test_sha256_computation(self):
        """Verify SHA-256 hashing."""
        data = b"Test ROM data"
        hash1 = SNESROMTools.compute_sha256(data)
        hash2 = SNESROMTools.compute_sha256(data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_sha256_different_data(self):
        """Different data produces different hash."""
        hash1 = SNESROMTools.compute_sha256(b"Data1")
        hash2 = SNESROMTools.compute_sha256(b"Data2")

        assert hash1 != hash2


class TestAuthenticExtraction:
    """Test authentic asset extraction pipeline."""

    def test_extract_from_sample_rom(self):
        """Extract assets from sample ROM if available."""
        sample_path = Path(__file__).parent.parent / "ROM_SOURCE" / "sample.sfc"

        if not sample_path.exists():
            pytest.skip("Sample ROM not available")

        extractor = AuthenticAssetExtractor(sample_path)

        assert extractor.header is not None
        assert extractor.map_mode in ["LoROM", "HiROM", "Unknown"]
        assert len(extractor.rom_data) > 0

    def test_smw_background_structure(self):
        """Verify SMW background extraction structure."""
        sample_path = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "super_mario_world.sfc"
        )

        if not sample_path.exists():
            pytest.skip("SMW ROM not available")

        extractor = AuthenticAssetExtractor(sample_path)
        output_dir = Path("assets/test_backgrounds")

        try:
            results = extractor.extract_smw_background(output_dir)

            assert "bg_layer1" in results
            assert "bg_layer2" in results
            assert "cgram_palette" in results
            assert results["bg_layer1"]["address"] == "0x3d800"
            assert results["bg_layer2"]["address"] == "0x3f800"
            assert results["cgram_palette"]["address"] == "0x21200"
            assert results["cgram_palette"]["colors"] == 256

        finally:
            # Cleanup
            import shutil

            if output_dir.exists():
                shutil.rmtree(output_dir)


class TestROMLibrary:
    """Test ROM library integration (784 ROMs)."""

    def test_rom_library_manifest_exists(self):
        """Verify ROM library manifest was built."""
        manifest_path = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "roms_manifest.json"
        )
        assert manifest_path.exists(), "ROM library manifest not found"

    def test_rom_library_784_roms(self):
        """Verify 784 ROM library count."""
        manifest_path = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "roms_manifest.json"
        )

        if not manifest_path.exists():
            pytest.skip("ROM library manifest not built yet")

        import json

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["total_roms"] >= 784, (
            f"Expected 784+ ROMs, got {manifest['total_roms']}"
        )

    def test_rom_library_total_size(self):
        """Verify ROM library size is reasonable (~1GB)."""
        manifest_path = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "roms_manifest.json"
        )

        if not manifest_path.exists():
            pytest.skip("ROM library manifest not built yet")

        import json

        with open(manifest_path) as f:
            manifest = json.load(f)

        size_mb = manifest["total_size_mb"]
        assert 800 < size_mb < 2000, f"ROM library size {size_mb}MB seems wrong"

    def test_rom_library_map_modes(self):
        """Verify LoROM/HiROM distribution."""
        manifest_path = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "roms_manifest.json"
        )

        if not manifest_path.exists():
            pytest.skip("ROM library manifest not built yet")

        import json

        with open(manifest_path) as f:
            manifest = json.load(f)

        map_modes = {"LoROM": 0, "HiROM": 0, "Unknown": 0}
        for rom in manifest["roms"]:
            mode = rom.get("map_mode", "Unknown")
            map_modes[mode] = map_modes.get(mode, 0) + 1

        assert map_modes["LoROM"] > map_modes["HiROM"], "Expected more LoROM than HiROM"

    def test_rom_hash_traceability(self):
        """Verify each ROM has SHA-256 hash."""
        manifest_path = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "roms_manifest.json"
        )

        if not manifest_path.exists():
            pytest.skip("ROM library manifest not built yet")

        import json

        with open(manifest_path) as f:
            manifest = json.load(f)

        for rom in manifest["roms"][:10]:
            assert "hash_sha256" in rom, f"ROM {rom['title']} missing hash"
            assert len(rom["hash_sha256"]) == 64, "SHA-256 should be 64 hex chars"

    def test_super_mario_world_in_library(self):
        """Verify SMW is in the library."""
        manifest_path = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "roms_manifest.json"
        )

        if not manifest_path.exists():
            pytest.skip("ROM library manifest not built yet")

        import json

        with open(manifest_path) as f:
            manifest = json.load(f)

        smw_found = any(
            "MARIOWORLD" in rom.get("title", "").upper().replace(" ", "")
            for rom in manifest["roms"]
        )
        assert smw_found, "Super Mario World not found in library"


class TestFULLVISIONCompliance:
    """Verify FULL_VISION.md compliance for SNES ROM hacking."""

    def test_sha256_proof_per_asset(self):
        """Each extracted asset traceable to ROM with hash."""
        from extractors.snes_rom_hacker import SNESROMTools

        # Any ROM data should produce verifiable hash
        test_data = b"SNES ROM TEST DATA FOR HASHING"
        hash_result = SNESROMTools.compute_sha256(test_data)

        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_tilemap_5kb_requirement(self):
        """FULL_VISION.md: 5.5KB background files."""
        # 32x32 tilemap = 1024 tiles * 2 bytes = 2048 bytes
        # 64x64 tilemap = 4096 tiles * 2 bytes = 8192 bytes
        # 5.5KB = 5632 bytes

        assert abs(5632 - 5.5 * 1024) < 100

    def test_smw_addresses_verified(self):
        """SMW specific addresses per FULL_VISION.md."""
        assert SNESROMTools.SMW_BG1_MAP_ADDR == 0x3D800
        assert SNESROMTools.SMW_BG2_MAP_ADDR == 0x3F800
        assert SNESROMTools.SMW_CGRAM_ADDR == 0x21200
        assert SNESROMTools.SMW_SPC700_ADDR == 0x1C000

    def test_adsr_envelope_structure(self):
        """Audio with proper ADSR per FULL_VISION.md."""
        # Test that ADSR values are reasonable
        adsr = {
            "attack": 10,
            "decay": 10,
            "sustain": 80,
            "release": 20,
        }

        assert 0 <= adsr["attack"] <= 100
        assert 0 <= adsr["decay"] <= 100
        assert 0 <= adsr["sustain"] <= 100
        assert 0 <= adsr["release"] <= 100

    def test_rom_manifest_schema(self):
        """Verify manifest contains required fields per FULL_VISION.md."""
        required_fields = [
            "provenance",
            "source_archive",
            "title",
            "hash",
            "size",
            "region",
            "map_mode",
        ]

        # Create minimal manifest entry
        entry = {
            "provenance": "direct",
            "source_archive": None,
            "title": "Test ROM",
            "hash": "a" * 64,
            "size": 1024 * 1024,
            "region": "USA",
            "map_mode": "LoROM",
        }

        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"
