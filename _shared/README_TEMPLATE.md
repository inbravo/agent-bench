# [task] / [framework] / [backend]

**Phase N — Phase Name**  
One-line description of what this example is and why it exists.

---

## What It Shows

- Bullet 1 — the core agentic concept demonstrated
- Bullet 2 — the domain knowledge applied
- Bullet 3 — what's different vs adjacent examples

---

## Quick Start

```bash
# 1. Prerequisites (Ollama model or Databricks credentials)
ollama pull llama3.1:8b   # or set .env for Databricks

# 2. Install
pip install <requirements>

# 3. Run
cd [task]-[framework]-[backend]-[YYYY-MM]
python agent.py

# 4. Test
pytest tests/ -v
```

---

## Architecture

```
  HumanMessage("...")
         │
         ▼
  ┌─────────────┐
  │             │  ASCII diagram of the agent loop or crew
  │             │
  └─────────────┘
         │
         ▼
   output → scorer.py → CPCD
```

---

## Options

| Config key | Default | Alternatives |
|---|---|---|
| `active_backend` | `ollama` | `databricks` |
| `ollama.model` | `llama3.1:8b` | `qwen2.5:7b` |

---

## Key Difference

> **Callout box: what makes this example unique vs the adjacent ones.**

---

## Decision Economics

| Metric | Ollama | Databricks |
|---|---|---|
| Token cost | $0.00 | ~$0.000XX |
| Quality target | ≥ 0.70 | ≥ 0.70 |
| CPCD | $0.00 | ~$0.000XX |
