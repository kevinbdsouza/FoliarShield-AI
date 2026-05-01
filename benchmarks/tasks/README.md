# Benchmark Tasks

Task definitions currently live in `configs/pilot_tasks.yaml`. The local workflow can
materialize seed dataset slices for both configured pilots at:

- `data/processed/pilot_task_datasets.json`

Each task should specify:

- input manifests
- candidate generation constraints
- evaluation objectives
- baseline methods
- required output schema

The current seed slices are workflow fixtures only. Benchmark-ready task runs still need
larger reviewed evidence, objective thresholds, and scorecard schemas.
