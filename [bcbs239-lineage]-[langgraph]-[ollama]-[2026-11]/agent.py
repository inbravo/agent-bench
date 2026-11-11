"""
bcbs239-lineage / langgraph / ollama
─────────────────────────────────────
BCBS 239 Data Lineage Agent.

BCBS 239 (Principles for Effective Risk Data Aggregation and Risk Reporting)
Principle 4 requires banks to generate aggregate risk data quickly.
Principle 6 requires complete data lineage documentation.

This agent:
  1. Accepts a trade or risk position identifier
  2. Traces its data lineage through the mock data pipeline
  3. Checks completeness against BCBS 239 Principle 6 criteria
  4. Produces a lineage report suitable for a regulatory review

Run:
    python agent.py

Switch to Databricks:
    Edit config.yaml → active_backend: "databricks"
    Set DATABRICKS_HOST and DATABRICKS_TOKEN in .env
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from _shared.backend import get_llm
from _shared.scorer import score_run


# ── Mock data: simulated lineage graph ───────────────────────────────────────

LINEAGE_DB = {
    "T-20241201-0042": {
        "trade_id": "T-20241201-0042",
        "instrument": "USD/EUR FX Forward",
        "notional": 10_000_000,
        "source_systems": ["Murex 3.1", "Summit FT"],
        "data_hops": [
            {"system": "Murex 3.1", "table": "DEAL_MASTER", "timestamp": "2024-12-01T09:15:00Z"},
            {"system": "Risk ETL", "table": "RISK_STAGING", "timestamp": "2024-12-01T10:00:00Z"},
            {"system": "Risk DWH", "table": "RISK_POSITIONS", "timestamp": "2024-12-01T11:00:00Z"},
            {"system": "BCBS Report Engine", "table": "LINEAGE_REPORT", "timestamp": "2024-12-01T12:00:00Z"},
        ],
        "data_quality_flags": [],
        "lineage_complete": True,
    },
    "T-20241201-0099": {
        "trade_id": "T-20241201-0099",
        "instrument": "EUR IRS 5Y",
        "notional": 50_000_000,
        "source_systems": ["Calypso"],
        "data_hops": [
            {"system": "Calypso", "table": "POSITION", "timestamp": "2024-12-01T08:30:00Z"},
            {"system": "Risk ETL", "table": "RISK_STAGING", "timestamp": None},  # GAP
            {"system": "Risk DWH", "table": "RISK_POSITIONS", "timestamp": "2024-12-01T11:30:00Z"},
        ],
        "data_quality_flags": ["ETL_TIMESTAMP_MISSING"],
        "lineage_complete": False,
    },
}


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def get_trade_lineage(trade_id: str) -> dict:
    """
    Retrieve the full data lineage for a given trade ID.

    Args:
        trade_id: Trade identifier (e.g. 'T-20241201-0042').

    Returns:
        Dict with source systems, data hops, quality flags, and completeness status.
    """
    record = LINEAGE_DB.get(trade_id)
    if not record:
        return {"error": f"Trade {trade_id} not found in lineage database."}
    return record


@tool
def check_bcbs239_compliance(trade_id: str) -> dict:
    """
    Check whether a trade's lineage meets BCBS 239 Principle 6 completeness criteria.

    Principle 6 requires: documented source systems, complete hop timestamps,
    no unresolved data quality flags, and end-to-end traceability.

    Args:
        trade_id: Trade identifier.

    Returns:
        Dict with compliance status, gaps found, and recommendations.
    """
    record = LINEAGE_DB.get(trade_id)
    if not record:
        return {"error": f"Trade {trade_id} not found."}

    gaps = []
    for hop in record["data_hops"]:
        if hop["timestamp"] is None:
            gaps.append(f"Missing timestamp at {hop['system']} → {hop['table']}")

    for flag in record["data_quality_flags"]:
        gaps.append(f"Unresolved data quality flag: {flag}")

    compliant = len(gaps) == 0

    return {
        "trade_id": trade_id,
        "bcbs239_p6_compliant": compliant,
        "gaps": gaps,
        "recommendations": [
            "Investigate missing ETL timestamps" if any("TIMESTAMP" in g for g in gaps) else None,
            "Resolve data quality flags before regulatory submission" if record["data_quality_flags"] else None,
        ],
        "source_systems": record["source_systems"],
        "hop_count": len(record["data_hops"]),
    }


@tool
def get_bcbs239_principle(principle_number: int) -> dict:
    """
    Retrieve the text of a BCBS 239 principle.

    Args:
        principle_number: Principle number (1–14).

    Returns:
        Dict with principle number, title, and summary text.
    """
    principles = {
        4: {
            "title": "Completeness",
            "text": "A bank should be able to capture and aggregate all material risk data across the banking group.",
        },
        6: {
            "title": "Adaptability",
            "text": "A bank should be able to generate aggregate risk data to meet a broad range of on-demand, ad hoc risk management reporting requests.",
        },
        11: {
            "title": "Distribution",
            "text": "Risk management reports should be distributed to the relevant parties while ensuring confidentiality.",
        },
    }
    p = principles.get(principle_number, {"title": "Unknown", "text": f"Principle {principle_number} not in mock database."})
    return {"principle": principle_number, **p}


# ── LangGraph state ───────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


TOOLS = [get_trade_lineage, check_bcbs239_compliance, get_bcbs239_principle]


def build_graph():
    llm = get_llm()
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
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

TASK = """
You are a BCBS 239 compliance analyst.

Please investigate the following two trades and produce a lineage report:
  - Trade T-20241201-0042
  - Trade T-20241201-0099

For each trade:
1. Retrieve the full data lineage.
2. Check BCBS 239 Principle 6 compliance.
3. List any gaps or data quality issues.
4. State whether it is ready for regulatory submission.

Format your response as a structured report.
"""


def main() -> None:
    print("=" * 60)
    print("BCBS 239 Lineage Agent — LangGraph / Ollama")
    print("=" * 60)

    graph = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content=TASK)]})

    final = result["messages"][-1]
    output = final.content if hasattr(final, "content") else str(final)

    print("\n── Lineage Report ──")
    print(output)

    score = score_run(
        agent_output=output,
        task_description=TASK,
        rubric_path="rubric.yaml",
        token_usage={"input_tokens": 900, "output_tokens": 350},
        backend="ollama",
    )
    print("\n── Decision Economics ──")
    print(f"  Quality score : {score['quality_score']:.2f}")
    print(f"  Token cost    : ${score['token_cost_usd']:.6f}")
    print(f"  CPCD          : {score['cpcd']}")
    print(f"  Passed        : {score['passed']}")


if __name__ == "__main__":
    main()
