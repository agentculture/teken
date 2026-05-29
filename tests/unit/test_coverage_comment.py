"""Unit tests for the CI coverage-comment renderer (.github/scripts).

The script lives under .github/scripts (a CI helper, outside the package), so we
load it by path. We only test the pure ``build_comment`` renderer — the posting
path shells out to ``gh`` and is exercised in CI, not here.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "coverage_comment.py"

_SAMPLE_XML = """<?xml version="1.0" ?>
<coverage line-rate="0.909" branch-rate="0.75" lines-covered="200" lines-valid="220"
          branches-valid="8" branches-covered="6">
  <packages>
    <package name="agentfront">
      <classes>
        <class filename="agentfront/full.py" line-rate="1.0">
          <lines><line number="1" hits="1"/></lines>
        </class>
        <class filename="agentfront/partial.py" line-rate="0.5">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""


@pytest.fixture()
def comment() -> str:
    spec = importlib.util.spec_from_file_location("coverage_comment", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_comment(_SAMPLE_XML)


def test_overall_line_coverage_rendered(comment: str) -> None:
    assert "90.9%" in comment
    assert "200/220 lines" in comment


def test_branch_coverage_rendered_when_present(comment: str) -> None:
    assert "75.0%" in comment
    assert "8 branches" in comment


def test_sticky_marker_present(comment: str) -> None:
    assert "<!-- coverage-report -->" in comment


def test_partial_file_listed_full_file_omitted(comment: str) -> None:
    assert "agentfront/partial.py" in comment  # below 100% → listed
    assert "agentfront/full.py" not in comment  # fully covered → omitted


def test_green_icon_above_threshold(comment: str) -> None:
    assert "🟢" in comment  # 90.9% ≥ 80
