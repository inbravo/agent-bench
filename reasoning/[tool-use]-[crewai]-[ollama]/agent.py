"""
agent.py — Tool Use pattern: weather assistant (CrewAI + Ollama).

Description : Demonstrates the Tool Use agentic pattern using CrewAI by building
              a weather assistant with the same two tools as the LangGraph version
              — get_current_weather and convert_temperature. A single CrewAI agent
              with tool access decides which tools to call based on the task. Scored
              on the identical rubric, enabling direct CPCD comparison with the
              LangGraph implementation.

Pattern     : Tool Use
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
log = logging.getLogger("agent.tool-use.weather.crewai")

# ── imports ───────────────────────────────────────────
from crewai       import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic     import BaseModel, Field

# ── constants ─────────────────────────────────────────
CONFIG_PATH  = str(Path(__file__).parent / "config.yaml")
DEFAULT_TASK = "What is the current temperature in Tokyo? Convert it to Fahrenheit."

MOCK_WEATHER_DB = {
    "london":    {"temp_c": 12, "condition": "Cloudy"},
    "new york":  {"temp_c": 18, "condition": "Sunny"},
    "tokyo":     {"temp_c": 22, "condition": "Clear"},
    "sydney":    {"temp_c": 25, "condition": "Partly cloudy"},
    "bangalore": {"temp_c": 28, "condition": "Humid"},
}

# ── tools ─────────────────────────────────────────────

class WeatherInput(BaseModel):
    city: str = Field(description="City name, e.g. 'London' or 'Tokyo'")

class GetCurrentWeatherTool(BaseTool):
    name: str        = "get_current_weather"
    description: str = "Return the current temperature (Celsius) and weather condition for a city."
    args_schema: type[BaseModel] = WeatherInput

    def _run(self, city: str) -> dict:
        log.debug("get_current_weather called: city=%s", city)
        data = MOCK_WEATHER_DB.get(city.lower())
        if not data:
            return {"error": f"No weather data for '{city}'. Known cities: {list(MOCK_WEATHER_DB)}"}
        return {"city": city, **data}


class ConvertInput(BaseModel):
    value:     float = Field(description="Temperature value to convert")
    from_unit: str   = Field(description="Source unit: 'C', 'F', or 'K'")
    to_unit:   str   = Field(description="Target unit: 'C', 'F', or 'K'")

class ConvertTemperatureTool(BaseTool):
    name: str        = "convert_temperature"
    description: str = "Convert a temperature value between Celsius (C), Fahrenheit (F), and Kelvin (K)."
    args_schema: type[BaseModel] = ConvertInput

    def _run(self, value: float, from_unit: str, to_unit: str) -> dict:
        log.debug("convert_temperature: %.1f %s -> %s", value, from_unit, to_unit)
        fu, tu = from_unit.upper(), to_unit.upper()

        if fu == "C":   celsius = value
        elif fu == "F": celsius = (value - 32) * 5 / 9
        elif fu == "K": celsius = value - 273.15
        else:           return {"error": f"Unknown from_unit: '{from_unit}'"}

        if tu == "C":   result = celsius
        elif tu == "F": result = celsius * 9 / 5 + 32
        elif tu == "K": result = celsius + 273.15
        else:           return {"error": f"Unknown to_unit: '{to_unit}'"}

        return {"converted": round(result, 2), "unit": tu}


TOOLS = [GetCurrentWeatherTool(), ConvertTemperatureTool()]

# ── crew ──────────────────────────────────────────────

def build_crew(task_description: str, config_path: str = CONFIG_PATH) -> Crew:
    """Build and return a CrewAI Crew for the weather assistant task."""
    llm = get_llm(config_path)

    weather_agent = Agent(
        role="Weather Assistant",
        goal="Answer weather questions accurately by using the available tools.",
        backstory=(
            "You are a precise weather assistant. You always call get_current_weather "
            "to fetch live data, and convert_temperature when a unit conversion is needed. "
            "You never guess values — you always use your tools."
        ),
        tools=TOOLS,
        llm=llm,
        verbose=True,
    )

    weather_task = Task(
        description=task_description,
        expected_output=(
            "A concise answer stating the current temperature in the requested city "
            "and its converted value in the requested unit, with no padding."
        ),
        agent=weather_agent,
    )

    return Crew(
        agents=[weather_agent],
        tasks=[weather_task],
        process=Process.sequential,
        verbose=True,
    )


def run_agent(task: str, config_path: str = CONFIG_PATH) -> dict:
    """Run the weather CrewAI agent and return a scored result."""
    log.info("─── tool-use / weather / crewai starting ───")
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
    log.info("─── tool-use / weather / crewai done ───")
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
