# Agent Design Patterns

> **Repo**: `agent-bench` — agentic framework benchmarking and decision economics  
> **Author**: Amit Dixit ([@inbravo](https://github.com/inbravo))

---

## Status Tracker

| # | Category | Pattern | Folder | Status |
|---|---|---|---|---|
| 1 | Reasoning Mechanics | Tool Use | `reasoning/[tool-use]-[langgraph]-[ollama]` | ✅ Done |
| 2 | Reasoning Mechanics | ReAct | `reasoning/[react]-[langgraph]-[ollama]` | ✅ Done |
| 3 | Reasoning Mechanics | ReAct (Databricks) | `reasoning/[react]-[langgraph]-[databricks]` | 🔲 Planned |
| 4 | Reasoning Mechanics | Reflection | `reasoning/[reflection]-[langgraph]-[ollama]` | 🔲 Planned |
| 5 | Reasoning Mechanics | Plan-and-Execute | `reasoning/[plan-exec]-[langgraph]-[ollama]` | 🔲 Planned |
| 6 | Agent Topology | Framework Swap | `topology/[fw-swap]-[crewai]-[ollama]` | ✅ Done |
| 7 | Agent Topology | Role-Based Crew | `topology/[role-crew]-[crewai]-[ollama]` | 🔲 Planned |
| 8 | Agent Topology | Orchestrator-Worker | `topology/[orch-worker]-[langgraph]-[ollama]` | 🔲 Planned |
| 9 | Agent Topology | Parallel Fan-out | `topology/[fan-out]-[langgraph]-[ollama]` | 🔲 Planned |
| 10 | Tool & Context Integration | MCP Tools | `context-integration/[mcp-tools]-[langgraph]-[ollama]` | 🔲 Planned |
| 11 | Tool & Context Integration | RAG-as-Tool | `context-integration/[rag-tool]-[langgraph]-[ollama]` | 🔲 Planned |
| 12 | Tool & Context Integration | Memory | `context-integration/[memory]-[langgraph]-[ollama]` | 🔲 Planned |
| 13 | Evaluation & Observability | LLM-as-Judge | `evaluation/[llm-judge]-[multi]-[ollama]` | 🔲 Planned |
| 14 | Evaluation & Observability | Trace-and-Score | `evaluation/[trace-score]-[langgraph]-[ollama]` | 🔲 Planned |
| 15 | Decision Economics | CPCD | `decision-econ/[cpcd]-[multi]-[ollama]` | ✅ Done |
| 16 | Decision Economics | Pareto Frontier | `decision-econ/[pareto]-[multi]-[ollama]` | 🔲 Planned |
| 17 | Decision Economics | Decision Budget | `decision-econ/[budget]-[langgraph]-[ollama]` | 🔲 Planned |
| 18 | Decision Economics | Cost-Tier Routing | `decision-econ/[tier-routing]-[langgraph]-[ollama]` | 🔲 Planned |
| 19 | Decision Economics | Degradation Curve | `decision-econ/[degrad-curve]-[multi]-[ollama]` | 🔲 Planned |
| 20 | Safety, Control & Governance | HITL | `governance/[hitl]-[langgraph]-[ollama]` | 🔲 Planned |
| 21 | Safety, Control & Governance | Guardrails | `governance/[guardrails]-[langgraph]-[ollama]` | 🔲 Planned |
| 22 | Safety, Control & Governance | Adversarial Stress | `governance/[adversarial]-[langgraph]-[ollama]` | 🔲 Planned |
| 23 | Deployment & Backend Portability | Backend Swap | `portability/[backend-swap]-[langgraph]-[multi]` | 🔲 Planned |
| 24 | Deployment & Backend Portability | Framework Swap (compare) | `portability/[fw-compare]-[multi]-[ollama]` | 🔲 Planned |
| 25 | Deployment & Backend Portability | Model Fallback Chain | `portability/[fallback]-[langgraph]-[multi]` | 🔲 Planned |

**Legend**: ✅ Done · 🔲 Planned · 🚧 In Progress

---

## 1 · Reasoning Mechanics

> *How does the agent think and decide what to do next?*

### Tool Use

**What it is**: The agent selects a tool from a fixed set, calls it with arguments, and uses the result to answer. No loop — single-shot dispatch.

**Scenario**: Weather assistant — `get_current_weather(city)`, `convert_temperature(value, unit)`

**When NOT to use it**:
- When the task requires evaluating intermediate results before choosing the next action — use ReAct
- When tool selection depends on a prior tool's output — use ReAct or Plan-and-Execute
- When no tools are needed — just call the LLM directly

---

### ReAct (Reason + Act)

**What it is**: The agent alternates between Thought and Action, looping until it has enough information. Each observation can change the next thought.

**Scenario**: Book finder — `search_books(query)`, `check_availability(title)`, `get_similar_books(title)`

**When NOT to use it**:
- When the full plan is known upfront and steps are independent — use Plan-and-Execute
- When only one tool call is needed — Tool Use is simpler
- When you need guaranteed termination with bounded steps — add a step counter

---

### Reflection

**What it is**: The agent produces a first draft, critiques it, then revises. The LLM acts as both author and reviewer.

**Scenario**: *(Planned)* — draft-critique-revise loop on a short essay

**When NOT to use it**:
- When the task is factual retrieval — reflection adds latency without quality gain
- When the LLM consistently agrees with itself — an external judge is more reliable
- When budget is tight — reflection doubles or triples token usage

---

### Plan-and-Execute

**What it is**: Creates a full multi-step plan first, then executes each step in sequence. The plan can be revised mid-execution if a step fails.

**Scenario**: *(Planned)* — multi-step research assistant that plans its searches before making any

**When NOT to use it**:
- When the plan cannot be known upfront — use ReAct
- When steps are highly interdependent and unpredictable — ReAct adapts better
- When the task is a single action — no plan needed

---

## 2 · Agent Topology

> *How are multiple agents structured and how do they hand off work?*

### Framework Swap

**What it is**: The same task is implemented with two different frameworks (LangGraph and CrewAI). Goal: direct CPCD comparison.

**Scenario**: Blog post crew — Researcher → Writer → Editor (CrewAI sequential)

**When NOT to use it**:
- When you are not benchmarking — just choose the right framework
- When the task is too simple for a crew — a single agent is faster and cheaper
- When role boundaries are unclear — agents will overlap

---

### Role-Based Crew

**What it is**: Multiple specialised agents, each with a defined role, collaborate on a task. Roles are non-overlapping.

**Scenario**: *(Planned)* — content production team (Researcher, Writer, SEO Editor, Fact Checker)

**When NOT to use it**:
- When a single ReAct agent can do the job
- When role boundaries are artificial — overlap leads to contradictory outputs
- When you need tight loop control — use Orchestrator-Worker

---

### Orchestrator-Worker

**What it is**: A central orchestrator decomposes a task, dispatches sub-tasks to workers, and aggregates results. Workers do not communicate with each other.

**Scenario**: *(Planned)* — research orchestrator spawning per-topic worker agents

**When NOT to use it**:
- When sub-tasks are sequential and dependent — use Plan-and-Execute or ReAct
- When you only have one domain — a single capable agent is simpler

---

### Parallel Fan-out

**What it is**: The orchestrator dispatches multiple workers simultaneously and waits for all to complete before aggregating.

**Scenario**: *(Planned)* — multi-source news aggregator fanning out to 3 search workers in parallel

**When NOT to use it**:
- When tasks must run sequentially
- When the LLM API has strict rate limits that make parallel calls fail
- When results from one worker are needed to decide what other workers should do

---

## 3 · Tool & Context Integration

> *How does the agent access external data, persistent memory, and live services?*

### MCP Tools

**What it is**: The agent connects to external services via the Model Context Protocol (MCP), treating each service as a tool.

**Scenario**: *(Planned)* — file system + calendar access via MCP servers

**When NOT to use it**:
- When the service has a stable Python SDK — a `@tool` wrapper is simpler
- When latency of the MCP round-trip is unacceptable
- When the MCP server is unavailable in your deployment environment

---

### RAG-as-Tool

**What it is**: A vector search retrieval function is registered as an agent tool. The agent decides *when* to retrieve and *what query* to use.

**Scenario**: *(Planned)* — policy Q&A agent that retrieves relevant clauses on demand

**When NOT to use it**:
- When every answer requires retrieval — use a standard RAG pipeline instead
- When the knowledge base is small enough to fit in context — just inject it
- When retrieval quality is poor — garbage in, garbage out

---

### Memory

**What it is**: The agent reads from and writes to a persistent memory store across turns.

**Scenario**: *(Planned)* — personal assistant that remembers user preferences across sessions

**When NOT to use it**:
- When every session is stateless by design
- When memory growth is unbounded and no pruning strategy exists
- When stored memory is sensitive and no access control is in place

---

## 4 · Evaluation & Observability

> *How do you know the agent is working correctly and improving?*

### LLM-as-Judge

**What it is**: A second LLM call evaluates the primary agent's output against a rubric, returning a numeric score.

**Scenario**: *(Planned)* — standalone judge that takes `(task, answer, rubric)` and returns a structured score

**When NOT to use it**:
- When the task has a deterministic correct answer — use exact match or regex
- When the judge and agent share the same model — correlated errors
- When judge latency is unacceptable in production — cache or batch judge calls

---

### Trace-and-Score

**What it is**: Every agent run emits a structured trace (tool calls, intermediate states, latency, token counts). The trace is scored post-hoc.

**Scenario**: *(Planned)* — LangSmith / OpenTelemetry trace capture with post-run CPCD scoring

**When NOT to use it**:
- When you do not need to debug intermediate steps — a simple scorer suffices
- When trace storage is expensive or regulated (PII in traces)

---

## 5 · Decision Economics

> *How much does correctness cost, and is it worth it?*

### CPCD (Cost-Per-Correct-Decision)

**What it is**: `CPCD = token_cost_usd / quality_score` — the primary benchmarking metric of this repo.

**Scenario**: Multi-framework comparison dashboard — LangGraph vs CrewAI on the same task

**When NOT to use it**:
- When all runs are free (Ollama) — CPCD = 0 for everyone; rank by quality instead
- When tasks are not comparable (different rubrics)
- When you have only one candidate — CPCD needs at least two to be meaningful

---

### Pareto Frontier

**What it is**: Plot all candidate runs on a (cost, quality) plane. Pareto-optimal runs are those where no other run is both cheaper and higher quality.

**Scenario**: *(Planned)* — 6-way comparison across 3 frameworks × 2 backends

**When NOT to use it**:
- When you have fewer than 4 candidate runs — the frontier is trivial
- When quality and cost are not the only constraints (latency, safety also matter)

---

### Decision Budget

**What it is**: The agent is given a token or cost budget and must decide how many reasoning steps to take, trading depth against cost.

**Scenario**: *(Planned)* — research agent with a $0.05 budget that must decide how many search calls to make

**When NOT to use it**:
- When cost is not a constraint in your deployment
- When budget estimation is unreliable (variable-length outputs)

---

### Cost-Tier Routing

**What it is**: Route each task to the cheapest model tier that can answer it at acceptable quality. Simple tasks → cheap model; complex tasks → expensive model.

**Scenario**: *(Planned)* — routing agent classifying task complexity and dispatching to tier-1/2/3

**When NOT to use it**:
- When all tasks are equally complex
- When routing latency exceeds the savings from using a cheaper tier
- When you have only one model available

---

### Degradation Curve

**What it is**: Measure how quality degrades as you reduce cost. Plot the curve to find the quality cliff.

**Scenario**: *(Planned)* — same task on llama3.1:8b, llama3.1:70b, GPT-4o-mini, GPT-4o

**When NOT to use it**:
- When you cannot control model selection (vendor lock-in)
- When the rubric does not capture the quality loss that matters in production

---

## 6 · Safety, Control & Governance

> *How do you keep the agent from doing something harmful, unintended, or ungoverned?*

### HITL (Human-in-the-Loop)

**What it is**: The agent pauses at defined decision points and waits for human confirmation before proceeding.

**Scenario**: *(Planned)* — expense approval agent that pauses before submitting any amount > £500

**When NOT to use it**:
- When all actions are reversible and low-risk
- When human latency would make the agent impractical (real-time systems)
- When you want full automation — design guardrails instead

---

### Guardrails

**What it is**: Input and output filters that block disallowed content, enforce response format, and prevent prompt injection.

**Scenario**: *(Planned)* — customer-facing chatbot with topic guardrails

**When NOT to use it**:
- When every task is internal and fully trusted
- When guardrail latency adds unacceptable overhead
- When guardrails are over-broad and block legitimate tasks — tune first

---

### Adversarial Stress

**What it is**: Systematically test the agent against prompt injection, goal hijacking, and jailbreak attempts.

**Scenario**: *(Planned)* — adversarial test suite: 20 injection attempts, scoring policy adherence

**When NOT to use it**:
- When the agent is fully sandboxed with no external inputs
- When you are still in early prototyping — do this before production

---

## 7 · Deployment & Backend Portability

> *How easily can the agent move across models, frameworks, and infrastructure?*

### Backend Swap

**What it is**: The agent code is identical; only the LLM backend changes (Ollama → OpenAI → Databricks → Anthropic) via `config.yaml`.

**Scenario**: *(Planned)* — weather assistant running on Ollama, then swapped to GPT-4o-mini via config only

**When NOT to use it**:
- When your backend is fixed by contract or compliance
- When the abstraction layer adds meaningful latency or complexity

---

### Framework Swap (compare)

**What it is**: Document and measure the effort required to migrate from one framework to another.

**Scenario**: *(Planned)* — migration journal: LangGraph → CrewAI

**When NOT to use it**:
- When you are not migrating frameworks — this is a migration-time pattern

---

### Model Fallback Chain

**What it is**: The agent tries a primary model; on failure it falls back to a secondary, then a tertiary model.

**Scenario**: *(Planned)* — fallback chain: GPT-4o → GPT-4o-mini → Ollama llama3.1:8b

**When NOT to use it**:
- When reliability is not a concern (pure research/benchmarking)
- When all fallback models are equally unreliable
- When cost of fallback chain evaluation exceeds savings

---

*Last updated: 2026-11-15*
