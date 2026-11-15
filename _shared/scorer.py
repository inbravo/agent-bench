"""
_shared/scorer.py — Decision Economics scorer.

Computes three metrics for every agent run:

    quality_score  = weighted sum of LLM-as-judge criteria  (0.0 – 1.0)
    token_cost_usd = input + output token spend in USD
    cpcd           = token_cost_usd / quality_score   (cost-per-correct-decision)

CPCD is $0.00 on Ollama (local tokens are free) and meaningful on Databricks,
where real token costs make framework choice a financial decision.

Usage:
    from _shared.scorer import score_run

    result = score_run(
        agent_output     = "The BCBS 239 lineage for trade T-001 is ...",
        task_description = "Identify the data lineage for trade T-001 per BCBS 239.",
        rubric_path      = "rubric.yaml",
        token_usage      = {"input_tokens": 512, "output_tokens": 128},
        backend          = "ollama",
    )
    # → {"quality_score": 0.82, "token_cost_usd": 0.0, "cpcd": 0.0, "passed": True, ...}
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import logging_config

logging_config.setup()
log = logging.getLogger("agent.scorer")


# ── Public API ────────────────────────────────────────────────────────────────

def score_run(
    agent_output: str | None = None,
    task_description: str | None = None,
    rubric_path: str = "rubric.yaml",
    token_usage: dict[str, int] | None = None,
    backend: str = "ollama",
    config_path: str | None = None,
    # Convenience aliases used by agent.py call sites
    answer: str | None = None,
    task: str | None = None,
) -> dict[str, Any]:
    """
    Score a single agent run against a rubric and return decision economics.

    Args:
        agent_output / answer:          The agent's final response text.
        task_description / task:        What the agent was asked to do.
        rubric_path:                    Path to rubric YAML (relative to cwd or absolute).
        token_usage:                    {"input_tokens": int, "output_tokens": int}
        backend:                        "ollama" or "databricks" — determines cost rates.
        config_path:                    Optional path to config.yaml.

    Returns:
        Dict with quality_score, token_cost_usd, cpcd, criteria_scores, passed, answer.
    """
    # Accept both naming conventions
    agent_output     = agent_output     or answer          or ""
    task_description = task_description or task            or ""

    # Resolve rubric_path relative to the config file's directory when possible
    if rubric_path == "rubric.yaml" and config_path:
        rubric_path = str(Path(config_path).parent / "rubric.yaml")
    rubric = _load_rubric(rubric_path)
    config = _load_config(config_path)

    criteria_scores = _judge(
        agent_output     = agent_output,
        task_description = task_description,
        rubric           = rubric,
        backend          = backend,
        config           = config,
    )

    quality_score = _weighted_sum(criteria_scores, rubric["criteria"])
    token_cost    = _compute_token_cost(token_usage or {}, backend, config)
    threshold     = rubric.get("scoring", {}).get("pass_threshold", 0.70)
    passed        = quality_score >= threshold

    cpcd: float | None = None
    if passed and token_cost > 0:
        cpcd = token_cost / quality_score
    elif passed and token_cost == 0:
        cpcd = 0.0  # Ollama: correct answer at zero monetary cost

    log.info(
        "Score: quality=%.3f  cost=$%.8f  cpcd=%s  passed=%s  backend=%s",
        quality_score, token_cost, cpcd, passed, backend,
    )

    return {
        "answer":         agent_output,
        "quality_score":  round(quality_score, 4),
        "token_cost_usd": round(token_cost, 8),
        "cpcd":           round(cpcd, 8) if cpcd is not None else None,
        "criteria_scores": criteria_scores,
        "passed":         passed,
        "backend":        backend,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_rubric(rubric_path: str) -> dict[str, Any]:
    path = Path(rubric_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        path = Path(__file__).parent / "rubric_base.yaml"
    log.debug("Loading rubric from %s", path)
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
    """Call the judge LLM and return criterion id → score (0.0 – 1.0)."""
    criteria     = rubric["criteria"]
    prefix       = rubric.get("judge_prompt_prefix", "")
    ids          = [c["name"] for c in criteria]
    criteria_desc = "\n".join(
        f'- {c["name"]}: {c["description"]}'
        for c in criteria
    )

    prompt = (
        f"{prefix}\n\n"
        f"Task: {task_description}\n\n"
        f"Agent output:\n{agent_output}\n\n"
        f"Criteria to score:\n{criteria_desc}\n\n"
        f"Return JSON with keys: {ids}"
    )

    try:
        from backend import get_llm  # type: ignore
        llm      = get_llm()
        response = llm.invoke(prompt)
        content  = response.content if hasattr(response, "content") else str(response)
        start    = content.find("{")
        end      = content.rfind("}") + 1
        if start >= 0 and end > start:
            scores = json.loads(content[start:end])
            log.debug("Judge scores: %s", scores)
            return {k: float(scores.get(k, 0.5)) for k in ids}
    except Exception as exc:
        log.warning("Judge LLM failed (%s) — using neutral fallback scores", exc)

    # Fallback: neutral scores so caller can still compute CPCD
    return {c["name"]: 0.5 for c in criteria}


def _weighted_sum(scores: dict[str, float], criteria: list[dict[str, Any]]) -> float:
    total = sum(
        c["weight"] * scores.get(c["name"], 0.0)
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

    input_rate  = de.get("input_token_cost_usd",  {}).get(backend, 0.0)
    output_rate = de.get("output_token_cost_usd", {}).get(backend, 0.0)
    input_toks  = token_usage.get("input_tokens",  0)
    output_toks = token_usage.get("output_tokens", 0)

    cost = (input_toks * input_rate) + (output_toks * output_rate)
    log.debug(
        "Token cost: input=%d×%.8f + output=%d×%.8f = $%.8f",
        input_toks, input_rate, output_toks, output_rate, cost,
    )
    return cost
