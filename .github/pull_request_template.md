## Type of contribution

- [ ] New model/system results (leaderboard submission)
- [ ] New benchmark domain
- [ ] Bug fix or documentation improvement

---

## Checklist

### For leaderboard submissions
- [ ] `benchmarks/<benchmark>/results/results.csv` updated via `evaluate.py --append-results`
- [ ] New row added to `leaderboard.md`
- [ ] Model name and backbone clearly identified

### For new benchmark domains
- [ ] Issue opened and discussed before this PR
- [ ] `benchmarks/<domain>/` directory follows the structure in CONTRIBUTING.md
- [ ] At least 20 cases, each with `case_id`, `dimensions`, `ground_truth_vector`, `session.messages`
- [ ] `schema.md` defines all dimensions and their indices
- [ ] `evaluate.py` BENCHMARKS list updated
- [ ] `example_baseline.py` tested against the new benchmark

### For all PRs
- [ ] No raw session data or credentials included
- [ ] `example_baseline.py` still runs without errors after this change
