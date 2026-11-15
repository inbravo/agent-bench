"""
test_local.py — Unit and integration tests for the Tool Use / weather-assistant agent.

Description : Verifies tool invocation logic (get_current_weather, convert_temperature),
              MOCK_WEATHER_DB lookups, and the full agent run against a scored rubric.
              Uses importlib to load the agent module from its bracket-named folder path.

Pattern     : Tool Use
Category    : Reasoning Mechanics
Framework   : LangGraph
Backend     : Ollama (local)
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parents[3]))
sys.path.insert(0, str(Path(__file__).parents[3] / "_shared"))

# Use importlib to handle bracket folder names
import importlib.util, types

def _load(rel):
    """Load a module from a path that contains brackets."""
    abs_path = Path(__file__).parents[3] / rel
    spec = importlib.util.spec_from_file_location("_mod", abs_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

agent = _load("reasoning/[tool-use]-[langgraph]-[ollama]/agent.py")

get_current_weather  = agent.get_current_weather
convert_temperature  = agent.convert_temperature
MOCK_WEATHER_DB      = agent.MOCK_WEATHER_DB
build_graph          = agent.build_graph
run_agent            = agent.run_agent
CONFIG_PATH          = agent.CONFIG_PATH


class TestGetCurrentWeather:
    def test_known_city_returns_data(self):
        r = get_current_weather.invoke({"city": "Tokyo"})
        assert "temp_c" in r
        assert r["temp_c"] == 22

    def test_case_insensitive(self):
        assert get_current_weather.invoke({"city": "london"}) == \
               get_current_weather.invoke({"city": "LONDON"})

    def test_unknown_city_returns_error(self):
        r = get_current_weather.invoke({"city": "Atlantis"})
        assert "error" in r

    def test_all_mock_cities_present(self):
        for city in MOCK_WEATHER_DB:
            r = get_current_weather.invoke({"city": city})
            assert "temp_c" in r


class TestConvertTemperature:
    def test_c_to_f(self):
        r = convert_temperature.invoke({"value": 0.0, "from_unit": "C", "to_unit": "F"})
        assert r["converted"] == 32.0

    def test_c_to_k(self):
        r = convert_temperature.invoke({"value": 0.0, "from_unit": "C", "to_unit": "K"})
        assert r["converted"] == 273.15

    def test_f_to_c(self):
        r = convert_temperature.invoke({"value": 32.0, "from_unit": "F", "to_unit": "C"})
        assert r["converted"] == 0.0

    def test_unknown_unit_returns_error(self):
        r = convert_temperature.invoke({"value": 100.0, "from_unit": "X", "to_unit": "C"})
        assert "error" in r

    def test_identity_conversion(self):
        r = convert_temperature.invoke({"value": 25.0, "from_unit": "C", "to_unit": "C"})
        assert r["converted"] == 25.0


class TestRunAgent:
    @patch.object(agent, "build_graph")
    def test_returns_required_keys(self, mock_build):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "messages": [MagicMock(content="Tokyo is 22°C (71.6°F), Clear.")]
        }
        mock_build.return_value = mock_graph
        result = run_agent("What is the weather in Tokyo?", CONFIG_PATH)
        for key in ("task", "answer", "quality_score", "token_cost_usd", "cpcd"):
            assert key in result

    @patch.object(agent, "build_graph")
    def test_quality_score_in_range(self, mock_build):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "messages": [MagicMock(content="Sydney is 25°C, partly cloudy.")]
        }
        mock_build.return_value = mock_graph
        result = run_agent("Weather in Sydney?", CONFIG_PATH)
        assert 0.0 <= result["quality_score"] <= 1.0
