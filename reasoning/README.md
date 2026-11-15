# Reasoning Mechanics

> **Category 1 of 7** · How an agent thinks, plans, and decides which tool to call next.

Reasoning is the foundation. Before worrying about topology, cost, or safety, an
agent must be able to reason well. The patterns in this category benchmark that
capability in isolation.

---

## Patterns

| Folder | Pattern | Scenario | Status |
|---|---|---|---|
| [`[tool-use]-[langgraph]-[ollama]`]([tool-use]-[langgraph]-[ollama]/README.md) | Tool Use | Weather assistant | ✅ Done |
| [`[react]-[langgraph]-[ollama]`]([react]-[langgraph]-[ollama]/README.md) | ReAct | Book finder with availability check | ✅ Done |
| `[react]-[langgraph]-[databricks]` | ReAct | Same book finder, Databricks backend | 🔲 Planned |
| `[reflection]-[langgraph]-[ollama]` | Reflection | Agent critiques and rewrites its own output | 🔲 Planned |
| `[plan-exec]-[langgraph]-[ollama]` | Plan-and-Execute | Planner + executor split for multi-step tasks | 🔲 Planned |

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

← [Back to repo root](../README.md) · [Full pattern catalogue](../PATTERNS.md)
