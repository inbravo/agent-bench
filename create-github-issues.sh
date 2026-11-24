#!/usr/bin/env bash
# create-github-issues.sh
# Creates GitHub labels, milestones (one per pattern), and issues
# (dev + stress-test) for every agent-bench example.
#
# Prerequisites: gh CLI authenticated, run from the repo root.
# Re-run safe: label/milestone creation uses || true.
#
# Usage:
#   chmod +x create-github-issues.sh
#   ./create-github-issues.sh

set -euo pipefail

REPO="inbravo/agent-bench"
ASSIGNEE="inbravo"

log() { echo "▸ $*"; }
ok()  { echo "  ✓ $*"; }

# ── 1. Labels ─────────────────────────────────────────────────────────────────
log "Creating labels..."
gh label create "enhancement" \
  --color "84b6eb" \
  --description "New example implementation" \
  --repo "$REPO" 2>/dev/null || true
ok "label: enhancement"

gh label create "stress-test" \
  --color "e4e669" \
  --description "Stress-test and pass/fail assertions for an example" \
  --repo "$REPO" 2>/dev/null || true
ok "label: stress-test"

# ── 2. Milestones (one per pattern, ASCII titles only) ────────────────────────
ensure_milestone() {
  local title="$1"
  local desc="$2"
  gh api "repos/${REPO}/milestones" \
    --method POST \
    --field title="${title}" \
    --field description="${desc}" \
    --jq ".number" 2>/dev/null || \
  gh api "repos/${REPO}/milestones?state=open&per_page=100" \
    --jq ".[] | select(.title == \"${title}\") | .number" | head -1
}

log "Creating milestones (one per pattern)..."
MS_TOOL_USE="Pattern: Tool Use"
MS_REACT="Pattern: ReAct"
MS_FW_SWAP="Pattern: Framework Swap"
MS_CPCD="Pattern: CPCD"
MS_PROMPT_OPT="Pattern: Prompt Optimisation"
MS_SELF_CRIT="Pattern: Self-Critique"

ensure_milestone "$MS_TOOL_USE"    "Single-shot tool dispatch" >/dev/null || true
ok "milestone: $MS_TOOL_USE"
ensure_milestone "$MS_REACT"       "Reason+Act loop" >/dev/null || true
ok "milestone: $MS_REACT"
ensure_milestone "$MS_FW_SWAP"     "Same task, different framework" >/dev/null || true
ok "milestone: $MS_FW_SWAP"
ensure_milestone "$MS_CPCD"        "Cost-Per-Correct-Decision metric" >/dev/null || true
ok "milestone: $MS_CPCD"
ensure_milestone "$MS_PROMPT_OPT"  "DSPy BootstrapFewShot compilation" >/dev/null || true
ok "milestone: $MS_PROMPT_OPT"
ensure_milestone "$MS_SELF_CRIT"   "Producer-critique revision loop" >/dev/null || true
ok "milestone: $MS_SELF_CRIT"

echo ""
log "Milestones ready. Creating issues..."
echo ""

# ── 3. Issue factory ──────────────────────────────────────────────────────────
# create_issues <tag> <milestone_title> <name> <folder> <pattern> <scenario> <framework> <assertions>
create_issues() {
  local tag="$1"
  local ms_title="$2"   # passed directly to --milestone (gh uses title)
  local name="$3"
  local folder="$4"
  local pattern="$5"
  local scenario="$6"
  local framework="$7"
  local assertions="$8"

  # ── Dev issue ──────────────────────────────────────────────────────────────
  local dev_body
  dev_body=$(cat <<EOF
## Overview
Implement the **${pattern}** pattern for the **${scenario}** scenario using **${framework}**.

## Folder
\`${folder}/\`

## What to build
- \`agent.py\` — main agent using the ${pattern} pattern
- \`config.yaml\` — model, backend, and scorer settings
- \`rubric.yaml\` — evaluation criteria with per-criterion weights summing to 1.0
- \`README.md\` — pattern description, design decisions, framework comparison table
- \`tests/test_local.py\` — unit tests for tool functions and agent construction

## Definition of done
- [ ] \`python ${folder}/agent.py\` runs end-to-end without errors
- [ ] \`scorer.py\` returns \`{ quality_score, token_cost_usd, cpcd }\`
- [ ] All tests in \`tests/test_local.py\` pass
- [ ] README documents at least one "When NOT to use it" for this pattern
- [ ] Folder follows the \`[pattern]-[framework]-[backend]\` naming convention

## Pattern context
See [PATTERNS.md](../blob/main/PATTERNS.md) for full description and "When NOT to use it" notes.
EOF
)

  gh issue create \
    --repo "$REPO" \
    --title "[${tag}] Implement: ${name}" \
    --label "enhancement" \
    --assignee "$ASSIGNEE" \
    --milestone "${ms_title}" \
    --body "$dev_body" \
    > /dev/null
  ok "[${tag}] Implement: ${name}"

  # ── Stress-test issue ──────────────────────────────────────────────────────
  local stress_body
  stress_body=$(cat <<EOF
## Overview
Stress-test the **${pattern}** implementation in \`${folder}/\` with concrete pass/fail assertions.

## Folder
\`${folder}/\`

## Assertions — all must pass

${assertions}

## How to run
\`\`\`bash
# Unit tests
python -m pytest ${folder}/tests/test_local.py -v

# Full agent run
python ${folder}/agent.py

# CPCD scorer
python _shared/scorer.py --config ${folder}/config.yaml
\`\`\`

## Pass criteria
- All pytest assertions green
- \`quality_score >= 0.7\` on at least 3 consecutive runs
- \`cpcd\` value logged without division-by-zero or NaN
- No unhandled exceptions across 10 consecutive runs
EOF
)

  gh issue create \
    --repo "$REPO" \
    --title "[${tag}] Stress test: ${name}" \
    --label "stress-test" \
    --assignee "$ASSIGNEE" \
    --milestone "${ms_title}" \
    --body "$stress_body" \
    > /dev/null
  ok "[${tag}] Stress test: ${name}"
}

# ─────────────────────────────────────────────────────────────────────────────
# Pattern: Tool Use
# ─────────────────────────────────────────────────────────────────────────────
log "Pattern: Tool Use"

create_issues "tool-use" "$MS_TOOL_USE" \
  "Weather assistant (LangGraph)" \
  "reasoning/[tool-use]-[langgraph]-[ollama]" \
  "Tool Use" "Weather assistant" "LangGraph" \
"- [ ] \`get_current_weather('london')\` returns a dict with keys \`temperature\`, \`unit\`, \`condition\`
- [ ] \`convert_temperature(100, 'C')\` returns \`212.0\` (Fahrenheit)
- [ ] Agent selects \`get_current_weather\` on a city query without being told to
- [ ] Agent selects \`convert_temperature\` when unit conversion is requested
- [ ] Agent does NOT call both tools when only one is needed
- [ ] Response includes the city name, temperature value, and unit
- [ ] \`quality_score\` >= 0.7 when judged against the rubric
- [ ] Token count for a single-tool call does not exceed 2000 tokens"

create_issues "tool-use" "$MS_TOOL_USE" \
  "Weather assistant (CrewAI)" \
  "reasoning/[tool-use]-[crewai]-[ollama]" \
  "Tool Use" "Weather assistant" "CrewAI" \
"- [ ] \`get_current_weather('tokyo')\` returns the mock value from MOCK_WEATHER_DB
- [ ] CrewAI \`BaseTool\` subclass raises \`ToolException\` for an unknown city rather than returning empty
- [ ] Crew produces exactly one final answer (no duplicate agent turns)
- [ ] Response cites both temperature and condition
- [ ] \`quality_score\` >= 0.7 across 3 consecutive runs
- [ ] CPCD for CrewAI is computed and logged; no NaN or division-by-zero"

create_issues "tool-use" "$MS_TOOL_USE" \
  "Weather assistant (AG2)" \
  "reasoning/[tool-use]-[ag2]-[ollama]" \
  "Tool Use" "Weather assistant" "AG2" \
"- [ ] Both tools are registered in \`llm_config['functions']\` via \`autogen.register_function\`
- [ ] \`build_agents()\` returns a tuple \`(AssistantAgent, UserProxyAgent)\`
- [ ] Conversation terminates when 'TERMINATE' appears in the last message
- [ ] \`max_turns\` is respected — conversation never exceeds 6 turns
- [ ] \`quality_score\` >= 0.7 when judged against the rubric
- [ ] Native Ollama tool calling (\`api_type: 'ollama'\`, \`native_tool_calls: True\`) is used"

# ─────────────────────────────────────────────────────────────────────────────
# Pattern: ReAct
# ─────────────────────────────────────────────────────────────────────────────
log "Pattern: ReAct"

create_issues "react" "$MS_REACT" \
  "Book finder (LangGraph)" \
  "reasoning/[react]-[langgraph]-[ollama]" \
  "ReAct" "Book finder" "LangGraph" \
"- [ ] Agent emits at least one Thought -> Action -> Observation cycle before the final answer
- [ ] \`search_book('dune')\` returns a dict with \`title\`, \`author\`, \`year\`
- [ ] \`get_similar_books('Dune')\` returns a non-empty list
- [ ] \`get_book_rating('Dune')\` returns a float between 0.0 and 5.0
- [ ] Agent does NOT call \`get_similar_books\` before \`search_book\` on a bare title query
- [ ] \`quality_score\` >= 0.7 across 3 runs
- [ ] Step count logged; average steps <= 5 for a single-book query"

create_issues "react" "$MS_REACT" \
  "Book finder (CrewAI)" \
  "reasoning/[react]-[crewai]-[ollama]" \
  "ReAct" "Book finder" "CrewAI" \
"- [ ] System message contains the words 'Thought', 'Action', and 'Observation'
- [ ] All three tools (\`search_book\`, \`get_similar_books\`, \`get_book_rating\`) are registered on the agent
- [ ] Agent produces a 'Final Answer:' line before the crew task ends
- [ ] No tool is called with an empty-string argument
- [ ] \`quality_score\` >= 0.7 when judged against the rubric
- [ ] CPCD <= 2x LangGraph CPCD for the same query (portability baseline)"

create_issues "react" "$MS_REACT" \
  "Book finder (AG2)" \
  "reasoning/[react]-[ag2]-[ollama]" \
  "ReAct" "Book finder" "AG2" \
"- [ ] System message contains 'Thought', 'Action', 'Observation', and 'Final Answer'
- [ ] All three tools registered via \`autogen.register_function\`
- [ ] \`max_consecutive_auto_reply\` is set to 8 or higher
- [ ] Conversation terminates cleanly on 'TERMINATE' or when max turns reached
- [ ] Agent does not loop indefinitely on an unknown book title — returns a 'not found' answer within max turns
- [ ] \`quality_score\` >= 0.7 across 3 consecutive runs"

# ─────────────────────────────────────────────────────────────────────────────
# Pattern: Framework Swap
# ─────────────────────────────────────────────────────────────────────────────
log "Pattern: Framework Swap"

create_issues "fw-swap" "$MS_FW_SWAP" \
  "Blog post crew (CrewAI)" \
  "topology/[fw-swap]-[crewai]-[ollama]" \
  "Framework Swap" "Blog post crew (Researcher -> Writer -> Editor)" "CrewAI" \
"- [ ] Three agents exist: Researcher, Writer, Editor in that sequential order
- [ ] Researcher output is passed verbatim as Writer input (no data loss between tasks)
- [ ] Editor output is the crew's final result — no extra agent turn after Editor
- [ ] Final output contains at least 150 words
- [ ] No agent calls a tool that belongs to a different agent's role
- [ ] \`quality_score\` >= 0.7 when rubric evaluates structure, coherence, and completeness
- [ ] Crew completes in <= 10 LLM calls total"

# ─────────────────────────────────────────────────────────────────────────────
# Pattern: CPCD
# ─────────────────────────────────────────────────────────────────────────────
log "Pattern: CPCD"

create_issues "cpcd" "$MS_CPCD" \
  "Multi-framework comparison dashboard (Multi)" \
  "decision-econ/[cpcd]-[multi]-[ollama]" \
  "CPCD" "Multi-framework CPCD comparison dashboard" "Multi (LangGraph + CrewAI)" \
"- [ ] Dashboard computes CPCD for at least 2 frameworks on the same task
- [ ] \`token_cost_usd\` is non-zero when a paid backend is used; 0.0 acceptable for Ollama
- [ ] \`quality_score\` is in the range [0.0, 1.0] — no value outside this range
- [ ] Division-by-zero is handled gracefully when \`quality_score == 0\`
- [ ] Output table contains columns: framework, quality_score, token_cost_usd, cpcd
- [ ] CPCD values are ranked lowest-first (lower = better)
- [ ] Re-running with the same inputs produces CPCD values within +/-10% (determinism check)"

# ─────────────────────────────────────────────────────────────────────────────
# Pattern: Prompt Optimisation
# ─────────────────────────────────────────────────────────────────────────────
log "Pattern: Prompt Optimisation"

create_issues "prompt-opt" "$MS_PROMPT_OPT" \
  "BootstrapFewShot on weather task (DSPy)" \
  "self-improvement/[prompt-opt]-[dspy]-[ollama]" \
  "Prompt Optimisation" "BootstrapFewShot optimiser on weather task" "DSPy" \
"- [ ] \`CPCD_before\` and \`CPCD_after\` are both logged; \`CPCD_delta = CPCD_before - CPCD_after\`
- [ ] \`CPCD_delta\` >= 0 (optimised run is not worse than the baseline)
- [ ] BootstrapFewShot compiles with at least 3 training examples — fewer raises a clear error
- [ ] Compiled prompt contains at least one few-shot demonstration (not empty)
- [ ] \`quality_score\` after optimisation >= \`quality_score\` before on the same eval set
- [ ] Optimiser does not call the LLM more than 50 times during compile
- [ ] The compiled module can be saved and reloaded without re-running the optimiser"

# ─────────────────────────────────────────────────────────────────────────────
# Pattern: Self-Critique
# ─────────────────────────────────────────────────────────────────────────────
log "Pattern: Self-Critique"

create_issues "self-critique" "$MS_SELF_CRIT" \
  "Producer-critique revision loop (ollama-harness)" \
  "self-improvement/[research-swarm]-[ollama-harness]-[ollama]" \
  "Self-Critique" "Producer-critique revision loop" "ollama-harness" \
"- [ ] Critic returns exactly 'ACCEPT' or 'REVISE: <text>' — any other format is a test failure
- [ ] Loop terminates within \`max_revisions\` turns — never runs forever
- [ ] When critic and producer use different system prompts, at least one revision occurs on a deliberately flawed input
- [ ] \`CPCD_delta\` is positive when the revision loop improves a flawed first draft
- [ ] \`harness_mode: 'fallback'\` path (stdlib urllib) produces the same final answer structure as \`'native'\`
- [ ] No revision occurs when the first answer already meets the quality threshold
- [ ] Token count per revision loop is logged; total does not exceed \`max_revisions * 2\` LLM calls"

# ─────────────────────────────────────────────────────────────────────────────
echo ""
log "All done. Issues created on ${REPO}."
