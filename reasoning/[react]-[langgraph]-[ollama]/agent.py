"""
agent.py — ReAct pattern: book finder (LangGraph + Ollama).

Pattern   : ReAct (Reason + Act)
Category  : Reasoning Mechanics
Framework : LangGraph
Backend   : Ollama (local)
"""

# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import sys
import logging
from pathlib import Path

# ── path setup ────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[2] / "_shared"))

# ── shared setup ──────────────────────────────────────
import logging_config
logging_config.setup()

from backend import get_config, get_llm
from scorer  import score_run

# ── logging ───────────────────────────────────────────
log = logging.getLogger("agent.react.book-finder")

# ── imports ───────────────────────────────────────────
from langchain_core.tools    import tool
from langgraph.prebuilt      import create_react_agent
from langchain_core.messages import HumanMessage

# ── constants ─────────────────────────────────────────
CONFIG_PATH = str(Path(__file__).parent / "config.yaml")

DEFAULT_TASK = (
    "Find me a book on machine learning for beginners. "
    "Check if it is available. If not, suggest similar alternatives."
)

MOCK_BOOK_CATALOGUE = {
    "Python Machine Learning": {
        "author":    "Sebastian Raschka",
        "topic":     ["machine learning", "python", "beginner"],
        "available": True,
    },
    "Hands-On Machine Learning with Scikit-Learn and TensorFlow": {
        "author":    "Aurélien Géron",
        "topic":     ["machine learning", "deep learning", "scikit-learn"],
        "available": False,
    },
    "Deep Learning": {
        "author":    "Ian Goodfellow",
        "topic":     ["deep learning", "neural networks", "advanced"],
        "available": True,
    },
    "Python Data Science Handbook": {
        "author":    "Jake VanderPlas",
        "topic":     ["data science", "python", "beginner"],
        "available": True,
    },
    "Pattern Recognition and Machine Learning": {
        "author":    "Christopher Bishop",
        "topic":     ["machine learning", "statistics", "advanced"],
        "available": False,
    },
}

SIMILAR_BOOKS_MAP = {
    "Python Machine Learning": [
        "Hands-On Machine Learning with Scikit-Learn and TensorFlow",
        "Python Data Science Handbook",
    ],
    "Hands-On Machine Learning with Scikit-Learn and TensorFlow": [
        "Python Machine Learning",
        "Deep Learning",
    ],
    "Deep Learning": [
        "Pattern Recognition and Machine Learning",
        "Hands-On Machine Learning with Scikit-Learn and TensorFlow",
    ],
    "Python Data Science Handbook": [
        "Python Machine Learning",
    ],
    "Pattern Recognition and Machine Learning": [
        "Deep Learning",
        "Python Machine Learning",
    ],
}

# ── tools ─────────────────────────────────────────────

@tool
def search_books(query: str) -> list:
    """Search the book catalogue by keyword.

    Args:
        query: Keywords to search (e.g. 'machine learning beginner').

    Returns:
        List of matching book dicts with title, author, available.
    """
    log.debug("search_books: query=%s", query)
    keywords = query.lower().split()
    results  = []
    for title, meta in MOCK_BOOK_CATALOGUE.items():
        if any(kw in " ".join(meta["topic"]).lower() or kw in title.lower()
               for kw in keywords):
            results.append({"title": title, "author": meta["author"], "available": meta["available"]})
    return results


@tool
def check_availability(title: str) -> str:
    """Check whether a book is currently available for borrowing.

    Args:
        title: Exact book title.

    Returns:
        Availability status string.
    """
    log.debug("check_availability: title=%s", title)
    meta = MOCK_BOOK_CATALOGUE.get(title)
    if not meta:
        return f"Book not found: '{title}'"
    status = "available" if meta["available"] else "not available"
    return f"'{title}' by {meta['author']} is currently {status}."


@tool
def get_similar_books(title: str) -> list:
    """Get a list of books similar to the given title.

    Args:
        title: Title of the reference book.

    Returns:
        List of similar book titles.
    """
    log.debug("get_similar_books: title=%s", title)
    similar = SIMILAR_BOOKS_MAP.get(title)
    if similar:
        return similar
    # Fallback: return all available books except the queried one
    fallback = [t for t in MOCK_BOOK_CATALOGUE if t != title and MOCK_BOOK_CATALOGUE[t]["available"]]
    return fallback or ["No similar books found."]


TOOLS = [search_books, check_availability, get_similar_books]

# ── graph ─────────────────────────────────────────────

def build_graph(config_path: str = CONFIG_PATH):
    """Build and return a compiled LangGraph ReAct agent."""
    config = get_config(config_path=config_path)
    llm    = get_llm(config)
    return create_react_agent(llm, tools=TOOLS)


def run_agent(task: str, config_path: str = CONFIG_PATH) -> dict:
    """Run the book-finder agent and return a scored result."""
    log.info("─── react / book-finder starting ───")
    log.info("task: %s", task)

    graph    = build_graph(config_path)
    response = graph.invoke({"messages": [HumanMessage(content=task)]})
    answer   = response["messages"][-1].content

    log.info("answer: %s", answer[:200])

    scored = score_run(task=task, answer=answer, config_path=config_path)
    log.info(
        "score=%.3f  token_cost=$%.6f  cpcd=$%.6f",
        scored["quality_score"], scored["token_cost_usd"], scored["cpcd"],
    )
    log.info("─── react / book-finder done ───")
    return scored


# ── entrypoint ────────────────────────────────────────

if __name__ == "__main__":
    task   = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK
    result = run_agent(task)
    print("\n── result ──────────────────────────────────────")
    print(f"Answer : {result['answer']}")
    print(f"Score  : {result['quality_score']:.3f}")
    print(f"Cost   : ${result['token_cost_usd']:.6f}")
    print(f"CPCD   : ${result['cpcd']:.6f}")
