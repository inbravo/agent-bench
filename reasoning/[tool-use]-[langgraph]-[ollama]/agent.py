"""
agent.py — Tool Use pattern: weather assistant (LangGraph + Ollama).

Pattern   : Tool Use
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
log = logging.getLogger("agent.tool-use.weather")

# ── imports ───────────────────────────────────────────
from langchain_core.tools    import tool
from langgraph.prebuilt      import create_react_agent
from langchain_core.messages import HumanMessage

# ── constants ─────────────────────────────────────────
CONFIG_PATH = str(Path(__file__).parent / "config.yaml")

DEFAULT_TASK = "What is the current temperature in Tokyo? Convert it to Fahrenheit."

MOCK_WEATHER_DB = {
    "london":   {"temp_c": 12, "condition": "Cloudy"},
    "new york": {"temp_c": 18, "condition": "Sunny"},
    "tokyo":    {"temp_c": 22, "condition": "Clear"},
    "sydney":   {"temp_c": 25, "condition": "Partly cloudy"},
    "bangalore":{"temp_c": 28, "condition": "Humid"},
}

# ── tools ─────────────────────────────────────────────

@tool
def get_current_weather(city: str) -> dict:
    """Return the current weather for a city.

    Args:
        city: City name (e.g. 'London', 'Tokyo').

    Returns:
        Dict with temp_c and condition, or an error message.
    """
    log.debug("get_current_weather called: city=%s", city)
    data = MOCK_WEATHER_DB.get(city.lower())
    if not data:
        return {"error": f"No weather data for '{city}'. Known cities: {list(MOCK_WEATHER_DB)}"}
    return {"city": city, **data}


@tool
def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a temperature between Celsius, Fahrenheit, and Kelvin.

    Args:
        value:     The temperature value to convert.
        from_unit: Source unit — 'C', 'F', or 'K'.
        to_unit:   Target unit — 'C', 'F', or 'K'.

    Returns:
        Dict with the converted value and unit label.
    """
    log.debug("convert_temperature: %.1f %s -> %s", value, from_unit, to_unit)
    fu, tu = from_unit.upper(), to_unit.upper()

    # Normalise to Celsius first
    if fu == "C":   celsius = value
    elif fu == "F": celsius = (value - 32) * 5 / 9
    elif fu == "K": celsius = value - 273.15
    else:           return {"error": f"Unknown from_unit: '{from_unit}'"}

    # Convert from Celsius to target
    if tu == "C":   result = celsius
    elif tu == "F": result = celsius * 9 / 5 + 32
    elif tu == "K": result = celsius + 273.15
    else:           return {"error": f"Unknown to_unit: '{to_unit}'"}

    return {"converted": round(result, 2), "unit": tu}


TOOLS = [get_current_weather, convert_temperature]

# ── graph ─────────────────────────────────────────────

def build_graph(config_path: str = CONFIG_PATH):
    """Build and return a compiled LangGraph ReAct agent."""
    config = get_config(config_path=config_path)
    llm    = get_llm(config)
    return create_react_agent(llm, tools=TOOLS)


def run_agent(task: str, config_path: str = CONFIG_PATH) -> dict:
    """Run the weather agent and return a scored result."""
    log.info("─── tool-use / weather starting ───")
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
    log.info("─── tool-use / weather done ───")
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
