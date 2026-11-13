# bcbs239-lineage / langgraph / databricks

**Phase 1 — Foundations**  
Same BCBS 239 agent as the Ollama version — now on Databricks with MLflow tracing.

---

## What It Shows

- Identical agent code, different backend — one config.yaml line switches it
- MLflow 3 auto-tracing: every tool call and LLM invoke captured
- Token cost is real → CPCD is meaningful and comparable to Ollama ($0.00)
- MLflow experiment in Databricks → shareable trace URL for client demos
- Llama 3.1 70B vs 8B: quality score difference (run both and compare)

---

## Setup

```bash
# 1. Copy and fill .env
cp ../.env.example .env
# Set DATABRICKS_HOST and DATABRICKS_TOKEN

# 2. Install dependencies
pip install langchain-databricks mlflow langgraph pyyaml

# 3. Run
cd [bcbs239-lineage]-[langgraph]-[databricks]-[2026-11]
python agent.py
```

---

## Architecture

```
  HumanMessage("Investigate T-0042 and T-0099 per BCBS 239")
           │
           ▼
  ┌────────────────────────────────────────────────┐
  │            LangGraph StateGraph                 │
  │                                                │
  │  ┌─────────┐             ┌──────────────────┐  │
  │  │  agent  │ ──tools──►  │    ToolNode       │  │
  │  │  node   │ ◄─results─  │  (same as Ollama) │  │
  │  │  (Llama │             └──────────────────┘  │
  │  │  3.1 70B│                                   │
  │  │  via DB)│                                   │
  │  └────┬────┘                                   │
  └───────┼────────────────────────────────────────┘
          │
          ▼                        ┌─────────────────────┐
   Final report  ──────────────►  │  MLflow 3 Trace      │
                                   │  (auto-logged)       │
                                   │  Databricks workspace│
                                   └─────────────────────┘
          │
          ▼
   scorer.py → CPCD (non-zero — real API cost)
```

---

## Key Difference vs Ollama Version

> **CPCD is now real.**  
> Ollama CPCD = $0.00 (free hardware). Databricks CPCD ≈ $0.00093 per run.  
> Same quality score. The difference is what you pay for production inference.  
> This is the decision economics comparison the lab is built around.

---

## MLflow Traces

After running, open your Databricks workspace:

```
Experiments → /Shared/agent-bench/bcbs239 → [your run]
```

Each run shows:
- Input/output per LLM call
- Tool call parameters and results
- Latency per hop
- Token counts (use these for accurate CPCD)

---

## Decision Economics

| Metric | Ollama (8B) | Databricks (70B) |
|---|---|---|
| Token cost | $0.00 | ~$0.00065 per run |
| Quality target | ≥ 0.70 | ≥ 0.70 |
| CPCD | $0.00 | ~$0.00093 |
| Recommendation | Dev/iteration | Client demo, regulatory evidence |
