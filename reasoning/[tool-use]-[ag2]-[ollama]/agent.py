"""
agent.py — Tool Use pattern: weather assistant (AG2 + Ollama).

Description : Demonstrates the Tool Use agentic pattern using AG2 (the
              community-maintained successor to AutoGen) by building a weather
              assistant with the same two mock tools as the LangGraph and CrewAI
              versions — get_current_weather and convert_temperature. An
              AssistantAgent with native Ollama tool calling decides which tools
              to invoke. Scored on the identical rubric, enabling direct CPCD
              comparison across all three frameworks.

Pattern     : Tool Use
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
log = logging.getLogger("agent.tool-use.weather.ag2")

# ── imports ───────────────────────────────────────────
import autogen   # pip install ag2  (ag2 ships as the 'autogen' namespace)

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

# ── tool functions ────────────────────────────────────
# AG2 registers tools via @user_proxy.register_for_execution() +
# @assistant.register_for_llm() decorators, or via function_map.
# We define them as plain functions first, then register below.

def get_current_weather(city: str) -> dict:
    """Return the current temperature (Celsius) and weather condition for a city."""
    log.debug("get_current_weather: city=%s", city)
    data = MOCK_WEATHER_DB.get(city.lower())
    if not data:
        return {"error": f"No weather data for '{city}'. Known: {list(MOCK_WEATHER_DB)}"}
    return {"city": city, **data}


def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a temperature value between Celsius (C), Fahrenheit (F), and Kelvin (K)."""
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


# ── AG2 agent construction ────────────────────────────

def build_agents(config_path: str = CONFIG_PATH):
    """Build and return (assistant, user_proxy) AG2 agents."""
    cfg   = get_llm_config(config_path)
    model = cfg.get("llm_model",   "llama3.1:8b")
    host  = cfg.get("ollama_host", "http://localhost:11434")

    # AG2 native Ollama config (no LiteLLM proxy needed)
    llm_config = {
        "config_list": [
            {
                "model":            model,
                "api_type":         "ollama",
                "client_host":      host,
                "native_tool_calls": True,
            }
        ],
        "timeout": 120,
    }

    assistant = autogen.AssistantAgent(
        name       = "weather_assistant",
        system_message = (
            "You are a precise weather assistant. "
            "Always call get_current_weather first to fetch the data, "
            "then call convert_temperature if a unit conversion is requested. "
            "Never guess values — always use your tools."
        ),
        llm_config = llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name             = "user_proxy",
        human_input_mode = "NEVER",
        max_consecutive_auto_reply = 5,
        is_termination_msg = lambda msg: (
            msg.get("content", "").strip().upper() in ("TERMINATE", "DONE")
            or "TERMINATE" in msg.get("content", "")
        ),
        code_execution_config = False,
    )

    # Register tools
    for fn in (get_current_weather, convert_temperature):
        autogen.register_function(
            fn,
            caller   = assistant,
            executor = user_proxy,
            name        = fn.__name__,
            description = fn.__doc__,
        )

    return assistant, user_proxy


# ── run helper ────────────────────────────────────────

def run_agent(task: str, config_path: str = CONFIG_PATH) -> dict:
    """Run the AG2 weather agent and return a scored result."""
    log.info("─── tool-use / weather / ag2 starting ───")
    log.info("task: %s", task)

    assistant, user_proxy = build_agents(config_path)

    # Capture the last assistant message as the answer
    chat_result = user_proxy.initiate_chat(
        recipient  = assistant,
        message    = task,
        max_turns  = 6,
        summary_method = "last_msg",
    )

    # Extract answer from chat history
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
    log.info("─── tool-use / weather / ag2 done ───")
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
