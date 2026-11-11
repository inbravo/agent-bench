"""
bcbs239-lineage / crewai / ollama
──────────────────────────────────
BCBS 239 Data Lineage — CrewAI role-based crew.

Same task as [bcbs239-lineage]-[langgraph]-[ollama]-[2026-11], now implemented
as a three-agent crew:

  1. Data Steward       — retrieves lineage records from source systems
  2. BCBS 239 Analyst   — checks compliance against Principle 6 criteria
  3. Report Writer      — produces the final regulatory-ready lineage report

Compare with the LangGraph version to see:
  - Role-based reasoning vs stateful graph
  - Different tool-calling patterns
  - Quality score and CPCD for the same task

Install:
    pip install crewai crewai-tools pyyaml

Run:
    python agent.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from _shared.scorer import score_run


# ── Load config ───────────────────────────────────────────────────────────────

def _load_config() -> dict:
    with open(Path(__file__).parent / "config.yaml") as f:
        return yaml.safe_load(f)


def _get_ollama_llm(cfg: dict):
    """Return a LangChain Ollama LLM for CrewAI."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as e:
        raise ImportError("pip install langchain-ollama") from e

    return ChatOllama(
        base_url=cfg["ollama"]["base_url"],
        model=cfg["ollama"]["model"],
        temperature=cfg["ollama"]["temperature"],
    )


# ── Mock data (same as LangGraph version) ─────────────────────────────────────

LINEAGE_DB = {
    "T-20241201-0042": {
        "trade_id": "T-20241201-0042",
        "instrument": "USD/EUR FX Forward",
        "source_systems": ["Murex 3.1", "Summit FT"],
        "data_hops": [
            {"system": "Murex 3.1", "table": "DEAL_MASTER", "timestamp": "2024-12-01T09:15:00Z"},
            {"system": "Risk ETL", "table": "RISK_STAGING", "timestamp": "2024-12-01T10:00:00Z"},
            {"system": "Risk DWH", "table": "RISK_POSITIONS", "timestamp": "2024-12-01T11:00:00Z"},
        ],
        "data_quality_flags": [],
        "lineage_complete": True,
    },
    "T-20241201-0099": {
        "trade_id": "T-20241201-0099",
        "instrument": "EUR IRS 5Y",
        "source_systems": ["Calypso"],
        "data_hops": [
            {"system": "Calypso", "table": "POSITION", "timestamp": "2024-12-01T08:30:00Z"},
            {"system": "Risk ETL", "table": "RISK_STAGING", "timestamp": None},
            {"system": "Risk DWH", "table": "RISK_POSITIONS", "timestamp": "2024-12-01T11:30:00Z"},
        ],
        "data_quality_flags": ["ETL_TIMESTAMP_MISSING"],
        "lineage_complete": False,
    },
}


# ── CrewAI tools ──────────────────────────────────────────────────────────────

class LineageInput(BaseModel):
    trade_id: str = Field(description="Trade identifier, e.g. T-20241201-0042")


class GetLineageTool(BaseTool):
    name: str = "get_trade_lineage"
    description: str = "Retrieve the full data lineage record for a trade ID."
    args_schema: type[BaseModel] = LineageInput

    def _run(self, trade_id: str) -> str:
        record = LINEAGE_DB.get(trade_id)
        if not record:
            return f"Trade {trade_id} not found."
        return str(record)


class CheckComplianceTool(BaseTool):
    name: str = "check_bcbs239_compliance"
    description: str = "Check BCBS 239 Principle 6 compliance for a trade."
    args_schema: type[BaseModel] = LineageInput

    def _run(self, trade_id: str) -> str:
        record = LINEAGE_DB.get(trade_id)
        if not record:
            return f"Trade {trade_id} not found."

        gaps = []
        for hop in record["data_hops"]:
            if hop["timestamp"] is None:
                gaps.append(f"Missing timestamp at {hop['system']} → {hop['table']}")
        for flag in record["data_quality_flags"]:
            gaps.append(f"Data quality flag: {flag}")

        compliant = len(gaps) == 0
        return str({
            "trade_id": trade_id,
            "bcbs239_p6_compliant": compliant,
            "gaps": gaps,
        })


# ── Crew definition ───────────────────────────────────────────────────────────

TASK_DESCRIPTION = """
Investigate the following two trades and produce a BCBS 239 lineage report:
  - Trade T-20241201-0042
  - Trade T-20241201-0099

Expected output: a structured report with compliance verdict and gaps for each trade.
"""


def build_crew(llm) -> Crew:
    tools = [GetLineageTool(), CheckComplianceTool()]

    data_steward = Agent(
        role="Data Steward",
        goal="Retrieve complete data lineage records for all assigned trades.",
        backstory=(
            "You are a senior data steward at a tier-1 bank. "
            "Your job is to pull lineage records from source systems "
            "and document every data hop from trade capture to risk reporting."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
    )

    bcbs_analyst = Agent(
        role="BCBS 239 Compliance Analyst",
        goal="Assess each trade's lineage against BCBS 239 Principle 6 criteria.",
        backstory=(
            "You are a regulatory compliance specialist with deep expertise in BCBS 239. "
            "You review data lineage records and identify gaps that would fail a regulatory review."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
    )

    report_writer = Agent(
        role="Regulatory Report Writer",
        goal="Produce a clear, structured lineage report suitable for regulatory submission.",
        backstory=(
            "You write regulatory reports that are clear, accurate, and actionable. "
            "Your reports are read by risk committees and regulators."
        ),
        llm=llm,
        verbose=True,
    )

    retrieve_task = Task(
        description=(
            "Retrieve the data lineage for trades T-20241201-0042 and T-20241201-0099. "
            "Document the source systems and all data hops."
        ),
        agent=data_steward,
        expected_output="Data lineage records for both trades with all hops listed.",
    )

    analyze_task = Task(
        description=(
            "Using the lineage records, check each trade against BCBS 239 Principle 6. "
            "Identify any gaps (missing timestamps, data quality flags). "
            "State the compliance verdict for each trade."
        ),
        agent=bcbs_analyst,
        expected_output="Compliance assessment with specific gaps listed for each trade.",
    )

    report_task = Task(
        description=(
            "Write a final BCBS 239 lineage report covering both trades. "
            "Include: trade ID, instrument, source systems, compliance verdict, "
            "gaps found, and recommendations. Format clearly."
        ),
        agent=report_writer,
        expected_output="Structured BCBS 239 lineage report ready for regulatory submission.",
    )

    return Crew(
        agents=[data_steward, bcbs_analyst, report_writer],
        tasks=[retrieve_task, analyze_task, report_task],
        process=Process.sequential,
        verbose=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    cfg = _load_config()
    llm = _get_ollama_llm(cfg)

    print("=" * 60)
    print("BCBS 239 Lineage Agent — CrewAI / Ollama")
    print(f"Model: {cfg['ollama']['model']}")
    print("=" * 60)

    crew = build_crew(llm)
    result = crew.kickoff()
    output = str(result)

    print("\n── Crew Output ──")
    print(output)

    score = score_run(
        agent_output=output,
        task_description=TASK_DESCRIPTION,
        rubric_path=str(Path(__file__).parent / "rubric.yaml"),
        token_usage={"input_tokens": 1800, "output_tokens": 600},  # CrewAI uses more tokens
        backend="ollama",
    )
    print("\n── Decision Economics ──")
    print(f"  Quality score : {score['quality_score']:.2f}")
    print(f"  Token cost    : ${score['token_cost_usd']:.6f}")
    print(f"  CPCD          : {score['cpcd']}")
    print(f"  Passed        : {score['passed']}")
    print("\nCompare with LangGraph version token usage to see framework overhead.")


if __name__ == "__main__":
    main()
