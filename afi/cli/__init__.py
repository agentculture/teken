"""Unified CLI entry point for afi.

Noun-based command groups will be registered here as they land. The initial
scaffold ships only the top-level parser, ``--version``, and a ``learn`` stub
so the agent-learnability principle is wired in from commit one.

Error propagation contract
--------------------------
Every handler raises :class:`afi.cli._errors.AfiError` on failure; the
top-level ``main()`` catches it via ``_dispatch()`` and routes through
:mod:`afi.cli._output`. Unknown exceptions are wrapped into an ``AfiError``
so no Python traceback leaks to stderr.
"""

from __future__ import annotations

import argparse
import sys

from afi import __version__
from afi.cli._errors import EXIT_USER_ERROR, AfiError
from afi.cli._output import emit_error


def _cmd_learn(_args: argparse.Namespace) -> int:
    """Print a minimal self-description aimed at an agent reader.

    The ``learn`` affordance: an agent runs ``afi learn`` and gets enough to
    author its own usage skill without scraping ``--help``. Content expands in
    later commits; kept terse here so commit 1 stays focused on error plumbing.
    """
    print(
        "afi — Agent First Interface scaffolder.\n"
        "\n"
        "Status: scaffold only. No feature commands yet.\n"
        "\n"
        "Planned surfaces (all generated from one source of truth):\n"
        "  - CLI with learn affordance (this command is the prototype).\n"
        "  - MCP server with a minimal menu.\n"
        "  - HTTP site with markdown pages and a sitemap.\n"
        "\n"
        "See: https://github.com/agentculture/afi-cli"
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="afi",
        description="afi — Agent First Interface scaffolder",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    learn = sub.add_parser("learn", help="Print a self-description for agent consumers.")
    learn.set_defaults(func=_cmd_learn)

    return parser


def _dispatch(args: argparse.Namespace) -> int:
    """Invoke the registered handler and translate exceptions to exit codes.

    Extracted from ``main()`` so unit tests can exercise the error-handling
    path without going through argparse.
    """
    json_mode = bool(getattr(args, "json", False))
    try:
        return args.func(args)
    except AfiError as err:
        emit_error(err, json_mode=json_mode)
        return err.code
    except Exception as err:  # noqa: BLE001 - last-resort; wrap and route cleanly
        wrapped = AfiError(
            code=EXIT_USER_ERROR,
            message=f"unexpected: {err.__class__.__name__}: {err}",
            remediation="file a bug at https://github.com/agentculture/afi-cli/issues",
        )
        emit_error(wrapped, json_mode=json_mode)
        return wrapped.code


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return _dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
