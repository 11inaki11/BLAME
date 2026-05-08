# Contributing to BLAME

BLAME grows through community contributions. There are two ways to contribute:

1. **Evaluate your system** on an existing benchmark and submit results
2. **Add a new benchmark domain** — a multi-agent system with injected faults

Both are equally valuable. New domains are especially encouraged: the more diverse
the systems represented, the more meaningful the benchmark becomes.

---

## 1. Submitting results for a new model or system

Run your fault-attribution system on the benchmark cases and produce a `predictions.csv`:

```csv
case_id,predicted_vector
cortex_session_10,"1,0,0,1,0,0,0"
cortex_session_20,"0,0,0,0,0,0,0"
```

Then evaluate and record the results:

```bash
python evaluate.py --benchmark cortex \
    --predictions predictions.csv \
    --model "YourSystem-v1" \
    --append-results
```

Open a pull request with:

- The updated `benchmarks/<benchmark>/results/results.csv`
- A new row in `leaderboard.md`

---

## 2. Adding a new benchmark domain

> **We actively welcome new systems.** If you have a multi-agent system where you
> can inject controlled faults, it is a good candidate for BLAME. You do not need
> to build a perfect benchmark — opening an issue to discuss the domain first is
> the right place to start.

### What makes a good BLAME domain

- A **multi-agent system** where different components have distinct, attributable roles
- A way to **inject faults** into individual components (wrong data, corrupted prompts,
  misconfigured behaviour) and record the resulting session
- At least **20 cases** with varied fault locations and counts
- Each case must be **self-contained** — a reader must be able to attribute blame
  from the session transcript alone, without access to internal system state

### Minimum directory structure

```text
benchmarks/<domain>/
├── README.md          # Domain description, agent roles, quick start
├── schema.md          # Dimension definitions, message format, results CSV format
├── agents/            # One JSON per agent (system prompt, tools, dimension index)
├── cases/             # One JSON per session (≥ 20 files)
└── results/           # Empty directory (evaluate.py writes results.csv here)
```

### Case JSON — required fields

```json
{
  "case_id":             "yourdomain_session_001",
  "domain":              "your_domain_name",
  "system":              "YourSystemName",
  "agents":              ["agent_a", "agent_b"],
  "dimensions":          ["Component A", "Component B", "Infrastructure X"],
  "ground_truth_vector": [1, 0, 0],
  "n_errors":            1,
  "injected_hazards":    "Agent A was given contradictory instructions",
  "faulty_components": [
    {
      "dimension_index":   0,
      "dimension_name":    "Component A",
      "fault_description": "Specific description of what was injected"
    }
  ],
  "session": {
    "messages": [
      {
        "index":   1,
        "type":    "HumanMessage",
        "from":    "system",
        "to":      "agent_a",
        "content": "..."
      }
    ]
  },
  "metadata": {}
}
```

> **Important:** `dimensions[i]` must correspond exactly to `ground_truth_vector[i]`.
> The index ordering must be consistent across every case file and the `schema.md`.

### Hooking into the evaluator

Add your benchmark name to `BENCHMARKS` in `evaluate.py` (line 32):

```python
BENCHMARKS = ["cortex", "trading_agents", "your_domain"]
```

The evaluator will automatically discover your cases from `benchmarks/your_domain/cases/`.

### Case quality guidelines

- Every case must have at least one faulty component (`n_errors >= 1`)
- The session must contain enough diagnostic signal to be solvable (≥ 5 turns)
- Faults must be realistic and domain-grounded — not arbitrary or trivially obvious
- Include a mix of single-fault and multi-fault cases where possible
- Fault descriptions in `injected_hazards` and `faulty_components` must be specific
  enough for a human to verify the ground truth

### Submitting

Open an issue first to discuss the domain before preparing cases. This avoids
duplicate effort and lets us give early feedback on case quality and schema design.

Once ready, open a pull request with the full `benchmarks/<domain>/` directory and
a row in the main `README.md` benchmarks table.
