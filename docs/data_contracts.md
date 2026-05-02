# Data Contracts

All FoliarShield-AI artifacts must preserve reviewable provenance.

## Common Required Fields

Every domain record includes:

- `id`
- `source`
- `license`
- `provenance`
- `confidence`
- `created_at`
- `version`

Open release artifacts must use an approved license value from
`foliarshield_ai.schemas.OPEN_RELEASE_LICENSES`.

## Implemented Records

The current skeleton includes source manifests, literature records, crop and assay
contexts, assay endpoint schemas, formulation materials, release triggers,
encapsulation architectures, evidence records, candidate designs, evaluation results,
and benchmark results. It also retains compatibility records for `Taxon`, `Strain`,
`Genome`, `ProteinOrGeneFeature`, and `Phenotype` so starter Bacillus-like payload and
migrated reports can continue to validate.

`AssayEndpointSchema` records define the expected raw measurements, derived metrics,
units, quality checks, and objective links for fast foliar assays. The starter adapters
cover imaging, wash-off, retained-intensity, evaporation/residence-time, and early
release endpoints.

## Implemented CLI Contracts

- `foliarshield-ai ingest-seed-strains` ingests starter living-payload metadata.
- `foliarshield-ai ingest-crop-stress` ingests starter leaf/crop assay-context records.
- `foliarshield-ai ingest-formulation` ingests starter formulation, encapsulation, and
  release-trigger records.
- `foliarshield-ai chunk-literature` creates deterministic literature document and chunk
  records.
- `foliarshield-ai data-quality-report` and `foliarshield-ai curation-report` summarize
  fixture readiness and review needs.
- `foliarshield-ai build-retrieval-index`, `query-retrieval`, `extract-evidence`,
  `build-review-queue`, `evaluate-extractions`, `build-knowledge-graph`, and
  `validate-knowledge-graph` maintain the evidence layer.
- `foliarshield-ai build-feature-table`, `build-pilot-datasets`,
  `run-heuristic-baselines`, `sample-random-candidates`,
  `define-evaluator-objectives`, `build-candidate-scorecards`,
  `build-candidate-search-space`, `build-candidate-encoding`,
  `run-optimizer-only-baseline`, `run-reasoning-only-baseline`,
  `run-optimizer-proposals`, `build-baseline-benchmark-report`, and
  `build-candidate-shortlist` maintain local modeling and benchmark scaffolds.

The `seed` term in these commands means starter fixture data. It does not mean seed
coating or seed delivery.

## Candidate Composition

Foliar candidate records should link:

- leaf/crop context;
- payload type and compatibility constraints;
- formulation material;
- encapsulation or cloaking architecture;
- release trigger and target release profile;
- assay tier;
- evidence IDs;
- responsible-use status.

Promotion to higher-fidelity testing requires human review when living payloads,
ambiguous evidence, unresolved source rights, or biosafety flags are present.
