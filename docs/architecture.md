# Architecture Overview

FoliarShield-AI is organized as a batched discovery loop for foliar delivery
formulations. The first implementation keeps every layer file-backed and deterministic so
contracts can be tested before live assay data, model-backed retrieval, and active
learning are introduced.

## Layers

1. **Source manifests and ingestion**
   - Track source URL, license, provenance, retrieval date, and redistribution status.
   - Store starter leaf, payload, formulation, assay, and literature fixtures under
     `data/raw/`.

2. **Domain schemas**
   - Use `foliarshield_ai.schemas` for provenance-first records.
   - Preserve compatibility-era strain and candidate fields while the project migrates
     toward explicit foliar payload and formulation aliases.

3. **Evidence layer**
   - Normalize leaf-surface, formulation, payload, assay, and literature claims into
     citation-backed records.
   - Build deterministic retrieval, structured extraction, review queues, extraction
     evaluation, and file-backed knowledge graph artifacts.

4. **Candidate generation and evaluation**
   - Build candidate formulations from payload compatibility, crop/leaf context,
     formulation material, encapsulation architecture, release trigger, and responsible
     use status.
   - Score starter candidates on retention, rainfastness, release fit, sprayability,
     microbial viability compatibility, manufacturability, uncertainty, and review gates.

5. **Batched active learning**
   - Use fast physical assay labels for most iterations.
   - Promote only shortlisted candidates to release kinetics, microbial viability, and
     contained plant/polyhouse labels.
   - Replace deterministic surrogate scaffolds with physics-aware multi-objective BO and
     expected Pareto improvement.

6. **AI co-scientist**
   - Retrieve evidence, explain hypotheses, check constraints, call tools, and prepare
     auditable rationales for human review.
   - Keep policy learning outside the wet-lab control loop.

## Initial Storage Choices

- Configs: YAML and JSON under `configs/`
- Raw fixtures: JSONL under `data/raw/`
- Processed artifacts: JSON under `data/processed/`
- Retrieval index: lexical plus deterministic hashed-vector scaffold
- Knowledge graph: JSON node-edge export
- Reports: JSON and Markdown under `benchmarks/reports/`

## Non-Goals

- No direct field-use recommendations.
- No autonomous real-time lab control.
- No unreviewed living-payload release claims.
- No public redistribution of closed or ambiguous-license source content.
