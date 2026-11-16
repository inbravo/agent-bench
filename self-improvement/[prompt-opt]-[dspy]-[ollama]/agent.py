"""
agent.py — Prompt Optimisation pattern: weather assistant (DSPy + Ollama).

Description : Demonstrates the Prompt Optimisation self-improvement pattern using
              DSPy. The agent is defined as a typed Signature; BootstrapFewShot
              then automatically optimises the prompt and few-shot examples against
              a quality metric derived from the CPCD rubric. Running the agent
              before and after optimisation reveals the CPCD delta — the core
              finding of the self-improvement category.

Pattern     : Prompt Optimisation (Self-Improvement)
Category    : Self-Improvement
Framework   : DSPy
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
log = logging.getLogger("agent.prompt-opt.weather.dspy")

# ── imports ───────────────────────────────────────────
import dspy

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

# ── mock tool functions ───────────────────────────────
# DSPy tools are plain Python functions decorated with dspy.tool (or passed as
# callables). We reuse the same mock DB as all other reasoning examples.

def get_current_weather(city: str) -> dict:
    """Return the current temperature (Celsius) and condition for a city."""
    data = MOCK_WEATHER_DB.get(city.lower())
    if not data:
        return {"error": f"No weather data for '{city}'. Known: {list(MOCK_WEATHER_DB)}"}
    return {"city": city, **data}


def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert temperature between Celsius (C), Fahrenheit (F), Kelvin (K)."""
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


TOOLS = [get_current_weather, convert_temperature]

# ── DSPy signature ────────────────────────────────────

class WeatherQuery(dspy.Signature):
    """Answer a weather question by calling the available tools when needed."""
    question: str = dspy.InputField(desc="A weather question, possibly requesting a unit conversion.")
    answer:   str = dspy.OutputField(desc="Concise answer with the temperature value and unit.")


# ── DSPy agent module ─────────────────────────────────

class WeatherAgent(dspy.Module):
    """ReAct-style DSPy module that uses the weather tools to answer queries."""

    def __init__(self):
        self.react = dspy.ReAct(WeatherQuery, tools=TOOLS)

    def forward(self, question: str) -> dspy.Prediction:
        return self.react(question=question)


# ── LLM configuration ─────────────────────────────────

def configure_dspy(config_path: str = CONFIG_PATH) -> None:
    """Configure DSPy to use the Ollama backend from config.yaml."""
    cfg = get_llm_config(config_path)
    model      = cfg.get("llm_model",   "llama3.1:8b")
    ollama_host = cfg.get("ollama_host", "http://localhost:11434")

    lm = dspy.LM(
        model    = f"ollama_chat/{model}",
        api_base = ollama_host,
        api_key  = "ollama",           # required by LiteLLM; not validated locally
    )
    dspy.configure(lm=lm)
    log.info("DSPy configured: model=%s  host=%s", model, ollama_host)


# ── training set for optimiser ───────────────────────
# Small demonstration set — in production, expand to 10-20 examples.

TRAINSET = [
    dspy.Example(
        question="What is the weather in London? Give the temperature in Celsius.",
        answer="London is currently 12°C and Cloudy.",
    ).with_inputs("question"),
    dspy.Example(
        question="What is the current temperature in New York in Fahrenheit?",
        answer="New York is currently 18°C (64.4°F) and Sunny.",
    ).with_inputs("question"),
    dspy.Example(
        question="How warm is it in Sydney? Convert to Kelvin.",
        answer="Sydney is currently 25°C (298.15K) and Partly cloudy.",
    ).with_inputs("question"),
]


# ── CPCD-aware metric for the optimiser ──────────────

def quality_metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
    """
    Lightweight rubric used by BootstrapFewShot.
    Returns a 0-1 score based on whether key facts appear in the answer.
    Full CPCD scoring (token cost) runs separately via score_run.
    """
    answer = (pred.answer or "").lower()
    score  = 0.0
    # tool_selection (0.35): did it produce a temperature value?
    if any(c.isdigit() for c in answer):
        score += 0.35
    # answer_accuracy (0.35): does the answer mention the city from the question?
    city = example.question.split()[-1].rstrip("?.").lower()
    if city in answer:
        score += 0.35
    # completeness (0.20): does it mention a unit?
    if any(u in answer for u in ["°c", "°f", "celsius", "fahrenheit", "kelvin", "°k"]):
        score += 0.20
    # conciseness (0.10): short answers score full; long answers score partial
    score += 0.10 if len(answer) < 200 else 0.05
    return round(score, 3)


# ── run helpers ───────────────────────────────────────

def run_agent(task: str, config_path: str = CONFIG_PATH, optimise: bool = False) -> dict:
    """
    Run the DSPy weather agent and return a scored result.

    Parameters
    ----------
    task      : The weather question to answer.
    optimise  : If True, run BootstrapFewShot optimisation before inference.
                Set to False for the baseline (pre-optimisation) CPCD measurement.
    """
    configure_dspy(config_path)
    agent = WeatherAgent()

    if optimise:
        log.info("Running BootstrapFewShot optimisation …")
        optimiser = dspy.BootstrapFewShot(metric=quality_metric, max_bootstrapped_demos=2)
        agent     = optimiser.compile(agent, trainset=TRAINSET)
        log.info("Optimisation complete.")

    log.info("─── prompt-opt / weather / dspy  [optimised=%s] ───", optimise)
    log.info("task: %s", task)

    pred   = agent(question=task)
    answer = pred.answer

    log.info("answer: %s", answer[:200])

    scored = score_run(task=task, answer=answer, config_path=config_path)
    scored["optimised"] = optimise
    log.info(
        "score=%.3f  token_cost=$%.6f  cpcd=%s  optimised=%s",
        scored["quality_score"], scored["token_cost_usd"],
        f'${scored["cpcd"]:.6f}' if scored["cpcd"] is not None else "N/A",
        optimise,
    )
    log.info("─── prompt-opt / weather / dspy done ───")
    return scored


# ── entrypoint ────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DSPy weather agent (prompt optimisation)")
    parser.add_argument("--optimise", action="store_true", help="Run BootstrapFewShot before inference")
    parser.add_argument("task", nargs="*", help="Weather question (default: Tokyo)")
    args = parser.parse_args()

    task   = " ".join(args.task) if args.task else DEFAULT_TASK
    result = run_agent(task, optimise=args.optimise)

    print("\n── result ──────────────────────────────────────")
    print(f"Answer    : {result['answer']}")
    print(f"Optimised : {result['optimised']}")
    print(f"Score     : {result['quality_score']:.3f}")
    print(f"Cost      : ${result['token_cost_usd']:.6f}")
    print(f"CPCD      : " + (f"${result['cpcd']:.6f}" if result["cpcd"] is not None else "N/A"))
