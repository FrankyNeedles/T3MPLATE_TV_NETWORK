import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def full_pipeline():
    """Full pipeline for E2E tests."""
    print("Full pipeline mock successful.")
    return {"status": "success"}
