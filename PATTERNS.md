# Agent Design Patterns

> **Repo**: `agent-bench` — agentic framework benchmarking and decision economics  
> **Author**: Amit Dixit ([@inbravo](https://github.com/inbravo))

---

## Status Tracker

| # | Category | Pattern | Framework | Folder | Status |
|---|---|---|---|---|---|
| 1 | Reasoning Mechanics | Tool Use | LangGraph | `reasoning/[tool-use]-[langgraph]-[ollama]` | ✅ Done |
| 2 | Reasoning Mechanics | Tool Use | CrewAI | `reasoning/[tool-use]-[crewai]-[ollama]` | ✅ Done |
| 3 | Reasoning Mechanics | Tool Use | AG2 | `reasoning/[tool-use]-[ag2]-[ollama]` | ✅ Done |
| 4 | Reasoning Mechanics | ReAct | LangGraph | `reasoning/[react]-[langgraph]-[ollama]` | ✅ Done |
| 5 | Reasoning Mechanics | ReAct | CrewAI | `reasoning/[react]-[crewai]-[ollama]` | ✅ Done |
| 6 | Reasoning Mechanics | ReAct | AG2 | `reasoning/[react]-[ag2]-[ollama]` | ✅ Done |
| 7 | Reasoning Mechanics | ReAct (Databricks) | LangGraph | `reasoning/[react]-[langgraph]-[databricks]` | 🔲 Planned |
| 8 | Reasoning Mechanics | Reflection | LangGraph | `reasoning/[reflection]-[langgraph]-[ollama]` | 🔲 Planned |
| 9 | Reasoning Mechanics | Plan-and-Execute | LangGraph | `reasoning/[plan-exec]-[langgraph]-[ollama]` | 🔲 Planned |
| 10 | Agent Topology | Framework Swap | CrewAI | `topology/[fw-swap]-[crewai]-[ollama]` | ✅ Done |
| 11 | Agent Topology | Role-Based Crew | CrewAI | `topology/[role-crew]-[crewai]-[ollama]` | 🔲 Planned |
| 12 | Agent Topology | Orchestrator-Worker | LangGraph | `topology/[orch-worker]-[langgraph]-[ollama]` | 🔲 Planned |
| 13 | Agent Topology | Parallel Fan-out | LangGraph | `topology/[fan-out]-[langgraph]-[ollama]` | 🔲 Planned |
| 14 | Tool & Context Integration | MCP Tools | LangGraph | `context-integration/[mcp-tools]-[langgraph]-[ollama]` | 🔲 Planned |
| 15 | Tool & Context Integration | RAG-as-Tool | LangGraph | `context-integration/[rag-tool]-[langgraph]-[ollama]` | 🔲 Planned |
| 16 | Tool & Context Integration | Memory | LangGraph | `context-integration/[memory]-[langgraph]-[ollama]` | 🔲 Planned |
| 17 | Evaluation & Observability | LLM-as-Judge | Multi | `evaluation/[llm-judge]-[multi]-[ollama]` | 🔲 Planned |
| 18 | Evaluation & Observability | Trace-and-Score | LangGraph | `evaluation/[trace-score]-[langgraph]-[ollama]` | 🔲 Planned |
| 19 | Decision Economics | CPCD | Multi | `decision-econ/[cpcd]-[multi]-[ollama]` | ✅ Done |
| 20 | Decision Economics | Pareto Frontier | Multi | `decision-econ/[pareto]-[multi]-[ollama]` | 🔲 Planned |
| 21 | Decision Economics | Decision Budget | LangGraph | `decision-econ/[budget]-[langgraph]-[ollama]` | 🔲 Planned |
| 22 | Decision Economics | Cost-Tier Routing | LangGraph | `decision-econ/[tier-routing]-[langgraph]-[ollama]` | 🔲 Planned |
| 23 | Decision Economics | Degradation Curve | Multi | `decision-econ/[degrad-curve]-[multi]-[ollama]` | 🔲 Planned |
| 24 | Safety, Control & Governance | HITL | LangGraph | `governance/[hitl]-[langgraph]-[ollama]` | 🔲 Planned |
| 25 | Safety, Control & Governance | Guardrails | LangGraph | `governance/[guardrails]-[langgraph]-[ollama]` | 🔲 Planned |
| 26 | Safety, Control & Governance | Adversarial Stress | LangGraph | `governance/[adversarial]-[langgraph]-[ollama]` | 🔲 Planned |
| 27 | Deployment & Backend Portability | Backend Swap | LangGraph | `portability/[backend-swap]-[langgraph]-[multi]` | 🔲 Planned |
| 28 | Deployment & Backend Portability | Framework Swap (compare) | Multi | `portability/[fw-compare]-[multi]-[ollama]` | 🔲 Planned |
| 29 | Deployment & Backend Portability | Model Fallback Chain | LangGraph | `portability/[fallback]-[langgraph]-[multi]` | 🔲 Planned |
| 30 | Self-Improvement | Prompt Optimisation | DSPy | `self-improvement/[prompt-opt]-[dspy]-[ollama]` | ✅ Done |
| 31 | Self-Improvement | Self-Critique | ollama-harness | `self-improvement/[research-swarm]-[ollama-harness]-[ollama]` | ✅ Done |
| 32 | Self-Improvement | Recursive Harness Opt | harness² | `self-improvement/[harness-opt]-[harness2]-[vertexai]` | 🔲 Planned |
| 33 | Reasoning Mechanics | Chain-of-Verification (CoVe) | LangGraph | `reasoning/[cove]-[langgraph]-[ollama]` | 🔲 Planned |
| 34 | Safety, Control & Governance | Dry-Run (Approval Gate) | LangGraph | `governance/[dry-run]-[langgraph]-[ollama]` | 🔲 Planned |
| 35 | Tool & Context Integration | GraphRAG | LangGraph | `context-integration/[graphrag]-[langgraph]-[ollama]` | 🔲 Planned |

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

### Chain-of-Verification (CoVe)

**What it is**: The agent generates a baseline answer, decomposes it into a checklist of verifiable claims, verifies each claim independently (via tool call or LLM re-query), then revises the answer to remove any claim that failed verification.

**Scenario**: *(Planned)* — BCBS 239 data quality checker: generate a data lineage summary, extract each traceability claim, verify each claim against source metadata, revise the report

**When NOT to use it**:
- When the task has a single atomic answer that cannot be decomposed into claims
- When you have no verification mechanism (no tools, no second-pass LLM) — the loop is hollow
- When all claims are equally unverifiable — a standard ReAct loop is simpler
- When latency is critical — CoVe runs N+1 LLM calls for N claims

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

### GraphRAG

**What it is**: Retrieval is performed over a knowledge graph rather than a flat vector index. Entities (people, systems, regulations) and their relationships are stored as nodes and edges. The agent traverses the graph to retrieve structured, relationship-aware context — not just similar chunks.

**Scenario**: *(Planned)* — BCBS 239 data lineage agent: knowledge graph of source systems → transformations → reports; agent traverses lineage paths to answer "which upstream systems affect this regulatory figure?"

**When NOT to use it**:
- When your knowledge base has no meaningful entity relationships — plain RAG is simpler
- When the graph is too sparse (fewer than ~50 entities) — overhead exceeds benefit
- When graph construction cost is prohibitive and the knowledge base changes frequently
- When you need sub-second retrieval — graph traversal is slower than ANN vector search

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

### Dry-Run (Approval Gate)

**What it is**: The agent proposes an action, simulates its effect without executing it, presents the proposal to a human (or policy engine), and waits for explicit approval before proceeding. The agentic equivalent of a four-eyes principle.

**Scenario**: *(Planned)* — regulatory report submission agent: drafts the COREP filing, presents a diff of what will change, waits for Compliance sign-off before submitting

**When NOT to use it**:
- When all actions are fully reversible and low-risk — approval gates add latency
- When the agent is running in real-time with no human available — use Guardrails instead
- When every step requires approval — the agent loses autonomy entirely; scope approval to high-impact steps only
- When simulation is not possible (external side-effects cannot be safely dry-run)

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

*Last updated: 2026-11-17*

---

## 8 · Self-Improvement

> *How does an agent get better at a task without manual prompt engineering?*

**New CPCD axis**: `CPCD_delta = CPCD_before − CPCD_after`
Does the cost of optimisation produce a measurable quality gain?

### Prompt Optimisation (DSPy / BootstrapFewShot)

**What it is**: Treats prompts as learnable parameters. A `BootstrapFewShot`
optimiser generates labelled demonstrations from a small training set, then
recompiles the agent's prompt to include the highest-scoring examples.
Improvement is **batch / offline** — optimise once, then deploy.

**Scenario**: DSPy ReAct over the same weather task as `reasoning/`. The agent
runs before and after `optimiser.compile()`; CPCD_delta measures the gain.

**When NOT to use it**:
- When you have no labelled training examples (need at least 3–10)
- When the task changes frequently — compiled demos go stale
- When the LLM is frozen / API-only and you can't run DSPy's teleprompter
- When latency at compile time (many LLM calls) is unacceptable

---

### Self-Critique (ollama-harness / Producer-Critique Loop)

**What it is**: An online, **per-query** revision loop. A producer LLM generates
an answer; a critic LLM says `ACCEPT` or `REVISE: <improved>`. The loop runs up
to `max_revisions` times. No training data needed — the critic evaluates the
answer directly against the task.

**Scenario**: ollama-harness producer-critique loop on the weather task.
`harness_mode: "native"` (ollama-harness pip) or `"fallback"` (stdlib urllib).

**When NOT to use it**:
- When every query has a clear deterministic answer — critique adds no value
- When latency is tight — each revision doubles the LLM calls
- When the critic and producer use the same model with the same system prompt —
  they will agree unconditionally, defeating the loop
- When quality threshold is set too low — the loop exits immediately

---

### Recursive Harness Optimisation (harness²)

**What it is**: A meta-optimiser that wraps an entire benchmark harness.
Across multiple task runs it learns which prompt variants, tool orderings, or
agent configurations produce the lowest CPCD, then rewrites the harness itself.
Improvement is **across tasks** — the harness improves as more tasks are run.

**Scenario**: *(Planned)* — harness² running over the weather + book tasks,
rewriting agent configs to minimise cumulative CPCD.

**When NOT to use it**:
- When you have only one task — the meta-optimiser needs a task distribution
- When Vertex AI / Google AI is not available in your environment
- When the harness is not structured as parameterisable YAML configs

---

---

## Adding a New Pattern — File Boilerplate

Every new Python file in this repo must open with the following docstring structure.
Copy and fill in all fields; do not omit `Description`.

### `agent.py` template

```python
"""
agent.py — <Pattern name>: <one-line scenario summary> (<Framework> + <Backend>).

Description : <2–3 sentences. State what agentic pattern is being demonstrated,
              what the agent does (tools it calls, task it solves), and how the
              result is measured (rubric / CPCD). Be specific — name the tools
              and the scenario.>

Pattern     : <Pattern name, e.g. ReAct (Reason + Act)>
Category    : <Category, e.g. Reasoning Mechanics | Agent Topology | Decision Economics>
Framework   : <e.g. LangGraph | CrewAI | Multi (LangGraph + CrewAI)>
Backend     : <e.g. Ollama (local) | Databricks | OpenAI>
"""
```

### `tests/test_local.py` template

```python
"""
test_local.py — Unit and integration tests for the <Pattern> / <scenario> agent.

Description : <2–3 sentences. State what is being tested — which tools, which
              mock data structures, and whether the full agent run + rubric scoring
              is covered. Note the importlib pattern used for bracket-named paths.>

Pattern     : <Pattern name>
Category    : <Category>
Framework   : <Framework>
Backend     : <Backend>
"""
```

### `_shared/` utility template

```python
"""
<filename>.py — <One-line purpose>.

Description : <2–3 sentences. Explain the module's role in the shared harness,
              what it provides to agent files, and any key configuration it reads
              (e.g. config.yaml keys, rubric.yaml structure).>

Module      : Shared utility
Used by     : All agent.py files
"""
```
