# Reasoning Mechanics

> **Category 1 of 7** · How an agent thinks, plans, and decides which tool to call next.

Reasoning is the foundation. Before worrying about topology, cost, or safety, an
agent must be able to reason well. The patterns in this category benchmark that
capability in isolation.

---

## Patterns

| Folder | Pattern | Framework | Scenario | Status |
|---|---|---|---|---|
| [`[tool-use]-[langgraph]-[ollama]`]([tool-use]-[langgraph]-[ollama]/README.md) | Tool Use | LangGraph | Weather assistant | ✅ Done |
| [`[tool-use]-[crewai]-[ollama]`]([tool-use]-[crewai]-[ollama]/README.md) | Tool Use | CrewAI | Weather assistant | ✅ Done |
| [`[tool-use]-[ag2]-[ollama]`]([tool-use]-[ag2]-[ollama]/README.md) | Tool Use | AG2 | Weather assistant | ✅ Done |
| [`[react]-[langgraph]-[ollama]`]([react]-[langgraph]-[ollama]/README.md) | ReAct | LangGraph | Book finder | ✅ Done |
| [`[react]-[crewai]-[ollama]`]([react]-[crewai]-[ollama]/README.md) | ReAct | CrewAI | Book finder | ✅ Done |
| [`[react]-[ag2]-[ollama]`]([react]-[ag2]-[ollama]/README.md) | ReAct | AG2 | Book finder | ✅ Done |
| `[react]-[langgraph]-[databricks]` | ReAct | LangGraph | Book finder, Databricks backend | 🔲 Planned |
| `[reflection]-[langgraph]-[ollama]` | Reflection | LangGraph | Agent critiques and rewrites its own output | 🔲 Planned |
| `[plan-exec]-[langgraph]-[ollama]` | Plan-and-Execute | LangGraph | Planner + executor split for multi-step tasks | 🔲 Planned |

---

## Pattern Summary

### Tool Use
Single-shot: the agent identifies the right tool, calls it once, and answers.
No loop. Use when the tool and its arguments are determined by the question alone.
→ [`[tool-use]-[langgraph]-[ollama]`]([tool-use]-[langgraph]-[ollama]/README.md)

### ReAct (Reason + Act)
Iterative: Thought → Action → Observation → repeat until done.
Each observation can change the next action. Use when outcomes of one tool call
determine whether and how to call the next.
→ [`[react]-[langgraph]-[ollama]`]([react]-[langgraph]-[ollama]/README.md)

### Reflection *(planned)*
The agent produces a first answer, critiques it against a rubric, then rewrites.
Use when output quality matters more than speed.

### Plan-and-Execute *(planned)*
A planner LLM generates a step-by-step plan; an executor LLM runs each step.
Use when the full scope of work must be mapped before any step begins.

---

## Choosing a Reasoning Pattern

```
Is one tool call enough?
  ├── Yes → Tool Use
  └── No
       ├── Does the full plan depend on seeing results first?
       │    ├── Yes → ReAct
       │    └── No  → Plan-and-Execute
       └── Does quality need a self-review pass?
            └── Yes → Reflection (after ReAct or Plan-and-Execute)
```

---

---

## References

| Source | What it covers | Link |
|--------|---------------|------|
| Andrew Ng (2024) | Foundational 4 patterns: Reflection, Tool Use, Planning, Multi-Agent Collaboration | [deeplearning.ai](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/) |
| Anthropic — Building Effective Agents | Workflow patterns: chains, routing, parallelisation, orchestrator-workers, evaluator-optimiser | [anthropic.com](https://www.anthropic.com/research/building-effective-agents) |
| arXiv:2605.13850 (A*STAR, May 2026) | Two-dimensional framework: Cognitive Function × Execution Topology; synthesises Anthropic, Google, LangChain | [arxiv.org](https://arxiv.org/abs/2605.13850) |
| aiagentrank.io (May 2026) | 9 patterns with latency and token-cost trade-offs — maps well to CPCD reasoning | [aiagentrank.io](https://aiagentrank.io/blog/ai-agent-design-patterns-2026) |
| dev.to / Innovatrix (2026) | 7 patterns with 2026 production-readiness scorecard | [dev.to](https://dev.to/emperorakashi20/the-7-agentic-ai-design-patterns-every-developer-should-know-react-reflection-tool-use-and-more-3bba) |

← [Back to repo root](../README.md) · [Full pattern catalogue](../PATTERNS.md)
