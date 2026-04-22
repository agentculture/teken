"""Bundle 3 — machine readability (``--json`` on listing verbs)."""

from __future__ import annotations

import json

from afi.rubric._types import CheckResult, VerifyContext

BUNDLE = "json"


def _check_learn_json_parseable(ctx: VerifyContext) -> CheckResult:
    out = ctx.runner.run(["learn", "--json"], timeout=5.0)
    if out.returncode != 0:
        return CheckResult(
            BUNDLE,
            "learn_json_exit_zero",
            False,
            "error",
            f"exit={out.returncode}",
            remediation="add `--json` flag to the `learn` command",
        )
    try:
        json.loads(out.stdout)
    except json.JSONDecodeError as err:
        return CheckResult(
            BUNDLE,
            "learn_json_parseable",
            False,
            "error",
            f"stdout is not valid JSON: {err}",
            remediation="make `learn --json` emit a parseable JSON object",
        )
    return CheckResult(
        BUNDLE, "learn_json_parseable", True, "info", f"{len(out.stdout)} chars JSON"
    )


def _check_stderr_clean_on_success(ctx: VerifyContext) -> CheckResult:
    out = ctx.runner.run(["learn", "--json"], timeout=5.0)
    if out.returncode == 0 and out.stderr == "":
        return CheckResult(
            BUNDLE, "stderr_clean_on_success", True, "info", "stderr empty on success"
        )
    return CheckResult(
        BUNDLE,
        "stderr_clean_on_success",
        False,
        "warn",
        f"stderr leaked {len(out.stderr)} chars on success",
        remediation="route results to stdout only; stderr should be empty on success",
    )


def _check_explain_json_parseable(ctx: VerifyContext) -> CheckResult:
    out = ctx.runner.run(["explain", "--json"], timeout=5.0)
    if out.returncode != 0:
        return CheckResult(
            BUNDLE,
            "explain_json_exit_zero",
            False,
            "warn",
            f"exit={out.returncode}",
            remediation="add `--json` flag to the `explain` command",
        )
    try:
        json.loads(out.stdout)
    except json.JSONDecodeError as err:
        return CheckResult(
            BUNDLE,
            "explain_json_parseable",
            False,
            "warn",
            f"stdout is not valid JSON: {err}",
            remediation="make `explain --json` emit a parseable JSON object",
        )
    return CheckResult(
        BUNDLE, "explain_json_parseable", True, "info", f"{len(out.stdout)} chars JSON"
    )


CHECKS = [
    _check_learn_json_parseable,
    _check_stderr_clean_on_success,
    _check_explain_json_parseable,
]


def run(ctx: VerifyContext) -> list[CheckResult]:
    return [check(ctx) for check in CHECKS]
