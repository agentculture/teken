"""Cite engine — copies the reference tree and updates ``.gitignore``.

The operation is safe by construction:

* writes only under ``out`` (default ``<target>/.afi/reference/<lang>-cli/``);
* adds one line to ``<target>/.gitignore`` only when ``.afi/`` is absent;
* touches nothing else in the target project;
* re-running wipes and re-copies ``out`` — always the latest reference.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from afi.cli._errors import EXIT_ENV_ERROR, EXIT_USER_ERROR, AfiError

SUPPORTED_LANGS = ("python",)

GITIGNORE_ENTRY = ".afi/"

_REFERENCES_DIR = Path(__file__).resolve().parent / "references"


@dataclass(frozen=True)
class CiteReport:
    out: Path
    written_count: int
    gitignore_updated: bool

    def describe_next_steps(self) -> list[str]:
        return [
            f"Read {self.out / 'AGENT.md'} — describes each file's role "
            "(stable-contract vs shape-adapt) and lists the {{tokens}} to substitute.",
            "Apply the pattern to your project: copy stable-contract files verbatim, "
            "reshape shape-adapt files to your module layout, then substitute "
            "{{project_name}}, {{slug}}, {{module}} throughout.",
            "Run `afi cli verify .` to confirm the result satisfies the agent-first rubric.",
        ]

    def to_dict(self) -> dict[str, object]:
        return {
            "out": str(self.out),
            "written_count": self.written_count,
            "gitignore_updated": self.gitignore_updated,
            "next_steps": self.describe_next_steps(),
            "further_reading": {
                "agent_md": str(self.out / "AGENT.md"),
                "explain": ["afi explain cli cite", "afi explain cli verify"],
            },
        }


def emit_reference(
    target_path: Path,
    *,
    lang: str = "python",
    out: Path | None = None,
) -> CiteReport:
    """Copy the ``lang`` reference tree into ``out`` and touch ``.gitignore``."""
    if lang not in SUPPORTED_LANGS:
        raise AfiError(
            code=EXIT_USER_ERROR,
            message=f"unsupported lang: {lang}",
            remediation=f"supported langs: {', '.join(SUPPORTED_LANGS)}",
        )
    target_path = target_path.resolve()
    if not target_path.is_dir():
        raise AfiError(
            code=EXIT_USER_ERROR,
            message=f"target path does not exist: {target_path}",
            remediation="pass a path to an existing directory, or '.' for cwd",
        )

    if out is None:
        out = target_path / ".afi" / "reference" / f"{lang}-cli"

    src = _REFERENCES_DIR / f"{lang}-cli"
    if not src.is_dir():
        raise AfiError(
            code=EXIT_ENV_ERROR,
            message=f"reference tree missing at {src}",
            remediation="file a bug — reference data not packaged",
        )

    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, out)

    written = sum(1 for p in out.rglob("*") if p.is_file())
    gitignore_updated = _ensure_gitignore_line(target_path / ".gitignore")

    return CiteReport(out=out, written_count=written, gitignore_updated=gitignore_updated)


def _ensure_gitignore_line(gitignore: Path) -> bool:
    """Ensure ``GITIGNORE_ENTRY`` is present in ``gitignore``.

    Returns ``True`` if the file was created or appended; ``False`` if the
    line (or an equivalent glob) was already present.
    """
    line = GITIGNORE_ENTRY
    equivalents = {line, line.rstrip("/"), line + "**", line.rstrip("/") + "/**"}
    if gitignore.is_file():
        existing = {s.strip() for s in gitignore.read_text().splitlines()}
        if existing & equivalents:
            return False
        body = gitignore.read_text()
        if body and not body.endswith("\n"):
            body += "\n"
        body += line + "\n"
        gitignore.write_text(body)
        return True
    gitignore.write_text(line + "\n")
    return True
