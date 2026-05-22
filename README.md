# teken

**Agent First Interface** — scaffold tools whose primary consumer is an AI agent, not a human.

> Formerly `afi-cli`. The project was renamed to **teken** (Hebrew תֶּקֶן, "standard"). The `afi-cli` package and the `afi` command still work as deprecated aliases — see [Install](#install).

From a single source of truth, teken generates three interface surfaces, each shaped by a different agent-ergonomic principle:

- **CLI** — with a `learn` affordance so an agent can introspect the tool and author its own usage skill (not just read `--help`).
- **MCP server** — a deliberately minimal menu, tuned for low surface area over maximal API coverage.
- **HTTP site** — markdown pages plus a sitemap, navigable by any agent with a fetch tool.

Part of the [AgentCulture](https://github.com/agentculture) OSS org — see [`docs/agentculture.md`](./docs/agentculture.md) for the org, its paradigm, and how teken is foundational to it. The design brief is in [`docs/agent-first.md`](./docs/agent-first.md); the concrete rubric that `teken cli doctor` enforces is in [`docs/rubric.md`](./docs/rubric.md).

## Install

```bash
uv tool install teken
```

Then `teken --version` should work on your PATH. `uv tool install` is the supported path — not `pip install`.

```bash
uv tool install afi-cli   # still works: a thin wrapper that installs teken
```

The `afi` command is retained as a deprecated alias for `teken` (it prints a one-line notice to stderr and forwards). New usage should prefer `teken`.

## Usage

Every teken command supports `--json` where it produces a listing or report, and respects the [exit-code policy](./docs/rubric.md#exit-code-policy) (`0` success / `1` user error / `2` env error).

### Introspect

```bash
teken learn                       # structured self-teaching prompt for an agent
teken learn --json                # same, as a JSON payload
teken explain cli cite            # markdown docs for any noun/verb path
teken explain teken               # top-level map
```

### CLI scaffolding

```bash
teken cli cite [path]             # emit the agent-first reference tree into
                                  # <path>/.teken/reference/python-cli/ (tokens left literal,
                                  # adds `.teken/` to .gitignore)
teken cli doctor [path]           # audit a CLI at <path> against the seven-bundle rubric
teken cli doctor . --json         # full structured report
teken cli doctor . --strict       # treat warnings as failures
```

`teken cli cite` writes only under `.teken/` plus one line in `.gitignore` — it never modifies the rest of the target project. The emitted tree has literal `{{project_name}}`, `{{slug}}`, `{{module}}` tokens; an agent reads the accompanying `AGENT.md` and applies the pattern to the host project on its own terms. Reference trees cited before the rename (under `.afi/`) are still detected.

`teken cli doctor` is a **hybrid** auditor: static checks for repo structure (`pyproject.toml`, `tests/`) and black-box subprocess probes for behavior (`learn`, `--json`, error discipline, `explain`). Every failure includes a concrete `remediation` pointer. (`teken cli verify` remains as a deprecated alias for `cli doctor`.)

### MCP / HTTP

Not implemented yet. Planned for v0.4 / v0.5.

## Develop

```bash
uv sync                          # install + dev deps
uv run pytest -n auto -v         # tests (includes the self-doctor acceptance gate)
uv run teken cli doctor .        # same gate, interactive
uv run pre-commit install        # enable lint hooks
```

The `tests/test_self_doctor.py` acceptance gate runs the rubric and self-doctor in-process against the repo root; any regression that breaks a bundle blocks the commit.

See [`CLAUDE.md`](./CLAUDE.md) for design intent and full command reference.

## License

MIT. © 2026 Ori Nachum / AgentCulture.
