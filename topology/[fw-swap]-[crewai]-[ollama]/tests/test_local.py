"""
test_local.py — Unit and integration tests for the Framework Swap / blog-crew agent.

Description : Verifies FetchFactsTool lookups against MOCK_FACTS_DB, crew construction
              via build_crew, and the full agent run against a scored rubric. Uses
              importlib to load the agent module from its bracket-named folder path.

Pattern     : Framework Swap
Category    : Agent Topology
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
    abs_path = Path(__file__).parents[3] / rel
    spec = importlib.util.spec_from_file_location("_mod", abs_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

agent = _load("topology/[fw-swap]-[crewai]-[ollama]/agent.py")

FetchFactsTool  = agent.FetchFactsTool
MOCK_FACTS_DB   = agent.MOCK_FACTS_DB
build_crew      = agent.build_crew
run_agent       = agent.run_agent
CONFIG_PATH     = agent.CONFIG_PATH


class TestFetchFactsTool:
    def setup_method(self):
        self.tool = FetchFactsTool()

    def test_known_topic_returns_list(self):
        r = self.tool._run("walking")
        assert isinstance(r, list) and len(r) > 0

    def test_case_insensitive(self):
        assert self.tool._run("walking") == self.tool._run("WALKING")

    def test_unknown_topic_returns_message(self):
        r = self.tool._run("quantum physics")
        assert len(r) == 1 and "No facts found" in r[0]

    def test_all_mock_topics_have_entries(self):
        for topic in MOCK_FACTS_DB:
            r = self.tool._run(topic)
            assert len(r) >= 1


class TestBuildCrew:
    def test_crew_has_three_agents(self):
        crew = build_crew({"llm_model": "llama3.1:8b", "ollama_host": "http://localhost:11434"})
        assert len(crew.agents) == 3

    def test_crew_has_three_tasks(self):
        crew = build_crew({"llm_model": "llama3.1:8b", "ollama_host": "http://localhost:11434"})
        assert len(crew.tasks) == 3

    def test_researcher_has_fetch_facts_tool(self):
        crew = build_crew({"llm_model": "llama3.1:8b", "ollama_host": "http://localhost:11434"})
        tool_names = [t.name for t in crew.agents[0].tools]
        assert "fetch_facts" in tool_names


class TestRunAgent:
    @patch.object(agent, "build_crew")
    def test_returns_required_keys(self, mock_build):
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = "A polished blog post about walking."
        mock_build.return_value = mock_crew
        result = run_agent("Write a blog post about walking.", CONFIG_PATH)
        for k in ("task", "answer", "quality_score", "token_cost_usd", "cpcd"):
            assert k in result

    @patch.object(agent, "build_crew")
    def test_quality_score_in_range(self, mock_build):
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = "Blog post complete."
        mock_build.return_value = mock_crew
        result = run_agent("Write about exercise.", CONFIG_PATH)
        assert 0.0 <= result["quality_score"] <= 1.0
