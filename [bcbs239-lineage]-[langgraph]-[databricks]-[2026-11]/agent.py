"""
agent.py — BCBS 239 data lineage agent (LangGraph + Databricks).

Identical task and tools to the Ollama variant — only the backend changes.
Every run is auto-traced to MLflow on Databricks; traces appear at the
experiment path configured in config.yaml.

The backend switch is entirely in config.yaml:
    active_backend: "databricks"

Requires:
    DATABRICKS_HOST  — set in .env or environment
    DATABRICKS_TOKEN — set in .env or environment

MLflow experiment:
    /Shared/agentic-ai-lab  (configurable in config.yaml)

Run:
    python agent.py
    python agent.py "Investigate trade T-20241201-0099 and check BCBS 239 compliance"
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

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "_shared"))

import logging_config
logging_config.setup()
log = logging.getLogger("agent.bcbs239-lineage.databricks")

# Re-use all tools and graph logic from the Ollama variant
from _shared.backend import get_llm, get_config
from _shared.scorer  import score_run

# Import the graph builder and task from the sibling Ollama folder
OLLAMA_DIR = (
    Path(__file__).parents[1]
    / "[bcbs239-lineage]-[langgraph]-[ollama]-[2026-11]"
)
sys.path.insert(0, str(OLLAMA_DIR))
from agent import build_graph, DEFAULT_TASK  # noqa: E402


# ── Constants ─────────────────────────────────────────────────────────────────

CONFIG_PATH = str(Path(__file__).parent / "config.yaml")


# ── Agent runner ──────────────────────────────────────────────────────────────

def run_agent(task: str) -> None:
    cfg = get_config(CONFIG_PATH)
    log.info("Backend: %s", cfg.get("active_backend"))
    log.info("Agent task: %s", task[:120])

    print(f"\nTask: {task}")
    print("=" * 65)

    from langchain_core.messages import HumanMessage
    graph  = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content=task)]})

    final  = result["messages"][-1]
    output = final.content if hasattr(final, "content") else str(final)

    print(f"\nAnswer:\n{output}")
    print("=" * 65)

    score = score_run(
        agent_output     = output,
        task_description = task,
        rubric_path      = str(Path(__file__).parent / "rubric.yaml"),
        token_usage      = {"input_tokens": 800, "output_tokens": 300},
        backend          = "databricks",
        config_path      = CONFIG_PATH,
    )

    experiment = cfg.get("databricks", {}).get("mlflow_experiment", "/Shared/agentic-ai-lab")
    print(f"\n  MLflow traces → {experiment}")
    print("\n── Decision Economics ───────────────────────────────")
    print(f"  Quality score : {score['quality_score']:.2f}")
    print(f"  Token cost    : ${score['token_cost_usd']:.6f}")
    print(f"  CPCD          : ${score['cpcd']:.6f}" if score["cpcd"] else "  CPCD          : N/A")
    print(f"  Passed        : {'✓' if score['passed'] else '✗'}")
    print("─" * 52)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK
    run_agent(task)
