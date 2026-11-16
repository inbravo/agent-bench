"""
test_local.py — Unit and integration tests for the ReAct / book-finder agent (CrewAI).

Description : Verifies tool invocation logic (SearchBooksTool, CheckAvailabilityTool,
              GetSimilarBooksTool), MOCK_BOOK_CATALOGUE lookups, and the full CrewAI
              agent run against a scored rubric. Uses importlib to load the agent
              module from its bracket-named folder path.

Pattern     : ReAct (Reason + Act) — CrewAI approximation
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

agent = _load("reasoning/[react]-[crewai]-[ollama]/agent.py")

SearchBooksTool       = agent.SearchBooksTool
CheckAvailabilityTool = agent.CheckAvailabilityTool
GetSimilarBooksTool   = agent.GetSimilarBooksTool
MOCK_BOOK_CATALOGUE   = agent.MOCK_BOOK_CATALOGUE
SIMILAR_BOOKS_MAP     = agent.SIMILAR_BOOKS_MAP
build_crew            = agent.build_crew
run_agent             = agent.run_agent
CONFIG_PATH           = agent.CONFIG_PATH


class TestSearchBooksTool:
    def setup_method(self):
        self.tool = SearchBooksTool()

    def test_known_keyword_returns_match(self):
        r = self.tool._run("machine learning")
        titles = [b["title"] for b in r]
        assert any("Machine Learning" in t for t in titles)

    def test_beginner_keyword_filters(self):
        r = self.tool._run("beginner")
        titles = [b["title"] for b in r]
        assert "Python Machine Learning" in titles

    def test_unknown_keyword_returns_empty(self):
        r = self.tool._run("quantum physics")
        assert r == []

    def test_results_have_required_keys(self):
        r = self.tool._run("python")
        for book in r:
            assert "title"     in book
            assert "author"    in book
            assert "available" in book


class TestCheckAvailabilityTool:
    def setup_method(self):
        self.tool = CheckAvailabilityTool()

    def test_available_book(self):
        r = self.tool._run("Python Machine Learning")
        assert "available" in r.lower()
        assert "not" not in r.lower()

    def test_unavailable_book(self):
        r = self.tool._run("Hands-On Machine Learning with Scikit-Learn and TensorFlow")
        assert "not available" in r.lower()

    def test_unknown_title(self):
        r = self.tool._run("Nonexistent Book Title")
        assert "not found" in r.lower()


class TestGetSimilarBooksTool:
    def setup_method(self):
        self.tool = GetSimilarBooksTool()

    def test_known_title_returns_list(self):
        r = self.tool._run("Python Machine Learning")
        assert isinstance(r, list)
        assert len(r) > 0

    def test_unknown_title_returns_fallback(self):
        r = self.tool._run("A Book That Does Not Exist")
        assert isinstance(r, list)
        assert len(r) > 0

    def test_similar_map_coverage(self):
        for title in MOCK_BOOK_CATALOGUE:
            r = self.tool._run(title)
            assert isinstance(r, list), f"Similar books not list for {title}"


class TestMockCatalogue:
    def test_all_entries_have_required_keys(self):
        for title, meta in MOCK_BOOK_CATALOGUE.items():
            assert "author"    in meta, f"Missing author for {title}"
            assert "topic"     in meta, f"Missing topic for {title}"
            assert "available" in meta, f"Missing available for {title}"

    def test_similar_books_map_references_valid_titles(self):
        for title, similars in SIMILAR_BOOKS_MAP.items():
            for s in similars:
                assert s in MOCK_BOOK_CATALOGUE, f"Similar book '{s}' not in catalogue"
