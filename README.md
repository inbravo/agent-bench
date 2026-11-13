# agent-bench

> This lab is my place to keep the Agentic AI stuff — practical blueprints for agent evaluation, harness design, and decision economics, running the same BFSI task across multiple frameworks and backends.

---

## What Makes This Lab Different

Most agentic AI repos compare frameworks with toy examples (weather APIs, travel planners).  
This lab runs **real BFSI/RegTech tasks** (BCBS 239 lineage, FRTB calculations, COREP reporting) across multiple frameworks, on both **Ollama (local)** and **Databricks (production)**, and scores every run on **cost-per-correct-decision** — not just whether it worked.

| Other repos | This lab |
|---|---|
| Generic toy tasks | BFSI/RegTech domain tasks (BCBS 239, FRTB, COREP) |
| Framework-first organisation | **Task-first** — same task, multiple frameworks |
| One backend | **Dual-backend**: Ollama locally, Databricks for production |
| Feature comparisons | **Decision economics**: cost per correct decision scored |
| Qualitative | **Quantitative**: rubric YAML + LLM-as-judge scoring |

---

## Repository Structure

### Naming Convention

Folders follow `[task]-[framework]-[backend]-[YYYY-MM]`, with each part in square brackets:

- `[task]` — the BFSI/RegTech or generic problem being solved (e.g. `bcbs239-lineage`, `frtb-calc`, `tool-use-baseline`, `decision-econ`)
- `[framework]` — the agentic framework under study (e.g. `langgraph`, `crewai`, `mosaic`, `cortex`, `openai-sdk`, `claude-sdk`)
- `[backend]` — the LLM/platform backend (e.g. `ollama`, `databricks`, `snowflake`, `generic`)
- `[YYYY-MM]` — the month the example was created

> The same `[task]` appearing across multiple `[framework]` and `[backend]` folders is the point — that's where the comparison lives.

---

### Directory Listing

| # | Folder | Framework | Backend | Phase |
|---|---|---|---|---|
| 1 | `[tool-use-baseline]-[langgraph]-[ollama]-[2026-11]` | LangGraph | Ollama | 1 — Foundations |
| 2 | `[bcbs239-lineage]-[langgraph]-[ollama]-[2026-11]` | LangGraph | Ollama | 1 — Foundations |
| 3 | `[bcbs239-lineage]-[langgraph]-[databricks]-[2026-11]` | LangGraph | Databricks | 1 — Foundations |
| 4 | `[bcbs239-lineage]-[crewai]-[ollama]-[2026-12]` | CrewAI | Ollama | 2 — Multi-Agent |
| 5 | `[decision-econ]-[generic]-[ollama]-[2026-12]` | Generic | Ollama | 5 — Decision Economics |

---

## Learning Phases

### Phase 1 — Foundations (Weeks 1–3): Core agentic primitives
LangGraph is the production default — 34.5M monthly downloads, used at JPMorgan, BlackRock, Barclays.  
Learn the mental model here: stateful graphs, nodes, edges, checkpoints, human-in-the-loop.

```
[tool-use-baseline]-[langgraph]-[ollama]-[2026-11]      ← calibration: which Ollama models handle tool calls
[bcbs239-lineage]-[langgraph]-[ollama]-[2026-11]        ← your domain moat: BCBS 239 lineage agent
[bcbs239-lineage]-[langgraph]-[databricks]-[2026-11]    ← same task, MLflow trace, demoable at Barclays
```

### Phase 2 — Multi-Agent Patterns (Week 4–5): CrewAI
Role-based crews — fastest path to a multi-agent prototype.  
Same BFSI task as Phase 1 so the framework comparison is apples-to-apples.

```
[bcbs239-lineage]-[crewai]-[ollama]-[2026-12]
[frtb-calc]-[crewai]-[ollama]-[2026-12]
```

### Phase 3 — Enterprise Data Platforms (Weeks 6–9): Databricks + Snowflake
Where BFSI enterprises actually run their data. Governed agents on Unity Catalog and Cortex.

```
[bcbs239-lineage]-[mosaic]-[databricks]-[2026-12]       ← Agent Bricks + MLflow tracing
[bcbs239-lineage]-[mosaic]-[databricks]-[2026-12]       ← Mosaic AI Agent Evaluation
[corep-report]-[cortex]-[snowflake]-[2027-01]           ← Cortex Analyst + governed data
[corep-report]-[cortex-gateway]-[snowflake]-[2027-01]   ← Cortex AI Gateway + guardrails
```

### Phase 4 — AI Cloud Providers (Weeks 10–12): How they plug into the platforms
```
[kyc-check]-[claude-sdk]-[generic]-[2027-01]
[kyc-check]-[openai-sdk]-[generic]-[2027-01]
[trade-surveillance]-[microsoft-af]-[databricks]-[2027-01]
[trade-surveillance]-[google-adk]-[generic]-[2027-02]
```

### Phase 5 — Cross-Cutting Concerns (Ongoing)
```
[decision-econ]-[generic]-[ollama]-[2026-12]            ← token cost × quality = cost per correct decision
[agent-eval]-[generic]-[ollama]-[2027-01]               ← LLM-as-judge, rubric YAML, scoring
[mcp-tools]-[generic]-[ollama]-[2027-01]                ← MCP as the interop layer across all providers
```

---

## Two-Backend Testing Strategy

Every example in this lab is **backend-agnostic by design**. A single `config.yaml` switches between local Ollama and Databricks Foundation Model APIs.

```
[any-task]-[any-framework]-[ollama]-[YYYY-MM]/     ← iterate fast locally, no cost
[any-task]-[any-framework]-[databricks]-[YYYY-MM]/ ← validate on production LLM, capture MLflow trace
```

### Recommended Ollama Models

| Model | Best for |
|---|---|
| `llama3.2:3b` | Fast iteration, harness logic testing |
| `llama3.1:8b` | Serious agent reasoning — sweet spot |
| `qwen2.5:7b` | Structured output, JSON tool calls |
| `mistral-nemo` | Multi-step reasoning chains |
| `phi3.5-mini` | Lightweight harness testing |

### Recommended Databricks Setup

- **Foundation Model APIs**: `databricks-meta-llama-3-1-70b-instruct` or `databricks-dbrx-instruct`
- **Tracing**: MLflow 3 auto-tracing via `mlflow.langchain.autolog()`
- **Tool governance**: Unity Catalog Functions as MCP-compatible tools
- **Evaluation**: Mosaic AI Agent Evaluation with AI judges

---

## Per-Example Structure

Every folder follows this layout:

```
[task]-[framework]-[backend]-[YYYY-MM]/
├── agent.py              ← the agent (backend-agnostic)
├── config.yaml           ← LLM_BACKEND, LLM_MODEL, endpoint
├── tools/                ← tool definitions (MCP-ready)
├── rubric.yaml           ← evaluation rubric for LLM-as-judge
├── tests/
│   ├── test_local.py     ← runs against Ollama
│   └── test_databricks.py ← runs against Databricks Foundation Model APIs
├── traces/               ← saved MLflow traces from Databricks runs
└── README.md             ← what it shows, quick start, architecture diagram
```

---

## Agentic AI Landscape (Nov 2026)

### Open Source Frameworks

| Framework | Stars | Monthly Downloads | Status | Best for |
|---|---|---|---|---|
| LangGraph | 44K | 34.5M | 🟢 Active v1.2.x | Production stateful workflows |
| CrewAI | 60K | 5.2M | 🟢 Active v1.15.x | Role-based multi-agent prototypes |
| Microsoft Agent Framework | 12K | — | 🟢 GA April 2026 | Azure-native, successor to AutoGen+SK |
| OpenAI Agents SDK | — | 10.4M | 🟢 Active | Handoffs, guardrails, tracing |
| Google ADK | — | — | 🟢 Active | GCP-native, A2A protocol |
| Pydantic AI | — | — | 🟡 Rising | Type-safe Python agents |
| AutoGen (legacy) | 58K | 0.4M | 🔴 Maintenance | Superseded by MS Agent Framework |

### Enterprise Data Platforms

| Platform | Agentic Stack | Governance |
|---|---|---|
| Databricks | Mosaic AI Agent Framework, Agent Bricks, MLflow 3 | Unity Catalog, AI Gateway |
| Snowflake | Cortex Agents, CoWork, CoCo, Cortex AI Gateway | Horizon Catalog, Business Ontology |

---

## Decision Economics — The Signature Metric

Every example in this lab can optionally compute **cost-per-correct-decision (CPCD)**:

```
CPCD = token_cost / quality_score
```

Where:
- `token_cost` = (input_tokens × input_rate) + (output_tokens × output_rate)
- `quality_score` = LLM-as-judge score (0.0–1.0) against `rubric.yaml`

This makes agent performance economically defensible — not just "did it work" but "what did it cost per correct answer."

---

## Learning Progression

| # | Example | What you learn |
|---|---|---|
| 1 | tool-use-baseline / langgraph / ollama | Which local models reliably call tools — your calibration baseline |
| 2 | bcbs239-lineage / langgraph / ollama | LangGraph stateful graph, BCBS 239 domain, local iteration |
| 3 | bcbs239-lineage / langgraph / databricks | Same agent on Databricks, MLflow tracing, production LLM |
| 4 | bcbs239-lineage / crewai / ollama | Same task, role-based crew — framework comparison starts here |
| 5 | decision-econ / generic / ollama | CPCD metric, rubric YAML, LLM-as-judge scoring |

---

## Glossary

| Term | Definition |
|---|---|
| **Agentic AI** | AI systems that perceive, reason, plan, and act autonomously using tools and memory |
| **LangGraph** | Graph-based agent framework — nodes are LLM/tool steps, edges are flow control |
| **CrewAI** | Role-based multi-agent framework — agents have role, goal, backstory, tasks |
| **MCP** | Model Context Protocol — Anthropic's open standard for tool/data interop across providers |
| **A2A** | Agent-to-Agent protocol — Google's standard for inter-agent communication |
| **Mosaic AI** | Databricks' ML/AI product layer — includes Agent Framework, Agent Bricks, MLflow 3 |
| **Cortex Agents** | Snowflake's managed agent runtime — governed data access, REST API deployment |
| **Ollama** | Local LLM runtime — runs Llama, Mistral, Qwen and others on your own hardware |
| **Foundation Model APIs** | Databricks-hosted LLM endpoints — Llama 3.1 70B, DBRX, Claude via Mosaic |
| **MLflow 3** | Databricks GenAI lifecycle backbone — tracing, evaluation, model registry |
| **Unity Catalog** | Databricks governance layer — tables, models, functions, MCP-compatible tools |
| **BCBS 239** | Basel Committee standard for risk data aggregation and reporting |
| **FRTB** | Fundamental Review of the Trading Book — Basel IV market risk capital framework |
| **COREP** | Common Reporting — EBA standard for regulatory capital reporting |
| **CPCD** | Cost-per-correct-decision — token spend divided by LLM-as-judge quality score |
| **LLM-as-judge** | Using an LLM to evaluate another LLM's output against a rubric |
| **Rubric YAML** | A structured evaluation spec defining criteria, weights, and scoring logic |
| **Decision Economics** | The discipline of measuring agent cost and quality to make AI economically defensible |
| **Human-in-the-loop** | Agent pattern where execution pauses for human approval at defined checkpoints |
| **Dual-backend** | Running the same agent code against both Ollama (local) and Databricks (production) |

---

## Companion Repositories

| Repo | Focus |
|---|---|
| [context-lab](https://github.com/inbravo/context-lab) | Context Engineering — data contracts, semantic layers, ontologies, MCP, decision economics |
| [agent-bench](https://github.com/inbravo/agent-bench) | Agentic AI — frameworks, harness, eval, decision economics on BFSI tasks |

---

## License

MIT — see [LICENSE](LICENSE)

## Author

[Amit Dixit (InBravo)](https://linkedin.com/in/inbravo) — Lead Presales Architect, BFSI/RegTech specialist
