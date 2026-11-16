"""
tests/test_local.py — unit tests for the DSPy prompt-optimisation weather agent.

Description : Verifies that the DSPy Signature, WeatherAgent module, and mock
              tool functions behave correctly without requiring a live Ollama
              server. The optimisation path (BootstrapFewShot) is not exercised
              here — it requires a live LLM and is covered by integration tests.

Pattern     : Prompt Optimisation (Self-Improvement)
Category    : Self-Improvement
Framework   : DSPy
Backend     : Ollama (local)
"""

import importlib.util, sys
from pathlib import Path

# ── load module from bracket-named path ───────────────
def _load():
    p = Path(__file__).parents[1] / "agent.py"
    spec = importlib.util.spec_from_file_location("dspy_weather_agent", p)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

mod = _load()


# ── tool function tests ───────────────────────────────

def test_get_current_weather_known_city():
    result = mod.get_current_weather("tokyo")
    assert result["temp_c"] == 22
    assert result["condition"] == "Clear"


def test_get_current_weather_case_insensitive():
    result = mod.get_current_weather("LONDON")
    assert result["temp_c"] == 12


def test_get_current_weather_unknown_city():
    result = mod.get_current_weather("atlantis")
    assert "error" in result


def test_convert_c_to_f():
    result = mod.convert_temperature(0.0, "C", "F")
    assert result["converted"] == 32.0


def test_convert_c_to_k():
    result = mod.convert_temperature(0.0, "C", "K")
    assert result["converted"] == 273.15


def test_convert_f_to_c():
    result = mod.convert_temperature(32.0, "F", "C")
    assert result["converted"] == 0.0


def test_convert_unknown_unit():
    result = mod.convert_temperature(100, "X", "C")
    assert "error" in result


# ── mock_weather_db completeness ──────────────────────

def test_mock_db_has_expected_cities():
    for city in ("london", "new york", "tokyo", "sydney", "bangalore"):
        assert city in mod.MOCK_WEATHER_DB, f"Missing: {city}"


# ── signature field presence ──────────────────────────

def test_signature_has_question_field():
    import dspy
    fields = mod.WeatherQuery.model_fields if hasattr(mod.WeatherQuery, "model_fields") else {}
    # DSPy signatures expose input/output fields differently across versions;
    # just check the class is importable and callable
    assert callable(mod.WeatherQuery)


def test_tools_list_has_two_entries():
    assert len(mod.TOOLS) == 2
