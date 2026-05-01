# FoliarShield-AI MVP Progress Tracker

Updated: 2026-05-01

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| Repository migration | Complete | the legacy codebase has been moved into the FoliarShield-AI repo while preserving the FoliarShield-AI Git remote. |
| Package rename | Complete | Python package is now `foliarshield_ai`; CLI entry point is `foliarshield-ai`. |
| Revised proposal alignment | In Progress | README, docs, starter fixtures, and planning files now target foliar retention, rainfastness, controlled release, and batched active learning. |
| Evidence layer | In Progress | Deterministic ingestion, manifests, retrieval, extraction, review queue, and KG export scaffolds are retained. Real foliar literature import remains. |
| Candidate/evaluator layer | In Progress | Existing candidate and scorecard scaffolds remain usable for foliar formulation ranking; objective weights need domain review. |
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
- Kept deterministic local reports and tests available for regression validation.

## Next Work

1. Import license-compatible public literature for cloaked droplets, emulsion impact,
   polymer droplets, liquid-liquid encapsulation, foliar Bacillus delivery, and BO.
2. Add explicit assay schemas or adapters for imaging, wash-off, retention, evaporation,
   and release endpoints.
3. Rename compatibility-era schema fields that still mention strains or consortia once
   downstream artifacts no longer need migration compatibility.
4. Replace fixture-derived scores with batched experimental labels.
5. Add multi-objective BO with expected Pareto improvement and auditable experiment-batch
   traces.
6. Add AI co-scientist tool interfaces and citation/constraint enforcement.

## Open Questions

| Question | Owner | Status |
| --- | --- | --- |
| Which Bacillus-like strain or surrogate will be approved for contained foliar delivery assays? | Domain team | Open |
| Which nonliving payload gives the cleanest retained-intensity and release measurements? | Experimental team | Open |
| Which waxy brassica/cabbage cultivar should anchor the difficult-to-wet benchmark? | Experimental team | Open |
| Which objective weights should govern fast-label to high-fidelity promotion? | Domain + ML team | Open |
