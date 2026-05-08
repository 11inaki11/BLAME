"""
BLAME — Evaluator
======================================
Evaluates any system's predictions against CORTEX or TradingAgents benchmark cases.

Usage
-----
  python evaluate.py --benchmark cortex --predictions my_predictions.csv
  python evaluate.py --benchmark trading_agents --predictions my_predictions.csv --model "GPT-4o"
  python evaluate.py --benchmark cortex --predictions my_predictions.csv --append-results

Predictions CSV format
----------------------
  case_id,predicted_vector
  cortex_session_10,"1,0,0,1,0,0,0"
  cortex_session_20,"0,0,0,0,0,0,0"

Output
------
  - Terminal report: overall accuracy, accuracy by n_errors, per-dimension precision/recall
  - Optional: appends rows to benchmarks/<benchmark>/results/results.csv
"""

import os
import json
import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime, timezone


BENCHMARKS = ["cortex", "trading_agents"]
BASE_DIR   = Path(__file__).parent / "benchmarks"


def load_cases(benchmark: str) -> dict:
    """Load all case JSON files for a benchmark. Returns {case_id: case_dict}."""
    cases_dir = BASE_DIR / benchmark / "cases"
    if not cases_dir.exists():
        sys.exit(f"[ERROR] Cases directory not found: {cases_dir}")
    cases = {}
    for f in sorted(cases_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        cases[data["case_id"]] = data
    if not cases:
        sys.exit(f"[ERROR] No case files found in {cases_dir}")
    return cases


def parse_vector(s: str) -> tuple:
    """Parse a comma-separated binary string (with or without surrounding quotes) into a tuple of ints."""
    return tuple(int(x.strip()) for x in s.strip().strip('"').split(","))


def load_predictions(path: str) -> dict:
    """
    Load predictions CSV. Returns {case_id: predicted_vector_tuple}.

    Expected columns: case_id, predicted_vector
    Exits with a clear message if the file is missing or malformed.
    """
    p = Path(path)
    if not p.exists():
        sys.exit(f"[ERROR] Predictions file not found: {path}")

    preds = {}
    with open(p, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            sys.exit(f"[ERROR] Predictions file is empty: {path}")

        required = {"case_id", "predicted_vector"}
        missing_cols = required - {c.strip() for c in reader.fieldnames}
        if missing_cols:
            sys.exit(
                f"[ERROR] Predictions CSV is missing required column(s): {missing_cols}\n"
                f"  Expected columns: case_id, predicted_vector\n"
                f"  Found columns:    {list(reader.fieldnames)}"
            )

        for line_num, row in enumerate(reader, start=2):
            case_id = row["case_id"].strip()
            raw_vec = row["predicted_vector"].strip()
            try:
                vec = parse_vector(raw_vec)
            except ValueError:
                sys.exit(
                    f"[ERROR] Cannot parse predicted_vector on line {line_num} "
                    f"for case '{case_id}': {raw_vec!r}\n"
                    f"  Expected comma-separated integers, e.g. \"1,0,0,1,0,0,0\""
                )
            preds[case_id] = vec
    return preds


def validate_predictions(cases: dict, predictions: dict, benchmark: str):
    """
    Validate that predictions are structurally compatible with the benchmark cases.
    Exits with a clear message on any error.
    """
    errors = []

    for case_id, pred in predictions.items():
        if case_id not in cases:
            errors.append(
                f"  case '{case_id}' in predictions does not exist in the {benchmark} benchmark"
            )
            continue

        gt = cases[case_id]["ground_truth_vector"]
        expected_len = len(gt)

        if len(pred) != expected_len:
            errors.append(
                f"  case '{case_id}': predicted vector length {len(pred)} "
                f"does not match benchmark dimension count {expected_len}"
            )

        non_binary = [v for v in pred if v not in (0, 1)]
        if non_binary:
            errors.append(
                f"  case '{case_id}': predicted vector contains non-binary values: {non_binary}"
            )

    if errors:
        sys.exit("[ERROR] Prediction validation failed:\n" + "\n".join(errors))


def evaluate(cases: dict, predictions: dict, model: str) -> list:
    """Compare predictions against ground truth. Returns list of result dicts."""
    results = []
    for case_id, case in cases.items():
        gt   = tuple(case["ground_truth_vector"])
        pred = predictions.get(case_id)
        if pred is None:
            print(f"  [WARN] No prediction for {case_id} — skipping")
            continue
        results.append({
            "case_id":             case_id,
            "model":               model,
            "predicted_vector":    ",".join(str(x) for x in pred),
            "ground_truth_vector": ",".join(str(x) for x in gt),
            "is_correct":          pred == gt,
            "n_errors":            case.get("n_errors", sum(gt)),
            "timestamp":           datetime.now(timezone.utc).isoformat(),
        })
    return results


def print_report(results: list, benchmark: str):
    """Print a human-readable evaluation report to stdout."""
    total   = len(results)
    correct = sum(1 for r in results if r["is_correct"])

    print(f"\n{'='*60}")
    print(f"  {benchmark.upper()} — Evaluation Report")
    print(f"{'='*60}")
    print(f"  Model    : {results[0]['model'] if results else 'N/A'}")
    print(f"  Cases    : {total}")
    if total:
        print(f"  Correct  : {correct}  ({correct / total * 100:.1f}%)")
    else:
        print("  No results")

    # By n_errors
    by_n: dict = {}
    for r in results:
        n = r["n_errors"]
        by_n.setdefault(n, {"total": 0, "correct": 0})
        by_n[n]["total"] += 1
        by_n[n]["correct"] += 1 if r["is_correct"] else 0

    print(f"\n  Accuracy by fault count:")
    for n in sorted(by_n):
        d = by_n[n]
        print(f"    {n} fault(s): {d['correct']}/{d['total']}  "
              f"({d['correct'] / d['total'] * 100:.1f}%)")

    # Per-dimension precision / recall
    dim_len = len(parse_vector(results[0]["ground_truth_vector"])) if results else 0
    if dim_len:
        tp = [0] * dim_len
        fp = [0] * dim_len
        fn = [0] * dim_len
        for r in results:
            gt   = parse_vector(r["ground_truth_vector"])
            pred = parse_vector(r["predicted_vector"])
            for i in range(dim_len):
                if pred[i] == 1 and gt[i] == 1:
                    tp[i] += 1
                elif pred[i] == 1 and gt[i] == 0:
                    fp[i] += 1
                elif pred[i] == 0 and gt[i] == 1:
                    fn[i] += 1

        print(f"\n  Per-dimension (TP/FP/FN):")
        for i in range(dim_len):
            prec = tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) else 0.0
            rec  = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) else 0.0
            print(f"    dim[{i:2d}]  TP={tp[i]}  FP={fp[i]}  FN={fn[i]}"
                  f"  P={prec:.2f}  R={rec:.2f}")

    print(f"{'='*60}\n")


def append_results(results: list, benchmark: str):
    """Append evaluation rows to benchmarks/<benchmark>/results/results.csv."""
    out_path = BASE_DIR / benchmark / "results" / "results.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not out_path.exists()
    fieldnames = ["case_id", "model", "predicted_vector",
                  "ground_truth_vector", "is_correct", "n_errors", "timestamp"]
    with open(out_path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in fieldnames})
    print(f"  Results appended to {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="BLAME Benchmark Evaluator — fault attribution accuracy for multi-agent systems"
    )
    parser.add_argument("--benchmark", "-b", choices=BENCHMARKS, required=True,
                        help="Benchmark to evaluate against")
    parser.add_argument("--predictions", "-p", required=True,
                        help="CSV file with columns: case_id, predicted_vector")
    parser.add_argument("--model", "-m", default="unknown",
                        help="Model/system name for result logging (default: 'unknown')")
    parser.add_argument("--append-results", action="store_true",
                        help="Append results to benchmarks/<benchmark>/results/results.csv")
    args = parser.parse_args()

    cases       = load_cases(args.benchmark)
    predictions = load_predictions(args.predictions)
    validate_predictions(cases, predictions, args.benchmark)
    results     = evaluate(cases, predictions, args.model)

    if not results:
        print("[WARN] No results to report — check that your case IDs match the benchmark.")
        return

    print_report(results, args.benchmark)

    if args.append_results:
        append_results(results, args.benchmark)


if __name__ == "__main__":
    main()
