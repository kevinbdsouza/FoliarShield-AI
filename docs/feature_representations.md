# Feature Representations

The current feature table is deterministic scaffolding for workflow validation. It keeps
schemas, baselines, scorecards, and reports wired together until real foliar assay labels
and model-backed embeddings are available.

## Artifact

`foliarshield-ai build-feature-table` writes
`data/processed/seed_feature_table.json`.

The artifact currently includes:

- living-payload compatibility features;
- formulation material features;
- encapsulation and release-trigger features;
- leaf/crop assay-context features;
- candidate feature counts and version metadata.

## Payload Compatibility Features

Compatibility-era `Strain` records represent contained Bacillus-like living payload
metadata. Features include taxonomic labels, phenotype tags, biosafety flags, and optional
genome-derived deterministic vectors. These vectors are placeholders for plumbing only;
they are not biological sequence embeddings.

## Formulation Features

Formulation features join `FormulationMaterial`, `EncapsulationArchitecture`, and
`ReleaseTrigger` records. Useful foliar terms include water response, hydrophobic-leaf
retention, rainfastness, cloaking, liquid-liquid encapsulation, sprayability, evaporation,
release-window, processing risk, and payload compatibility.

## Leaf And Assay Context Features

Crop/stress context features are repurposed for leaf-panel and assay contexts. Starter
fixtures include rice, waxy brassica/cabbage, and optional moderate-wettability leaves.
The next schema pass should add explicit leaf wettability, contact-angle, surface wax,
spray, wash-off, retained-intensity, and release-label fields.

## Optimizer Features

Candidate encodings should eventually include:

- material descriptors;
- emulsion/polymer/rheology descriptors;
- droplet-impact and spread labels;
- retention and wash-off endpoints;
- release kinetics;
- payload viability compatibility;
- uncertainty and cost estimates;
- hard feasibility and responsible-use constraints.
