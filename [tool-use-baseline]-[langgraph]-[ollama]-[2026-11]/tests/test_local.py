"""
Tests for tool-use-baseline — runs against local Ollama.
Run: pytest tests/test_local.py -v
Requires: Ollama running on localhost:11434 with llama3.1:8b pulled.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))


def test_get_market_price_tool():
    """get_market_price returns a dict with the expected keys."""
    from agent import get_market_price
    result = get_market_price.invoke({"ticker": "JPM"})
    assert isinstance(result, dict)
    assert "price" in result
    assert result["ticker"] == "JPM"
    assert result["price"] > 0


def test_calculate_var_tool():
    """calculate_var returns a positive VaR for a valid position."""
    from agent import calculate_var
    result = calculate_var.invoke({"notional": 1_000_000, "confidence_level": 0.99})
    assert isinstance(result, dict)
    assert result["var_usd"] > 0
    assert result["confidence_level"] == 0.99


def test_fetch_regulation_text_tool():
    """fetch_regulation_text returns text for a known reference."""
    from agent import fetch_regulation_text
    result = fetch_regulation_text.invoke({"reference": "BCBS-239-P4"})
    assert isinstance(result, dict)
    assert "BCBS-239-P4" in result["reference"]
    assert len(result["text"]) > 10


def test_fetch_regulation_text_unknown():
    """fetch_regulation_text handles unknown references gracefully."""
    from agent import fetch_regulation_text
    result = fetch_regulation_text.invoke({"reference": "UNKNOWN-99"})
    assert "not found" in result["text"].lower()


@pytest.mark.integration
def test_full_agent_run():
    """Full agent run against Ollama — calls all three tools and returns a summary."""
    pytest.importorskip("langchain_ollama", reason="langchain-ollama not installed")
    from agent import TASK, build_graph
    from langchain_core.messages import HumanMessage

    graph = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content=TASK)]})
    final = result["messages"][-1]
    output = final.content if hasattr(final, "content") else str(final)

    assert len(output) > 50, "Agent output is suspiciously short"
    # At least one of the expected results should appear
    assert any(keyword in output.lower() for keyword in ["jpm", "var", "bcbs", "principle"])
