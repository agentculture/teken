"""Tests for rubric bundle 3: json output."""

from __future__ import annotations

from pathlib import Path

from afi.rubric._types import RunOutput, VerifyContext
from afi.rubric.checks import json_output
from tests.unit._fake_runner import FakeRunner


def _ctx(tmp_path: Path, runner: FakeRunner) -> VerifyContext:
    return VerifyContext(tmp_path, "demo", runner)


def test_pass_on_valid_json(tmp_path: Path) -> None:
    runner = FakeRunner(
        responses={
            ("learn", "--json"): RunOutput(0, '{"ok": true}\n', ""),
            ("explain", "--json"): RunOutput(0, '{"path": [], "markdown": "..."}', ""),
        }
    )
    results = json_output.run(_ctx(tmp_path, runner))
    assert all(r.passed for r in results), [r for r in results if not r.passed]


def test_fail_on_non_json_learn(tmp_path: Path) -> None:
    runner = FakeRunner(
        responses={
            ("learn", "--json"): RunOutput(0, "not json at all", ""),
            ("explain", "--json"): RunOutput(0, "{}", ""),
        }
    )
    results = json_output.run(_ctx(tmp_path, runner))
    by_name = {r.check: r for r in results}
    assert not by_name["learn_json_parseable"].passed


def test_warn_on_stderr_leak(tmp_path: Path) -> None:
    runner = FakeRunner(
        responses={
            ("learn", "--json"): RunOutput(0, "{}", "some diagnostic"),
            ("explain", "--json"): RunOutput(0, "{}", ""),
        }
    )
    results = json_output.run(_ctx(tmp_path, runner))
    by_name = {r.check: r for r in results}
    assert not by_name["stderr_clean_on_success"].passed
    assert by_name["stderr_clean_on_success"].severity == "warn"
