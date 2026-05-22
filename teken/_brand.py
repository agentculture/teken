"""Single source of truth for brand-identifying strings.

The project was renamed from ``afi`` to ``teken`` (Hebrew תֶּקֶן, "standard").
Every user-facing reference to the program name, distribution, or dot-directory
should read from here so a future rename is a one-line change. ``LEGACY_*``
values keep the old ``afi`` surface working during the migration.
"""

PROG = "teken"  # primary CLI command + argparse prog
LEGACY_PROG = "afi"  # deprecated alias command
DIST = "teken"  # canonical PyPI distribution (importlib.metadata key)
LEGACY_DIST = "afi-cli"  # wrapper distribution; self-doctor still recognises it
DOTDIR = ".teken"  # primary dot-directory for cited references
LEGACY_DOTDIR = ".afi"  # read-fallback dot-directory (existing trees)
REPO_URL = "https://github.com/agentculture/teken"
ISSUES_URL = f"{REPO_URL}/issues"

__all__ = [
    "PROG",
    "LEGACY_PROG",
    "DIST",
    "LEGACY_DIST",
    "DOTDIR",
    "LEGACY_DOTDIR",
    "REPO_URL",
    "ISSUES_URL",
]
