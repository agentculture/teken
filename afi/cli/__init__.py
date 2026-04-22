"""Unified CLI entry point for afi.

Noun-based command groups and globals are registered here. Top-level globals
(``learn``, ``explain``) live under :mod:`afi.cli._commands`; per-noun groups
(``cli``, later ``mcp``, ``site``) are registered via their own ``register()``
functions following the same pattern.

Error propagation contract
--------------------------
Every handler raises :class:`afi.cli._errors.AfiError` on failure; the
top-level ``main()`` catches it via :func:`_dispatch` and routes through
:mod:`afi.cli._output`. Unknown exceptions are wrapped into an ``AfiError``
so no Python traceback leaks to stderr.
"""

from __future__ import annotations

import argparse
import sys

from afi import __version__
from afi.cli._commands import explain as _explain_cmd
from afi.cli._commands import learn as _learn_cmd
from afi.cli._errors import EXIT_USER_ERROR, AfiError
from afi.cli._output import emit_error


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

    # Globals (top-level, not nested under a noun).
    _learn_cmd.register(sub)
    _explain_cmd.register(sub)

    # Noun groups slot in here in later commits:
    #   _cli_group.register(sub)
    #   _mcp_group.register(sub)
    #   _site_group.register(sub)

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
