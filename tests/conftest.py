"""Make the game packages importable without installing them."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "python"

if str(PYTHON) not in sys.path:
    sys.path.insert(0, str(PYTHON))
