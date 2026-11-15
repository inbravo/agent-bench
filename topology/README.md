# Agent Topology

> **Category 2 of 7** · How agents are structured, how they hand off work, and how frameworks compare on the same task.

Once you know an agent can reason, the next question is *shape*: should it be a
single agent with many tools, a crew of specialists, or a hierarchical
orchestrator-worker arrangement? This category benchmarks those structural choices.

---

## Patterns

| Folder | Pattern | Scenario | Status |
|---|---|---|---|
| [`[fw-swap]-[crewai]-[ollama]`]([fw-swap]-[crewai]-[ollama]/README.md) | Framework Swap | Blog post crew (Researcher → Writer → Editor) | ✅ Done |
| `[role-crew]-[crewai]-[ollama]` | Role-Based Crew | Multi-role analysis crew with specialised agents | 🔲 Planned |
| `[orch-worker]-[langgraph]-[ollama]` | Orchestrator-Worker | Central planner dispatches sub-agents | 🔲 Planned |
| `[fan-out]-[langgraph]-[ollama]` | Parallel Fan-out | Multiple agents run in parallel, results merged | 🔲 Planned |

---

## Pattern Summary

### Framework Swap
Run the same task through different frameworks (LangGraph, CrewAI, etc.) and
compare on CPCD. The scenario is fixed; only the framework changes.
→ [`[fw-swap]-[crewai]-[ollama]`]([fw-swap]-[crewai]-[ollama]/README.md)

### Role-Based Crew *(planned)*
Each agent has a named role and a narrowly scoped task. Agents do not overlap.
Use when a task naturally decomposes into specialist responsibilities.

### Orchestrator-Worker *(planned)*
A planner/orchestrator agent breaks down work and delegates to worker agents.
Use when subtasks are heterogeneous and best handled by different specialists.

### Parallel Fan-out *(planned)*
Multiple agents run the same (or different) subtasks simultaneously; results
are aggregated. Use when subtasks are independent and latency matters.

---

## Choosing a Topology

```
Single agent or multiple?
  ├── Single → Reasoning Mechanics (see ../reasoning/)
  └── Multiple
       ├── Sequential handoffs with named roles? → Role-Based Crew
       ├── Central planner + workers?             → Orchestrator-Worker
       ├── Independent parallel subtasks?         → Parallel Fan-out
       └── Benchmarking framework choice?         → Framework Swap
```

---

← [Back to repo root](../README.md) · [Full pattern catalogue](../PATTERNS.md)
