"""
example_baseline.py — BLAME Benchmark Usage Example
=====================================================

Demonstrates the full workflow for using the BLAME benchmark:
  1. Load cases from a benchmark
  2. Inspect case structure (session messages, dimensions, agents)
  3. Implement a fault-attribution system (three trivial baselines shown)
  4. Write a predictions CSV
  5. Evaluate against ground truth

Run:
  python example_baseline.py --benchmark cortex --strategy random
  python example_baseline.py --benchmark trading_agents --strategy zeros
  python example_baseline.py --benchmark cortex --strategy message_count

The --strategy argument selects one of three illustrative baselines:
  zeros         — always predict no fault (all zeros)
  random        — random binary vector (seed fixed for reproducibility)
  message_count — flag the dimension whose agent spoke most (heuristic)

After producing predictions.csv, the script calls evaluate.py automatically.
Replace the `predict()` function with your own system to benchmark it.
"""

import argparse
import csv
import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

BENCHMARKS = ["cortex", "trading_agents"]
BASE_DIR   = Path(__file__).parent / "benchmarks"


# --───────────────────────────────────────────────────────────────────────────
# Case loading
# --───────────────────────────────────────────────────────────────────────────

def load_cases(benchmark: str) -> list[dict]:
    """Return all cases for a benchmark as a list of dicts, sorted by case_id."""
    cases_dir = BASE_DIR / benchmark / "cases"
    cases = []
    for f in sorted(cases_dir.glob("*.json")):
        cases.append(json.loads(f.read_text(encoding="utf-8")))
    print(f"Loaded {len(cases)} cases from '{benchmark}'")
    return cases


def load_agents(benchmark: str) -> dict:
    """Return agent definitions keyed by agent_id."""
    agents_dir = BASE_DIR / benchmark / "agents"
    agents = {}
    for f in agents_dir.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        agents[d["agent_id"]] = d
    return agents


# --───────────────────────────────────────────────────────────────────────────
# Case inspection helpers — use these as a starting point for your own system
# --───────────────────────────────────────────────────────────────────────────

def get_messages(case: dict) -> list[dict]:
    """Return the ordered list of session messages."""
    return case["session"]["messages"]


def get_agent_messages(case: dict, agent_id: str) -> list[dict]:
    """Return all messages sent by a specific agent."""
    return [m for m in get_messages(case) if m.get("from") == agent_id]


def get_dimensions(case: dict) -> list[str]:
    """Return the ordered dimension names. dimensions[i] maps to ground_truth_vector[i]."""
    return case["dimensions"]


def get_agent_for_dimension(case: dict, agents: dict, dim_index: int) -> str | None:
    """Return the agent_id whose dimension_index matches dim_index, or None for infra dims."""
    for agent_id, agent in agents.items():
        if agent.get("dimension_index") == dim_index:
            return agent_id
    return None


# --───────────────────────────────────────────────────────────────────────────
# Baseline strategies
# Replace `predict()` with your own fault-attribution system.
# Input:  a single case dict  +  agents dict
# Output: a binary list of length len(case["dimensions"])
# --───────────────────────────────────────────────────────────────────────────

def predict_zeros(case: dict, agents: dict) -> list[int]:
    """Baseline: predict no fault in any component."""
    return [0] * len(get_dimensions(case))


def predict_random(case: dict, agents: dict, rng: random.Random) -> list[int]:
    """Baseline: random binary vector (at least one 1)."""
    n = len(get_dimensions(case))
    vec = [rng.randint(0, 1) for _ in range(n)]
    if sum(vec) == 0:           # ensure at least one fault is predicted
        vec[rng.randrange(n)] = 1
    return vec


def predict_message_count(case: dict, agents: dict) -> list[int]:
    """
    Heuristic baseline: count how many AIMessages each agent produced.
    Flag the dimension whose agent generated the most output.

    This is intentionally simple — it ignores message *content* entirely.
    A real system would read the session and reason about anomalies.
    """
    dims = get_dimensions(case)
    n    = len(dims)

    # Count AIMessages per agent
    counts: Counter = Counter()
    for msg in get_messages(case):
        if msg.get("type") == "AIMessage":
            counts[msg.get("from", "")] += 1

    # Map each dimension to its agent's message count
    dim_counts = []
    for i in range(n):
        agent_id = get_agent_for_dimension(case, agents, i)
        dim_counts.append(counts.get(agent_id, 0) if agent_id else 0)

    if max(dim_counts) == 0:
        return [0] * n          # no agent messages found — predict nothing

    max_count = max(dim_counts)
    return [1 if c == max_count else 0 for c in dim_counts]


# --───────────────────────────────────────────────────────────────────────────
# Main
# --───────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BLAME example baseline")
    parser.add_argument("--benchmark", "-b", choices=BENCHMARKS, required=True)
    parser.add_argument(
        "--strategy", "-s",
        choices=["zeros", "random", "message_count"],
        default="zeros",
        help="Which baseline strategy to use (default: zeros)",
    )
    parser.add_argument(
        "--out", default="predictions.csv",
        help="Output predictions CSV path (default: predictions.csv)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for the 'random' strategy (default: 42)",
    )
    parser.add_argument(
        "--no-eval", action="store_true",
        help="Skip automatic evaluation after writing predictions",
    )
    args = parser.parse_args()

    cases  = load_cases(args.benchmark)
    agents = load_agents(args.benchmark)
    rng    = random.Random(args.seed)

    # --Inspect the first case so you can see what the data looks like --──────
    if cases:
        ex = cases[0]
        print(f"\n--Example case: {ex['case_id']} --")
        print(f"   Dimensions  : {ex['dimensions']}")
        print(f"   Ground truth: {ex['ground_truth_vector']}  ({ex['n_errors']} fault(s))")
        print(f"   Fault desc  : {ex['injected_hazards']}")
        msgs = get_messages(ex)
        print(f"   Messages    : {len(msgs)} total")
        types = Counter(m["type"] for m in msgs)
        print(f"   Msg types   : { {k: v for k, v in types.most_common()} }")

        # Show the first message so the reader knows what a message looks like
        first = msgs[0]
        print(f"   First msg   : [{first.get('type')}] from={first.get('from')} "
              f"to={first.get('to')}  content={str(first.get('content',''))[:80]!r}...")
        print()

    # --Run the selected strategy on all cases --──────────────────────────────
    predictions = {}
    for case in cases:
        case_id = case["case_id"]

        if args.strategy == "zeros":
            pred = predict_zeros(case, agents)
        elif args.strategy == "random":
            pred = predict_random(case, agents, rng)
        else:  # message_count
            pred = predict_message_count(case, agents)

        predictions[case_id] = pred

    # --Write predictions CSV --───────────────────────────────────────────────
    out_path = Path(args.out)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["case_id", "predicted_vector"])
        for case_id, vec in sorted(predictions.items()):
            writer.writerow([case_id, ",".join(str(x) for x in vec)])

    print(f"Predictions written to: {out_path}  ({len(predictions)} cases)")

    # --Evaluate --────────────────────────────────────────────────────────────
    if not args.no_eval:
        print()
        sys.stdout.flush()
        subprocess.run(
            [
                sys.executable, "evaluate.py",
                "--benchmark", args.benchmark,
                "--predictions", str(out_path),
                "--model", f"baseline-{args.strategy}",
            ],
            check=False,
        )


if __name__ == "__main__":
    main()
