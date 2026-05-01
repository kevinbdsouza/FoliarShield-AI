# Reproducibility Conventions

The MVP uses small filesystem manifests before introducing experiment-tracking services.

## Run Manifests

Every benchmark or candidate-generation run should record:

- artifact ID;
- creation timestamp;
- code version;
- config files;
- data sources;
- random seed;
- generated outputs;
- notes on known limitations.

Use `configs/reproducibility_manifest.example.json` as the starting point.

## Benchmark Result Schema

Benchmark outputs should include a `BenchmarkResult` record with:

- task and run IDs;
- method name;
- primary metrics;
- optional baseline metrics;
- linked candidate IDs;
- artifact paths and limitations notes.

The local smoke workflow writes a synthetic benchmark artifact to `benchmarks/reports/local-smoke-result.json` when run with:

```bash
foliarshield-ai smoke-run --output benchmarks/reports/local-smoke-result.json
```

Starter fixture baseline comparison reports are generated from deterministic local artifacts:

```bash
foliarshield-ai run-optimizer-only-baseline \
  --output benchmarks/reports/seed_optimizer_only_baseline.json

foliarshield-ai run-optimizer-proposals \
  --output benchmarks/reports/seed_optimizer_proposals.json

foliarshield-ai run-reasoning-only-baseline \
  --output benchmarks/reports/seed_reasoning_only_baseline.json

foliarshield-ai build-baseline-benchmark-report \
  --output benchmarks/reports/seed_baseline_benchmark_report.json

foliarshield-ai build-candidate-shortlist \
  --output benchmarks/reports/seed_candidate_shortlist.json
```

The current benchmark metrics are proxy-only scaffolds. Hit rate, top-k enrichment, search
cost, calibration proxy, and failure cases are computed from starter scorecards until
reviewed foliar assay labels or held-out outcomes exist.

## Naming

Use stable, readable IDs:

- `payload:<name-or-source-id>` or compatibility-era `strain:<name-or-source-id>`
- `material:<name-or-source-id>`
- `evidence:<source-id>`
- `candidate:<task-id>-<index>`
- `eval:<candidate-id>`
- `run:<workflow>-<date-or-index>`

## Random Seeds

Use `1729` as the default random seed for deterministic local smoke tests unless a task config overrides it.

## Data Versioning

Raw source artifacts belong in `data/raw/`, normalized intermediate artifacts in `data/interim/`, and public benchmark-ready artifacts in `data/processed/`. Manifests should state whether each source can be redistributed or must be fetched by the user.
