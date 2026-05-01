# Baselines

The first deterministic seed heuristic report is generated at:

- `benchmarks/reports/seed_heuristic_baselines.json`
- `benchmarks/reports/seed_random_candidate_baseline.json`
- `benchmarks/reports/seed_optimizer_only_baseline.json`
- `benchmarks/reports/seed_reasoning_only_baseline.json`
- `benchmarks/reports/seed_baseline_benchmark_report.json`
- `benchmarks/reports/seed_candidate_shortlist.json`

Implemented heuristic scaffolds:

- literature evidence scoring
- stress relevance scoring
- crop relevance scoring
- biosafety exclusion filtering
- diversity-aware pair assembly
- release-profile formulation scoring
- viability-risk formulation scoring
- manufacturability proxy scoring
- seeded random valid candidate sampling
- optimizer-only no-reasoning seed search over deterministic candidate scorecards
- retrieval-grounded reasoning-only seed hypotheses with explicit evidence links
- baseline benchmark metrics for hit rate, top-k enrichment, search cost, calibration
  proxy, and failure cases
- research-review shortlist export with uncertainty intervals and guardrail status

Remaining baseline work:

- model-backed linear or tree scorer if enough reviewed labels become available
- model-backed Bayesian optimizer to replace the deterministic seed search harness
