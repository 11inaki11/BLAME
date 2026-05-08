# Leaderboard

Exact vector match accuracy (prediction must match all fault dimensions simultaneously).  
POIROT entries use majority vote over multiple runs per case.

Last updated: 2026-04-25

## CORTEX (Medical Rehabilitation — 7 dimensions)

| System | Backbone | Overall | 1-fault | 2-fault | 5-fault | Cases |
|--------|----------|---------|---------|---------|---------|-------|
| POIROT | gemini-2.5-pro | 53.3% | 60.0% | 55.6% | 0.0% | 15 |
| POIROT | deepseek-reasoner | 46.7% | 100.0% | 22.2% | 0.0% | 15 |
| POIROT | gpt-oss:120b | 33.3% | 60.0% | 22.2% | 0.0% | 15 |
| POIROT | gpt-oss:20b | 20.0% | 20.0% | 22.2% | 0.0% | 15 |

## TradingAgents (Algorithmic Trading — 15 dimensions)

| System | Backbone | Overall | 1-fault | 2-fault | 3+-fault | Cases |
|--------|----------|---------|---------|---------|---------|-------|
| POIROT | gpt-oss:120b (vllm) | 48.7% | 48.7% | — | — | 6 |
| POIROT | gpt-oss:20b (vllm) | 48.4% | 48.4% | — | — | 6 |

---

## How to submit results

Run the evaluator with `--append-results` and open a pull request adding your row to this table.  
See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
