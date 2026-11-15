"""
agent.py — Framework Swap pattern: blog post crew (CrewAI + Ollama).

Pattern   : Framework Swap
Category  : Agent Topology
Framework : CrewAI
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
log = logging.getLogger("agent.fw-swap.blog-crew")

# ── imports ───────────────────────────────────────────
from crewai        import Agent, Task, Crew, Process
from crewai.tools  import BaseTool
from pydantic      import BaseModel, Field

# ── constants ─────────────────────────────────────────
CONFIG_PATH  = str(Path(__file__).parent / "config.yaml")
DEFAULT_TASK = "Write a short blog post about the benefits of walking every day."

MOCK_FACTS_DB = {
    "walking": [
        "Walking 30 minutes a day reduces the risk of heart disease by up to 35%.",
        "Regular walking improves mood by releasing endorphins.",
        "Walking after meals helps regulate blood sugar levels.",
        "A daily walk can burn between 150 and 200 calories.",
        "Walking strengthens leg muscles and improves joint flexibility.",
    ],
    "exercise": [
        "Even light exercise is better than no exercise.",
        "Consistency matters more than intensity for long-term health.",
    ],
}

# ── tools ─────────────────────────────────────────────

class FactQueryInput(BaseModel):
    topic: str = Field(description="Topic to fetch facts about (e.g. 'walking')")


class FetchFactsTool(BaseTool):
    name: str        = "fetch_facts"
    description: str = "Fetch a list of factual statements about a given topic."
    args_schema      = FactQueryInput

    def _run(self, topic: str) -> list:
        log.debug("FetchFactsTool called: topic=%s", topic)
        facts = MOCK_FACTS_DB.get(topic.lower(), [])
        if not facts:
            return [f"No facts found for topic: '{topic}'"]
        return facts


# ── agents ────────────────────────────────────────────

def build_crew(config: dict) -> Crew:
    """Build a three-agent CrewAI crew: Researcher -> Writer -> Editor."""
    llm_model   = config.get("llm_model", "llama3.1:8b")
    llm_string  = f"ollama/{llm_model}"
    fetch_facts = FetchFactsTool()

    researcher = Agent(
        role="Research Analyst",
        goal="Find accurate and relevant facts on the given topic.",
        backstory="You are a thorough researcher who backs claims with facts.",
        tools=[fetch_facts],
        llm=llm_string,
        verbose=True,
    )
    writer = Agent(
        role="Content Writer",
        goal="Write a clear, engaging, and well-structured short blog post.",
        backstory="You turn raw facts into compelling, readable content.",
        llm=llm_string,
        verbose=True,
    )
    editor = Agent(
        role="Senior Editor",
        goal="Improve clarity, flow, and conciseness of the draft.",
        backstory="You tighten prose and ensure a strong opening and clear conclusion.",
        llm=llm_string,
        verbose=True,
    )

    research_task = Task(
        description="Research facts about the topic: {topic}. Use the fetch_facts tool.",
        expected_output="A bullet list of relevant facts about {topic}.",
        agent=researcher,
    )
    write_task = Task(
        description="Using the research facts, write a short blog post (3-4 paragraphs) about {topic}.",
        expected_output="A complete short blog post with a title and 3-4 paragraphs.",
        agent=writer,
        context=[research_task],
    )
    edit_task = Task(
        description="Review and improve the draft. Tighten language, remove filler, ensure compelling opening.",
        expected_output="A polished final blog post ready to publish.",
        agent=editor,
        context=[write_task],
    )

    return Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, write_task, edit_task],
        process=Process.sequential,
        verbose=True,
    )


def run_agent(task: str, config_path: str = CONFIG_PATH) -> dict:
    """Run the blog-post crew and return a scored result."""
    log.info("─── fw-swap / blog-crew starting ───")
    log.info("task: %s", task)

    config = get_config(config_path=config_path)
    crew   = build_crew(config)
    result = crew.kickoff(inputs={"topic": "walking"})
    answer = str(result)

    log.info("answer length: %d chars", len(answer))

    scored = score_run(task=task, answer=answer, config_path=config_path)
    log.info(
        "score=%.3f  token_cost=$%.6f  cpcd=%s",
        scored["quality_score"], scored["token_cost_usd"],
        f'${scored["cpcd"]:.6f}' if scored["cpcd"] is not None else "N/A (failed run)",
    )
    log.info("─── fw-swap / blog-crew done ───")
    return scored


# ── entrypoint ────────────────────────────────────────

if __name__ == "__main__":
    task   = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK
    result = run_agent(task)
    print("\n── result ──────────────────────────────────────")
    print(f"Answer : {result['answer'][:300]}...")
    print(f"Score  : {result['quality_score']:.3f}")
    print(f"Cost   : ${result['token_cost_usd']:.6f}")
    print(f"CPCD   : " + (f"${result['cpcd']:.6f}" if result["cpcd"] is not None else "N/A"))
