"""
tests/test_local.py — offline unit tests for [tool-use]-[ag2]-[ollama].

No Ollama instance required; tests cover the tool functions and agent
construction only, using importlib to load the bracket-named module path.
"""

import importlib.util
import sys
from pathlib import Path

# ── load agent module from bracket-named path ─────────────────────────────────
_AGENT_PATH = Path(__file__).parents[1] / "agent.py"

def _load():
    spec   = importlib.util.spec_from_file_location("agent_ag2_tool_use", _AGENT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_ag2_tool_use"] = module
    spec.loader.exec_module(module)
    return module

agent_mod = _load()


# ── tool function tests ────────────────────────────────────────────────────────

class TestGetCurrentWeather:
    def test_known_city_returns_data(self):
        result = agent_mod.get_current_weather("tokyo")
        assert result["temp_c"] == 22
        assert result["condition"] == "Clear"
        assert result["city"] == "tokyo"

    def test_case_insensitive(self):
        assert agent_mod.get_current_weather("LONDON")["temp_c"] == 12
        assert agent_mod.get_current_weather("New York")["temp_c"] == 18

    def test_unknown_city_returns_error(self):
        result = agent_mod.get_current_weather("atlantis")
        assert "error" in result

    def test_all_mock_cities_present(self):
        for city in ("london", "new york", "tokyo", "sydney", "bangalore"):
            r = agent_mod.get_current_weather(city)
            assert "error" not in r, f"Missing city: {city}"


class TestConvertTemperature:
    def test_c_to_f(self):
        result = agent_mod.convert_temperature(0.0, "C", "F")
        assert result["converted"] == 32.0
        assert result["unit"] == "F"

    def test_c_to_k(self):
        result = agent_mod.convert_temperature(0.0, "C", "K")
        assert abs(result["converted"] - 273.15) < 0.01

    def test_f_to_c(self):
        result = agent_mod.convert_temperature(32.0, "F", "C")
        assert abs(result["converted"] - 0.0) < 0.01

    def test_tokyo_weather_in_f(self):
        tokyo  = agent_mod.get_current_weather("tokyo")
        result = agent_mod.convert_temperature(tokyo["temp_c"], "C", "F")
        # 22 C = 71.6 F
        assert abs(result["converted"] - 71.6) < 0.1

    def test_unknown_unit_returns_error(self):
        result = agent_mod.convert_temperature(100, "X", "F")
        assert "error" in result


# ── agent construction test (no LLM call) ─────────────────────────────────────

class TestBuildAgents:
    def test_build_agents_returns_pair(self, tmp_path):
        """build_agents() should return (AssistantAgent, UserProxyAgent) without
        making any network calls — it only configures the agents."""
        import autogen
        cfg_text = """
example_name: tool-use-weather-ag2
llm_backend:  ollama
llm_model:    llama3.1:8b
ollama_host:  http://localhost:11434
scorer:
  judge_model: llama3.1:8b
  input_rate:  0.0
  output_rate: 0.0
  rubric_path: rubric.yaml
"""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(cfg_text)

        assistant, proxy = agent_mod.build_agents(str(cfg_file))
        assert isinstance(assistant, autogen.AssistantAgent)
        assert isinstance(proxy,     autogen.UserProxyAgent)
        assert assistant.name == "weather_assistant"
        assert proxy.name     == "user_proxy"

    def test_tools_registered(self, tmp_path):
        """Both tools should appear in the assistant's llm_config function list."""
        cfg_text = """
example_name: tool-use-weather-ag2
llm_backend:  ollama
llm_model:    llama3.1:8b
ollama_host:  http://localhost:11434
scorer:
  judge_model: llama3.1:8b
  input_rate:  0.0
  output_rate: 0.0
  rubric_path: rubric.yaml
"""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(cfg_text)

        assistant, _ = agent_mod.build_agents(str(cfg_file))
        functions = assistant.llm_config.get("functions") or []
        names = {f["name"] for f in functions}
        assert "get_current_weather"  in names
        assert "convert_temperature"  in names
