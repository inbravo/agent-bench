"""
_shared/backend.py — Backend-agnostic LLM client factory.

Reads config.yaml from the calling example's directory (or falls back to
_shared/config.yaml).  Returns a ChatOpenAI-compatible client regardless of
which backend is active.

Supported backends:
  ollama      — local Ollama server (default)
  databricks  — Databricks Model Serving + MLflow auto-tracing

Usage:
    from _shared.backend import get_llm, get_config

    llm = get_llm()       # reads config.yaml in cwd
    cfg = get_config()    # returns the full config dict

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
import os
import sys
from pathlib import Path
from typing import Any

import yaml

# Allow importing logging_config from _shared/
sys.path.insert(0, str(Path(__file__).parent))
import logging_config

logging_config.setup()
log = logging.getLogger("agent.backend")


# ── Public API ────────────────────────────────────────────────────────────────

def get_config(config_path: str | None = None) -> dict[str, Any]:
    """
    Load config.yaml, falling back to _shared/config.yaml if not found in cwd.

    Args:
        config_path: Explicit path to a config.yaml, or None to auto-discover.

    Returns:
        Parsed config dict.
    """
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    candidates.append(Path.cwd() / "config.yaml")
    candidates.append(Path(__file__).parent / "config.yaml")

    for path in candidates:
        if path.exists():
            log.debug("Loading config from %s", path)
            with open(path) as f:
                return yaml.safe_load(f)

    raise FileNotFoundError(
        "No config.yaml found. Run from an example directory, "
        "or pass config_path explicitly."
    )


def get_llm(config_path: str | None = None):
    """
    Return a LangChain-compatible chat LLM configured for the active backend.

    Config keys (flat structure in config.yaml):
        llm_backend:  ollama | databricks   (default: ollama)
        llm_model:    e.g. llama3.1:8b
        ollama_host:  http://localhost:11434

    Returns:
        ChatOllama or ChatDatabricks — both implement BaseChatModel so agent
        code is fully backend-agnostic.
    """
    cfg     = get_config(config_path)
    backend = cfg.get("llm_backend", cfg.get("active_backend", "ollama"))
    log.info("Backend selected: %s", backend)

    if backend == "ollama":
        return _make_ollama_llm(cfg)
    elif backend == "databricks":
        return _make_databricks_llm(cfg)
    else:
        raise ValueError(
            f"Unknown backend: {backend!r}. "
            "Supported values: 'ollama', 'databricks'."
        )


# ── Backend factories ─────────────────────────────────────────────────────────

def _make_ollama_llm(cfg: dict[str, Any]):
    """Create a ChatOllama instance from flat config keys."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as e:
        raise ImportError(
            "langchain-ollama is required for the ollama backend.\n"
            "Run: pip install langchain-ollama"
        ) from e

    model = cfg.get("llm_model", "llama3.1:8b")
    log.info("Ollama model: %s", model)

    return ChatOllama(
        base_url   = cfg.get("ollama_host", "http://localhost:11434"),
        model      = model,
        temperature= cfg.get("temperature", 0.0),
        timeout    = cfg.get("timeout_seconds", 120),
    )


def _make_databricks_llm(cfg: dict[str, Any]):
    """Create a ChatDatabricks instance with MLflow auto-tracing enabled."""
    try:
        import mlflow
        from langchain_databricks import ChatDatabricks
    except ImportError as e:
        raise ImportError(
            "langchain-databricks and mlflow are required for the databricks backend.\n"
            "Run: pip install langchain-databricks mlflow"
        ) from e

    host  = _resolve_env(cfg.get("databricks_host",  "${DATABRICKS_HOST}"))
    token = _resolve_env(cfg.get("databricks_token", "${DATABRICKS_TOKEN}"))

    if not host or not token:
        raise EnvironmentError(
            "DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env or environment.\n"
            "Copy .env.example to .env and fill in your values."
        )

    experiment = cfg.get("mlflow_experiment", "/Shared/agent-bench")
    mlflow.langchain.autolog()
    mlflow.set_experiment(experiment)
    log.info("Databricks model: %s  experiment: %s", cfg.get("llm_model"), experiment)

    return ChatDatabricks(
        endpoint   = cfg.get("llm_model", "databricks-meta-llama-3-1-70b-instruct"),
        temperature= cfg.get("temperature", 0.0),
        host       = host,
        token      = token,
    )


# ── Utilities ─────────────────────────────────────────────────────────────────

def _resolve_env(value: str) -> str:
    """Expand ${VAR} placeholders using environment variables."""
    if value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        return os.environ.get(var_name, "")
    return value
