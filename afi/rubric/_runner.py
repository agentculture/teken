"""Subprocess-backed :class:`Runner` implementation.

Tries to invoke the target tool directly first; falls back to
``uv run --project <path> <tool>``. The resolved base argv is cached on
first success so subsequent calls don't pay the lookup cost.
"""

from __future__ import annotations

import subprocess  # noqa: S404 — the whole point of this module
from dataclasses import dataclass, field
from pathlib import Path

from afi.cli._errors import EXIT_ENV_ERROR, AfiError
from afi.rubric._types import RunOutput


@dataclass
class SubprocessRunner:
    cwd: Path
    tool_name: str
    _base_argv: list[str] = field(default_factory=list, init=False, repr=False)

    def _resolve_base(self) -> list[str]:
        if self._base_argv:
            return self._base_argv

        # Direct invocation.
        try:
            proc = subprocess.run(  # noqa: S603 - argv is controlled
                [self.tool_name, "--version"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            if proc.returncode == 0:
                self._base_argv = [self.tool_name]
                return self._base_argv
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # uv run fallback.
        try:
            proc = subprocess.run(  # noqa: S603, S607 - uv is on PATH by convention
                [
                    "uv",
                    "run",
                    "--project",
                    str(self.cwd),
                    self.tool_name,
                    "--version",
                ],
                capture_output=True,
                text=True,
                timeout=30.0,
                check=False,
            )
            if proc.returncode == 0:
                self._base_argv = [
                    "uv",
                    "run",
                    "--project",
                    str(self.cwd),
                    self.tool_name,
                ]
                return self._base_argv
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        raise AfiError(
            code=EXIT_ENV_ERROR,
            message=f"cannot invoke '{self.tool_name}' in {self.cwd}",
            remediation=f"run 'uv sync' in '{self.cwd}' so the tool is installed",
        )

    def run(self, args: list[str], *, timeout: float = 10.0) -> RunOutput:
        argv = self._resolve_base() + list(args)
        proc = subprocess.run(  # noqa: S603 - argv is controlled
            argv,
            cwd=self.cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return RunOutput(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
