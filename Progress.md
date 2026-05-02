# FoliarShield-AI MVP Progress Tracker

Updated: 2026-05-02

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| Repository migration | Complete | the legacy codebase has been moved into the FoliarShield-AI repo while preserving the FoliarShield-AI Git remote. |
| Package rename | Complete | Python package is now `foliarshield_ai`; CLI entry point is `foliarshield-ai`. |
| Revised proposal alignment | In Progress | README, docs, starter fixtures, and planning files now target foliar retention, rainfastness, controlled release, and batched active learning. |
| Evidence layer | In Progress | Deterministic ingestion, manifests, retrieval, extraction, review queue, and KG export scaffolds are retained. Starter literature now includes citation-backed foliar retention, encapsulation, Bacillus, and BO records, plus endpoint schemas for fast foliar assays. |
| Candidate/evaluator layer | Complete | Existing candidate and scorecard scaffolds remain usable for foliar formulation ranking; objective weights need domain review. |
| Active learning | In Progress | Deterministic surrogate/acquisition reports exist for regression tests; physics-aware multi-objective BO and experiment traces remain. |
| AI co-scientist | Not Started | Requires reliable tools, citation enforcement, constraint checks, and policy-learning evaluation. |

## Scope Decisions

- First leaf panel: rice and waxy brassica/cabbage-type leaf.
- Optional later leaf: tomato, bean, or groundnut after the workflow stabilizes.
- Payloads: one fast nonliving benchmark payload and one contained Bacillus-like foliar
  microbial payload.
- Primary labels: droplet impact, contact-line motion, coverage, retained intensity,
  wash-off/rainfastness, evaporation, and early release.
- Higher-fidelity labels: release kinetics, microbial viability, leaf persistence, and
  contained plant/polyhouse response.
- Seed delivery is a future scalability pathway, not a first-year objective.

## Completed

- Migrated code into `FoliarShield-AI`.
- Preserved `origin` as `git@github.com:kevinbdsouza/FoliarShield-AI.git`.
- Renamed package imports and console script.
- Rewrote top-level README, ToDo, progress tracker, and docs around the revised
  FoliarShield-AI scope.
- Replaced starter raw fixture records with foliar leaf, formulation, payload, and
  literature examples.
- Added citation-backed literature metadata for cloaked droplets, polymer droplet
  deposition, liquid-shell encapsulation, temperature-responsive foliar formulations,
  foliar Bacillus persistence/rice colonization, constrained BO, and qNEHVI.
- Added assay metadata rows for droplet impact videos, spray coverage images, simulated
  rain wash-off, retained fluorescence, evaporation/residence time, and early release.
- Added explicit assay endpoint schemas and ingestion adapters for imaging, wash-off,
  retained intensity, evaporation/residence time, and early release labels.
- Regenerated processed evidence, retrieval, extraction, knowledge-graph, feature,
  pilot-task, and benchmark artifacts from the expanded fixtures.
- Kept deterministic local reports and tests available for regression validation.
- Renamed compatibility-era schema fields that still mention strains or consortia to payload terminology.
- Added explicit objective weights and promotion threshold schemas.

## Next Work

1. Replace fixture-derived scores with batched experimental labels.
2. Add multi-objective BO with expected Pareto improvement and auditable experiment-batch
   traces.
3. Add AI co-scientist tool interfaces and citation/constraint enforcement.

## Open Questions

| Question | Owner | Status |
| --- | --- | --- |
| Which Bacillus-like strain or surrogate will be approved for contained foliar delivery assays? | Domain team | Open |
| Which nonliving payload gives the cleanest retained-intensity and release measurements? | Experimental team | Open |
| Which waxy brassica/cabbage cultivar should anchor the difficult-to-wet benchmark? | Experimental team | Open |
| Which objective weights should govern fast-label to high-fidelity promotion? | Domain + ML team | Open |
