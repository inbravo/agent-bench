"""
agent.py — ReAct pattern: book finder (CrewAI + Ollama).

Description : Approximates the ReAct (Reason + Act) pattern using CrewAI's
              single-agent tool loop, which internally cycles through thought,
              action, and observation steps. The agent uses the same three tools
              as the LangGraph version — search_books, check_availability, and
              get_similar_books — on the identical book-finder task and rubric,
              enabling direct CPCD comparison. Note: CrewAI's loop is framework-
              managed rather than graph-explicit; see README for architectural
              differences.

Pattern     : ReAct (Reason + Act) — CrewAI approximation
Category    : Reasoning Mechanics
Framework   : CrewAI
Backend     : Ollama (local)
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

from backend import get_llm
from scorer  import score_run

# ── logging ───────────────────────────────────────────
log = logging.getLogger("agent.react.book-finder.crewai")

# ── imports ───────────────────────────────────────────
from crewai       import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic     import BaseModel, Field

# ── constants ─────────────────────────────────────────
CONFIG_PATH  = str(Path(__file__).parent / "config.yaml")

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
        "author":    "Aurelien Geron",
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

class SearchInput(BaseModel):
    query: str = Field(description="Keywords to search, e.g. 'machine learning beginner'")

class SearchBooksTool(BaseTool):
    name: str        = "search_books"
    description: str = "Search the book catalogue by keyword. Returns matching books with availability."
    args_schema: type[BaseModel] = SearchInput

    def _run(self, query: str) -> list:
        log.debug("search_books: query=%s", query)
        keywords = query.lower().split()
        results  = []
        for title, meta in MOCK_BOOK_CATALOGUE.items():
            if any(kw in " ".join(meta["topic"]).lower() or kw in title.lower()
                   for kw in keywords):
                results.append({"title": title, "author": meta["author"], "available": meta["available"]})
        return results


class AvailabilityInput(BaseModel):
    title: str = Field(description="Exact book title to check availability for")

class CheckAvailabilityTool(BaseTool):
    name: str        = "check_availability"
    description: str = "Check whether a specific book is currently available for borrowing."
    args_schema: type[BaseModel] = AvailabilityInput

    def _run(self, title: str) -> str:
        log.debug("check_availability: title=%s", title)
        meta = MOCK_BOOK_CATALOGUE.get(title)
        if not meta:
            return f"Book not found: '{title}'"
        status = "available" if meta["available"] else "not available"
        return f"'{title}' by {meta['author']} is currently {status}."


class SimilarInput(BaseModel):
    title: str = Field(description="Title of the reference book to find similar books for")

class GetSimilarBooksTool(BaseTool):
    name: str        = "get_similar_books"
    description: str = "Get a list of books similar to a given title."
    args_schema: type[BaseModel] = SimilarInput

    def _run(self, title: str) -> list:
        log.debug("get_similar_books: title=%s", title)
        similar = SIMILAR_BOOKS_MAP.get(title)
        if similar:
            return similar
        fallback = [t for t in MOCK_BOOK_CATALOGUE if t != title and MOCK_BOOK_CATALOGUE[t]["available"]]
        return fallback or ["No similar books found."]


TOOLS = [SearchBooksTool(), CheckAvailabilityTool(), GetSimilarBooksTool()]

# ── crew ──────────────────────────────────────────────

def build_crew(task_description: str, config_path: str = CONFIG_PATH) -> Crew:
    """Build and return a CrewAI Crew for the book-finder task."""
    llm = get_llm(config_path)

    book_agent = Agent(
        role="Book Finder",
        goal="Help users find books that match their interests and confirm availability.",
        backstory=(
            "You are a knowledgeable librarian assistant. When asked to find a book, "
            "you first search the catalogue, then check availability, and if a book is "
            "unavailable you always suggest similar alternatives. You use your tools "
            "in sequence and adapt based on what each tool returns."
        ),
        tools=TOOLS,
        llm=llm,
        verbose=True,
    )

    book_task = Task(
        description=task_description,
        expected_output=(
            "A clear answer naming the book found, its availability status, and "
            "at least one alternative if the book is not available."
        ),
        agent=book_agent,
    )

    return Crew(
        agents=[book_agent],
        tasks=[book_task],
        process=Process.sequential,
        verbose=True,
    )


def run_agent(task: str, config_path: str = CONFIG_PATH) -> dict:
    """Run the book-finder CrewAI agent and return a scored result."""
    log.info("─── react / book-finder / crewai starting ───")
    log.info("task: %s", task)

    crew   = build_crew(task, config_path)
    result = crew.kickoff()
    answer = str(result)

    log.info("answer: %s", answer[:200])

    scored = score_run(task=task, answer=answer, config_path=config_path)
    log.info(
        "score=%.3f  token_cost=$%.6f  cpcd=%s",
        scored["quality_score"], scored["token_cost_usd"],
        f'${scored["cpcd"]:.6f}' if scored["cpcd"] is not None else "N/A (failed run)",
    )
    log.info("─── react / book-finder / crewai done ───")
    return scored


# ── entrypoint ────────────────────────────────────────

if __name__ == "__main__":
    task   = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK
    result = run_agent(task)
    print("\n── result ──────────────────────────────────────")
    print(f"Answer : {result['answer']}")
    print(f"Score  : {result['quality_score']:.3f}")
    print(f"Cost   : ${result['token_cost_usd']:.6f}")
    print(f"CPCD   : " + (f"${result['cpcd']:.6f}" if result["cpcd"] is not None else "N/A"))
