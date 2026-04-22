"""Tests for rubric bundle 1: structure."""

from __future__ import annotations

from pathlib import Path

from afi.rubric._types import RunOutput, VerifyContext
from afi.rubric.checks import structure
from tests.unit._fake_runner import FakeRunner


def _ctx(tmp_path: Path, runner: FakeRunner | None = None) -> VerifyContext:
    return VerifyContext(tmp_path, "demo", runner or FakeRunner())


def _write_pyproject(tmp_path: Path, *, with_scripts: bool = True) -> None:
    body = '[project]\nname = "demo"\nversion = "0.0.1"\n'
    if with_scripts:
        body += '\n[project.scripts]\ndemo = "demo:main"\n'
    (tmp_path / "pyproject.toml").write_text(body)


def test_all_pass_on_good_layout(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, with_scripts=True)
    (tmp_path / "tests").mkdir()
    runner = FakeRunner(responses={("--help",): RunOutput(0, "usage: demo ...\n", "")})
    results = structure.run(_ctx(tmp_path, runner))
    assert all(r.passed for r in results), [r for r in results if not r.passed]


def test_missing_pyproject_fails(tmp_path: Path) -> None:
    results = structure.run(_ctx(tmp_path))
    by_name = {r.check: r for r in results}
    assert not by_name["pyproject_exists"].passed
    assert by_name["pyproject_exists"].severity == "error"


def test_missing_scripts_fails(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, with_scripts=False)
    results = structure.run(_ctx(tmp_path))
    by_name = {r.check: r for r in results}
    assert not by_name["project_scripts"].passed
    assert "add a [project.scripts] entry" in by_name["project_scripts"].remediation


def test_missing_tests_dir_warns(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    results = structure.run(_ctx(tmp_path))
    by_name = {r.check: r for r in results}
    assert not by_name["tests_dir"].passed
    assert by_name["tests_dir"].severity == "warn"


def test_help_failure_is_error(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    (tmp_path / "tests").mkdir()
    runner = FakeRunner(responses={("--help",): RunOutput(2, "", "nope")})
    results = structure.run(_ctx(tmp_path, runner))
    by_name = {r.check: r for r in results}
    assert not by_name["top_help_runs"].passed
    assert by_name["top_help_runs"].severity == "error"
