# decision-econ / generic / ollama

**Phase 5 — Cross-Cutting Concerns**  
The lab's signature metric: cost-per-correct-decision across all frameworks and backends.

---

## What It Shows

- LLM-as-judge scoring against a `rubric.yaml`
- Weighted-sum quality score (0.0–1.0) per criterion
- Token cost calculation (Ollama = $0.00, Databricks = real cost)
- CPCD formula: `token_cost_usd / quality_score`
- Multi-run comparison table sorted by CPCD
- Framework-agnostic: works with LangGraph, CrewAI, or any agent output

---

## Quick Start

```bash
cd [cpcd]-[generic]-[multi]-[ollama]
python agent.py
```

Expected output: a comparison table of three synthetic runs (LangGraph/Ollama, CrewAI/Ollama, LangGraph/Databricks).

---

## Architecture

```
  Agent outputs (from any framework)
           │
           ▼
  ┌─────────────────────────────────┐
  │         scorer.py               │
  │                                 │
  │  rubric.yaml → criteria weights  │
  │  LLM-as-judge → criteria scores  │
  │  weighted_sum → quality_score   │
  │  token_usage + rates → cost_usd │
  │  cost / quality → CPCD          │
  └─────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Run ID              Framework  Backend  Quality  CPCD   │
  │  langgraph-databricks  langgraph  databricks  0.88  $0.00074 │
  │  langgraph-ollama      langgraph  ollama      0.82  $0.00    │
  │  crewai-ollama         crewai     ollama      0.76  $0.00    │
  └─────────────────────────────────────────────────────────┘
```

---

## The CPCD Formula

```
CPCD = token_cost_usd / quality_score

Where:
  token_cost_usd = (input_tokens × input_rate) + (output_tokens × output_rate)
  quality_score  = Σ (criterion_weight × judge_score)   [0.0 – 1.0]
```

**What CPCD tells you:**
- Ollama: CPCD = $0.00 → free but bounded by local hardware
- Databricks 70B at 0.88 quality = ~$0.00074 per correct decision
- If a smaller model scores 0.70 at half the tokens → better CPCD than a larger model at 0.88

---

## Key Difference

> **This is the meta-example.**  
> Every other example in this lab produces an `agent_output`. This one scores it.  
> Import `compare_runs()` from `agent.py` into any framework example to get CPCD automatically.

---

## Usage as a Library

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd().parents[0]))

from [cpcd]-[generic]-[multi]-[ollama].agent import AgentRun, compare_runs, print_comparison_table

runs = [
    AgentRun(
        run_id="my-run",
        framework="langgraph",
        backend="ollama",
        task_description="...",
        agent_output="...",
        token_usage={"input_tokens": 800, "output_tokens": 200},
    )
]
scored = compare_runs(runs, rubric_path="rubric.yaml")
print_comparison_table(scored)
```
