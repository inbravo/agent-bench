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

---

## References

| Source | What it covers | Link |
|--------|---------------|------|
| aiagentrank.io (May 2026) | Per-pattern latency and token-cost trade-offs — the closest published work to CPCD | [aiagentrank.io](https://aiagentrank.io/blog/ai-agent-design-patterns-2026) |
| Anthropic — Building Effective Agents | Evaluator-optimiser pattern; cost/quality iteration loops | [anthropic.com](https://www.anthropic.com/research/building-effective-agents) |
| arXiv:2605.13850 (A*STAR, May 2026) | Framework-neutral taxonomy; design trade-off analysis across cognitive and topology axes | [arxiv.org](https://arxiv.org/abs/2605.13850) |
| Andrew Ng (2024) | Foundational agentic patterns vocabulary referenced throughout the CPCD methodology | [deeplearning.ai](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/) |
| SitePoint Definitive Guide (2026) | Decision framework for pattern selection — complements cost-tier routing | [sitepoint.com](https://www.sitepoint.com/the-definitive-guide-to-agentic-design-patterns-in-2026/) |

> **Note:** CPCD (Cost-Per-Correct-Decision) as a primary benchmark metric is an original contribution of this repository. The references above provide the pattern vocabulary and cost/quality framing that CPCD is built on.

← [Back to repo root](../README.md) · [Full pattern catalogue](../PATTERNS.md)
