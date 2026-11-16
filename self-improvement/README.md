# Self-Improvement Patterns

> *How agents improve themselves — without changing model weights.*

This category benchmarks the **self-improvement layer** of the agent stack:
frameworks and patterns that optimise prompts, harnesses, or answers
autonomously, using feedback signals rather than human intervention.

---

## Why a separate category?

The existing categories measure how well an agent executes a task
(`reasoning/`) or how agents connect (`topology/`). Self-improvement adds a
**vertical axis** — quality over iterations or across tasks — that those
categories do not capture.

| Existing categories | Axis |
|---|---|
| `reasoning/` | How an agent thinks *within* a task |
| `topology/` | How agents are arranged |
| `decision-econ/` | Cost vs quality tradeoff |
| **`self-improvement/`** | How an agent improves *across* tasks or iterations |

---

## The new CPCD question

Standard CPCD asks: *what does one correct decision cost?*

Self-improvement CPCD asks: *does the improvement justify the extra cost?*

```
CPCD_delta = CPCD_before − CPCD_after
```

A positive delta means the agent produces higher quality per dollar after
self-improvement. A negative delta means the optimisation cost more than it
was worth.

---

## Examples

| Folder | Pattern | Framework | Backend | Status |
|---|---|---|---|---|
| `[prompt-opt]-[dspy]-[ollama]` | Prompt Optimisation | DSPy | Ollama | ✅ Done |
| `[research-swarm]-[ollama-harness]-[ollama]` | Research Swarm / Self-Critique | ollama-harness | Ollama | ✅ Done |
| `[harness-opt]-[harness2]-[vertexai]` | Recursive Harness Optimisation | Google harness² | Vertex AI | 🔜 Planned |

---

## Self-improvement taxonomy

| Type | When it runs | Scope | Example framework |
|---|---|---|---|
| **Prompt optimisation** | Before inference (compile) | Across tasks | DSPy |
| **Self-critique loop** | During inference (per query) | Single answer | ollama-harness |
| **Recursive harness opt** | After inference (across tasks) | Full harness | Google harness² |

---

## References

| Source | Relevance |
|---|---|
| [DSPy — Stanford NLP](https://github.com/stanfordnlp/dspy) | Compiler-driven prompt optimisation |
| [ollama-harness — PyPI](https://pypi.org/project/ollama-harness/) | Local self-improving research swarm |
| [Google harness² — GitHub](https://github.com/google-research/harness2) | Recursive harness optimisation |
| [arXiv:2606.05922 — RHO](https://arxiv.org/abs/2606.05922) | Retrospective Harness Optimisation |
| [arXiv:2608.15071 — Evo-Harness](https://arxiv.org/abs/2608.15071) | Context-to-harness skill compilation |

---

← [Back to repo root](../README.md) · [Full pattern catalogue](../PATTERNS.md)
