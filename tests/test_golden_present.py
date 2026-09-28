from pathlib import Path

import pytest


def test_golden_fixture_exists():
    path = Path(__file__).parent / "fixtures" / "parity_golden.json"
    assert path.exists(), "Run: python tests/generate_parity_golden.py"
