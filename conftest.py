"""Root conftest — ensures the project root is on sys.path for src imports."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
