"""
tests/test_local.py — unit tests for the ollama-harness research-swarm agent.

Description : Verifies tool functions, mock database, and fallback loop logic
              without requiring a live Ollama server or the ollama-harness
              package. The native Pipeline path is an integration test and is
              not covered here.

Pattern     : Research Swarm / Self-Critique Loop
Category    : Self-Improvement
Framework   : ollama-harness
Backend     : Ollama (local)
"""

import importlib.util
from pathlib import Path


def _load():
    p    = Path(__file__).parents[1] / "agent.py"
    spec = importlib.util.spec_from_file_location("oh_weather_agent", p)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load()


# ── tool function tests ───────────────────────────────

def test_get_weather_tokyo():
    r = mod.get_current_weather("tokyo")
    assert r["temp_c"] == 22
    assert r["condition"] == "Clear"


def test_get_weather_case_insensitive():
    r = mod.get_current_weather("BANGALORE")
    assert r["temp_c"] == 28


def test_get_weather_unknown():
    r = mod.get_current_weather("narnia")
    assert "error" in r


def test_convert_c_to_f_freezing():
    r = mod.convert_temperature(0.0, "C", "F")
    assert r["converted"] == 32.0


def test_convert_c_to_f_boiling():
    r = mod.convert_temperature(100.0, "C", "F")
    assert r["converted"] == 212.0


def test_convert_bad_unit():
    r = mod.convert_temperature(10.0, "Z", "C")
    assert "error" in r


# ── mock db completeness ──────────────────────────────

def test_mock_db_cities():
    for city in ("london", "new york", "tokyo", "sydney", "bangalore"):
        assert city in mod.MOCK_WEATHER_DB


# ── build_pipeline returns a tuple ───────────────────

def test_build_pipeline_returns_tuple():
    cfg    = {"llm_model": "llama3.1:8b", "ollama_host": "http://localhost:11434"}
    result = mod._build_pipeline(cfg)
    assert isinstance(result, tuple)
    assert len(result) == 2
    # mode is either "native" or "fallback"
    assert result[1] in ("native", "fallback")
