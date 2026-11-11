"""
tool-use-baseline / langgraph / ollama
───────────────────────────────────────
Calibration agent: runs three simple tool calls and reports whether the model
handled them correctly.  Use this to validate a new Ollama model before building
domain-specific examples on top of it.

Tools exercised:
  1. get_market_price(ticker)      — simple string lookup
  2. calculate_var(positions, cl)  — numeric computation
  3. fetch_regulation_text(ref)    — structured output

Run:
    python agent.py

Switch model:
    Edit config.yaml → ollama.model
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow importing _shared from anywhere
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


# ── Tool definitions ──────────────────────────────────────────────────────────

@tool
def get_market_price(ticker: str) -> dict:
    """Return the current mock market price for a given ticker symbol."""
    prices = {
        "AAPL": 189.42,
        "MSFT": 415.23,
        "JPM": 198.76,
        "GS": 452.10,
    }
    price = prices.get(ticker.upper(), 0.0)
    return {"ticker": ticker.upper(), "price": price, "currency": "USD"}


@tool
def calculate_var(notional: float, confidence_level: float = 0.99) -> dict:
    """
    Calculate a simplified Value at Risk (VaR) for a single position.

    Args:
        notional: Position size in USD.
        confidence_level: 0.95 or 0.99 (default 0.99).

    Returns:
        Dict with var_usd and methodology.
    """
    z = 2.326 if confidence_level >= 0.99 else 1.645
    daily_vol = 0.015  # simplified 1.5% daily volatility
    var = notional * z * daily_vol
    return {
        "var_usd": round(var, 2),
        "confidence_level": confidence_level,
        "methodology": "parametric",
        "notional": notional,
    }


@tool
def fetch_regulation_text(reference: str) -> dict:
    """
    Fetch a mock regulatory text snippet by reference code.

    Args:
        reference: Regulation reference, e.g. 'BCBS-239-P4', 'FRTB-SA-1'.
    """
    texts = {
        "BCBS-239-P4": "Principle 4: Banks should have the capability to generate aggregate risk data quickly.",
        "FRTB-SA-1": "The standardised approach (SA) requires banks to calculate capital requirements for market risk.",
        "COREP-C02": "COREP C 02.00 covers own funds requirements under CRR Article 92.",
    }
    text = texts.get(reference.upper(), f"Reference '{reference}' not found in mock database.")
    return {"reference": reference, "text": text}


# ── LangGraph state ───────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ── Graph builder ─────────────────────────────────────────────────────────────

TOOLS = [get_market_price, calculate_var, fetch_regulation_text]


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

TASK = (
    "Please do the following three things:\n"
    "1. Get the current market price of JPM.\n"
    "2. Calculate the 99% VaR for a $1,000,000 position.\n"
    "3. Fetch the regulatory text for BCBS-239-P4.\n"
    "Summarise all three results clearly."
)


def main() -> None:
    print("=" * 60)
    print("Tool-Use Baseline — LangGraph / Ollama")
    print("=" * 60)

    graph = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content=TASK)]})

    final_message = result["messages"][-1]
    output = final_message.content if hasattr(final_message, "content") else str(final_message)

    print("\n── Agent output ──")
    print(output)

    # Score the run
    score = score_run(
        agent_output=output,
        task_description=TASK,
        rubric_path="rubric.yaml",
        token_usage={"input_tokens": 600, "output_tokens": 200},  # approximate
        backend="ollama",
    )
    print("\n── Decision Economics ──")
    print(f"  Quality score : {score['quality_score']:.2f}")
    print(f"  Token cost    : ${score['token_cost_usd']:.6f}")
    print(f"  CPCD          : {score['cpcd']}")
    print(f"  Passed        : {score['passed']}")


if __name__ == "__main__":
    main()
