# Decision Economics

> **Category 5 of 7** · The signature category of this repo. Measuring whether the smarter agent is worth it.

Every engineering team eventually asks the same question:

> *"Is the more expensive model / framework actually worth the extra cost?"*

Decision Economics patterns answer that with data, not intuition.
The primary metric is **CPCD** — Cost-Per-Correct-Decision.

---

## The CPCD Metric

```
CPCD = token_cost_usd / quality_score
```

| Situation | Interpretation |
|---|---|
| CPCD = 0.0 | Free inference (Ollama local); rank by quality only |
| CPCD is low | Good value — high quality relative to cost |
| CPCD is high | Expensive relative to quality; consider a cheaper tier |
| CPCD = ∞ | Zero quality — the run failed; discard |

The scorer uses an **LLM-as-Judge** pattern: a second LLM call rates the
primary agent's answer against a per-example `rubric.yaml`. Criteria weights
sum to 1.0. The final `quality_score` is a weighted average in [0, 1].

---

## Patterns

| Folder | Pattern | Scenario | Status |
|---|---|---|---|
| [`[cpcd]-[multi]-[ollama]`]([cpcd]-[multi]-[ollama]/README.md) | CPCD Comparison | Multi-framework benchmark dashboard | ✅ Done |
| `[pareto]-[multi]-[ollama]` | Pareto Frontier | Plot quality vs cost across model tiers | 🔲 Planned |
| `[budget]-[langgraph]-[ollama]` | Decision Budget | Hard token/cost cap with graceful degradation | 🔲 Planned |
| `[tier-routing]-[langgraph]-[ollama]` | Cost-Tier Routing | Route tasks to cheap/mid/expensive tiers by complexity | 🔲 Planned |
| `[degrad-curve]-[multi]-[ollama]` | Degradation Curve | How quality degrades as cost is squeezed | 🔲 Planned |

---

## Pattern Summary

### CPCD Comparison
Runs the same task through multiple framework/backend candidates.
Scores each with LLM-as-Judge. Ranks by CPCD ascending (lower = better value).
→ [`[cpcd]-[multi]-[ollama]`]([cpcd]-[multi]-[ollama]/README.md)

### Pareto Frontier *(planned)*
Plots (quality, cost) pairs for each candidate. Identifies the Pareto-optimal
set — agents that are not dominated on both dimensions simultaneously.

### Decision Budget *(planned)*
Runs the agent inside a hard token/cost cap. Measures how gracefully it
degrades when the budget is tightened step by step.

### Cost-Tier Routing *(planned)*
Classifies incoming tasks by complexity, then routes cheap tasks to small
models and complex tasks to large models. Measures overall CPCD at the fleet level.

### Degradation Curve *(planned)*
Sweeps cost from high to low (fewer tokens, smaller models, truncated context)
and plots the resulting quality curve. Identifies the "cliff" — the point where
cutting cost suddenly destroys quality.

---

← [Back to repo root](../README.md) · [Full pattern catalogue](../PATTERNS.md)
