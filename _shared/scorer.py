"""
_shared/scorer.py
─────────────────
Decision Economics scorer.

Computes:
    quality_score  = weighted sum of LLM-as-judge criteria (0.0 – 1.0)
    token_cost_usd = input + output token spend in USD
    cpcd           = token_cost_usd / quality_score  (cost-per-correct-decision)

Usage:
    from _shared.scorer import score_run

    result = score_run(
        agent_output="The BCBS 239 lineage for trade T-001 is ...",
        task_description="Identify the data lineage for trade T-001 per BCBS 239.",
        rubric_path="rubric.yaml",
        token_usage={"input_tokens": 512, "output_tokens": 128},
        backend="ollama",
    )
    print(result)
    # {
    #   "quality_score": 0.82,
    #   "token_cost_usd": 0.0,
    #   "cpcd": 0.0,            ← free on Ollama
    #   "criteria_scores": {"correctness": 0.9, "tool_use": 0.8, ...},
    #   "passed": True,
    # }
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def score_run(
    agent_output: str,
    task_description: str,
    rubric_path: str = "rubric.yaml",
    token_usage: dict[str, int] | None = None,
    backend: str = "ollama",
    config_path: str | None = None,
) -> dict[str, Any]:
    """
    Score a single agent run.

    Args:
        agent_output:    The agent's final response text.
        task_description: What the agent was asked to do.
        rubric_path:     Path to the rubric YAML (relative to cwd or absolute).
        token_usage:     {"input_tokens": int, "output_tokens": int}
        backend:         "ollama" or "databricks" — determines cost rates.
        config_path:     Optional path to config.yaml (defaults to cwd/config.yaml).

    Returns:
        Dict with quality_score, token_cost_usd, cpcd, criteria_scores, passed.
    """
    rubric = _load_rubric(rubric_path)
    config = _load_config(config_path)

    criteria_scores = _judge(
        agent_output=agent_output,
        task_description=task_description,
        rubric=rubric,
        backend=backend,
        config=config,
    )

    quality_score = _weighted_sum(criteria_scores, rubric["rubric"]["criteria"])
    token_cost = _compute_token_cost(token_usage or {}, backend, config)
    threshold = rubric["rubric"]["scoring"].get("pass_threshold", 0.70)
    passed = quality_score >= threshold

    cpcd: float | None = None
    if passed and token_cost > 0:
        cpcd = token_cost / quality_score
    elif passed and token_cost == 0:
        cpcd = 0.0  # Ollama: correct answer at zero cost

    return {
        "quality_score": round(quality_score, 4),
        "token_cost_usd": round(token_cost, 8),
        "cpcd": round(cpcd, 8) if cpcd is not None else None,
        "criteria_scores": criteria_scores,
        "passed": passed,
        "backend": backend,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_rubric(rubric_path: str) -> dict[str, Any]:
    path = Path(rubric_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        # Fall back to base rubric in _shared/
        path = Path(__file__).parent / "rubric_base.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def _load_config(config_path: str | None) -> dict[str, Any]:
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    candidates.append(Path.cwd() / "config.yaml")
    candidates.append(Path(__file__).parent / "config.yaml")
    for p in candidates:
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f)
    return {}


def _judge(
    agent_output: str,
    task_description: str,
    rubric: dict[str, Any],
    backend: str,
    config: dict[str, Any],
) -> dict[str, float]:
    """Call the judge LLM and return criterion id → score."""
    criteria = rubric["rubric"]["criteria"]
    prefix = rubric["rubric"].get("judge_prompt_prefix", "")

    criteria_desc = "\n".join(
        f'- {c["id"]}: {c["description"]}'
        for c in criteria
    )
    ids = [c["id"] for c in criteria]

    prompt = (
        f"{prefix}\n\n"
        f"Task: {task_description}\n\n"
        f"Agent output:\n{agent_output}\n\n"
        f"Criteria to score:\n{criteria_desc}\n\n"
        f"Return JSON with keys: {ids}"
    )

    try:
        from _shared.backend import get_llm  # type: ignore
        judge_model_key = config.get("decision_economics", {}).get("judge_model", {}).get(backend, "")
        # Use a fresh LLM configured for the judge model if specified
        llm = get_llm()
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            scores = json.loads(content[start:end])
            return {k: float(scores.get(k, 0.5)) for k in ids}
    except Exception:
        pass

    # Fallback: return neutral scores so caller can still compute CPCD
    return {c["id"]: 0.5 for c in criteria}


def _weighted_sum(scores: dict[str, float], criteria: list[dict[str, Any]]) -> float:
    total = sum(
        c["weight"] * scores.get(c["id"], 0.0)
        for c in criteria
    )
    return min(1.0, max(0.0, total))


def _compute_token_cost(
    token_usage: dict[str, int],
    backend: str,
    config: dict[str, Any],
) -> float:
    de = config.get("decision_economics", {})
    if not de.get("enabled", True):
        return 0.0

    input_rate = de.get("input_token_cost_usd", {}).get(backend, 0.0)
    output_rate = de.get("output_token_cost_usd", {}).get(backend, 0.0)

    input_tokens = token_usage.get("input_tokens", 0)
    output_tokens = token_usage.get("output_tokens", 0)

    return (input_tokens * input_rate) + (output_tokens * output_rate)
