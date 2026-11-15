# ─────────────────────────────────────────────────────────────────────────────
# agent-bench — Makefile
# Author   : Amit Dixit (https://github.com/inbravo)
# ─────────────────────────────────────────────────────────────────────────────

PYTHON   := python
VENV     := .venv
PIP      := $(VENV)/bin/pip
PYTEST   := $(VENV)/bin/pytest

.PHONY: setup
setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install langgraph langchain-community crewai pyyaml pytest

.PHONY: tool-use
tool-use:
	$(PYTHON) reasoning/\[tool-use\]-\[langgraph\]-\[ollama\]/agent.py

.PHONY: react
react:
	$(PYTHON) reasoning/\[react\]-\[langgraph\]-\[ollama\]/agent.py

.PHONY: fw-swap
fw-swap:
	$(PYTHON) topology/\[fw-swap\]-\[crewai\]-\[ollama\]/agent.py

.PHONY: cpcd
cpcd:
	$(PYTHON) decision-econ/\[cpcd\]-\[multi\]-\[ollama\]/agent.py

.PHONY: test-tool-use
test-tool-use:
	$(PYTEST) reasoning/\[tool-use\]-\[langgraph\]-\[ollama\]/tests/ -v

.PHONY: test-react
test-react:
	$(PYTEST) reasoning/\[react\]-\[langgraph\]-\[ollama\]/tests/ -v

.PHONY: test-fw-swap
test-fw-swap:
	$(PYTEST) topology/\[fw-swap\]-\[crewai\]-\[ollama\]/tests/ -v

.PHONY: test
test:
	$(PYTEST) reasoning/ topology/ decision-econ/ -v

.PHONY: all
all: tool-use react fw-swap cpcd

.PHONY: help
help:
	@echo ""
	@echo "agent-bench — available targets"
	@echo "────────────────────────────────────────"
	@echo "  setup        Create venv and install dependencies"
	@echo "  tool-use     Run reasoning/[tool-use]-[langgraph]-[ollama]"
	@echo "  react        Run reasoning/[react]-[langgraph]-[ollama]"
	@echo "  fw-swap      Run topology/[fw-swap]-[crewai]-[ollama]"
	@echo "  cpcd         Run decision-econ/[cpcd]-[multi]-[ollama]"
	@echo "  test         Run all tests"
	@echo "  all          Run all completed examples"
	@echo "────────────────────────────────────────"
	@echo ""
