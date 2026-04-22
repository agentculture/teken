"""Bundle 1 — structure & argparse discipline (static checks)."""

from __future__ import annotations

import tomllib

from afi.rubric._types import CheckResult, VerifyContext

BUNDLE = "structure"


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


CHECKS = [
    _check_pyproject_exists,
    _check_project_scripts,
    _check_tests_dir,
    _check_top_help_runs,
]


def run(ctx: VerifyContext) -> list[CheckResult]:
    return [check(ctx) for check in CHECKS]
