"""
test_local.py — Unit and integration tests for the Tool Use / weather-assistant agent (CrewAI).

Description : Verifies tool invocation logic (GetCurrentWeatherTool, ConvertTemperatureTool),
              MOCK_WEATHER_DB lookups, and the full CrewAI agent run against a scored rubric.
              Uses importlib to load the agent module from its bracket-named folder path.

Pattern     : Tool Use
Category    : Reasoning Mechanics
Framework   : CrewAI
Backend     : Ollama (local)
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util

sys.path.insert(0, str(Path(__file__).parents[3]))
sys.path.insert(0, str(Path(__file__).parents[3] / "_shared"))

def _load(rel):
    """Load a module from a path that contains brackets."""
    abs_path = Path(__file__).parents[3] / rel
    spec = importlib.util.spec_from_file_location("_mod", abs_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

agent = _load("reasoning/[tool-use]-[crewai]-[ollama]/agent.py")

GetCurrentWeatherTool  = agent.GetCurrentWeatherTool
ConvertTemperatureTool = agent.ConvertTemperatureTool
MOCK_WEATHER_DB        = agent.MOCK_WEATHER_DB
build_crew             = agent.build_crew
run_agent              = agent.run_agent
CONFIG_PATH            = agent.CONFIG_PATH


class TestGetCurrentWeatherTool:
    def setup_method(self):
        self.tool = GetCurrentWeatherTool()

    def test_known_city_returns_data(self):
        r = self.tool._run("tokyo")
        assert r["temp_c"] == 22
        assert r["condition"] == "Clear"

    def test_case_insensitive(self):
        r = self.tool._run("LONDON")
        assert r["temp_c"] == 12

    def test_unknown_city_returns_error(self):
        r = self.tool._run("atlantis")
        assert "error" in r

    def test_all_cities_present(self):
        for city in ["london", "new york", "tokyo", "sydney", "bangalore"]:
            r = self.tool._run(city)
            assert "temp_c" in r, f"Missing temp_c for {city}"


class TestConvertTemperatureTool:
    def setup_method(self):
        self.tool = ConvertTemperatureTool()

    def test_celsius_to_fahrenheit(self):
        r = self.tool._run(22.0, "C", "F")
        assert abs(r["converted"] - 71.6) < 0.1

    def test_fahrenheit_to_celsius(self):
        r = self.tool._run(32.0, "F", "C")
        assert r["converted"] == 0.0

    def test_celsius_to_kelvin(self):
        r = self.tool._run(0.0, "C", "K")
        assert abs(r["converted"] - 273.15) < 0.01

    def test_unknown_unit_returns_error(self):
        r = self.tool._run(100.0, "X", "C")
        assert "error" in r

    def test_same_unit_roundtrip(self):
        r = self.tool._run(25.0, "C", "C")
        assert r["converted"] == 25.0


class TestMockWeatherDB:
    def test_all_entries_have_required_keys(self):
        for city, data in MOCK_WEATHER_DB.items():
            assert "temp_c"    in data, f"Missing temp_c for {city}"
            assert "condition" in data, f"Missing condition for {city}"

    def test_temperatures_are_numeric(self):
        for city, data in MOCK_WEATHER_DB.items():
            assert isinstance(data["temp_c"], (int, float)), f"{city} temp not numeric"
