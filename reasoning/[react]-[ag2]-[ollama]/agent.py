"""
agent.py — ReAct pattern: book finder (AG2 + Ollama).

Description : Demonstrates the ReAct (Reason + Act) agentic pattern using AG2.
              An AssistantAgent reasons step-by-step over a book catalogue,
              calling search and similarity tools as needed. Same task as the
              LangGraph and CrewAI ReAct versions — enables direct CPCD
              comparison across all three frameworks.

Pattern     : ReAct (Reason + Act)
Category    : Reasoning Mechanics
Framework   : AG2 (AutoGen community fork)
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

from backend import get_llm_config
from scorer  import score_run

# ── logging ───────────────────────────────────────────
log = logging.getLogger("agent.react.books.ag2")

# ── imports ───────────────────────────────────────────
import autogen   # pip install ag2

# ── constants ─────────────────────────────────────────
CONFIG_PATH  = str(Path(__file__).parent / "config.yaml")
DEFAULT_TASK = (
    "I enjoyed 'The Pragmatic Programmer'. "
    "Can you find it in the catalogue and suggest two similar books?"
)

# Book catalogue — identical to LangGraph + CrewAI ReAct versions
MOCK_BOOK_CATALOGUE = {
    "the pragmatic programmer": {
        "title":    "The Pragmatic Programmer",
        "authors":  ["David Thomas", "Andrew Hunt"],
        "genre":    "Software Engineering",
        "rating":   4.8,
        "isbn":     "978-0-13-595705-9",
    },
    "clean code": {
        "title":    "Clean Code",
        "authors":  ["Robert C. Martin"],
        "genre":    "Software Engineering",
        "rating":   4.7,
        "isbn":     "978-0-13-235088-4",
    },
    "designing data-intensive applications": {
        "title":    "Designing Data-Intensive Applications",
        "authors":  ["Martin Kleppmann"],
        "genre":    "Distributed Systems",
        "rating":   4.9,
        "isbn":     "978-1-4920-3289-5",
    },
    "the mythical man-month": {
        "title":    "The Mythical Man-Month",
        "authors":  ["Frederick P. Brooks Jr."],
        "genre":    "Software Engineering",
        "rating":   4.6,
        "isbn":     "978-0-20-130650-5",
    },
    "structure and interpretation of computer programs": {
        "title":    "Structure and Interpretation of Computer Programs",
        "authors":  ["Harold Abelson", "Gerald Jay Sussman"],
        "genre":    "Computer Science",
        "rating":   4.7,
        "isbn":     "978-0-26-251153-7",
    },
    "refactoring": {
        "title":    "Refactoring",
        "authors":  ["Martin Fowler"],
        "genre":    "Software Engineering",
        "rating":   4.6,
        "isbn":     "978-0-13-468599-1",
    },
}

SIMILAR_BOOKS_MAP = {
    "the pragmatic programmer":    ["clean code", "refactoring"],
    "clean code":                  ["the pragmatic programmer", "refactoring"],
    "designing data-intensive applications": [
        "structure and interpretation of computer programs",
        "the mythical man-month",
    ],
    "the mythical man-month":      ["the pragmatic programmer", "clean code"],
    "structure and interpretation of computer programs": [
        "designing data-intensive applications",
        "clean code",
    ],
    "refactoring": ["clean code", "the pragmatic programmer"],
}

# ── tool functions ────────────────────────────────────

def search_book(title: str) -> dict:
    """Search the book catalogue by title. Returns book details if found."""
    log.debug("search_book: title=%s", title)
    key = title.lower().strip()
    book = MOCK_BOOK_CATALOGUE.get(key)
    if not book:
        # fuzzy: check if key is a substring of any catalogue title
        for k, v in MOCK_BOOK_CATALOGUE.items():
            if key in k or k in key:
                return v
        return {"error": f"Book '{title}' not found.", "available": list(MOCK_BOOK_CATALOGUE)}
    return book


def get_similar_books(title: str) -> dict:
    """Return a list of books similar to the given title."""
    log.debug("get_similar_books: title=%s", title)
    key      = title.lower().strip()
    sim_keys = SIMILAR_BOOKS_MAP.get(key, [])
    if not sim_keys:
        return {"error": f"No similarity data for '{title}'."}
    similar = [MOCK_BOOK_CATALOGUE[k] for k in sim_keys if k in MOCK_BOOK_CATALOGUE]
    return {"similar_books": similar}


def get_book_rating(title: str) -> dict:
    """Return the rating (out of 5) for a book."""
    log.debug("get_book_rating: title=%s", title)
    book = search_book(title)
    if "error" in book:
        return book
    return {"title": book["title"], "rating": book["rating"]}


# ── agent construction ────────────────────────────────

REACT_SYSTEM_MSG = """\
You are a knowledgeable book assistant that uses the ReAct reasoning pattern.
For every request, reason step-by-step:

Thought: what do I need to find out?
Action:  which tool to call and with what arguments
Observation: what did the tool return?
... (repeat Thought/Action/Observation as needed)
Final Answer: a clear, complete response to the user's question.

Always call search_book first to verify a title exists before calling
get_similar_books. Use get_book_rating when the user asks about ratings.
Never guess book data — always use your tools.
"""


def build_agents(config_path: str = CONFIG_PATH):
    """Return (assistant, user_proxy) AG2 agents configured for book finding."""
    cfg   = get_llm_config(config_path)
    model = cfg.get("llm_model",   "llama3.1:8b")
    host  = cfg.get("ollama_host", "http://localhost:11434")

    llm_config = {
        "config_list": [
            {
                "model":             model,
                "api_type":          "ollama",
                "client_host":       host,
                "native_tool_calls": True,
            }
        ],
        "timeout": 180,
    }

    assistant = autogen.AssistantAgent(
        name           = "book_assistant",
        system_message = REACT_SYSTEM_MSG,
        llm_config     = llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name             = "user_proxy",
        human_input_mode = "NEVER",
        max_consecutive_auto_reply = 8,
        is_termination_msg = lambda msg: (
            "TERMINATE" in msg.get("content", "")
            or msg.get("content", "").strip().upper() in ("TERMINATE", "DONE")
        ),
        code_execution_config = False,
    )

    for fn in (search_book, get_similar_books, get_book_rating):
        autogen.register_function(
            fn,
            caller      = assistant,
            executor    = user_proxy,
            name        = fn.__name__,
            description = fn.__doc__,
        )

    return assistant, user_proxy


# ── run helper ────────────────────────────────────────

def run_agent(task: str, config_path: str = CONFIG_PATH) -> dict:
    """Run the AG2 book-finder agent and return a scored result dict."""
    log.info("─── react / books / ag2 starting ───")
    log.info("task: %s", task)

    assistant, user_proxy = build_agents(config_path)

    chat_result = user_proxy.initiate_chat(
        recipient      = assistant,
        message        = task,
        max_turns      = 8,
        summary_method = "last_msg",
    )

    answer = ""
    for msg in reversed(chat_result.chat_history):
        if msg.get("role") == "assistant" and msg.get("content"):
            answer = msg["content"].strip()
            break
    if not answer:
        answer = chat_result.summary or ""

    log.info("answer: %s", answer[:200])

    scored = score_run(task=task, answer=answer, config_path=config_path)
    log.info(
        "score=%.3f  token_cost=$%.6f  cpcd=%s",
        scored["quality_score"], scored["token_cost_usd"],
        f'${scored["cpcd"]:.6f}' if scored["cpcd"] is not None else "N/A",
    )
    log.info("─── react / books / ag2 done ───")
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
