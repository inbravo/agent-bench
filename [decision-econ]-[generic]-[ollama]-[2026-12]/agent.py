"""
decision-econ / generic / ollama
──────────────────────────────────
Decision Economics harness.

This module is framework-agnostic. It demonstrates:
  1. How to define a rubric YAML and use LLM-as-judge scoring
  2. How to compute CPCD (cost-per-correct-decision)
  3. How to compare multiple agent runs on the same task
  4. How to build a comparison table across frameworks/backends

Run standalone to see the scoring logic:
    python agent.py

Or import the harness into any framework example:
    from [decision-econ]-[generic]-[ollama]-[2026-12].harness import compare_runs
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parents[1]))

from _shared.scorer import score_run


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class AgentRun:
    """Record of a single agent run."""
    run_id: str
    framework: str
    backend: str
    task_description: str
    agent_output: str
    token_usage: dict[str, int]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredRun:
    """AgentRun with decision economics scores attached."""
    run: AgentRun
    quality_score: float
    token_cost_usd: float
    cpcd: float | None
    criteria_scores: dict[str, float]
    passed: bool


# ── Harness ───────────────────────────────────────────────────────────────────

def score_agent_run(
    run: AgentRun,
    rubric_path: str = "rubric.yaml",
    config_path: str | None = None,
) -> ScoredRun:
    """Score a single agent run and return a ScoredRun."""
    result = score_run(
        agent_output=run.agent_output,
        task_description=run.task_description,
        rubric_path=rubric_path,
        token_usage=run.token_usage,
        backend=run.backend,
        config_path=config_path,
    )
    return ScoredRun(
        run=run,
        quality_score=result["quality_score"],
        token_cost_usd=result["token_cost_usd"],
        cpcd=result["cpcd"],
        criteria_scores=result["criteria_scores"],
        passed=result["passed"],
    )


def compare_runs(
    runs: list[AgentRun],
    rubric_path: str = "rubric.yaml",
    config_path: str | None = None,
) -> list[ScoredRun]:
    """Score multiple runs and return them sorted by CPCD (best first)."""
    scored = [score_agent_run(r, rubric_path, config_path) for r in runs]
    # Sort: passed runs first, then by CPCD ascending, then by quality descending
    scored.sort(key=lambda s: (
        not s.passed,
        s.cpcd if s.cpcd is not None else float("inf"),
        -s.quality_score,
    ))
    return scored


def print_comparison_table(scored_runs: list[ScoredRun]) -> None:
    """Print a comparison table to stdout."""
    header = f"{'Run ID':<25} {'Framework':<12} {'Backend':<12} {'Quality':>8} {'Cost USD':>10} {'CPCD':>12} {'Pass':>5}"
    print("=" * len(header))
    print("DECISION ECONOMICS — RUN COMPARISON")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for s in scored_runs:
        cpcd_str = f"${s.cpcd:.6f}" if s.cpcd is not None else "n/a"
        cost_str = f"${s.token_cost_usd:.6f}"
        pass_str = "✓" if s.passed else "✗"
        print(
            f"{s.run.run_id:<25} "
            f"{s.run.framework:<12} "
            f"{s.run.backend:<12} "
            f"{s.quality_score:>8.2f} "
            f"{cost_str:>10} "
            f"{cpcd_str:>12} "
            f"{pass_str:>5}"
        )
    print("=" * len(header))

    if scored_runs:
        best = scored_runs[0]
        if best.passed:
            print(f"\n→ Best CPCD: {best.run.run_id} ({best.run.framework}/{best.run.backend})")
        else:
            print("\n→ No runs passed the quality threshold.")


# ── Demo: synthetic comparison ────────────────────────────────────────────────

DEMO_TASK = "Identify the data lineage gaps for trade T-20241201-0099 per BCBS 239 Principle 6."

DEMO_RUNS = [
    AgentRun(
        run_id="langgraph-ollama-8b",
        framework="langgraph",
        backend="ollama",
        task_description=DEMO_TASK,
        agent_output=(
            "Trade T-20241201-0099 (EUR IRS 5Y) has the following BCBS 239 P6 gap: "
            "the Risk ETL hop from Calypso POSITION to RISK_STAGING is missing its timestamp. "
            "This violates P6 completeness requirements. "
            "Recommendation: investigate the Calypso-to-ETL pipeline and add timestamp logging."
        ),
        token_usage={"input_tokens": 820, "output_tokens": 180},
    ),
    AgentRun(
        run_id="crewai-ollama-8b",
        framework="crewai",
        backend="ollama",
        task_description=DEMO_TASK,
        agent_output=(
            "The BCBS 239 lineage review for T-20241201-0099 found one gap: "
            "missing ETL timestamp at the Risk Staging hop. "
            "The trade is not compliant with BCBS 239 P6 and should not be submitted."
        ),
        token_usage={"input_tokens": 1800, "output_tokens": 400},
    ),
    AgentRun(
        run_id="langgraph-databricks-70b",
        framework="langgraph",
        backend="databricks",
        task_description=DEMO_TASK,
        agent_output=(
            "BCBS 239 Principle 6 Lineage Assessment — Trade T-20241201-0099: "
            "Source system: Calypso. Data hops: 3 total (Calypso POSITION → Risk ETL RISK_STAGING → Risk DWH RISK_POSITIONS). "
            "Gap identified: Risk ETL hop timestamp is null. This breaks the audit chain. "
            "Data quality flag: ETL_TIMESTAMP_MISSING. "
            "Verdict: NOT compliant with BCBS 239 P6. "
            "Recommendation: (1) Fix ETL timestamp logging. (2) Re-run lineage validation. "
            "(3) Re-submit only after all hops show timestamps."
        ),
        token_usage={"input_tokens": 820, "output_tokens": 280},
    ),
]


def main() -> None:
    print("Decision Economics Harness — demo with synthetic runs")
    print("(In production, replace DEMO_RUNS with real agent.py outputs)\n")

    rubric_path = str(Path(__file__).parent / "rubric.yaml")
    config_path = str(Path(__file__).parent / "config.yaml")

    scored = compare_runs(DEMO_RUNS, rubric_path=rubric_path, config_path=config_path)
    print_comparison_table(scored)

    print("\n── Per-criterion breakdown ──")
    for s in scored:
        print(f"\n  {s.run.run_id}:")
        for criterion, score in s.criteria_scores.items():
            print(f"    {criterion:<25} {score:.2f}")


if __name__ == "__main__":
    main()
