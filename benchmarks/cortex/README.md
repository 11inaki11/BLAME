# CORTEX Benchmark

**Domain:** Medical Rehabilitation (Paediatric Gait Rehabilitation)  
**System:** CORTEX — a three-agent LLM system that assists clinical teams in planning rehabilitation programmes for children with cerebral palsy using the Discover2Walk (D2W) exoskeleton.

## Agents

| Agent | Role |
|-------|------|
| Diagnosis Doctor | Performs clinical assessments and produces a diagnosis report |
| Chief of Rehabilitation | Selects and adapts D2W rehabilitation plans |
| General Physiotherapist | Provides physiotherapy-specific expertise |

Full agent definitions (system prompts, tools) are in [`agents/`](agents/).

## Fault Dimensions (7)

See [`schema.md`](schema.md) for the full dimension specification.

| Index | Dimension |
|-------|-----------|
| 0 | Diagnosis Doctor |
| 1 | Chief of Rehabilitation |
| 2 | General Physiotherapist |
| 3 | Discover2Walk Exoskeleton (Sensor) |
| 4 | Patient |
| 5 | Parent/Guardian |
| 6 | System Communication Channels |

A dimension is `1` if that component exhibited a fault during the session; `0` otherwise.

## Cases

15 cases covering 1- and 2-fault scenarios across all 7 dimensions.  
Each case is a self-contained JSON file in [`cases/`](cases/).

### Case structure

```json
{
  "case_id": "cortex_session_50",
  "domain": "cortex",
  "agents": ["doctor", "chief", "physio_general"],
  "dimensions": ["Diagnosis Doctor", ...],
  "ground_truth_vector": [1, 0, 0, 0, 0, 0, 0],
  "n_errors": 1,
  "injected_hazards": "...",
  "faulty_components": [...],
  "session": {
    "patient_id": "...",
    "messages": [
      {
        "index": 1,
        "type": "HumanMessage",
        "phase": "cortex_session",
        "from": "system",
        "to": "doctor",
        "content": "Below you have the initial medical report..."
      },
      ...
    ]
  }
}
```

### Message phases

- `cortex_session` — the main multi-agent diagnostic session
- `poirot_analysis` — post-session peer-consultation phase (present in most cases)

### Message types

- `HumanMessage` — input to an agent (from system, another agent, or a tool result)
- `AIMessage` — an agent's response, optionally with `tool_calls`
- `ToolMessage` — result returned by a tool call
- `SystemMessage` — agent system prompt context

## Quick start

```bash
# Evaluate your system's predictions
python ../../evaluate.py --benchmark cortex --predictions my_predictions.csv --model "MyModel"
```

Predictions CSV format:
```
case_id,predicted_vector
cortex_session_10,"0,0,0,0,0,0,0"
cortex_session_20,"1,0,0,0,0,0,0"
```

## Results

See [`results/results.csv`](results/results.csv) for all submitted evaluations.
