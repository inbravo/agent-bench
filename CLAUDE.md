# CLAUDE.md — agent-bench

This file tells Claude Code how to work in this repository.

## What this repo is

A research lab for Agentic AI: comparing LangGraph, CrewAI, Databricks Mosaic, Snowflake Cortex, OpenAI Agents SDK, and Claude SDK on **real BFSI/RegTech tasks** (BCBS 239, FRTB, COREP), scored on **cost-per-correct-decision**.

Companion repo: https://github.com/inbravo/context-lab

## Folder naming convention

```
[task]-[framework]-[backend]-[YYYY-MM]/
```

- `[task]` — the problem being solved (e.g. `bcbs239-lineage`, `frtb-calc`, `tool-use-baseline`)
- `[framework]` — the agentic framework (e.g. `langgraph`, `crewai`, `mosaic`, `cortex`)
- `[backend]` — the LLM backend (e.g. `ollama`, `databricks`, `snowflake`, `generic`)
- `[YYYY-MM]` — month created

**Always task-first.** This is intentional — the comparison axis is the task, not the framework.

## Per-example file layout

Every example folder must have:

```
agent.py              ← backend-agnostic agent code
config.yaml           ← LLM_BACKEND switch (ollama / databricks)
tools/                ← tool definitions (MCP-ready stubs)
rubric.yaml           ← evaluation rubric for LLM-as-judge scoring
tests/
  test_local.py       ← runs against Ollama
  test_databricks.py  ← runs against Databricks Foundation Model APIs
traces/
  .gitkeep            ← MLflow trace JSON files go here (gitignored)
README.md             ← what it shows, quick start, architecture ASCII
```

## Backend switching

`config.yaml` in each example has `active_backend: "ollama"` or `active_backend: "databricks"`.
Agent code reads this via `_shared/backend.py`. Never hardcode an endpoint in agent code.

## Decision Economics — the signature metric

Every example should optionally compute:

```python
cpcd = token_cost_usd / quality_score
```

Use `_shared/scorer.py` for this. `rubric.yaml` defines the LLM-as-judge criteria.

## Common commands

```bash
# Run a local example against Ollama
cd [task]-[framework]-[ollama]-[YYYY-MM]
python agent.py

# Run tests
pytest tests/test_local.py -v

# Switch to Databricks
# Edit config.yaml: active_backend: "databricks"
# Set .env: DATABRICKS_HOST, DATABRICKS_TOKEN
python agent.py

# Run Databricks tests
pytest tests/test_databricks.py -v
```

## Environment variables

```bash
# .env — never commit
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN=your-pat-token
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
```

## Style rules

- **Python 3.11+**
- Type hints everywhere
- Docstrings on all public functions
- `rubric.yaml` criteria are YAML, not Python dicts
- README for every example follows the template in `_shared/README_TEMPLATE.md`
- No OpenAI keys hardcoded — use env vars or config.yaml

## Phases

| Phase | Frameworks | Focus |
|---|---|---|
| 1 | LangGraph | Stateful graphs, BCBS 239, dual-backend basics |
| 2 | CrewAI | Role-based multi-agent, same BFSI tasks |
| 3 | Databricks Mosaic, Snowflake Cortex | Enterprise governed agents |
| 4 | OpenAI Agents SDK, Claude SDK, Microsoft AF, Google ADK | Cloud provider APIs |
| 5 | Generic | Decision economics, eval harness, MCP interop |
