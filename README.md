# BLAME

Two domain-specific evaluation suites for **multi-agent fault attribution** in safety-critical environments.

Given a complete record of a multi-agent session where one or more components have failed, can your system correctly identify *which* components are faulty?

---

## Benchmarks at a glance

| Benchmark | Domain | Agents | Fault dimensions | Cases |
|-----------|--------|--------|-----------------|-------|
| [CORTEX](benchmarks/cortex/) | Medical rehabilitation (paediatric gait) | 3 | 7 | 15 |
| [TradingAgents](benchmarks/trading_agents/) | Algorithmic trading | 12 | 15 | 6 |

---

## Repository layout

```text
blame/
├── evaluate.py                         # Evaluation script
├── requirements.txt
├── leaderboard.md                      # Results across models
├── CONTRIBUTING.md
└── benchmarks/
    ├── cortex/
    │   ├── schema.md                   # Dimension definitions
    │   ├── agents/                     # Agent definitions (system prompt, tools)
    │   │   ├── doctor.json
    │   │   ├── chief.json
    │   │   └── physio_general.json
    │   ├── cases/                      # One JSON per session
    │   │   ├── cortex_session_10.json
    │   │   └── ...
    │   └── results/
    │       └── results.csv             # Evaluation results (appended by evaluate.py)
    └── trading_agents/
        ├── schema.md
        ├── agents/
        │   ├── market_analyst.json
        │   └── ...
        ├── cases/
        │   ├── trading_session_2.json
        │   └── ...
        └── results/
            └── results.csv
```

---

## Quick start

```bash
pip install -r requirements.txt

# Run your fault-attribution system on the cases, produce a predictions CSV:
#   case_id,predicted_vector
#   cortex_session_10,"0,0,0,0,0,1,0"
#   cortex_session_20,"0,1,0,0,0,0,0"
#   ...

# Evaluate against ground truth
python evaluate.py --benchmark cortex --predictions my_predictions.csv --model "MySystem-v1"

# Optionally save results to results/results.csv
python evaluate.py --benchmark cortex --predictions my_predictions.csv \
    --model "MySystem-v1" --append-results
```

The evaluator prints accuracy by fault count and per-dimension precision/recall, then optionally appends rows to `benchmarks/<benchmark>/results/results.csv`.

### Example script

[`example_baseline.py`](example_baseline.py) demonstrates the full workflow end-to-end:
loading cases, reading session messages, producing a predictions CSV, and evaluating.
It also implements three trivial baselines (all-zeros, random, message-count heuristic)
as concrete starting points.

```bash
# Run a trivial baseline and see the evaluation report
python example_baseline.py --benchmark cortex --strategy random

# Explore a different benchmark without evaluating
python example_baseline.py --benchmark trading_agents --strategy zeros --no-eval
```

Replace the `predict_*` functions with your own system to benchmark it.

---

## The task

Each benchmark case is a real multi-agent session with **one or more injected faults**. Your system must read the full session and output a binary fault vector of length equal to the number of dimensions.

```text
predicted_vector[i] = 1   if component i was faulty
predicted_vector[i] = 0   if component i was normal
```

### Example (CORTEX — 7 dimensions)

```text
Index:      0                1                      2                       3                            4        5                6
Component:  Diagnosis Doctor Chief of Rehabilitation General Physiotherapist Discover2Walk Exoskeleton   Patient  Parent/Guardian  Comm. Channels
```

If the session log shows the Doctor produced a diagnosis inconsistent with the test results:

```text
ground_truth_vector = [1, 0, 0, 0, 0, 0, 0]
                       ^
                       Doctor is faulty; all others are normal
```

If both the Doctor and the Exoskeleton sensor were faulty:

```text
ground_truth_vector = [1, 0, 0, 1, 0, 0, 0]
                       ^        ^
                       Doctor   Exoskeleton
```

Your system reads the session and outputs a vector in the same format. A prediction is **correct** only if the entire vector matches ground truth (exact match). Partial credit metrics (precision/recall per dimension) are also reported.

---

## Case format

Every case is a self-contained JSON file. Top-level fields:

```json
{
  "case_id":             "cortex_session_50",
  "domain":              "medical_rehabilitation",
  "system":              "CORTEX",
  "agents":              ["doctor", "chief", "physio_general"],
  "dimensions":          ["Diagnosis Doctor", "Chief of Rehabilitation", ...],
  "ground_truth_vector": [1, 0, 0, 0, 0, 0, 0],
  "n_errors":            1,
  "injected_hazards":    "Human-readable description of what was broken",
  "faulty_components":   [...],
  "session":             { ... },
  "metadata":            { ... }
}
```

| Field | Description |
|-------|-------------|
| `dimensions` | Ordered list of component names — index i maps to `ground_truth_vector[i]` |
| `ground_truth_vector` | Binary vector; `1` = faulty, `0` = normal |
| `n_errors` | Number of faults (`sum(ground_truth_vector)`) |
| `injected_hazards` | Plain-text description of injected fault(s) for human reference |
| `faulty_components` | List of `{dimension_index, dimension_name, fault_description}` for faulty dims only |
| `session` | The full agent conversation (see below) |

### `faulty_components` entry

```json
{
  "dimension_index": 0,
  "dimension_name":  "Diagnosis Doctor",
  "fault_description": "Doctor produced a diagnosis inconsistent with test results..."
}
```

---

## Session messages

`session.messages` is a **single ordered list** of every message exchanged during the session, covering the full diagnostic/trading workflow and — where applicable — a post-session peer-consultation phase.

```json
"session": {
  "messages": [
    {
      "index":   1,
      "type":    "HumanMessage",
      "phase":   "cortex_session",
      "from":    "system",
      "to":      "doctor",
      "content": "Below you have the initial medical report of the patient..."
    },
    {
      "index":   2,
      "type":    "AIMessage",
      "phase":   "cortex_session",
      "from":    "doctor",
      "tool_calls": ["patient_retriever_tool", "perform_cardiopulmonary_test", ...]
    },
    {
      "index":   3,
      "type":    "ToolMessage",
      "phase":   "cortex_session",
      "from":    "tool:patient_retriever_tool",
      "to":      "doctor",
      "tool_name": "patient_retriever_tool",
      "content": "Document 1: CORTEX System Medical Report..."
    },
    ...
  ]
}
```

### Message fields

| Field | Present when | Description |
|-------|-------------|-------------|
| `index` | always | Sequential position in the conversation (1-based) |
| `type` | always | `HumanMessage`, `AIMessage`, `ToolMessage`, or `SystemMessage` |
| `phase` | CORTEX only | `cortex_session` or `poirot_analysis` |
| `from` | always | Sender: agent id, `"system"`, or `"tool:<tool_name>"` |
| `to` | when known | Recipient: agent id, `"broadcast"`, or `None` |
| `content` | when non-empty | Text content of the message |
| `tool_calls` | AIMessage with calls | List of tool names called by this agent |
| `tool_name` | ToolMessage | Name of the tool that produced this result |

### Message types

- **`HumanMessage`** — input injected into an agent's context (patient report, peer request, system instruction)
- **`AIMessage`** — an agent's response; may include `tool_calls` if the agent invoked tools
- **`ToolMessage`** — result returned by a tool call; `from` is `"tool:<name>"`, `to` is the calling agent
- **`SystemMessage`** — the agent's system prompt, included once per agent in TradingAgents cases

### Phases (CORTEX only)

| Phase | Description |
|-------|-------------|
| `cortex_session` | Main diagnostic session (Doctor → Chief → Physiotherapist workflow) |
| `poirot_analysis` | Post-session peer-consultation where agents review each other's reasoning |

---

## Agent definitions

Each benchmark includes an `agents/` directory with one JSON per agent. This lets you understand — or recreate — each agent's role, capabilities, and fault signature.

```json
{
  "agent_id":              "doctor",
  "display_name":          "Diagnosis Doctor",
  "dimension_index":       0,
  "fault_error_signature": "Error signature: ...",
  "system_prompt":         "You are a highly specialized medical expert...",
  "tools": [
    {
      "name":        "perform_cardiopulmonary_test",
      "description": "Performs a cardiopulmonary endurance assessment on the patient and returns the results.",
      "parameters":  []
    },
    ...
  ],
  "exclusive_tools": ["general_medicine_retriever_tool", "perform_cardiopulmonary_test", ...]
}
```

| Field | Description |
|-------|-------------|
| `dimension_index` | Maps this agent to `dimensions[i]` and `ground_truth_vector[i]` in every case |
| `fault_error_signature` | Description of the characteristic failure mode for this component |
| `system_prompt` | The full system prompt the agent received |
| `tools` | List of tools available to the agent, with description and parameter schema |
| `exclusive_tools` | Tools that *only* this agent can call — useful for attributing `AIMessage` senders |

---

## Evaluation metric

**Primary:** exact vector match accuracy — a prediction is correct only if all bits match.

**Secondary (reported per benchmark run):**

- Accuracy by fault count (`n_errors = 1`, `2`, `3+`)
- Per-dimension TP / FP / FN, precision, recall

```bash
python evaluate.py --benchmark cortex --predictions predictions.csv --model "GPT-4o"
```

Output example:

```text
============================================================
  CORTEX — Evaluation Report
============================================================
  Model    : GPT-4o
  Cases    : 15
  Correct  : 7  (46.7%)

  Accuracy by fault count:
    1 fault(s): 4/5  (80.0%)
    2 fault(s): 3/9  (33.3%)
    5 fault(s): 0/1  (0.0%)

  Per-dimension (TP/FP/FN):
    dim[0]  TP=4  FP=1  FN=1  P=0.80  R=0.80
    ...
============================================================
```

---

## Leaderboard

See [leaderboard.md](leaderboard.md) for submitted results. Rows are added via `--append-results` + a pull request.

---

## Contributing

**BLAME is an open benchmark — contributions are welcome and actively encouraged.**

There are two ways to contribute:

- **Evaluate your system** on an existing benchmark and submit results via pull request
- **Add a new benchmark domain** — if you have a multi-agent system where you can inject
  controlled faults into individual components, it is a strong candidate for inclusion

New domains are especially valuable: the benchmark grows more meaningful as it covers
more diverse systems, failure modes, and agent architectures. You do not need a production
system — research prototypes with injected faults are exactly what we are looking for.

See [CONTRIBUTING.md](CONTRIBUTING.md) for submission guidelines, the required case format,
and tips on domain design.
