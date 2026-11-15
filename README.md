# agent-bench

> **Agentic AI framework benchmarking — decision economics at the core**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-orange)](https://github.com/langchain-ai/langgraph)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.28%2B-purple)](https://github.com/joaomdmoura/crewAI)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What Is This Repo?

`agent-bench` is a structured collection of **agentic design pattern examples**
across multiple frameworks (LangGraph, CrewAI, Databricks Mosaic AI, Snowflake
Cortex, OpenAI SDK, Claude SDK). Each example is benchmarked on the same axis:

```
CPCD = token_cost_usd / quality_score
```

**Cost-Per-Correct-Decision (CPCD)** is the primary metric. Lower is better.
It answers the question every engineering team eventually asks: *Is the
smarter (more expensive) agent actually worth it?*

---

## Folder Convention

```
[pattern]-[framework]-[backend]/          ← generic examples
[pattern]-[task]-[framework]-[backend]/   ← domain-specific examples
```

Brackets `[]` are visual separators — they make the segments scannable in a file
tree. No dates. No version numbers.

**Segment reference**:

| Segment | Meaning | Examples |
|---|---|---|
| `pattern` | Agentic design pattern slug | `tool-use`, `react`, `fw-swap`, `cpcd` |
| `task` | Domain-specific task label | `bcbs239`, `credit-risk` |
| `framework` | Agent framework | `langgraph`, `crewai`, `openai`, `claude` |
| `backend` | LLM backend | `ollama`, `databricks`, `openai`, `anthropic` |

---

## Category Structure

```
agent-bench/
│
├── reasoning/              # 1. Reasoning Mechanics
│   ├── [tool-use]-[langgraph]-[ollama]/
│   ├── [react]-[langgraph]-[ollama]/
│   ├── [react]-[langgraph]-[databricks]/
│   ├── [reflection]-[langgraph]-[ollama]/       # planned
│   └── [plan-exec]-[langgraph]-[ollama]/        # planned
│
├── topology/               # 2. Agent Topology
│   ├── [fw-swap]-[crewai]-[ollama]/
│   ├── [role-crew]-[crewai]-[ollama]/           # planned
│   ├── [orch-worker]-[langgraph]-[ollama]/      # planned
│   └── [fan-out]-[langgraph]-[ollama]/          # planned
│
├── context-integration/    # 3. Tool & Context Integration
│   ├── [mcp-tools]-[langgraph]-[ollama]/        # planned
│   ├── [rag-tool]-[langgraph]-[ollama]/         # planned
│   └── [memory]-[langgraph]-[ollama]/           # planned
│
├── evaluation/             # 4. Evaluation & Observability
│   ├── [llm-judge]-[multi]-[ollama]/            # planned
│   └── [trace-score]-[langgraph]-[ollama]/      # planned
│
├── decision-econ/          # 5. Decision Economics  ← signature category
│   ├── [cpcd]-[multi]-[ollama]/
│   ├── [pareto]-[multi]-[ollama]/               # planned
│   ├── [budget]-[langgraph]-[ollama]/           # planned
│   ├── [tier-routing]-[langgraph]-[ollama]/     # planned
│   └── [degrad-curve]-[multi]-[ollama]/         # planned
│
├── governance/             # 6. Safety, Control & Governance
│   ├── [hitl]-[langgraph]-[ollama]/             # planned
│   ├── [guardrails]-[langgraph]-[ollama]/       # planned
│   └── [adversarial]-[langgraph]-[ollama]/      # planned
│
├── portability/            # 7. Deployment & Backend Portability
│   ├── [backend-swap]-[langgraph]-[multi]/      # planned
│   ├── [fw-compare]-[multi]-[ollama]/           # planned
│   └── [fallback]-[langgraph]-[multi]/          # planned
│
├── _shared/                # Shared utilities
│   ├── logging_config.py   ← structured logging setup
│   ├── backend.py          ← LLM factory (Ollama / OpenAI / Databricks / …)
│   └── scorer.py           ← LLM-as-Judge scorer, CPCD computation
│
├── PATTERNS.md             ← Full design pattern catalogue (this is the map)
├── Makefile
└── README.md
```

---

## Completed Examples

| Folder | Pattern | Scenario |
|---|---|---|
| `reasoning/[tool-use]-[langgraph]-[ollama]` | Tool Use | Weather assistant |
| `reasoning/[react]-[langgraph]-[ollama]` | ReAct | Book finder with availability check |
| `topology/[fw-swap]-[crewai]-[ollama]` | Framework Swap | Blog post crew (Researcher → Writer → Editor) |
| `decision-econ/[cpcd]-[multi]-[ollama]` | CPCD | Multi-framework CPCD comparison dashboard |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/inbravo/agent-bench.git
cd agent-bench

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Start Ollama (must be running locally)
ollama pull llama3.1:8b

# 5. Run your first example
python reasoning/\[tool-use\]-\[langgraph\]-\[ollama\]/agent.py

# 6. Run the CPCD comparison
python decision-econ/\[cpcd\]-\[multi\]-\[ollama\]/agent.py
```

---

## Shared Utilities (`_shared/`)

Every example imports from the same three modules:

| Module | Purpose |
|---|---|
| `logging_config.py` | Structured JSON logging, one-line setup |
| `backend.py` | `get_config(config_path)`, `get_llm(config)` — backend-agnostic LLM factory |
| `scorer.py` | `score_run(task, answer, config_path)` → `{ quality_score, token_cost_usd, cpcd }` |

The dual `sys.path` pattern in every `agent.py`:

```python
sys.path.insert(0, str(Path(__file__).parents[2]))          # repo root
sys.path.insert(0, str(Path(__file__).parents[2] / "_shared"))  # shared utils
```

---

## The CPCD Metric

```
CPCD = token_cost_usd / quality_score
```

| Situation | Interpretation |
|---|---|
| CPCD = 0.0 | Free inference (Ollama local); rank by quality only |
| CPCD is low | Good value — high quality relative to cost |
| CPCD is high | Expensive relative to quality — consider a cheaper tier |
| CPCD = ∞ | Zero quality — the run failed; discard |

The scorer uses an **LLM-as-Judge** pattern: a second LLM call rates the
primary agent's answer against a per-example `rubric.yaml`. Criteria weights
sum to 1.0. The final `quality_score` is a weighted average in [0, 1].

---

## Design Principles

1. **No BFSI domain knowledge required** — examples use weather, books, blog posts. Domain-specific patterns live in separate task-labelled folders.
2. **Config-driven backend swap** — change `llm_backend` in `config.yaml`; the agent code is unchanged.
3. **Shared scorer** — all examples produce the same `{ quality_score, token_cost_usd, cpcd }` dict. The CPCD dashboard can consume any example.
4. **Code style consistency** — author banner, `logging_config.setup()`, `SCREAMING_SNAKE_CASE` constants, `─────` section dividers, `sys.argv` CLI args.
5. **Futureproof categories** — 7 categories chosen for stability through 2027+. See `PATTERNS.md` for the full catalogue.

---

## See Also

- [`PATTERNS.md`](PATTERNS.md) — full catalogue: 25 patterns across 7 categories, status tracker, "When NOT to use it" for each
- [`context-lab`](https://github.com/inbravo/context-lab) — companion repo for context engineering, prompt design, and RAG pipelines

---

## Author

**Amit Dixit** · Lead Presales Architect  
[GitHub](https://github.com/inbravo) · [LinkedIn](https://www.linkedin.com/in/inbravo/) · [Web](https://inbravo.github.io)
