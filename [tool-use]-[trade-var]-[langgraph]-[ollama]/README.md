# tool-use / langgraph / ollama

**Phase 1 — Foundations**  
Calibrate which Ollama models reliably call tools before building domain examples.

---

## What It Shows

- LangGraph `StateGraph` with a `ToolNode` — the minimal agentic loop
- Three tool types: simple lookup, numeric computation, structured output
- How different Ollama models handle `bind_tools()` (not all do reliably)
- Decision Economics baseline: CPCD = 0 on Ollama (free compute) — your cost floor

---

## Quick Start

```bash
# 1. Pull a model (try these in order)
ollama pull llama3.1:8b
ollama pull qwen2.5:7b    # better tool calls
ollama pull mistral-nemo

# 2. Install dependencies
pip install langchain-ollama langgraph pyyaml

# 3. Run
cd [tool-use]-[trade-var]-[langgraph]-[ollama]
python agent.py

# 4. Run tests
pytest tests/test_local.py -v
pytest tests/test_local.py -v -m integration   # requires Ollama running
```

---

## Architecture

```
HumanMessage("Get JPM price, calc VaR, fetch BCBS-239-P4")
        │
        ▼
  ┌─────────────┐
  │   LangGraph  │
  │  StateGraph  │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐    tool_calls?    ┌────────────────────────┐
  │  agent node  │ ──────────────► │      ToolNode           │
  │  (LLM with   │                  │  get_market_price()     │
  │   tools)     │ ◄──────────────  │  calculate_var()        │
  └──────┬──────┘    tool results  │  fetch_regulation_text() │
         │                          └────────────────────────┘
         │  no more tool_calls
         ▼
      END
  final HumanMessage → scorer.py → CPCD
```

---

## Options

| Config key | Default | Alternatives |
|---|---|---|
| `ollama.model` | `llama3.1:8b` | `qwen2.5:7b`, `mistral-nemo`, `phi3.5-mini` |
| `ollama.temperature` | `0.0` | Keep at 0.0 for reproducible tool calls |
| `ollama.timeout_seconds` | `120` | Increase for larger models |

---

## Key Difference

> **This is calibration, not a domain example.**  
> Run this first whenever you pull a new Ollama model.  
> If `tool_calls_correct` scores below 0.7, the model isn't reliable for BFSI tasks.  
> Recommended order: `qwen2.5:7b` → `llama3.1:8b` → `mistral-nemo`.

---

## Decision Economics

| Metric | Value |
|---|---|
| Quality score (target) | ≥ 0.70 |
| Token cost (Ollama) | $0.00 |
| CPCD | $0.00 (free) — this is your baseline floor |
