# FoliarShield-AI MVP ToDo

## MVP Goal

Build an open proof-of-concept platform for designing foliar delivery formulations that
remain on difficult-to-wet leaves, resist wash-off, and release payloads on useful
timescales. The MVP should demonstrate the full evidence-to-candidate loop with starter
fixtures, then make the interfaces ready for real batched assay data.

## Scope Guardrails

- Target rice and a waxy brassica/cabbage-type benchmark leaf first.
- Use one nonliving payload for fast retention/release measurement and one contained,
  institutionally approved Bacillus-like payload for viability/persistence checks.
- Prioritize liquid-liquid encapsulation, cloaked droplets, sprayability, rainfastness,
  retained intensity, early release, and compatibility constraints.
- Treat greenhouse/polyhouse and living-payload outcomes as higher-fidelity labels for
  shortlisted candidates.
- Keep seed delivery as a later scalability pathway, not an MVP objective.

## Milestone A: Project Migration And Rename

- [x] Move the legacy codebase into the FoliarShield-AI repository.
- [x] Rename Python package imports to `foliarshield_ai`.
- [x] Rename CLI entry point to `foliarshield-ai`.
- [x] Preserve the FoliarShield-AI Git remote.
- [x] Update README, progress, docs, fixtures, and package metadata for revised scope.

## Milestone B: Foliar Evidence Layer

- [x] Keep provenance-first source registry and manifest contracts.
- [x] Replace starter raw fixtures with leaf-panel, foliar payload, formulation, and
  assay-context examples.
- [x] Maintain deterministic chunking, retrieval, extraction, review queue, and KG export
  scaffolds.
- [ ] Add real literature-derived records for cloaked droplets, emulsion impact,
  polymer droplets, liquid-liquid encapsulation, foliar Bacillus delivery, and BO.
- [ ] Add assay metadata for droplet impact videos, spray coverage images, simulated rain,
  retained fluorescence, evaporation, and early release.

## Milestone C: Candidate And Evaluator Layer

- [x] Keep candidate, formulation, release-trigger, evidence, and scorecard schemas.
- [x] Map starter candidates to foliar retention, release, sprayability, compatibility,
  and responsible-use objectives.
- [ ] Rename internal schema fields that still carry microbial-consortium terminology
  where a compatibility alias is no longer needed.
- [ ] Add explicit objective weights for retention, wash-off, release profile,
  sprayability, payload viability, material safety, and experiment cost.
- [ ] Define promotion thresholds for moving from fast physical labels to microbial
  viability and plant/polyhouse labels.

## Milestone D: Active Learning Loop

- [x] Keep deterministic surrogate/acquisition scaffolding for local regression tests.
- [ ] Replace fixture-derived scores with batched assay endpoints.
- [ ] Add expected Pareto improvement or compatible multi-objective acquisition.
- [ ] Persist experiment-batch traces, candidate rationales, model uncertainty, and
  decision audits.
- [ ] Add constraints for material availability, sprayability, biosafety review, and
  contained-use approval.

## Milestone E: AI Co-Scientist

- [ ] Connect retrieval, KG, evaluator, and optimizer tools through an auditable agent
  interface.
- [ ] Require cited evidence for all formulation hypotheses.
- [ ] Add contradiction checks and human-review flags for weak evidence.
- [ ] Train or evaluate policy-learning behavior on tool routing, critique quality,
  hypothesis ranking, and experiment planning logs.

## Milestone F: Validation And Release

- [ ] Add benchmark task cards for fast physical assays and high-fidelity checkpoints.
- [ ] Add reproducible data cards for every imported public source.
- [ ] Add responsible-use review gates for living-payload records.
- [ ] Publish a tagged MVP release after tests, lint, docs, and generated fixture reports
  are consistent.
