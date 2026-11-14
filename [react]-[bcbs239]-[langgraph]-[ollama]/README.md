# bcbs239 / langgraph / ollama

**Phase 1 — Foundations**  
Your first domain-specific agent: BCBS 239 data lineage on a stateful LangGraph graph.

---

## What It Shows

- LangGraph stateful graph with tool-calling loop
- Three domain tools: `get_trade_lineage`, `check_bcbs239_compliance`, `get_bcbs239_principle`
- Handling two trades — one compliant, one with a data gap — in a single run
- BCBS 239 Principle 6 completeness checking logic
- Decision Economics scored against a domain rubric

---

## Quick Start

```bash
# 1. Pull model (from tool-use, you already know which one works)
ollama pull llama3.1:8b

# 2. Install dependencies
pip install langchain-ollama langgraph pyyaml

# 3. Run
cd [react]-[bcbs239]-[langgraph]-[ollama]
python agent.py

# 4. Test
pytest tests/ -v
```

---

## Architecture

```
  HumanMessage("Investigate T-0042 and T-0099 per BCBS 239")
           │
           ▼
  ┌────────────────────────────────────────┐
  │            LangGraph StateGraph         │
  │                                        │
  │  ┌─────────┐    tool_calls?            │
  │  │  agent  │ ──────────────────────► ┌─┴──────────────────────────────────┐
  │  │  node   │                          │            ToolNode                │
  │  │  (LLM   │ ◄──────────────────────  │  get_trade_lineage(T-0042)         │
  │  │  +tools)│    tool results          │  check_bcbs239_compliance(T-0042)  │
  │  └────┬────┘                          │  get_trade_lineage(T-0099)         │
  │       │  END                          │  check_bcbs239_compliance(T-0099)  │
  │       │                               └────────────────────────────────────┘
  └───────┼────────────────────────────────┘
          │
          ▼
   Final lineage report → scorer.py → CPCD
```

---

## BCBS 239 Context

| Principle | Title | What we test |
|---|---|---|
| P4 | Completeness | Can the agent aggregate data across source systems? |
| P6 | Adaptability | Does the lineage cover all data hops with timestamps? |

**Expected output:**
- T-20241201-0042: ✅ Compliant — ready for regulatory submission
- T-20241201-0099: ❌ Not compliant — missing ETL timestamp at RISK_STAGING hop

---

## Key Difference vs tool-use

> **This example has domain semantics.**  
> The rubric now checks whether the agent understands BCBS 239 P6 — not just whether it called tools.  
> Compare the rubric `gap_identified` criterion vs `tool_calls_correct` in the baseline.

---

## Decision Economics

| Metric | Ollama | Databricks |
|---|---|---|
| Token cost | $0.00 | ~$0.00065 per run |
| Quality target | ≥ 0.70 | ≥ 0.70 |
| CPCD | $0.00 | ~$0.00093 |
