"""
bcbs239-lineage / langgraph / databricks
─────────────────────────────────────────
BCBS 239 Data Lineage Agent — Databricks backend.

Same agent logic as the Ollama version, now running on:
  - Databricks Foundation Model APIs (Llama 3.1 70B)
  - MLflow 3 auto-tracing (trace every tool call and LLM invoke)
  - MLflow experiment: /Shared/agentic-ai-lab/bcbs239

What's different from the Ollama version:
  - `active_backend: "databricks"` in config.yaml
  - MLflow auto-tracing enabled in backend.py → all runs saved to Databricks
  - Token cost is real (not zero) → CPCD is meaningful
  - Use this for client demos and regulatory evidence

Setup:
  1. Copy .env.example to .env
  2. Set DATABRICKS_HOST and DATABRICKS_TOKEN
  3. pip install langchain-databricks mlflow langgraph pyyaml

Run:
    python agent.py

Traces will appear in your Databricks MLflow experiment:
    https://your-workspace.azuredatabricks.net/ml/experiments/...
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

# Re-use all tool definitions and graph from the Ollama version
# The only difference is the backend — config.yaml switches it
sys.path.insert(0, str(Path(__file__).parent.parent / "[bcbs239-lineage]-[langgraph]-[ollama]-[2026-11]"))

from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from _shared.backend import get_llm, get_config
from _shared.scorer import score_run

# Import tools from the Ollama version (same domain logic, different backend)
from agent import (  # noqa: E402  (imported after sys.path manipulation)
    LINEAGE_DB,
    check_bcbs239_compliance,
    get_bcbs239_principle,
    get_trade_lineage,
    TASK,
)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


TOOLS = [get_trade_lineage, check_bcbs239_compliance, get_bcbs239_principle]


def build_graph():
    # get_llm() reads THIS folder's config.yaml → active_backend: databricks
    llm = get_llm(config_path=str(Path(__file__).parent / "config.yaml"))
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


def main() -> None:
    cfg = get_config(str(Path(__file__).parent / "config.yaml"))
    model = cfg["databricks"]["model"]

    print("=" * 60)
    print("BCBS 239 Lineage Agent — LangGraph / Databricks")
    print(f"Model : {model}")
    print(f"Traces: {cfg['databricks']['mlflow_experiment']}")
    print("=" * 60)

    graph = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content=TASK)]})

    final = result["messages"][-1]
    output = final.content if hasattr(final, "content") else str(final)

    # Approximate token usage — MLflow trace has the real numbers
    token_usage = {"input_tokens": 900, "output_tokens": 350}

    print("\n── Lineage Report ──")
    print(output)

    score = score_run(
        agent_output=output,
        task_description=TASK,
        rubric_path=str(Path(__file__).parent / "rubric.yaml"),
        token_usage=token_usage,
        backend="databricks",
        config_path=str(Path(__file__).parent / "config.yaml"),
    )
    print("\n── Decision Economics ──")
    print(f"  Quality score : {score['quality_score']:.2f}")
    print(f"  Token cost    : ${score['token_cost_usd']:.6f}")
    print(f"  CPCD          : ${score['cpcd']:.6f}" if score["cpcd"] else "  CPCD          : n/a (run failed)")
    print(f"  Passed        : {score['passed']}")
    print(f"\nMLflow traces saved to: {cfg['databricks']['mlflow_experiment']}")


if __name__ == "__main__":
    main()
