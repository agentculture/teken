"""Bundle 1 — structure & argparse discipline (static checks)."""

from __future__ import annotations

import subprocess  # noqa: S404 — we explicitly isolate target code via subprocess
import tomllib

from afi.rubric._types import CheckResult, VerifyContext

BUNDLE = "structure"

_MAIN_PROBE_TIMEOUT = 30.0


def _check_pyproject_exists(ctx: VerifyContext) -> CheckResult:
    p = ctx.target_path / "pyproject.toml"
    if p.is_file():
        return CheckResult(BUNDLE, "pyproject_exists", True, "info", f"found {p}")
    return CheckResult(
        BUNDLE,
        "pyproject_exists",
        False,
        "error",
        f"missing {p}",
        remediation="create a pyproject.toml with [project] metadata",
    )


def _check_project_scripts(ctx: VerifyContext) -> CheckResult:
    p = ctx.target_path / "pyproject.toml"
    if not p.is_file():
        return CheckResult(
            BUNDLE,
            "project_scripts",
            False,
            "error",
            "no pyproject.toml",
            remediation="create pyproject.toml first",
        )
    try:
        data = tomllib.loads(p.read_text())
    except tomllib.TOMLDecodeError as err:
        return CheckResult(
            BUNDLE,
            "project_scripts",
            False,
            "error",
            f"invalid TOML in {p}: {err}",
            remediation="fix the TOML syntax error in pyproject.toml",
        )
    scripts = data.get("project", {}).get("scripts", {})
    if scripts:
        return CheckResult(
            BUNDLE,
            "project_scripts",
            True,
            "info",
            f"{len(scripts)} entry/entries: {', '.join(scripts.keys())}",
        )
    return CheckResult(
        BUNDLE,
        "project_scripts",
        False,
        "error",
        "no [project.scripts] in pyproject.toml",
        remediation="add a [project.scripts] entry so the tool has an entry point",
    )


def _check_tests_dir(ctx: VerifyContext) -> CheckResult:
    tests = ctx.target_path / "tests"
    if tests.is_dir():
        return CheckResult(BUNDLE, "tests_dir", True, "info", f"found {tests}")
    return CheckResult(
        BUNDLE,
        "tests_dir",
        False,
        "warn",
        f"no tests/ directory at {tests}",
        remediation="add a tests/ directory with pytest smoke tests",
    )


def _check_top_help_runs(ctx: VerifyContext) -> CheckResult:
    out = ctx.runner.run(["--help"], timeout=5.0)
    if out.returncode == 0 and out.stdout.strip():
        return CheckResult(
            BUNDLE,
            "top_help_runs",
            True,
            "info",
            f"{len(out.stdout)} chars on stdout",
        )
    return CheckResult(
        BUNDLE,
        "top_help_runs",
        False,
        "error",
        f"--help exit={out.returncode} stdout_len={len(out.stdout)}",
        remediation="ensure `<tool> --help` exits 0 and prints usage",
    )


_MAIN_PROBE_SOURCE = r"""
import sys, io, inspect, importlib, contextlib

MODULE = {module!r}
FUNC = {func!r}

try:
    _m = importlib.import_module(MODULE)
except Exception as _e:
    sys.stderr.write(f"import_failed: {{type(_e).__name__}}: {{_e}}\n")
    sys.exit(2)

_func = getattr(_m, FUNC, None)
if _func is None or not callable(_func):
    sys.stderr.write(f"not_found: {{MODULE}}.{{FUNC}}\n")
    sys.exit(2)

_sig = inspect.signature(_func)
_params = list(_sig.parameters.values())

if len(_params) > 1:
    sys.stderr.write(
        f"bad_arity: expected 0 or 1 positional parameter, got {{len(_params)}}\n"
    )
    sys.exit(2)

if len(_params) == 1 and _params[0].default is inspect.Parameter.empty:
    sys.stderr.write(
        "no_default: argv parameter must default to None so main() can be called with no args\n"
    )
    sys.exit(2)

# Functional invariant: main(["--help"]) must terminate with an int exit code
# (either returned or via SystemExit). argparse's --help path SystemExits(0),
# which is the canonical conforming case.
_buf = io.StringIO()
_rc = None
try:
    with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
        _rc = _func(["--help"])
except SystemExit as _se:
    _code = _se.code
    if _code is None:
        _rc = 0
    elif isinstance(_code, int):
        _rc = _code
    else:
        sys.stderr.write(f"bad_exit: SystemExit.code is {{type(_code).__name__}}\n")
        sys.exit(2)
except TypeError as _e:
    sys.stderr.write(f"arity_mismatch: {{_e}}\n")
    sys.exit(2)
except Exception as _e:
    sys.stderr.write(f"invocation_raised: {{type(_e).__name__}}: {{_e}}\n")
    sys.exit(2)

if not isinstance(_rc, int):
    sys.stderr.write(
        f"bad_return: main(['--help']) returned {{type(_rc).__name__}}, expected int\n"
    )
    sys.exit(2)

sys.stdout.write("ok\n")
sys.exit(0)
"""


def _resolve_entry_target(ctx: VerifyContext) -> tuple[str, str] | None:
    """Return ``(module, func)`` for ``ctx.tool_name``'s script entry, or ``None``.

    The entry is chosen by matching the script name to ``ctx.tool_name``; if
    no match, the first declared script is used (consistent with the rest of
    afi's targeting heuristics).
    """
    p = ctx.target_path / "pyproject.toml"
    if not p.is_file():
        return None
    try:
        data = tomllib.loads(p.read_text())
    except tomllib.TOMLDecodeError:
        return None
    scripts = data.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict) or not scripts:
        return None
    target = scripts.get(ctx.tool_name)
    if not isinstance(target, str) or ":" not in target:
        target = next(iter(scripts.values()))
    if not isinstance(target, str) or ":" not in target:
        return None
    module, func = target.split(":", 1)
    return module, func


def _check_main_entry_contract(ctx: VerifyContext) -> CheckResult:
    """Assert the target's entry-point ``main`` matches the agent-first contract.

    Culture's embed harness calls ``module.main(argv) -> int`` on every
    embedded CLI. This check codifies the signature and functional invariant
    so a sibling CLI cannot drift (e.g. ``main()`` with no argv, or
    ``sys.exit``-ing on normal paths with a non-int code).

    Runs a subprocess probe — **never imports the target's code into the
    rubric runner's interpreter** — because targets may have import-time
    side effects.
    """
    resolved = _resolve_entry_target(ctx)
    if resolved is None:
        return CheckResult(
            BUNDLE,
            "main_entry_contract",
            False,
            "warn",
            "cannot resolve [project.scripts] entry for probe",
            remediation="ensure pyproject.toml declares [project.scripts] with module:func",
        )
    module, func = resolved
    probe = _MAIN_PROBE_SOURCE.format(module=module, func=func)

    argv = [
        "uv",
        "run",
        "--project",
        str(ctx.target_path),
        "python",
        "-c",
        probe,
    ]
    try:
        proc = subprocess.run(  # noqa: S603 - argv controlled; see _runner.py
            argv,
            cwd=ctx.target_path,
            capture_output=True,
            text=True,
            timeout=_MAIN_PROBE_TIMEOUT,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as err:
        return CheckResult(
            BUNDLE,
            "main_entry_contract",
            False,
            "warn",
            f"probe could not run: {err}",
            remediation="ensure `uv` is on PATH and `uv sync` has been run in the target project",
        )

    if proc.returncode == 0 and proc.stdout.strip() == "ok":
        return CheckResult(
            BUNDLE,
            "main_entry_contract",
            True,
            "info",
            f"`{module}.{func}(['--help'])` conforms to main(argv) -> int",
        )
    evidence = (proc.stderr.strip() or proc.stdout.strip() or f"exit={proc.returncode}")[:300]
    return CheckResult(
        BUNDLE,
        "main_entry_contract",
        False,
        "error",
        evidence,
        remediation=(
            "define `def main(argv: list[str] | None = None) -> int:` in the script entry "
            "module; no bare `sys.exit()` on normal paths (argparse --help SystemExit(0) is ok)"
        ),
    )


CHECKS = [
    _check_pyproject_exists,
    _check_project_scripts,
    _check_tests_dir,
    _check_top_help_runs,
    _check_main_entry_contract,
]


def run(ctx: VerifyContext) -> list[CheckResult]:
    return [check(ctx) for check in CHECKS]
