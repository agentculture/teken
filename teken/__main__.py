"""Allow running teken as ``python -m teken``."""

import sys

from teken.cli import main

if __name__ == "__main__":
    sys.exit(main())
