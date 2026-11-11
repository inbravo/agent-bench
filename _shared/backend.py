"""
_shared/backend.py
──────────────────
Backend-agnostic LLM client factory.
Reads config.yaml from the calling example's directory (or falls back to _shared/config.yaml).
Returns a ChatOpenAI-compatible client regardless of backend.

Usage:
    from _shared.backend import get_llm, get_config
    llm = get_llm()          # reads config.yaml in cwd
    cfg = get_config()       # returns the full config dict
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def get_config(config_path: str | None = None) -> dict[str, Any]:
    """Load config.yaml, falling back to _shared/config.yaml if not found in cwd."""
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    candidates.append(Path.cwd() / "config.yaml")
    candidates.append(Path(__file__).parent / "config.yaml")

    for path in candidates:
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f)

    raise FileNotFoundError("No config.yaml found. Run from an example directory.")


def get_llm(config_path: str | None = None):
    """
    Return a LangChain-compatible chat LLM configured for the active backend.

    Returns:
        ChatOllama or ChatDatabricks instance, both implementing the
        BaseChatModel interface so agent code is backend-agnostic.
    """
    cfg = get_config(config_path)
    backend = cfg.get("active_backend", "ollama")

    if backend == "ollama":
        return _make_ollama_llm(cfg["ollama"])
    elif backend == "databricks":
        return _make_databricks_llm(cfg["databricks"])
    else:
        raise ValueError(f"Unknown backend: {backend!r}. Use 'ollama' or 'databricks'.")


def _make_ollama_llm(ollama_cfg: dict[str, Any]):
    """Create a ChatOllama instance."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as e:
        raise ImportError(
            "langchain-ollama is required for the ollama backend. "
            "Run: pip install langchain-ollama"
        ) from e

    return ChatOllama(
        base_url=ollama_cfg.get("base_url", "http://localhost:11434"),
        model=ollama_cfg.get("model", "llama3.1:8b"),
        temperature=ollama_cfg.get("temperature", 0.0),
        timeout=ollama_cfg.get("timeout_seconds", 120),
    )


def _make_databricks_llm(db_cfg: dict[str, Any]):
    """Create a ChatDatabricks instance with MLflow auto-tracing enabled."""
    try:
        import mlflow
        from langchain_databricks import ChatDatabricks
    except ImportError as e:
        raise ImportError(
            "langchain-databricks and mlflow are required for the databricks backend. "
            "Run: pip install langchain-databricks mlflow"
        ) from e

    host = _resolve_env(db_cfg.get("host", "${DATABRICKS_HOST}"))
    token = _resolve_env(db_cfg.get("token", "${DATABRICKS_TOKEN}"))

    if not host or not token:
        raise EnvironmentError(
            "DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env or environment. "
            "Copy .env.example to .env and fill in your values."
        )

    # Enable MLflow tracing automatically for Databricks runs
    mlflow.langchain.autolog()
    experiment = db_cfg.get("mlflow_experiment", "/Shared/agentic-ai-lab")
    mlflow.set_experiment(experiment)

    return ChatDatabricks(
        endpoint=db_cfg.get("model", "databricks-meta-llama-3-1-70b-instruct"),
        temperature=db_cfg.get("temperature", 0.0),
        host=host,
        token=token,
    )


def _resolve_env(value: str) -> str:
    """Expand ${VAR} placeholders using environment variables."""
    if value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        return os.environ.get(var_name, "")
    return value
