"""
agent.py — Tool-use baseline agent (LangGraph + Ollama).

Calibration agent: runs three financial tool calls and scores whether the
model handled them correctly.  Use this to validate a new Ollama model before
building domain-specific examples on top of it.

Tools exercised:
  1. get_market_price(ticker)             — simple string lookup
  2. calculate_var(notional, confidence)  — numeric computation
  3. fetch_regulation_text(reference)     — structured text fetch

Run:
    python agent.py
    python agent.py "Get the price of GS and calculate 95pct VaR for $500k"

Switch model:
    Edit config.yaml → ollama.model

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

# Allow importing _shared from anywhere
sys.path.insert(0, str(Path(__file__).parents[1]))

import logging_config  # noqa: E402  (must come after sys.path insert)
logging_config.setup()
log = logging.getLogger("agent.tool-use-baseline")

from _shared.backend import get_llm    # noqa: E402
from _shared.scorer  import score_run  # noqa: E402


# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_TASK = (
    "Please do the following three things:\n"
    "1. Get the current market price of JPM.\n"
    "2. Calculate the 99% VaR for a $1,000,000 position.\n"
    "3. Fetch the regulatory text for BCBS-239-P4.\n"
    "Summarise all three results clearly."
)

MOCK_PRICES = {
    "AAPL": 189.42,
    "MSFT": 415.23,
    "JPM":  198.76,
    "GS":   452.10,
}

MOCK_REGS = {
    "BCBS-239-P4": "Principle 4: Banks should have the capability to generate aggregate risk data quickly.",
    "FRTB-SA-1":   "The standardised approach (SA) requires banks to calculate capital requirements for market risk.",
    "COREP-C02":   "COREP C 02.00 covers own funds requirements under CRR Article 92.",
}


# ── Tool definitions ──────────────────────────────────────────────────────────

@tool
def get_market_price(ticker: str) -> dict:
    """Return the current mock market price for a given ticker symbol."""
    price = MOCK_PRICES.get(ticker.upper(), 0.0)
    log.info("get_market_price: ticker=%s  price=%s", ticker.upper(), price)
    return {"ticker": ticker.upper(), "price": price, "currency": "USD"}


@tool
def calculate_var(notional: float, confidence_level: float = 0.99) -> dict:
    """
    Calculate a simplified Value at Risk (VaR) for a single position.

    Args:
        notional:         Position size in USD.
        confidence_level: 0.95 or 0.99 (default 0.99).

    Returns:
        Dict with var_usd, confidence_level, methodology, notional.
    """
    z         = 2.326 if confidence_level >= 0.99 else 1.645
    daily_vol = 0.015   # simplified 1.5% daily volatility
    var       = notional * z * daily_vol
    log.info(
        "calculate_var: notional=%.2f  cl=%.2f  var_usd=%.2f",
        notional, confidence_level, var,
    )
    return {
        "var_usd":           round(var, 2),
        "confidence_level":  confidence_level,
        "methodology":       "parametric",
        "notional":          notional,
    }


@tool
def fetch_regulation_text(reference: str) -> dict:
    """
    Fetch a mock regulatory text snippet by reference code.

    Args:
        reference: Regulation reference, e.g. 'BCBS-239-P4', 'FRTB-SA-1', 'COREP-C02'.
    """
    text = MOCK_REGS.get(
        reference.upper(),
        f"Reference '{reference}' not found in mock database.",
    )
    log.info("fetch_regulation_text: ref=%s", reference)
    return {"reference": reference, "text": text}


# ── LangGraph state ───────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ── Graph builder ─────────────────────────────────────────────────────────────

TOOLS = [get_market_price, calculate_var, fetch_regulation_text]


def build_graph():
    """Build and compile the LangGraph agent graph."""
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

    final   = result["messages"][-1]
    output  = final.content if hasattr(final, "content") else str(final)

    print(f"\nAnswer:\n{output}")
    print("=" * 65)

    # Score the run
    score = score_run(
        agent_output     = output,
        task_description = task,
        rubric_path      = "rubric.yaml",
        token_usage      = {"input_tokens": 600, "output_tokens": 200},
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
