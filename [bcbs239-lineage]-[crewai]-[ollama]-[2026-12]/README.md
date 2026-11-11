# bcbs239-lineage / crewai / ollama

**Phase 2 — Multi-Agent Patterns**  
Same BCBS 239 task, now as a three-agent CrewAI crew. Framework comparison starts here.

---

## What It Shows

- CrewAI role-based crew: Data Steward → BCBS 239 Analyst → Report Writer
- Sequential crew process — each agent hands off to the next
- Same rubric as the LangGraph version → quality score is comparable
- CrewAI uses ~2× more tokens (3 role invocations vs 1 LangGraph loop)
- Decision Economics: compare CPCD across frameworks on identical task

---

## Quick Start

```bash
# Install CrewAI
pip install crewai crewai-tools langchain-ollama pyyaml

# Run
cd [bcbs239-lineage]-[crewai]-[ollama]-[2026-12]
python agent.py
```

---

## Architecture

```
  kickoff("Investigate T-0042 and T-0099 per BCBS 239")
           │
           ▼
  ┌────────────────────────────────────────────────────┐
  │                  CrewAI Crew                        │
  │              process=sequential                     │
  │                                                    │
  │  ┌──────────────────┐                              │
  │  │   Data Steward   │  retrieves lineage records   │
  │  │   (Agent 1)      │  uses: get_trade_lineage     │
  │  └────────┬─────────┘                              │
  │            │ hands off context                     │
  │            ▼                                       │
  │  ┌──────────────────┐                              │
  │  │  BCBS 239        │  checks P6 compliance        │
  │  │  Analyst (Ag. 2) │  uses: check_bcbs239         │
  │  └────────┬─────────┘                              │
  │            │ hands off analysis                    │
  │            ▼                                       │
  │  ┌──────────────────┐                              │
  │  │  Report Writer   │  writes final report         │
  │  │  (Agent 3)       │  no tools — synthesis only   │
  │  └────────┬─────────┘                              │
  └───────────┼────────────────────────────────────────┘
              │
              ▼
         crew.kickoff() output → scorer.py → CPCD
```

---

## LangGraph vs CrewAI — Same Task

| Aspect | LangGraph | CrewAI |
|---|---|---|
| Mental model | Stateful graph | Role-based crew |
| Token usage | ~1,100 | ~2,400 |
| Quality score | 0.75–0.85 | 0.70–0.80 |
| Setup time | Medium (graph wiring) | Fast (role YAML) |
| Best for | Production workflows | Rapid prototyping |

> **This is the comparison point.**  
> Same task, same rubric, different framework. The numbers tell you which to use.

---

## Decision Economics

| Metric | LangGraph / Ollama | CrewAI / Ollama |
|---|---|---|
| Token cost | $0.00 | $0.00 |
| Approx tokens | ~1,100 | ~2,400 |
| CPCD | $0.00 | $0.00 |
| Databricks equivalent | ~$0.00093 | ~$0.00204 |
