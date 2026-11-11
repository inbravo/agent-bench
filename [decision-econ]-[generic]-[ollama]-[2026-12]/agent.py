"""
agent.py — Decision Economics comparison harness.

Scores and ranks synthetic agent runs from multiple frameworks side-by-side.
Use this to understand which framework produces the best cost-per-correct-decision
(CPCD) for a given BFSI task.

CPCD formula:
    cpcd = token_cost_usd / quality_score

Lower CPCD = better.  On Ollama all runs show $0.00 (local tokens are free).
On Databricks, real token costs make CPCD a live financial decision metric.

Frameworks compared in this demo:
  langgraph / ollama     — baseline (stateful graph, low token overhead)
  crewai / ollama        — multi-agent (higher token usage, richer output)
  langgraph / databricks — production (real cost, MLflow traces)

Run:
    python agent.py

Switch to real runs:
    Replace ScoredRun entries with calls to score_run() after running each example.
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parents[1]))

import logging_config
logging_config.setup()
log = logging.getLogger("agent.decision-econ")

from _shared.scorer import score_run


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class AgentRun:
    """Metadata and raw output from a single agent run."""
    run_id:           str
    framework:        str
    backend:          str
    task_description: str
    agent_output:     str
    token_usage:      dict[str, int]
    metadata:         dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredRun:
    """AgentRun enriched with decision economics metrics."""
    run:            AgentRun
    quality_score:  float
    token_cost_usd: float
    cpcd:           float | None
    criteria_scores: dict[str, float]
    passed:         bool


# ── Scoring helpers ───────────────────────────────────────────────────────────

def score_agent_run(
    run: AgentRun,
    rubric_path: str = "rubric.yaml",
    config_path: str | None = None,
) -> ScoredRun:
    """Score a single AgentRun and return a ScoredRun."""
    result = score_run(
        agent_output     = run.agent_output,
        task_description = run.task_description,
        rubric_path      = rubric_path,
        token_usage      = run.token_usage,
        backend          = run.backend,
        config_path      = config_path,
    )
    return ScoredRun(
        run             = run,
        quality_score   = result["quality_score"],
        token_cost_usd  = result["token_cost_usd"],
        cpcd            = result["cpcd"],
        criteria_scores = result["criteria_scores"],
        passed          = result["passed"],
    )


def compare_runs(
    runs: list[AgentRun],
    rubric_path: str = "rubric.yaml",
    config_path: str | None = None,
) -> list[ScoredRun]:
    """
    Score all runs and return them sorted by CPCD (passed runs first, then ascending CPCD).

    Args:
        runs:        List of AgentRun objects to compare.
        rubric_path: Shared rubric YAML path.
        config_path: Optional config.yaml path.

    Returns:
        Sorted list of ScoredRun objects.
    """
    scored = [score_agent_run(r, rubric_path, config_path) for r in runs]
    return sorted(
        scored,
        key=lambda s: (not s.passed, s.cpcd if s.cpcd is not None else float("inf")),
    )


# ── Output ────────────────────────────────────────────────────────────────────

def print_comparison_table(scored_runs: list[ScoredRun]) -> None:
    """Print a formatted comparison table to stdout."""
    header = (
        f"{'Run ID':<24}  {'Framework':<10}  {'Backend':<11}  "
        f"{'Quality':>7}  {'Cost USD':>10}  {'CPCD':>12}  {'Pass'}"
    )
    sep    = "─" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    for s in scored_runs:
        cpcd_str = f"${s.cpcd:.6f}" if s.cpcd is not None else "N/A"
        passed   = "✓" if s.passed else "✗"
        print(
            f"{s.run.run_id:<24}  {s.run.framework:<10}  {s.run.backend:<11}  "
            f"{s.quality_score:>7.2f}  ${s.token_cost_usd:>9.6f}  "
            f"{cpcd_str:>12}  {passed}"
        )

    print(sep)
    best = next((s for s in scored_runs if s.passed), None)
    if best:
        print(f"\n  Best CPCD: {best.run.run_id}  ({best.run.framework} / {best.run.backend})")
    print()


# ── Demo data ─────────────────────────────────────────────────────────────────

DEMO_TASK = (
    "Investigate data lineage for trade T-20241201-0042 and check BCBS 239 compliance."
)

DEMO_RUNS: list[AgentRun] = [
    AgentRun(
        run_id           = "run-langgraph-ollama",
        framework        = "langgraph",
        backend          = "ollama",
        task_description = DEMO_TASK,
        agent_output     = (
            "Trade T-20241201-0042 sourced from MUREX, loaded to RISK_DW via "
            "murex_to_dw_v3 at 2024-12-01T18:30:00Z. All BCBS 239 lineage fields "
            "present. Data quality: PASS. No compliance gaps found."
        ),
        token_usage = {"input_tokens": 800, "output_tokens": 300},
    ),
    AgentRun(
        run_id           = "run-crewai-ollama",
        framework        = "crewai",
        backend          = "ollama",
        task_description = DEMO_TASK,
        agent_output     = (
            "BCBS 239 Lineage Report — Trade T-20241201-0042\n"
            "Source: MUREX | Destination: RISK_DW | ETL Job: murex_to_dw_v3\n"
            "ETL Timestamp: 2024-12-01T18:30:00Z | Data Quality: PASS\n"
            "Compliance Status: COMPLIANT\n"
            "Violated Principles: None\n"
            "Recommendation: No action required."
        ),
        token_usage = {"input_tokens": 1600, "output_tokens": 600},  # ~2× LangGraph
    ),
    AgentRun(
        run_id           = "run-langgraph-databricks",
        framework        = "langgraph",
        backend          = "databricks",
        task_description = DEMO_TASK,
        agent_output     = (
            "Trade T-20241201-0042: MUREX → RISK_DW, ETL at 18:30 UTC. "
            "BCBS 239 compliant — all required fields populated. "
            "No remediation required."
        ),
        token_usage = {"input_tokens": 800, "output_tokens": 300},
    ),
]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Decision economics comparison — %d runs", len(DEMO_RUNS))

    print("=" * 65)
    print("Decision Economics — Framework Comparison")
    print("Task:", DEMO_TASK)
    print("=" * 65)

    scored = compare_runs(DEMO_RUNS, rubric_path="rubric.yaml")
    print_comparison_table(scored)

    print("Note: Ollama CPCD = $0.00 (local tokens are free).")
    print("      Switch to Databricks backend for real cost comparison.")
