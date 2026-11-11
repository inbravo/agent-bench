"""
agent.py — BCBS 239 data lineage agent (CrewAI + Ollama).

Same domain task as the LangGraph variant — different architecture.
Three specialist agents collaborate sequentially:

  1. Data Steward        — retrieves lineage metadata for each trade
  2. Compliance Analyst  — applies BCBS 239 rules and identifies gaps
  3. Report Writer       — produces the final lineage compliance report

Compare token usage vs. the LangGraph variant: CrewAI's role-based
orchestration typically uses ~2× more tokens for the same task.

Run:
    python agent.py
    python agent.py "Investigate trade T-20241201-0042 only"

Switch backend:
    Edit config.yaml → active_backend: "databricks"
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Type

from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "_shared"))

import logging_config
logging_config.setup()
log = logging.getLogger("agent.bcbs239-lineage.crewai")

from _shared.backend import get_config
from _shared.scorer  import score_run


# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_TASK = (
    "Investigate data lineage for trades T-20241201-0042 and T-20241201-0099. "
    "For each trade: retrieve lineage, check BCBS 239 compliance, and identify gaps. "
    "Produce a final lineage compliance report."
)

LINEAGE_DB: dict[str, dict] = {
    "T-20241201-0042": {
        "trade_id":       "T-20241201-0042",
        "source_system":  "MUREX",
        "destination":    "RISK_DW",
        "etl_job":        "murex_to_dw_v3",
        "etl_timestamp":  "2024-12-01T18:30:00Z",
        "data_quality":   "PASS",
        "lineage_gaps":   [],
    },
    "T-20241201-0099": {
        "trade_id":       "T-20241201-0099",
        "source_system":  "SUMMIT",
        "destination":    "RISK_DW",
        "etl_job":        "summit_to_dw_v2",
        "etl_timestamp":  None,
        "data_quality":   "FAIL",
        "lineage_gaps":   ["ETL_TIMESTAMP_MISSING"],
    },
}


# ── Tool schemas ──────────────────────────────────────────────────────────────

class LineageInput(BaseModel):
    trade_id: str = Field(description="Trade identifier, e.g. 'T-20241201-0042'")


# ── CrewAI tools ──────────────────────────────────────────────────────────────

class GetLineageTool(BaseTool):
    name: str        = "get_trade_lineage"
    description: str = "Retrieve data lineage metadata for a given trade ID."
    args_schema: Type[BaseModel] = LineageInput

    def _run(self, trade_id: str) -> str:
        record = LINEAGE_DB.get(trade_id)
        if record is None:
            log.warning("GetLineageTool: not found — %s", trade_id)
            return f"Trade {trade_id!r} not found in lineage database."
        log.info("GetLineageTool: trade=%s  gaps=%s", trade_id, record["lineage_gaps"])
        return str(record)


class CheckComplianceTool(BaseTool):
    name: str        = "check_bcbs239_compliance"
    description: str = "Check whether a trade's lineage record is BCBS 239-compliant."
    args_schema: Type[BaseModel] = LineageInput

    def _run(self, trade_id: str) -> str:
        record = LINEAGE_DB.get(trade_id)
        if record is None:
            return f"Trade {trade_id!r} not found."
        gaps         = record.get("lineage_gaps", [])
        is_compliant = len(gaps) == 0
        violated     = ["Principle 7 (Accuracy)"] if "ETL_TIMESTAMP_MISSING" in gaps else []
        result = {
            "trade_id":            trade_id,
            "compliant":           is_compliant,
            "violated_principles": violated,
            "gaps":                gaps,
            "recommendation": (
                "No action required."
                if is_compliant
                else f"Remediate: {', '.join(gaps)}"
            ),
        }
        log.info(
            "CheckComplianceTool: trade=%s  compliant=%s  violations=%s",
            trade_id, is_compliant, violated,
        )
        return str(result)


# ── CrewAI agents ─────────────────────────────────────────────────────────────

def build_crew(llm_model: str = "ollama/llama3.1:8b") -> Crew:
    """Build the three-agent BCBS 239 lineage crew."""
    data_steward = Agent(
        role       = "Data Steward",
        goal       = "Retrieve complete data lineage records for all trades under investigation.",
        backstory  = (
            "You are a senior data steward at a Tier-1 bank responsible for "
            "maintaining trade data lineage in compliance with BCBS 239."
        ),
        tools      = [GetLineageTool()],
        llm        = llm_model,
        verbose    = True,
    )

    compliance_analyst = Agent(
        role       = "BCBS 239 Compliance Analyst",
        goal       = "Assess each trade's lineage against BCBS 239 Principles 4 and 7, flagging any gaps.",
        backstory  = (
            "You are a regulatory compliance expert specialising in BCBS 239 "
            "risk data aggregation requirements. You review lineage records and "
            "identify gaps that must be remediated before the next regulator review."
        ),
        tools      = [CheckComplianceTool()],
        llm        = llm_model,
        verbose    = True,
    )

    report_writer = Agent(
        role       = "Report Writer",
        goal       = "Produce a concise BCBS 239 lineage compliance report from the analyst's findings.",
        backstory  = (
            "You transform technical compliance findings into clear, structured "
            "reports for the Chief Risk Officer and the regulator."
        ),
        tools      = [],
        llm        = llm_model,
        verbose    = True,
    )

    task_retrieve = Task(
        description  = "Retrieve lineage records for trades T-20241201-0042 and T-20241201-0099.",
        expected_output = "Full lineage records for both trades.",
        agent        = data_steward,
    )

    task_assess = Task(
        description  = (
            "Using the lineage records, check BCBS 239 compliance for each trade. "
            "Identify violated principles and remediation recommendations."
        ),
        expected_output = "Compliance verdict and gaps for each trade.",
        agent           = compliance_analyst,
        context         = [task_retrieve],
    )

    task_report = Task(
        description  = (
            "Write a final BCBS 239 lineage compliance report covering both trades. "
            "Include: trade IDs, compliance status, violated principles, and recommendations."
        ),
        expected_output = "A structured compliance report suitable for the Chief Risk Officer.",
        agent           = report_writer,
        context         = [task_assess],
    )

    return Crew(
        agents  = [data_steward, compliance_analyst, report_writer],
        tasks   = [task_retrieve, task_assess, task_report],
        process = Process.sequential,
        verbose = True,
    )


# ── Agent runner ──────────────────────────────────────────────────────────────

def run_agent(task: str) -> None:
    cfg       = get_config()
    ollama_m  = cfg.get("ollama", {}).get("model", "llama3.1:8b")
    llm_model = f"ollama/{ollama_m}"

    log.info("CrewAI  model=%s  task=%s", llm_model, task[:80])

    print(f"\nTask: {task}")
    print("=" * 65)

    crew   = build_crew(llm_model)
    output = crew.kickoff(inputs={"task": task})
    report = str(output)

    print(f"\nFinal report:\n{report}")
    print("=" * 65)

    score = score_run(
        agent_output     = report,
        task_description = task,
        rubric_path      = "rubric.yaml",
        token_usage      = {"input_tokens": 1600, "output_tokens": 600},  # ~2× LangGraph
        backend          = "ollama",
    )

    print("\n── Decision Economics ───────────────────────────────")
    print(f"  Quality score : {score['quality_score']:.2f}")
    print(f"  Token cost    : ${score['token_cost_usd']:.6f}")
    print(f"  CPCD          : {score['cpcd']}")
    print(f"  Passed        : {'✓' if score['passed'] else '✗'}")
    print("  Note: ~2× token usage vs LangGraph for identical task")
    print("─" * 52)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK
    run_agent(task)
