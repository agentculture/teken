---
title: afi-cli
nav_order: 0
permalink: /
description: Agent First Interface — scaffold CLI, MCP, and HTTP surfaces for tools whose primary consumer is an AI agent.
---

**Agent First Interface** — scaffold tools whose primary consumer is an AI
agent, not a human.
{: .fs-5 }

From a single source of truth, afi-cli generates three interface surfaces,
each shaped by a different agent-ergonomic principle:

- **CLI** — with a `learn` affordance so an agent can introspect the tool
  and author its own usage skill (not just read `--help`).
- **MCP server** — a deliberately minimal menu, tuned for low surface area
  over maximal API coverage.
- **HTTP site** — markdown pages plus a [sitemap](sitemap.xml), navigable
  by any agent with a fetch tool. *(This page is the HTTP surface.)*

## Quickstart

```bash
uv tool install afi-cli
afi explain afi            # top-level map
afi overview               # cross-surface rollup
afi learn                  # structured self-teaching prompt for an agent
```

`uv tool install` is the supported install path — not `pip install`.

## Read next

- [**AgentCulture**](agentculture.md) — the OSS org, its agents-as-members
  model, and where afi-cli sits inside it.
- [**Agent First**](agent-first.md) — the paradigm: learnability on the CLI,
  minimalism on MCP, discoverability on HTTP. The *why* behind every design
  call in this repo.
- [**Rubric**](rubric.md) — the five-bundle mechanical check that
  `afi cli verify` runs against any CLI. afi-cli itself is required to pass.

## Links

- **Repo:** <https://github.com/agentculture/afi-cli>
- **PyPI:** <https://pypi.org/project/afi-cli/>
- **Companion:** [agex-cli](https://culture.dev/agex) — agent *experience*
  inside a repo (hooks, CI, workflow). afi-cli is the agent's *interface*
  to a tool.
