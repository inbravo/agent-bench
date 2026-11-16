"""
tests/test_local.py — offline unit tests for [react]-[ag2]-[ollama].

No Ollama instance required; covers tool functions and agent construction.
"""

import importlib.util
import sys
from pathlib import Path

# ── load module from bracket-named path ───────────────────────────────────────
_AGENT_PATH = Path(__file__).parents[1] / "agent.py"

def _load():
    spec   = importlib.util.spec_from_file_location("agent_ag2_react", _AGENT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_ag2_react"] = module
    spec.loader.exec_module(module)
    return module

agent_mod = _load()


# ── tool function tests ────────────────────────────────────────────────────────

class TestSearchBook:
    def test_exact_match(self):
        result = agent_mod.search_book("the pragmatic programmer")
        assert result["title"] == "The Pragmatic Programmer"
        assert result["rating"] == 4.8

    def test_case_insensitive(self):
        result = agent_mod.search_book("CLEAN CODE")
        assert "error" not in result
        assert result["rating"] == 4.7

    def test_partial_match(self):
        # "pragmatic" should find "the pragmatic programmer"
        result = agent_mod.search_book("pragmatic")
        assert "error" not in result

    def test_unknown_returns_error(self):
        result = agent_mod.search_book("Harry Potter")
        assert "error" in result
        assert "available" in result

    def test_all_catalogue_entries_present(self):
        for title in agent_mod.MOCK_BOOK_CATALOGUE:
            r = agent_mod.search_book(title)
            assert "error" not in r, f"Catalogue entry missing: {title}"


class TestGetSimilarBooks:
    def test_pragmatic_programmer_has_two_similar(self):
        result = agent_mod.get_similar_books("the pragmatic programmer")
        assert "similar_books" in result
        assert len(result["similar_books"]) == 2

    def test_similar_books_are_in_catalogue(self):
        for title in agent_mod.SIMILAR_BOOKS_MAP:
            result = agent_mod.get_similar_books(title)
            assert "similar_books" in result, f"No similar_books key for {title}"
            for book in result["similar_books"]:
                assert "title" in book

    def test_unknown_returns_error(self):
        result = agent_mod.get_similar_books("unknown title xyz")
        assert "error" in result


class TestGetBookRating:
    def test_known_title_returns_rating(self):
        result = agent_mod.get_book_rating("clean code")
        assert result["rating"] == 4.7

    def test_ddia_rating(self):
        result = agent_mod.get_book_rating("designing data-intensive applications")
        assert result["rating"] == 4.9

    def test_unknown_returns_error(self):
        result = agent_mod.get_book_rating("nonexistent book")
        assert "error" in result


# ── agent construction test ────────────────────────────────────────────────────

class TestBuildAgents:
    def test_build_agents_returns_pair(self, tmp_path):
        import autogen
        cfg_text = """
example_name: react-books-ag2
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
        assert assistant.name == "book_assistant"

    def test_three_tools_registered(self, tmp_path):
        cfg_text = """
example_name: react-books-ag2
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
        assert "search_book"       in names
        assert "get_similar_books" in names
        assert "get_book_rating"   in names

    def test_react_system_message_present(self, tmp_path):
        cfg_text = """
example_name: react-books-ag2
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
        sys_msg = assistant.system_message
        assert "Thought" in sys_msg
        assert "Action"  in sys_msg
        assert "Observation" in sys_msg
