"""Markdown catalog for ``afi explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty
tuple and ``("afi",)`` both resolve to the root entry (aliased).

Keep bodies self-contained — an agent reading a single entry should get
enough context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# afi

afi is the AgentCulture Agent First Interface scaffolder. It emits reference
drops for agent-first CLIs (and, later, MCP servers and HTTP sites) and
audits any tool against the five-bundle agent-first rubric.

## Verbs

- `afi learn` — structured self-teaching prompt.
- `afi explain <path>` — markdown docs for any noun/verb.
- `afi cli cite [path]` — drop the CLI reference pattern into a project.
- `afi cli verify [path]` — audit a CLI against the rubric.

## Principles

afi is deliberately dumb: it emits references with literal `{{tokens}}` and
never merges into a consumer project. The agent running afi handles
integration. Pre-commit, CI, and other agent-workflow tooling live in the
sibling project `agex-cli`.

## Exit-code policy

- `0` success
- `1` user-input error (bad flag, bad path, missing arg)
- `2` environment / setup error (tool not installed, unreadable file)
- `3+` reserved

## See also

- `afi explain learn`
- `afi explain explain`
- `afi explain cli cite`
- `afi explain cli verify`
"""

_LEARN = """\
# afi learn

Prints a structured self-teaching prompt covering afi's purpose, command
map, exit-code policy, `--json` support, and `explain` pointer.

## Usage

    afi learn
    afi learn --json

In JSON mode, emits
`{"tool", "purpose", "commands", "exit_codes", "json_support", "explain_pointer"}`
to stdout.

## Rubric role

`learn` is bundle 2 (learnability) of the agent-first rubric. Any CLI that
passes bundle 2 prints ≥200 characters and mentions purpose, commands, exit
codes, `--json`, and `explain`.
"""

_EXPLAIN = """\
# afi explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help`
(terse, positional), `explain` is global and addressable by path.

## Usage

    afi explain afi
    afi explain learn
    afi explain cli
    afi explain cli cite
    afi explain cli verify --json

In text mode emits the markdown to stdout. In JSON mode emits
`{"path": [...], "markdown": "..."}` to stdout.

## Path resolution

Paths are shell-tokenised: `afi explain cli cite` resolves to the catalog
entry `("cli", "cite")`. Unknown paths exit `1` with a `hint:` pointing at
`afi explain afi` for the top-level map.

## Rubric role

`explain` is bundle 5 of the agent-first rubric: every registered noun must
resolve, and bad paths must exit non-zero with remediation.
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("afi",): _ROOT,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
}
