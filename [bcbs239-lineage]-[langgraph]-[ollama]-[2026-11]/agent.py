"""
agent.py — BCBS 239 data lineage agent (LangGraph + Ollama).

Investigates trade data lineage and flags BCBS 239 compliance gaps.
Demonstrates stateful multi-tool reasoning: each trade requires multiple
tool calls before the agent can reach a compliance verdict.

BCBS 239 scope:
  Principle 4 — Data aggregation completeness
  Principle 7 — Accuracy and integrity (ETL timestamp required)

Mock trades in this demo:
  T-20241201-0042  — compliant (all lineage fields populated)
  T-20241201-0099  — non-compliant (ETL_TIMESTAMP_MISSING gap)

Run:
    python agent.py
    python agent.py "Investigate trade T-20241201-0042 and check BCBS 239 compliance"

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
from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "_shared"))

import logging_config
logging_config.setup()
log = logging.getLogger("agent.bcbs239-lineage")

from _shared.backend import get_llm
from _shared.scorer  import score_run


# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_TASK = (
    "Investigate data lineage for trades T-20241201-0042 and T-20241201-0099. "
    "For each trade: (1) retrieve its lineage, (2) check BCBS 239 compliance, "
    "(3) look up the relevant BCBS 239 principle. "
    "Produce a lineage report identifying any compliance gaps."
)

LINEAGE_DB: dict[str, dict] = {
    "T-20241201-0042": {
        "trade_id":        "T-20241201-0042",
        "source_system":   "MUREX",
        "destination":     "RISK_DW",
        "etl_job":         "murex_to_dw_v3",
        "etl_timestamp":   "2024-12-01T18:30:00Z",
        "data_quality":    "PASS",
        "lineage_gaps":    [],
        "bcbs239_fields":  ["source", "destination", "etl_job", "etl_timestamp"],
    },
    "T-20241201-0099": {
        "trade_id":        "T-20241201-0099",
        "source_system":   "SUMMIT",
        "destination":     "RISK_DW",
        "etl_job":         "summit_to_dw_v2",
        "etl_timestamp":   None,
        "data_quality":    "FAIL",
        "lineage_gaps":    ["ETL_TIMESTAMP_MISSING"],
        "bcbs239_fields":  ["source", "destination", "etl_job"],
    },
}

BCBS239_PRINCIPLES: dict[str, str] = {
    "4": "Principle 4 — Completeness: A bank should be able to capture and aggregate all material risk data across the banking group.",
    "7": "Principle 7 — Accuracy: Risk data should be accurate and reliable. Data should be reconciled with risk management and accounting data sources.",
    "8": "Principle 8 — Timeliness: Risk management reports should be produced in a timeframe that meets the needs of the recipients.",
}


# ── Tool definitions ──────────────────────────────────────────────────────────

@tool
def get_trade_lineage(trade_id: str) -> dict:
    """
    Retrieve data lineage metadata for a given trade ID.

    Args:
        trade_id: Trade identifier, e.g. 'T-20241201-0042'.

    Returns:
        Dict with source_system, destination, etl_job, etl_timestamp,
        data_quality, and lineage_gaps.
    """
    result = LINEAGE_DB.get(trade_id)
    if result is None:
        log.warning("get_trade_lineage: trade not found — %s", trade_id)
        return {"error": f"Trade {trade_id!r} not found in lineage database."}
    log.info("get_trade_lineage: trade=%s  gaps=%s", trade_id, result["lineage_gaps"])
    return result


@tool
def check_bcbs239_compliance(trade_id: str) -> dict:
    """
    Check whether a trade's lineage record is BCBS 239-compliant.

    Returns a compliance verdict and a list of principles violated.

    Args:
        trade_id: Trade identifier, e.g. 'T-20241201-0042'.
    """
    record = LINEAGE_DB.get(trade_id)
    if record is None:
        return {"error": f"Trade {trade_id!r} not found."}

    gaps             = record.get("lineage_gaps", [])
    is_compliant     = len(gaps) == 0
    violated         = []

    if "ETL_TIMESTAMP_MISSING" in gaps:
        violated.append("7")  # Accuracy & integrity principle

    result = {
        "trade_id":           trade_id,
        "compliant":          is_compliant,
        "violated_principles": violated,
        "gaps":               gaps,
        "recommendation":     (
            "No action required."
            if is_compliant
            else f"Remediate gaps: {', '.join(gaps)}"
        ),
    }
    log.info(
        "check_bcbs239_compliance: trade=%s  compliant=%s  violations=%s",
        trade_id, is_compliant, violated,
    )
    return result


@tool
def get_bcbs239_principle(principle_number: str) -> dict:
    """
    Retrieve the text of a BCBS 239 principle by number.

    Args:
        principle_number: Principle number as string, e.g. '4', '7', '8'.
    """
    text = BCBS239_PRINCIPLES.get(str(principle_number))
    if text is None:
        return {"error": f"Principle {principle_number!r} not found."}
    log.info("get_bcbs239_principle: principle=%s", principle_number)
    return {"principle": principle_number, "text": text}


# ── LangGraph state ───────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ── Graph builder ─────────────────────────────────────────────────────────────

TOOLS = [get_trade_lineage, check_bcbs239_compliance, get_bcbs239_principle]


def build_graph():
    """Build and compile the BCBS 239 lineage agent graph."""
    llm            = get_llm()
    llm_with_tools = llm.bind_tools(TOOLS)

    def call_model(state: AgentState) -> AgentState:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", END: END}
    )
    graph.add_edge("tools", "agent")
    return graph.compile()


# ── Agent runner ──────────────────────────────────────────────────────────────

def run_agent(task: str) -> None:
    log.info("Agent task: %s", task[:120])

    print(f"\nTask: {task}")
    print("=" * 65)

    graph  = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content=task)]})

    final  = result["messages"][-1]
    output = final.content if hasattr(final, "content") else str(final)

    print(f"\nAnswer:\n{output}")
    print("=" * 65)

    score = score_run(
        agent_output     = output,
        task_description = task,
        rubric_path      = "rubric.yaml",
        token_usage      = {"input_tokens": 800, "output_tokens": 300},
        backend          = "ollama",
    )

    print("\n── Decision Economics ───────────────────────────────")
    print(f"  Quality score : {score['quality_score']:.2f}")
    print(f"  Token cost    : ${score['token_cost_usd']:.6f}")
    print(f"  CPCD          : {score['cpcd']}")
    print(f"  Passed        : {'✓' if score['passed'] else '✗'}")
    print("─" * 52)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK
    run_agent(task)
