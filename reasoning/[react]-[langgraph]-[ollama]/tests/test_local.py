"""
test_local.py — Unit and integration tests for the ReAct / book-finder agent.

Description : Verifies tool invocation logic (search_books, check_availability,
              get_similar_books), MOCK_BOOK_CATALOGUE lookups, and the full agent
              run against a scored rubric. Uses importlib to load the agent module
              from its bracket-named folder path.

Pattern     : ReAct (Reason + Act)
Category    : Reasoning Mechanics
Framework   : LangGraph
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

agent = _load("reasoning/[react]-[langgraph]-[ollama]/agent.py")

search_books        = agent.search_books
check_availability  = agent.check_availability
get_similar_books   = agent.get_similar_books
MOCK_BOOK_CATALOGUE = agent.MOCK_BOOK_CATALOGUE
run_agent           = agent.run_agent
CONFIG_PATH         = agent.CONFIG_PATH


class TestSearchBooks:
    def test_known_keyword_returns_match(self):
        r = search_books.invoke({"query": "machine learning"})
        assert isinstance(r, list) and len(r) >= 1

    def test_case_insensitive(self):
        lower = search_books.invoke({"query": "machine learning"})
        upper = search_books.invoke({"query": "MACHINE LEARNING"})
        assert lower == upper

    def test_unknown_returns_empty(self):
        r = search_books.invoke({"query": "advanced rocket propulsion"})
        assert r == []


class TestCheckAvailability:
    def test_known_available_title(self):
        t = next(t for t, d in MOCK_BOOK_CATALOGUE.items() if d["available"])
        r = check_availability.invoke({"title": t})
        assert "available" in r.lower()

    def test_known_unavailable_title(self):
        t = next(t for t, d in MOCK_BOOK_CATALOGUE.items() if not d["available"])
        r = check_availability.invoke({"title": t})
        assert "not available" in r.lower()

    def test_unknown_title_returns_not_found(self):
        r = check_availability.invoke({"title": "No Such Book XYZ"})
        assert "not found" in r.lower()


class TestGetSimilarBooks:
    def test_known_title_returns_list(self):
        t = list(MOCK_BOOK_CATALOGUE.keys())[0]
        r = get_similar_books.invoke({"title": t})
        assert isinstance(r, list)

    def test_does_not_include_original(self):
        t = list(MOCK_BOOK_CATALOGUE.keys())[0]
        r = get_similar_books.invoke({"title": t})
        assert t not in r


class TestRunAgent:
    @patch.object(agent, "build_graph")
    def test_returns_required_keys(self, mock_build):
        g = MagicMock()
        g.invoke.return_value = {"messages": [MagicMock(content="Python Machine Learning is available.")]}
        mock_build.return_value = g
        result = run_agent("Find an ML book.", CONFIG_PATH)
        for k in ("task", "answer", "quality_score", "token_cost_usd", "cpcd"):
            assert k in result

    @patch.object(agent, "build_graph")
    def test_quality_score_in_range(self, mock_build):
        g = MagicMock()
        g.invoke.return_value = {"messages": [MagicMock(content="Deep Learning by Goodfellow is available.")]}
        mock_build.return_value = g
        result = run_agent("Find a deep learning book.", CONFIG_PATH)
        assert 0.0 <= result["quality_score"] <= 1.0
