import sys
from pathlib import Path

import pytest


def main() -> None:
    tests_dir = Path(__file__).parent
    sys.exit(pytest.main([str(tests_dir), *sys.argv[1:]]))
