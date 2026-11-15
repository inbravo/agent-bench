"""
agent.py — CPCD Decision Economics pattern: multi-framework comparison.

Description : Benchmarks multiple agentic frameworks side-by-side on the same
              task and rubric, computing CPCD (token_cost_usd / quality_score)
              for each candidate. Identifies the most cost-efficient framework
              by running LangGraph and CrewAI agents sequentially and comparing
              their quality scores, token costs, and resulting CPCD values.

CPCD        = token_cost_usd / quality_score

Pattern     : CPCD / Decision Economics
Category    : Decision Economics
Framework   : Multi (LangGraph + CrewAI)
Backend     : Ollama (local)
"""

# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import sys
import logging
from pathlib import Path

# ── path setup ────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[2] / "_shared"))

# ── shared setup ──────────────────────────────────────
import logging_config
logging_config.setup()

from backend import get_config

# ── logging ───────────────────────────────────────────
log = logging.getLogger("agent.cpcd.multi-framework")

# ── constants ─────────────────────────────────────────
CONFIG_PATH  = str(Path(__file__).parent / "config.yaml")
DEFAULT_TASK = "Find a beginner-friendly book on machine learning. Check availability. Suggest alternatives if not available."

CANDIDATES = [
    {
        "label":       "LangGraph · ReAct · Ollama",
        "agent_path":  str(Path(__file__).parents[2] / "reasoning" / "[react]-[langgraph]-[ollama]" / "agent.py"),
        "config_path": str(Path(__file__).parents[2] / "reasoning" / "[react]-[langgraph]-[ollama]" / "config.yaml"),
    },
    {
        "label":       "CrewAI · FW-Swap · Ollama",
        "agent_path":  str(Path(__file__).parents[2] / "topology" / "[fw-swap]-[crewai]-[ollama]" / "agent.py"),
        "config_path": str(Path(__file__).parents[2] / "topology" / "[fw-swap]-[crewai]-[ollama]" / "config.yaml"),
    },
]


def _load_runner(agent_path: str):
    """Dynamically load run_agent from an agent.py file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_candidate", agent_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_agent


def run_comparison(task: str, config_path: str = CONFIG_PATH) -> list:
    """Run all candidates and return results sorted by CPCD (ascending)."""
    log.info("─── cpcd / multi-framework comparison starting ───")
    log.info("task: %s", task)

    results = []

    for candidate in CANDIDATES:
        label = candidate["label"]
        log.info("── running: %s", label)
        try:
            run_agent = _load_runner(candidate["agent_path"])
            scored    = run_agent(task=task, config_path=candidate["config_path"])
            scored["label"] = label
            results.append(scored)
            log.info(
                "%s → score=%.3f  cost=$%.6f  cpcd=$%.6f",
                label, scored["quality_score"], scored["token_cost_usd"], scored["cpcd"],
            )
        except Exception as exc:
            log.warning("SKIPPED %s — %s", label, exc)
            results.append({
                "label": label, "task": task, "answer": "",
                "quality_score": 0.0, "token_cost_usd": 0.0,
                "cpcd": float("inf"), "error": str(exc),
            })

    results.sort(key=lambda r: r["cpcd"])
    log.info("─── cpcd / multi-framework comparison done ───")
    return results


def _print_table(results: list) -> None:
    col = {"rank": 4, "label": 38, "score": 8, "cost": 14, "cpcd": 14}
    header = (
        f"{'#':<{col['rank']}} {'Framework':<{col['label']}} "
        f"{'Score':>{col['score']}} {'Cost (USD)':>{col['cost']}} {'CPCD (USD)':>{col['cpcd']}}"
    )
    div = "─" * len(header)
    print(f"\n{div}")
    print(" CPCD Pareto Comparison — lower CPCD = better value")
    print(div)
    print(header)
    print(div)
    for rank, r in enumerate(results, 1):
        cpcd_s  = "inf" if r["cpcd"] == float("inf") else f"${r['cpcd']:.6f}"
        tag     = " FAILED" if "error" in r else ""
        print(
            f"{rank:<{col['rank']}} {(r['label']+tag):<{col['label']}} "
            f"{r['quality_score']:>{col['score']}.3f} "
            f"${r['token_cost_usd']:>{col['cost']-1}.6f} "
            f"{cpcd_s:>{col['cpcd']}}"
        )
    print(div)
    print("CPCD = token_cost_usd / quality_score")
    print("Ollama local: cost = $0 -> CPCD = $0; rank by quality_score.\n")


if __name__ == "__main__":
    task    = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK
    results = run_comparison(task)
    _print_table(results)
