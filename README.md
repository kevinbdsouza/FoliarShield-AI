# FoliarShield-AI

FoliarShield-AI is an open AI-for-science research prototype for data-driven design of
retentive, rainfast, and controlled-release foliar delivery systems for climate-resilient
agriculture.

The first-year scope is deliberately narrow: difficult-to-wet leaf surfaces, one
nonliving benchmark payload, one non-pathogenic foliar-compatible Bacillus-like payload,
liquid-liquid encapsulation and cloaked/controlled-release formulations, a
literature-grounded knowledge graph, a domain-specific AI co-scientist, and batched
physics-aware Bayesian active learning. Outputs are research decision support only; they
are not field-use, regulatory, biosafety, or agronomic recommendations.

## Project Scope

FoliarShield-AI treats the leaf surface as a programmable delivery interface. The MVP
builds a reproducible evidence-to-candidate workflow for formulation batches that can be
tested through fast physical assays before slower biological labels are added.

Initial experimental boundary:

- Leaf panel: rice plus a waxy brassica or cabbage-type leaf as the stringent
  hydrophobic benchmark. Tomato, bean, or groundnut can be added after the assay and AI
  workflow are stable.
- Payloads: a fluorescent or otherwise measurable nonliving benchmark payload, plus a
  contained, institutionally approved Bacillus-like foliar microbial payload for
  delivery-survival assays.
- Formulation space: retentive spray droplets, cloaked droplets, liquid-liquid
  encapsulation, polymer/emulsion additives, release-trigger materials, and
  controlled-release shell architectures.
- Fast labels: droplet impact, contact-line motion, spray coverage, retained intensity,
  wash-off/rainfastness, evaporation, and early release.
- Higher-fidelity labels: release kinetics, microbial viability, persistence on leaf
  surfaces, and contained plant or polyhouse response tests for shortlisted candidates.

Seed delivery is retained only as a later scalability pathway through partners. It is not
the first-year optimization target.

## What The Code Does

The repository currently provides local, deterministic scaffolding for the FoliarShield-AI
data and modeling loop:

1. Register project-authored and public sources with license and redistribution review.
2. Ingest starter leaf-panel, payload/formulation, crop-context, and literature records
   from JSONL or CSV fixtures.
3. Normalize artifacts into stable, provenance-preserving schemas.
4. Generate source manifests with checksums.
5. Produce data quality and curation reports for coverage, missing fields, license
   status, duplicate records, and provenance completeness.
6. Build deterministic literature chunks, retrieval indexes, structured evidence
   extractions, review queues, and extraction evaluation reports.
7. Export a file-backed knowledge graph linking leaf contexts, assays, payloads,
   formulation materials, encapsulation architectures, release triggers, claims, and
   literature chunks.
8. Build starter feature tables, pilot task dataset slices, heuristic baselines,
   evaluator objectives, candidate scorecards, candidate search spaces, candidate
   encodings, optimizer proposal batches, and shortlist exports.
9. Validate workflow contracts with a local smoke run before replacing deterministic
   scaffolds with model-backed retrieval, extraction, surrogate modeling, and active
   learning.

The current data under `data/raw/` and `data/processed/` is starter fixture data for
workflow validation. It is not benchmark-ready experimental evidence.

## Architecture

```text
.
├── benchmarks/          # benchmark tasks, baselines, and generated reports
├── configs/             # source registry, pilot task, modeling, and reproducibility config
├── data/                # raw, interim, processed, and review artifacts
├── docs/                # architecture, data contracts, responsible-use, reproducibility
├── src/foliarshield_ai/ # Python package and CLI implementation
└── tests/               # schema, CLI, ingestion, evidence, and workflow tests
```

## Quickstart

Create a Python 3.11+ environment and install the package:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run local checks:

```bash
ruff check .
mypy
pytest
```

Run the smoke workflow:

```bash
foliarshield-ai smoke-run \
  --output benchmarks/reports/local-smoke-result.json
```

## CLI Workflows

The CLI still uses `seed` in file and command names to mean starter fixture data, not seed
delivery. The domain scope is foliar delivery.

```bash
foliarshield-ai ingest-seed-strains \
  --output data/processed/seed_strains.json \
  --manifest-output data/interim/source_manifest.seed-strains.json

foliarshield-ai ingest-crop-stress \
  --output data/processed/seed_crop_stress_evidence.json \
  --manifest-output data/interim/source_manifest.seed-crop-stress.json

foliarshield-ai ingest-formulation \
  --output data/processed/seed_formulation_evidence.json \
  --manifest-output data/interim/source_manifest.seed-formulation.json

foliarshield-ai chunk-literature \
  --documents-output data/processed/seed_literature_documents.json \
  --chunks-output data/processed/seed_literature_chunks.json \
  --manifest-output data/interim/source_manifest.seed-literature.json
```

Build evidence and modeling scaffolds:

```bash
foliarshield-ai data-quality-report --output data/processed/data_quality_report.json
foliarshield-ai curation-report --output data/processed/seed_curation_report.json
foliarshield-ai build-retrieval-index --output data/processed/seed_retrieval_index.json
foliarshield-ai extract-evidence --output data/processed/seed_structured_extractions.json
foliarshield-ai build-knowledge-graph --output data/processed/seed_knowledge_graph.json
foliarshield-ai build-feature-table --output data/processed/seed_feature_table.json
foliarshield-ai build-candidate-scorecards --output data/processed/seed_candidate_scorecards.json
foliarshield-ai build-candidate-search-space --output data/processed/seed_candidate_search_space.json
foliarshield-ai build-candidate-encoding --output data/processed/seed_candidate_encoding.json
foliarshield-ai run-optimizer-proposals --output benchmarks/reports/seed_optimizer_proposals.json
foliarshield-ai build-candidate-shortlist --output benchmarks/reports/seed_candidate_shortlist.json
```

## Proposal Alignment

The implementation tracks the revised proposal in `../docs/FoliarShield-AI.docx`:

- focus on foliar retention, rainfastness, and controlled release;
- build datasets through repeated batched assays rather than assuming a large starting
  dataset;
- use BO and expected Pareto improvement for experiment selection;
- use the LLM agent for evidence retrieval, hypothesis explanation, constraint checking,
  and auditable rationales;
- keep policy learning outside the wet-lab loop for tool routing, critique quality,
  hypothesis ranking, and experiment planning;
- keep living-payload experiments contained and review-gated.

## Responsible Use

FoliarShield-AI artifacts are intended for literature review, experiment planning,
benchmarking, and contained research workflows. They must not be interpreted as
deployment-ready pesticide, microbial, biostimulant, biosafety, regulatory, or field-use
guidance.

## Project Notes

- [ToDo](ToDo.md)
- [Progress tracker](Progress.md)
- [Architecture](docs/architecture.md)
- [Data contracts](docs/data_contracts.md)
- [Feature representations](docs/feature_representations.md)
- [Responsible use](docs/responsible_use.md)
- [Reproducibility](docs/reproducibility.md)
