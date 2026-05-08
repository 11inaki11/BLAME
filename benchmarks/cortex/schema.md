# CORTEX Benchmark — Schema

## Domain

**Medical rehabilitation robotics.** CORTEX is a multi-agent clinical decision support framework designed to assist in the operation of the Discover2Walk (D2W) robotic exoskeleton for paediatric neurorehabilitation of children with cerebral palsy.

Each case is a full multi-agent consultation session in which one or more components have been deliberately degraded or misconfigured. The benchmark tests whether a fault-attribution system can identify *which* components are faulty from the resulting conversation.

---

## Agents

| Agent key | Display name | Dimension index |
|-----------|--------------|-----------------|
| `doctor` | Diagnosis Doctor | 0 |
| `chief` | Chief of Rehabilitation | 1 |
| `physio_general` | General Physiotherapist | 2 |

---

## Fault Dimensions (7)

The ground truth is a binary vector of length 7. Each position corresponds to one system component:

| Index | Name | Fault signature |
|-------|------|-----------------|
| 0 | Diagnosis Doctor | Diagnosis inconsistent with test results; incorrect goals or contraindications |
| 1 | Chief of Rehabilitation | Wrong programme selection; miscommunication of treatment plan to parent/guardian |
| 2 | General Physiotherapist | Training volume or intensity exceeding what the functional profile supports |
| 3 | Discover2Walk Exoskeleton | Sensor miscalibration or hardware fault producing corrupted biomechanical data |
| 4 | Patient | Unexpected physiological change or behaviour not reflected in the clinical record |
| 5 | Parent/Guardian | Incorrect information provided during the consultation |
| 6 | System Communication Channels | Message loss or corruption between agents |

`1` at position `i` means component `i` is **faulty**.  
`0` means the component is **operating normally**.

Example: `[1, 0, 0, 1, 0, 0, 0]` — Doctor and Exoskeleton are faulty; all others are normal.

---

## Session Phases

Each CORTEX case contains two phases, recorded in `session.messages[*].phase`:

| Phase | Description |
|-------|-------------|
| `cortex_session` | Main diagnostic workflow: Doctor → Chief → Physiotherapist → Chief |
| `poirot_analysis` | Post-session peer-consultation where agents review each other's reasoning |

---

## Case JSON Fields

```
case_id             string   Unique identifier, e.g. "cortex_session_10"
domain              string   Always "medical_rehabilitation"
system              string   Always "CORTEX"
agents              list     Agent keys present in this session
dimensions          list     The 7 dimension names (fixed order, see table above)
ground_truth_vector list     Binary vector of length 7
n_errors            int      Number of faulty components (sum of ground_truth_vector)
injected_hazards    string   Human-readable description of what was injected
faulty_components   list     Per-fault details (see below)
session             object   Full message log (see below)
metadata            object   Source session id, generation timestamp
```

### `faulty_components` entry

```json
{
  "dimension_index":   0,
  "dimension_name":    "Diagnosis Doctor",
  "fault_description": "Doctor produced a diagnosis inconsistent with test results..."
}
```

### `session` object

```
session.messages    list    Ordered list of every message in the session (see below)
```

### Message fields

| Field | Present when | Description |
|-------|-------------|-------------|
| `index` | always | Sequential position (1-based) |
| `type` | always | `HumanMessage`, `AIMessage`, `ToolMessage`, or `SystemMessage` |
| `phase` | always | `cortex_session` or `poirot_analysis` |
| `from` | always | Sender: agent key, `"system"`, or `"tool:<tool_name>"` |
| `to` | when known | Recipient: agent key or `null` |
| `content` | when non-empty | Text content |
| `tool_calls` | AIMessage with calls | List of tool names invoked |
| `tool_name` | ToolMessage | Name of the tool that produced this result |

---

## Agent JSON Fields (`agents/`)

```
agent_id              string   Agent key, e.g. "doctor"
display_name          string   Human-readable name
dimension_index       int      Index in ground_truth_vector this agent maps to
fault_error_signature string   Characteristic failure mode description
system_prompt         string   Full system prompt the agent received
tools                 list     Tools available: {name, description, parameters}
exclusive_tools       list     Tool names only this agent can call
```

---

## Results CSV (`results/results.csv`)

One row per model evaluation, appended by `evaluate.py --append-results`:

```
case_id, model, predicted_vector, ground_truth_vector, is_correct, n_errors, timestamp
cortex_session_10, GPT-4o, "1,0,0,1,0,0,0", "1,0,0,1,0,0,0", True, 2, 2025-04-25T10:00:00
```

| Column | Description |
|--------|-------------|
| `case_id` | Benchmark case identifier |
| `model` | Model or system name passed via `--model` |
| `predicted_vector` | Comma-separated binary prediction |
| `ground_truth_vector` | Comma-separated ground truth |
| `is_correct` | `True` only when every bit matches (exact match) |
| `n_errors` | Number of faults in ground truth (`sum(ground_truth_vector)`) |
| `timestamp` | UTC ISO-8601 timestamp of the evaluation run |
