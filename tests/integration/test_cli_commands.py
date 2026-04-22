"""End-to-end tests for the ``afi cli {cite,verify}`` surface.

These drive afi as a subprocess (not via :func:`main`) to catch packaging
issues — the reference tree must be present in the installed distribution,
not just on disk under the source tree.
"""

from __future__ import annotations

import json
import subprocess  # noqa: S404 - integration tests need subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_afi(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "afi", *args],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_cite_writes_reference_and_gitignore(tmp_path: Path) -> None:
    result = _run_afi("cli", "cite", str(tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    ref = tmp_path / ".afi" / "reference" / "python-cli"
    assert ref.is_dir()
    assert (ref / "AGENT.md").is_file()
    assert (ref / "MANIFEST.json").is_file()
    # Tokens must be literal.
    content = (ref / "{{slug}}" / "cli" / "__init__.py").read_text()
    assert "{{project_name}}" in content
    # gitignore updated.
    assert ".afi/" in (tmp_path / ".gitignore").read_text()


def test_cite_json_mode_emits_parseable_payload(tmp_path: Path) -> None:
    result = _run_afi("cli", "cite", str(tmp_path), "--json", cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "out" in payload
    assert payload["gitignore_updated"] is True
    assert len(payload["next_steps"]) == 3


def test_cite_then_verify_round_trip(tmp_path: Path) -> None:
    """Citing into an empty dir makes the reference available, but the
    target project itself isn't a CLI — verify should fail on structure
    (no pyproject.toml). This guards against the reference being a hidden
    scaffolder: cite DOES NOT produce a working CLI; it produces a
    reference for an agent to apply.
    """
    _run_afi("cli", "cite", str(tmp_path), cwd=tmp_path)

    # The empty target is not a CLI project — verify should bail at structure.
    result = _run_afi("cli", "verify", str(tmp_path), cwd=tmp_path)

    assert result.returncode != 0
    assert "pyproject.toml" in (result.stderr + result.stdout).lower()


def test_verify_self_passes() -> None:
    """`afi cli verify .` on the afi-cli repo passes every bundle."""
    result = _run_afi("cli", "verify", str(REPO_ROOT), cwd=REPO_ROOT)

    assert (
        result.returncode == 0
    ), f"self-verify failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def test_verify_json_mode_emits_structured_report() -> None:
    result = _run_afi("cli", "verify", ".", "--json", cwd=REPO_ROOT)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["tool"] == "afi"
    assert payload["summary"]["errors"] == 0
    assert payload["summary"]["total"] > 0
    assert set(payload["summary"]["bundles"].keys()) == {
        "structure",
        "learnability",
        "json",
        "errors",
        "explain",
    }


def test_bogus_verb_exits_with_hint() -> None:
    result = _run_afi("bogus-verb-zzz")

    assert result.returncode != 0
    assert "error:" in result.stderr
    assert "hint:" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("path", ["afi", "learn", "explain", "cli", "cli cite", "cli verify"])
def test_every_registered_path_has_explain_entry(path: str) -> None:
    tokens = path.split()
    result = _run_afi("explain", *tokens)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("#")
