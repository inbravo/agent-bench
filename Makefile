.PHONY: setup run-example1 run-bcbs run-bcbs-databricks run-bcbs-crewai run-compare test test-all clean help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "venv ready. Activate with: source .venv/bin/activate"

run-example1:
	$(PYTHON) "[tool-use-baseline]-[langgraph]-[ollama]-[2026-11]/agent.py"

run-bcbs:
	$(PYTHON) "[bcbs239-lineage]-[langgraph]-[ollama]-[2026-11]/agent.py"

run-bcbs-databricks:
	$(PYTHON) "[bcbs239-lineage]-[langgraph]-[databricks]-[2026-11]/agent.py"

run-bcbs-crewai:
	$(PYTHON) "[bcbs239-lineage]-[crewai]-[ollama]-[2026-12]/agent.py"

run-compare:
	$(PYTHON) "[decision-econ]-[generic]-[ollama]-[2026-12]/agent.py"

test:
	$(VENV)/bin/pytest -v -m "not integration"

test-all:
	$(VENV)/bin/pytest -v

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

help:
	@echo "Available targets:"
	@echo "  setup               Create venv and install dependencies"
	@echo "  run-example1        LangGraph tool-use baseline (Ollama)"
	@echo "  run-bcbs            BCBS-239 lineage (LangGraph + Ollama)"
	@echo "  run-bcbs-databricks BCBS-239 lineage (LangGraph + Databricks)"
	@echo "  run-bcbs-crewai     BCBS-239 lineage (CrewAI + Ollama)"
	@echo "  run-compare         Decision economics comparison"
	@echo "  test                Unit tests only"
	@echo "  test-all            All tests including integration"
	@echo "  clean               Remove venv and cache"
