#!/usr/bin/env python3
"""
Asset Validator
Validates SNES asset manifests (JSON) for integrity.
Checks structure, required fields, and file existence.
"""

import json
from pathlib import Path

from ..config import CONFIG


def validate_manifests(
    manifests_dir: Path = CONFIG.assets_dir / "manifests",
) -> dict[str, any]:
    """
    Validate all manifest files.
    Returns report with valid/invalid counts and details.
    """
    report = {"total": 0, "valid": 0, "invalid": [], "missing_files": []}

    for manifest_file in manifests_dir.glob("*.json"):
        report["total"] += 1
        game_id = manifest_file.stem
        try:
            with open(manifest_file, "r") as f:
                data = json.load(f)

            # Required structure check
            required_keys = ["game_id", "sprites", "audio"]
            missing_keys = [k for k in required_keys if k not in data]
            if missing_keys:
                report["invalid"].append(
                    {"game": game_id, "error": f"Missing keys: {missing_keys}"}
                )
                continue

            # Validate sprites
            for sprite_name, sprite_info in data["sprites"].items():
                if "bank" not in sprite_info or "offset" not in sprite_info:
                    report["invalid"].append(
                        {
                            "game": game_id,
                            "sprite": sprite_name,
                            "error": "Missing bank/offset",
                        }
                    )

            # Validate audio
            for track_name, audio_info in data["audio"].items():
                if "brr_offset" not in audio_info:
                    report["invalid"].append(
                        {
                            "game": game_id,
                            "track": track_name,
                            "error": "Missing brr_offset",
                        }
                    )
                # Check if actual file exists (placeholder)
                audio_path = CONFIG.assets_dir / "audio" / f"{game_id}_{track_name}.brr"
                if not audio_path.exists():
                    report["missing_files"].append(str(audio_path))

            report["valid"] += 1
            print(f"Valid: {game_id}")

        except json.JSONDecodeError as e:
            report["invalid"].append({"game": game_id, "error": f"JSON error: {e}"})
            print(f"Invalid JSON: {game_id}")
        except Exception as e:
            report["invalid"].append({"game": game_id, "error": str(e)})
            print(f"Error in {game_id}: {e}")

    print(f"\nValidation complete: {report['valid']}/{report['total']} valid")
    if report["invalid"]:
        print(f"Invalid: {len(report['invalid'])}")
    if report["missing_files"]:
        print(f"Missing files: {len(report['missing_files'])}")

    return report


if __name__ == "__main__":
    result = validate_manifests()
    print(json.dumps(result, indent=2))
