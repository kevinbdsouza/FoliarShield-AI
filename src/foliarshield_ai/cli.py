"""Command-line workflows for FoliarShield-AI local smoke checks."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from foliarshield_ai import (
    Assay,
    BenchmarkResult,
    CandidateDesign,
    PayloadCombination,
    Crop,
    EncapsulationArchitecture,
    EvaluationResult,
    EvidenceRecord,
    FormulationMaterial,
    Genome,
    LicenseReviewStatus,
    Phenotype,
    ProteinOrGeneFeature,
    RedistributionMode,
    ReleaseTrigger,
    SoilContext,
    SourceRegistryEntry,
    Strain,
    StressContext,
    Taxon,
)
from foliarshield_ai.evidence import (
    build_evidence_review_queue,
    build_knowledge_graph,
    build_retrieval_index,
    evaluate_structured_extractions,
    extract_structured_evidence,
    merge_processed_records,
    query_retrieval_index,
    validate_knowledge_graph,
)
from foliarshield_ai.features import (
    build_baseline_benchmark_report,
    build_candidate_encoding_report,
    build_candidate_scorecards,
    build_candidate_search_space,
    build_candidate_shortlist_export,
    build_evaluator_objectives,
    build_feature_table,
    build_heuristic_baseline_report,
    build_optimizer_only_baseline_report,
    build_optimizer_proposal_report,
    build_pilot_task_datasets,
    build_random_candidate_sampler,
    build_reasoning_only_baseline_report,
)
from foliarshield_ai.ingestion import (
    artifact_records,
    build_crop_stress_evidence_records,
    build_curation_report,
    build_data_quality_report,
    build_formulation_evidence_records,
    build_literature_chunks,
    build_literature_documents,
    build_seed_strain_records,
    build_source_manifest,
    read_tabular_records,
    registry_by_id,
)
from foliarshield_ai.schemas import ProvenancedRecord, as_artifact_dict, validate_records


def build_smoke_records() -> list[ProvenancedRecord]:
    """Build deterministic records for validating the initial project workflow."""

    evidence = EvidenceRecord(
        id="evidence:smoke-foliar-retention-001",
        source="cli-smoke",
        license="CC-BY-4.0",
        provenance="src/foliarshield_ai/cli.py",
        confidence=0.7,
        citation="Synthetic smoke-test evidence record",
        evidence_type="foliar-retention-release",
        claims=("foliar retention and release proxy signals are available for CLI validation",),
    )
    candidate = CandidateDesign(
        id="candidate:pilot-1-smoke-001",
        source="cli-smoke",
        license="CC-BY-4.0",
        provenance="src/foliarshield_ai/cli.py",
        confidence=0.6,
        payload_ids=(
            "strain:smoke-bacillus-like-payload-foliar",
            "strain:smoke-bacillus-like-payload",
        ),
        payload_combination_id="payload-combination:smoke-payload-compatibility-001",
        payload_ratios={
            "strain:smoke-bacillus-like-payload-foliar": 0.6,
            "strain:smoke-bacillus-like-payload": 0.4,
        },
        crop="rice",
        stress_context="leaf-retention+rainfastness",
        formulation_material_id="material:smoke-cloaked-droplet",
        encapsulation_architecture="cloaked_droplet",
        target_release_profile="foliar retention and early controlled release",
    )
    return [
        Taxon(
            id="taxon:smoke-bacillus-subtilis",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.75,
            scientific_name="Bacillus subtilis",
            rank="species",
        ),
        Strain(
            id="strain:smoke-bacillus-like-payload-foliar",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.75,
            taxon="Bacillus subtilis",
            strain_label="contained foliar payload placeholder",
            phenotype_tags=("foliar-viability-proxy",),
        ),
        Strain(
            id="strain:smoke-bacillus-like-payload",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.72,
            taxon="Bacillus subtilis",
            strain_label="Bacillus-like compatibility placeholder",
            phenotype_tags=("release-compatibility-proxy",),
        ),
        Genome(
            id="genome:smoke-bacillus",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.6,
            taxon_id="taxon:smoke-bacillus-subtilis",
            strain_id="strain:smoke-bacillus-like-payload-foliar",
            accession="GCF_SMOKE_000001",
            assembly_level="synthetic",
        ),
        ProteinOrGeneFeature(
            id="feature:smoke-spore-viability",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.55,
            genome_id="genome:smoke-bacillus",
            feature_name="spore-viability-marker",
            feature_type="functional_marker",
            function_label="foliar viability proxy",
            evidence_ids=(evidence.id,),
        ),
        Crop(
            id="crop:smoke-rice",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.9,
            common_name="rice",
            scientific_name="Oryza sativa",
            region_tags=("foliar-delivery",),
        ),
        StressContext(
            id="stress:smoke-leaf-retention-rainfastness",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.8,
            stressors=("leaf-retention", "rainfastness"),
            crop_id="crop:smoke-rice",
            region="contained leaf-panel assays",
            temperature_c=(32.0, 42.0),
            moisture_regime="controlled leaf wetting and simulated rainfall",
        ),
        SoilContext(
            id="soil:smoke-leaf-surface",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.65,
            texture="waxy cuticle proxy",
            ph_range=(6.0, 8.0),
            organic_matter_level="low-to-medium",
            region="contained leaf-panel assays",
        ),
        Assay(
            id="assay:smoke-foliar-retention",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.6,
            assay_type="foliar-retention-proxy",
            fidelity_tier="low",
            measured_traits=("retained_intensity_proxy", "wash_off_proxy"),
            crop_id="crop:smoke-rice",
            stress_context_id="stress:smoke-leaf-retention-rainfastness",
        ),
        Phenotype(
            id="phenotype:smoke-foliar-viability",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.58,
            subject_id="strain:smoke-bacillus-like-payload-foliar",
            trait="foliar viability proxy",
            value="starter compatibility signal",
            assay_id="assay:smoke-foliar-retention",
            evidence_ids=(evidence.id,),
        ),
        PayloadCombination(
            id="payload-combination:smoke-payload-compatibility-001",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.55,
            payload_ids=(
                "strain:smoke-bacillus-like-payload-foliar",
                "strain:smoke-bacillus-like-payload",
            ),
            ratios={
                "strain:smoke-bacillus-like-payload-foliar": 0.6,
                "strain:smoke-bacillus-like-payload": 0.4,
            },
            compatibility_notes=("Synthetic payload compatibility placeholder.",),
        ),
        FormulationMaterial(
            id="material:smoke-cloaked-droplet",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.7,
            material_class="cloaked droplet",
            release_triggers=("leaf-deposition", "rainfall-challenge"),
            viability_notes="Synthetic local foliar formulation record.",
        ),
        ReleaseTrigger(
            id="trigger:smoke-rainfastness",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.65,
            trigger_type="rainfastness",
            condition="simulated rainfall after leaf deposition",
            target_release_window="early post-deposition release",
        ),
        EncapsulationArchitecture(
            id="architecture:smoke-cloaked-droplet",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.62,
            architecture_type="cloaked_droplet",
            material_ids=("material:smoke-cloaked-droplet",),
            release_trigger_ids=("trigger:smoke-rainfastness",),
            shell_layers=1,
            viability_constraints=("verify sprayability and payload compatibility",),
        ),
        evidence,
        candidate,
        EvaluationResult(
            id="eval:pilot-1-smoke-001",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=0.65,
            candidate_id=candidate.id,
            objective_scores={"retention_proxy": 0.62, "evidence_support": 0.7},
            uncertainty_intervals={"retention_proxy": (0.45, 0.75)},
            evidence_ids=(evidence.id,),
            proxy_to_target_risk_notes=("Synthetic smoke score; not a foliar efficacy claim.",),
            recommendation_rationale="CLI smoke candidate validates schema wiring only.",
        ),
        BenchmarkResult(
            id="benchmark:local-smoke-001",
            source="cli-smoke",
            license="CC-BY-4.0",
            provenance="src/foliarshield_ai/cli.py",
            confidence=1.0,
            task_id="pilot-1-foliar-retention-rainfastness",
            run_id="run:local-smoke-001",
            method="schema-smoke",
            metrics={"records_validated": 18.0, "candidate_count": 1.0},
            baseline_metrics={"minimum_expected_records": 5.0},
            candidate_ids=(candidate.id,),
            artifact_paths=("benchmarks/reports/local-smoke-result.json",),
            notes=("Synthetic local validation result; no data ingestion or ranking performed.",),
        ),
    ]


def _load_manifest(project_root: Path) -> dict[str, Any]:
    manifest_path = project_root / "configs" / "reproducibility_manifest.example.json"
    with manifest_path.open(encoding="utf-8") as manifest_file:
        raw_manifest = json.load(manifest_file)
    if not isinstance(raw_manifest, dict):
        raise ValueError("configs/reproducibility_manifest.example.json must be a JSON object")
    manifest = cast(dict[str, Any], raw_manifest)
    if not isinstance(manifest.get("random_seed"), int):
        raise ValueError(
            "configs/reproducibility_manifest.example.json requires integer random_seed"
        )
    return manifest


def _load_source_registry(project_root: Path) -> list[SourceRegistryEntry]:
    registry_path = project_root / "configs" / "source_registry.seed.json"
    with registry_path.open(encoding="utf-8") as registry_file:
        raw_registry = json.load(registry_file)
    if not isinstance(raw_registry, dict) or not isinstance(raw_registry.get("entries"), list):
        raise ValueError("configs/source_registry.seed.json must contain an entries list")

    entries: list[SourceRegistryEntry] = []
    for raw_entry in raw_registry["entries"]:
        if not isinstance(raw_entry, dict):
            raise ValueError("source registry entries must be JSON objects")
        entries.append(
            SourceRegistryEntry(
                id=str(raw_entry.get("id", "")),
                name=str(raw_entry.get("name", "")),
                source=str(raw_entry.get("source", "")),
                source_type=str(raw_entry.get("source_type", "")),
                license=str(raw_entry.get("license", "")),
                license_review_status=LicenseReviewStatus(
                    str(raw_entry.get("license_review_status", LicenseReviewStatus.PENDING))
                ),
                redistribution_mode=RedistributionMode(
                    str(raw_entry.get("redistribution_mode", RedistributionMode.MANIFEST_ONLY))
                ),
                homepage_url=str(raw_entry.get("homepage_url", "")),
                license_url=str(raw_entry.get("license_url", "")),
                license_reviewed_on=str(raw_entry.get("license_reviewed_on", "")),
                provenance=str(raw_entry.get("provenance", "")),
                confidence=float(raw_entry.get("confidence", 0)),
                planned_record_types=tuple(str(item) for item in raw_entry["planned_record_types"]),
                notes=tuple(str(item) for item in raw_entry.get("notes", [])),
            )
        )
    validate_records(entries, require_open_license=False)
    return entries


def _validate_required_files(project_root: Path) -> list[str]:
    required_paths = [
        "configs/pilot_tasks.yaml",
        "configs/modeling.yaml",
        "configs/reproducibility_manifest.example.json",
        "configs/source_registry.seed.json",
        "docs/data_contracts.md",
    ]
    missing = [path for path in required_paths if not (project_root / path).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Missing required project files: {joined}")
    return required_paths


def _resolve_project_path(project_root: Path, path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = project_root / path
    return path


def _artifact_path(project_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _write_json_if_requested(
    payload: dict[str, Any],
    output: str | None,
    project_root: Path,
) -> None:
    if output:
        output_path = _resolve_project_path(project_root, output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))


def _open_seed_source(project_root: Path, source_id: str) -> SourceRegistryEntry:
    registry_entries = _load_source_registry(project_root)
    registry = registry_by_id(registry_entries)
    if source_id not in registry:
        raise ValueError(f"Source {source_id!r} not found in configs/source_registry.seed.json")

    source_entry = registry[source_id]
    if source_entry.license_review_status != LicenseReviewStatus.APPROVED_OPEN:
        raise ValueError(f"Source {source_id!r} is not approved for open seed ingestion")
    return source_entry


def run_smoke(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    required_files = _validate_required_files(project_root)
    manifest = _load_manifest(project_root)
    registry_entries = _load_source_registry(project_root)
    records = build_smoke_records()
    validate_records(records, require_open_license=True)

    output_payload = {
        "status": "ok",
        "artifact_id": "run:local-smoke-001",
        "random_seed": manifest["random_seed"],
        "validated_files": required_files,
        "source_registry_entries": len(registry_entries),
        "records": [as_artifact_dict(record) for record in records],
    }

    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_ingest_seed_strains(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    source_id = str(args.source_id)
    source_entry = _open_seed_source(project_root, source_id)
    input_path = _resolve_project_path(project_root, args.input)
    rows = read_tabular_records(input_path)
    artifact_input_path = _artifact_path(project_root, input_path)
    records = build_seed_strain_records(
        rows,
        source_id=source_id,
        source_license=source_entry.license,
        default_provenance=artifact_input_path,
    )
    manifest = build_source_manifest(
        source_id=source_id,
        source_url=source_entry.homepage_url,
        source_license=source_entry.license,
        raw_path=input_path,
        content_type="seed_strain_metadata",
        record_count=len(rows),
        artifact_raw_path=artifact_input_path,
    )

    output_payload = {
        "status": "ok",
        "artifact_id": "ingest:seed-strains",
        "source_manifest": as_artifact_dict(manifest),
        "input_records": len(rows),
        "taxon_records": sum(1 for record in records if isinstance(record, Taxon)),
        "strain_records": sum(1 for record in records if isinstance(record, Strain)),
        "records": artifact_records(records),
    }

    if args.manifest_output:
        manifest_output = _resolve_project_path(project_root, args.manifest_output)
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(
            json.dumps(as_artifact_dict(manifest), indent=2) + "\n",
            encoding="utf-8",
        )

    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_ingest_crop_stress(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    source_id = str(args.source_id)
    source_entry = _open_seed_source(project_root, source_id)
    input_path = _resolve_project_path(project_root, args.input)
    rows = read_tabular_records(input_path)
    artifact_input_path = _artifact_path(project_root, input_path)
    records = build_crop_stress_evidence_records(
        rows,
        source_id=source_id,
        source_license=source_entry.license,
        default_provenance=artifact_input_path,
    )
    manifest = build_source_manifest(
        source_id=source_id,
        source_url=source_entry.homepage_url,
        source_license=source_entry.license,
        raw_path=input_path,
        content_type="seed_crop_stress_evidence",
        record_count=len(rows),
        artifact_raw_path=artifact_input_path,
        transformation_notes=(
            "Parsed local crop-stress evidence seed rows into domain records.",
            "Evidence claims are seed scaffolding and require human review before use.",
        ),
    )

    output_payload = {
        "status": "ok",
        "artifact_id": "ingest:seed-crop-stress",
        "source_manifest": as_artifact_dict(manifest),
        "input_records": len(rows),
        "crop_records": sum(1 for record in records if isinstance(record, Crop)),
        "stress_context_records": sum(1 for record in records if isinstance(record, StressContext)),
        "assay_records": sum(1 for record in records if isinstance(record, Assay)),
        "evidence_records": sum(1 for record in records if isinstance(record, EvidenceRecord)),
        "phenotype_records": sum(1 for record in records if isinstance(record, Phenotype)),
        "records": artifact_records(records),
    }

    if args.manifest_output:
        manifest_output = _resolve_project_path(project_root, args.manifest_output)
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(
            json.dumps(as_artifact_dict(manifest), indent=2) + "\n",
            encoding="utf-8",
        )

    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_ingest_formulation(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    source_id = str(args.source_id)
    source_entry = _open_seed_source(project_root, source_id)
    input_path = _resolve_project_path(project_root, args.input)
    rows = read_tabular_records(input_path)
    artifact_input_path = _artifact_path(project_root, input_path)
    records = build_formulation_evidence_records(
        rows,
        source_id=source_id,
        source_license=source_entry.license,
        default_provenance=artifact_input_path,
    )
    manifest = build_source_manifest(
        source_id=source_id,
        source_url=source_entry.homepage_url,
        source_license=source_entry.license,
        raw_path=input_path,
        content_type="seed_formulation_evidence",
        record_count=len(rows),
        artifact_raw_path=artifact_input_path,
        transformation_notes=(
            "Parsed local formulation evidence seed rows into domain records.",
            "Evidence claims are seed scaffolding and require human review before use.",
        ),
    )

    output_payload = {
        "status": "ok",
        "artifact_id": "ingest:seed-formulation",
        "source_manifest": as_artifact_dict(manifest),
        "input_records": len(rows),
        "material_records": sum(1 for record in records if isinstance(record, FormulationMaterial)),
        "trigger_records": sum(1 for record in records if isinstance(record, ReleaseTrigger)),
        "architecture_records": sum(
            1 for record in records if isinstance(record, EncapsulationArchitecture)
        ),
        "evidence_records": sum(1 for record in records if isinstance(record, EvidenceRecord)),
        "records": artifact_records(records),
    }

    if args.manifest_output:
        manifest_output = _resolve_project_path(project_root, args.manifest_output)
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(
            json.dumps(as_artifact_dict(manifest), indent=2) + "\n",
            encoding="utf-8",
        )

    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_chunk_literature(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    source_id = str(args.source_id)
    source_entry = _open_seed_source(project_root, source_id)
    input_path = _resolve_project_path(project_root, args.input)
    rows = read_tabular_records(input_path)
    artifact_input_path = _artifact_path(project_root, input_path)
    documents = build_literature_documents(
        rows,
        source_id=source_id,
        source_license=source_entry.license,
        default_provenance=artifact_input_path,
    )
    chunks = build_literature_chunks(documents, max_chars=int(args.max_chars))
    manifest = build_source_manifest(
        source_id=source_id,
        source_url=source_entry.homepage_url,
        source_license=source_entry.license,
        raw_path=input_path,
        content_type="seed_literature_documents",
        record_count=len(rows),
        artifact_raw_path=artifact_input_path,
        transformation_notes=(
            "Extracted local literature document metadata and deterministic abstract chunks.",
            "Chunks are retrieval scaffolding; no embeddings are generated by this command.",
        ),
    )

    output_payload = {
        "status": "ok",
        "artifact_id": "ingest:seed-literature-chunks",
        "source_manifest": as_artifact_dict(manifest),
        "input_records": len(rows),
        "document_records": len(documents),
        "chunk_records": len(chunks),
        "records": artifact_records([*documents, *chunks]),
    }

    if args.manifest_output:
        manifest_output = _resolve_project_path(project_root, args.manifest_output)
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(
            json.dumps(as_artifact_dict(manifest), indent=2) + "\n",
            encoding="utf-8",
        )

    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_data_quality_report(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    records: list[dict[str, Any]] = []
    for input_value in args.inputs:
        input_path = _resolve_project_path(project_root, input_value)
        with input_path.open(encoding="utf-8") as artifact_file:
            payload = json.load(artifact_file)
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
            raise ValueError(f"{input_path} must be a processed artifact with a records list")
        records.extend(cast(list[dict[str, Any]], payload["records"]))

    output_payload = build_data_quality_report(records)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_curation_report(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    output_payload = build_curation_report(records)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def _load_processed_artifacts(project_root: Path, inputs: Sequence[str]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for input_value in inputs:
        input_path = _resolve_project_path(project_root, input_value)
        with input_path.open(encoding="utf-8") as artifact_file:
            payload = json.load(artifact_file)
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
            raise ValueError(f"{input_path} must be a processed artifact with a records list")
        artifacts.append(cast(dict[str, Any], payload))
    return artifacts


def run_build_retrieval_index(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    output_payload = build_retrieval_index(records)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_query_retrieval(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    index_path = _resolve_project_path(project_root, args.index)
    with index_path.open(encoding="utf-8") as index_file:
        index = json.load(index_file)
    if not isinstance(index, dict):
        raise ValueError(f"{index_path} must contain a retrieval index JSON object")
    output_payload = query_retrieval_index(
        cast(dict[str, Any], index),
        query=str(args.query),
        top_k=int(args.top_k),
        crop=args.crop,
        stress=args.stress,
        material=args.material,
        evidence_type=args.evidence_type,
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_extract_evidence(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    output_payload = extract_structured_evidence(records)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_build_knowledge_graph(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    extraction_records: list[dict[str, Any]] = []
    if args.extractions:
        extraction_path = _resolve_project_path(project_root, args.extractions)
        if extraction_path.is_file():
            with extraction_path.open(encoding="utf-8") as extraction_file:
                extraction_payload = json.load(extraction_file)
            if not isinstance(extraction_payload, dict) or not isinstance(
                extraction_payload.get("records"), list
            ):
                raise ValueError(f"{extraction_path} must contain extraction records")
            extraction_records = cast(list[dict[str, Any]], extraction_payload["records"])

    output_payload = build_knowledge_graph(records, extraction_records=extraction_records)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def _load_record_payload(path: Path, *, expected_name: str = "records") -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as record_file:
        payload = json.load(record_file)
    if not isinstance(payload, dict) or not isinstance(payload.get(expected_name), list):
        raise ValueError(f"{path} must contain a {expected_name!r} list")
    return cast(list[dict[str, Any]], payload[expected_name])


def _load_pilot_tasks(project_root: Path, config_path: str) -> list[dict[str, Any]]:
    path = _resolve_project_path(project_root, config_path)
    tasks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list_key: str | None = None
    with path.open(encoding="utf-8") as config_file:
        for raw_line in config_file:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#") or stripped == "pilot_tasks:":
                continue
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                if ":" in item:
                    key, value = item.split(":", 1)
                    current = {key.strip(): value.strip()}
                    tasks.append(current)
                    current_list_key = None
                elif current is not None and current_list_key:
                    cast(list[str], current[current_list_key]).append(item)
                continue
            if current is None or ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                current[key] = value
                current_list_key = None
            else:
                current[key] = []
                current_list_key = key
    if not tasks:
        raise ValueError(f"{path} did not contain any pilot task entries")
    return tasks


def run_build_feature_table(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    output_payload = build_feature_table(records)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_build_pilot_datasets(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_pilot_task_datasets(records, tasks)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_heuristic_baselines(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_heuristic_baseline_report(records, tasks)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_random_candidates(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_random_candidate_sampler(
        records,
        tasks,
        random_seed=int(args.random_seed),
        samples_per_task=int(args.samples_per_task),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_evaluator_objectives(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_evaluator_objectives(tasks)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_candidate_scorecards(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_candidate_scorecards(
        records,
        tasks,
        random_seed=int(args.random_seed),
        samples_per_task=int(args.samples_per_task),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_build_search_space(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_candidate_search_space(
        records,
        tasks,
        max_payload_combination_size=int(args.max_payload_combination_size),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_build_candidate_encoding(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_candidate_encoding_report(
        records,
        tasks,
        max_payload_combination_size=int(args.max_payload_combination_size),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_optimizer_only_baseline(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_optimizer_only_baseline_report(
        records,
        tasks,
        random_seed=int(args.random_seed),
        initial_samples_per_task=int(args.initial_samples_per_task),
        proposal_batch_size=int(args.proposal_batch_size),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_optimizer_proposals(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_optimizer_proposal_report(
        records,
        tasks,
        random_seed=int(args.random_seed),
        initial_observations_per_task=int(args.initial_observations_per_task),
        proposal_batch_size=int(args.proposal_batch_size),
        exploration_weight=float(args.exploration_weight),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_reasoning_only_baseline(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    artifacts = _load_processed_artifacts(project_root, args.inputs)
    records = merge_processed_records(artifacts)
    tasks = _load_pilot_tasks(project_root, str(args.tasks_config))
    output_payload = build_reasoning_only_baseline_report(
        records,
        tasks,
        top_k=int(args.top_k),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_baseline_benchmark_report(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    heuristic_path = _resolve_project_path(project_root, args.heuristic_report)
    random_path = _resolve_project_path(project_root, args.random_candidate_report)
    scorecard_path = _resolve_project_path(project_root, args.scorecard_report)
    optimizer_path = _resolve_project_path(project_root, args.optimizer_report)
    reasoning_path = _resolve_project_path(project_root, args.reasoning_report)
    with heuristic_path.open(encoding="utf-8") as heuristic_file:
        heuristic_report = json.load(heuristic_file)
    with random_path.open(encoding="utf-8") as random_file:
        random_report = json.load(random_file)
    with scorecard_path.open(encoding="utf-8") as scorecard_file:
        scorecard_report = json.load(scorecard_file)
    with optimizer_path.open(encoding="utf-8") as optimizer_file:
        optimizer_report = json.load(optimizer_file)
    reasoning_report: dict[str, Any] | None = None
    if reasoning_path.is_file():
        with reasoning_path.open(encoding="utf-8") as reasoning_file:
            reasoning_report = cast(dict[str, Any], json.load(reasoning_file))
    output_payload = build_baseline_benchmark_report(
        cast(dict[str, Any], heuristic_report),
        cast(dict[str, Any], random_report),
        cast(dict[str, Any], scorecard_report),
        cast(dict[str, Any], optimizer_report),
        reasoning_report,
        review_threshold=float(args.review_threshold),
        top_k=int(args.top_k),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_candidate_shortlist(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    scorecard_path = _resolve_project_path(project_root, args.scorecard_report)
    optimizer_path = _resolve_project_path(project_root, args.optimizer_report)
    with scorecard_path.open(encoding="utf-8") as scorecard_file:
        scorecard_report = json.load(scorecard_file)
    with optimizer_path.open(encoding="utf-8") as optimizer_file:
        optimizer_report = json.load(optimizer_file)
    output_payload = build_candidate_shortlist_export(
        cast(dict[str, Any], scorecard_report),
        cast(dict[str, Any], optimizer_report),
        top_k=int(args.top_k),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_build_review_queue(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    extraction_path = _resolve_project_path(project_root, args.extractions)
    extraction_records = _load_record_payload(extraction_path)
    output_payload = build_evidence_review_queue(
        extraction_records,
        min_confidence=float(args.min_confidence),
    )
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_evaluate_extractions(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    extraction_path = _resolve_project_path(project_root, args.extractions)
    gold_path = _resolve_project_path(project_root, args.gold)
    extraction_records = _load_record_payload(extraction_path)
    gold_records = _load_record_payload(gold_path)
    output_payload = evaluate_structured_extractions(extraction_records, gold_records)
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def run_validate_knowledge_graph(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    graph_path = _resolve_project_path(project_root, args.graph)
    with graph_path.open(encoding="utf-8") as graph_file:
        graph_payload = json.load(graph_file)
    if not isinstance(graph_payload, dict):
        raise ValueError(f"{graph_path} must contain a graph JSON object")
    output_payload = validate_knowledge_graph(cast(dict[str, Any], graph_payload))
    _write_json_if_requested(output_payload, args.output, project_root)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foliarshield-ai",
        description="Local MVP workflows for FoliarShield-AI foliar delivery design.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke-run", help="Validate configs and schema smoke records.")
    smoke.add_argument("--project-root", default=".", help="Repository root to validate.")
    smoke.add_argument(
        "--output",
        help="Optional JSON output path for the smoke-run artifact.",
    )
    smoke.set_defaults(func=run_smoke)

    ingest_strains = subparsers.add_parser(
        "ingest-seed-strains",
        help=(
            "Parse starter Bacillus-like foliar payload metadata into validated "
            "compatibility records."
        ),
    )
    ingest_strains.add_argument("--project-root", default=".", help="Repository root to use.")
    ingest_strains.add_argument(
        "--input",
        default="data/raw/seed_strain_metadata.jsonl",
        help="Starter living-payload metadata input file (.jsonl or .csv).",
    )
    ingest_strains.add_argument(
        "--source-id",
        default="source:manual-strain-curation",
        help="Source registry ID that owns the starter payload data.",
    )
    ingest_strains.add_argument(
        "--output",
        help="Optional JSON output path for processed starter payload records.",
    )
    ingest_strains.add_argument(
        "--manifest-output",
        help="Optional JSON output path for the raw source manifest.",
    )
    ingest_strains.set_defaults(func=run_ingest_seed_strains)

    ingest_crop_stress = subparsers.add_parser(
        "ingest-crop-stress",
        help="Parse starter leaf-panel and foliar assay-context evidence into validated records.",
    )
    ingest_crop_stress.add_argument("--project-root", default=".", help="Repository root to use.")
    ingest_crop_stress.add_argument(
        "--input",
        default="data/raw/seed_crop_stress_evidence.jsonl",
        help="Starter leaf-panel evidence input file (.jsonl or .csv).",
    )
    ingest_crop_stress.add_argument(
        "--source-id",
        default="source:manual-crop-stress-curation",
        help="Source registry ID that owns the starter leaf-panel data.",
    )
    ingest_crop_stress.add_argument("--output", help="Optional JSON output path.")
    ingest_crop_stress.add_argument("--manifest-output", help="Optional manifest output path.")
    ingest_crop_stress.set_defaults(func=run_ingest_crop_stress)

    ingest_formulation = subparsers.add_parser(
        "ingest-formulation",
        help="Parse starter foliar formulation evidence into validated records.",
    )
    ingest_formulation.add_argument("--project-root", default=".", help="Repository root to use.")
    ingest_formulation.add_argument(
        "--input",
        default="data/raw/seed_formulation_evidence.jsonl",
        help="Starter foliar formulation evidence input file (.jsonl or .csv).",
    )
    ingest_formulation.add_argument(
        "--source-id",
        default="source:manual-material-curation",
        help="Source registry ID that owns the starter formulation data.",
    )
    ingest_formulation.add_argument("--output", help="Optional JSON output path.")
    ingest_formulation.add_argument("--manifest-output", help="Optional manifest output path.")
    ingest_formulation.set_defaults(func=run_ingest_formulation)

    chunk_literature = subparsers.add_parser(
        "chunk-literature",
        help="Extract local literature document metadata and deterministic retrieval chunks.",
    )
    chunk_literature.add_argument("--project-root", default=".", help="Repository root to use.")
    chunk_literature.add_argument(
        "--input",
        default="data/raw/seed_literature_documents.jsonl",
        help="Seed literature document input file (.jsonl or .csv).",
    )
    chunk_literature.add_argument(
        "--source-id",
        default="source:manual-crop-stress-curation",
        help="Source registry ID that owns the seed literature data.",
    )
    chunk_literature.add_argument("--max-chars", default=700, help="Maximum characters per chunk.")
    chunk_literature.add_argument("--output", help="Optional JSON output path.")
    chunk_literature.add_argument("--manifest-output", help="Optional manifest output path.")
    chunk_literature.set_defaults(func=run_chunk_literature)

    quality_report = subparsers.add_parser(
        "data-quality-report",
        help="Summarize coverage, missingness, licenses, and provenance for processed artifacts.",
    )
    quality_report.add_argument("--project-root", default=".", help="Repository root to use.")
    quality_report.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    quality_report.add_argument("--output", help="Optional JSON output path.")
    quality_report.set_defaults(func=run_data_quality_report)

    curation_report = subparsers.add_parser(
        "curation-report",
        help="Find duplicate seed records and emit normalized taxonomy review fields.",
    )
    curation_report.add_argument("--project-root", default=".", help="Repository root to use.")
    curation_report.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    curation_report.add_argument("--output", help="Optional JSON output path.")
    curation_report.set_defaults(func=run_curation_report)

    retrieval_index = subparsers.add_parser(
        "build-retrieval-index",
        help="Build a deterministic local lexical retrieval index from LiteratureChunk records.",
    )
    retrieval_index.add_argument("--project-root", default=".", help="Repository root to use.")
    retrieval_index.add_argument(
        "--inputs",
        nargs="+",
        default=["data/processed/seed_literature_chunks.json"],
        help="Processed artifact JSON files with LiteratureChunk records.",
    )
    retrieval_index.add_argument("--output", help="Optional JSON output path.")
    retrieval_index.set_defaults(func=run_build_retrieval_index)

    retrieval_query = subparsers.add_parser(
        "query-retrieval",
        help="Query a local retrieval index with citation-aware filters.",
    )
    retrieval_query.add_argument("--project-root", default=".", help="Repository root to use.")
    retrieval_query.add_argument(
        "--index",
        default="data/processed/seed_retrieval_index.json",
        help="Retrieval index JSON artifact.",
    )
    retrieval_query.add_argument("--query", required=True, help="Search query.")
    retrieval_query.add_argument("--top-k", default=5, help="Maximum results to return.")
    retrieval_query.add_argument("--crop", help="Optional crop filter.")
    retrieval_query.add_argument("--stress", help="Optional stress filter.")
    retrieval_query.add_argument("--material", help="Optional material filter.")
    retrieval_query.add_argument("--evidence-type", help="Optional evidence type filter.")
    retrieval_query.add_argument("--output", help="Optional JSON output path.")
    retrieval_query.set_defaults(func=run_query_retrieval)

    extraction = subparsers.add_parser(
        "extract-evidence",
        help="Extract structured seed evidence fields from LiteratureChunk records.",
    )
    extraction.add_argument("--project-root", default=".", help="Repository root to use.")
    extraction.add_argument(
        "--inputs",
        nargs="+",
        default=["data/processed/seed_literature_chunks.json"],
        help="Processed artifact JSON files with LiteratureChunk records.",
    )
    extraction.add_argument("--output", help="Optional JSON output path.")
    extraction.set_defaults(func=run_extract_evidence)

    graph = subparsers.add_parser(
        "build-knowledge-graph",
        help="Build a file-backed JSON node-edge graph from processed seed artifacts.",
    )
    graph.add_argument("--project-root", default=".", help="Repository root to use.")
    graph.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    graph.add_argument(
        "--extractions",
        default="data/processed/seed_structured_extractions.json",
        help="Optional structured extraction artifact.",
    )
    graph.add_argument("--output", help="Optional JSON output path.")
    graph.set_defaults(func=run_build_knowledge_graph)

    review_queue = subparsers.add_parser(
        "build-review-queue",
        help="Build a human-review queue from structured extraction records.",
    )
    review_queue.add_argument("--project-root", default=".", help="Repository root to use.")
    review_queue.add_argument(
        "--extractions",
        default="data/processed/seed_structured_extractions.json",
        help="Structured extraction artifact.",
    )
    review_queue.add_argument(
        "--min-confidence",
        default=0.5,
        help="Confidence threshold below which an extraction enters review.",
    )
    review_queue.add_argument("--output", help="Optional JSON output path.")
    review_queue.set_defaults(func=run_build_review_queue)

    extraction_eval = subparsers.add_parser(
        "evaluate-extractions",
        help="Compare structured extraction records with gold examples.",
    )
    extraction_eval.add_argument("--project-root", default=".", help="Repository root to use.")
    extraction_eval.add_argument(
        "--extractions",
        default="data/processed/seed_structured_extractions.json",
        help="Structured extraction artifact.",
    )
    extraction_eval.add_argument(
        "--gold",
        default="data/review/gold_extraction_examples.json",
        help="Gold extraction examples artifact.",
    )
    extraction_eval.add_argument("--output", help="Optional JSON output path.")
    extraction_eval.set_defaults(func=run_evaluate_extractions)

    graph_validation = subparsers.add_parser(
        "validate-knowledge-graph",
        help="Validate graph export shape and dangling edge references.",
    )
    graph_validation.add_argument("--project-root", default=".", help="Repository root to use.")
    graph_validation.add_argument(
        "--graph",
        default="data/processed/seed_knowledge_graph.json",
        help="Knowledge graph JSON artifact.",
    )
    graph_validation.add_argument("--output", help="Optional JSON output path.")
    graph_validation.set_defaults(func=run_validate_knowledge_graph)

    feature_table = subparsers.add_parser(
        "build-feature-table",
        help=(
            "Build deterministic seed feature records for strains, consortia, "
            "formulations, and crop-stress contexts."
        ),
    )
    feature_table.add_argument("--project-root", default=".", help="Repository root to use.")
    feature_table.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    feature_table.add_argument("--output", help="Optional JSON output path.")
    feature_table.set_defaults(func=run_build_feature_table)

    pilot_datasets = subparsers.add_parser(
        "build-pilot-datasets",
        help="Assemble explicit seed dataset slices for configured pilot tasks.",
    )
    pilot_datasets.add_argument("--project-root", default=".", help="Repository root to use.")
    pilot_datasets.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    pilot_datasets.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    pilot_datasets.add_argument("--output", help="Optional JSON output path.")
    pilot_datasets.set_defaults(func=run_build_pilot_datasets)

    heuristic_baselines = subparsers.add_parser(
        "run-heuristic-baselines",
        help="Run deterministic seed heuristic strain, payload combination, and formulation baselines.",
    )
    heuristic_baselines.add_argument("--project-root", default=".", help="Repository root to use.")
    heuristic_baselines.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    heuristic_baselines.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    heuristic_baselines.add_argument("--output", help="Optional JSON output path.")
    heuristic_baselines.set_defaults(func=run_heuristic_baselines)

    random_candidates = subparsers.add_parser(
        "sample-random-candidates",
        help="Sample deterministic random valid candidate designs for baseline comparisons.",
    )
    random_candidates.add_argument("--project-root", default=".", help="Repository root to use.")
    random_candidates.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    random_candidates.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    random_candidates.add_argument("--random-seed", default=1729, help="Sampler seed.")
    random_candidates.add_argument(
        "--samples-per-task",
        default=4,
        help="Number of candidate designs to sample per pilot task.",
    )
    random_candidates.add_argument("--output", help="Optional JSON output path.")
    random_candidates.set_defaults(func=run_random_candidates)

    evaluator_objectives = subparsers.add_parser(
        "define-evaluator-objectives",
        help="Write deterministic MVP evaluator objective definitions and weights.",
    )
    evaluator_objectives.add_argument("--project-root", default=".", help="Repository root.")
    evaluator_objectives.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    evaluator_objectives.add_argument("--output", help="Optional JSON output path.")
    evaluator_objectives.set_defaults(func=run_evaluator_objectives)

    candidate_scorecards = subparsers.add_parser(
        "build-candidate-scorecards",
        help="Score sampled seed candidate designs with deterministic evaluator scaffolding.",
    )
    candidate_scorecards.add_argument("--project-root", default=".", help="Repository root.")
    candidate_scorecards.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    candidate_scorecards.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    candidate_scorecards.add_argument("--random-seed", default=1729, help="Sampler seed.")
    candidate_scorecards.add_argument(
        "--samples-per-task",
        default=4,
        help="Number of sampled candidates to score per pilot task.",
    )
    candidate_scorecards.add_argument("--output", help="Optional JSON output path.")
    candidate_scorecards.set_defaults(func=run_candidate_scorecards)

    search_space = subparsers.add_parser(
        "build-candidate-search-space",
        help="Build constrained seed search spaces for optimizer inputs.",
    )
    search_space.add_argument("--project-root", default=".", help="Repository root.")
    search_space.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    search_space.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    search_space.add_argument(
        "--max-payload-combination-size",
        default=2,
        help="Largest payload combination size to include in the seed search space.",
    )
    search_space.add_argument("--output", help="Optional JSON output path.")
    search_space.set_defaults(func=run_build_search_space)

    candidate_encoding = subparsers.add_parser(
        "build-candidate-encoding",
        help="Encode constrained seed candidates for later optimizer models.",
    )
    candidate_encoding.add_argument("--project-root", default=".", help="Repository root.")
    candidate_encoding.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    candidate_encoding.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    candidate_encoding.add_argument(
        "--max-payload-combination-size",
        default=2,
        help="Largest payload combination size to include in the encoded seed candidates.",
    )
    candidate_encoding.add_argument("--output", help="Optional JSON output path.")
    candidate_encoding.set_defaults(func=run_build_candidate_encoding)

    optimizer_only = subparsers.add_parser(
        "run-optimizer-only-baseline",
        help="Run a deterministic no-reasoning optimizer-only seed baseline harness.",
    )
    optimizer_only.add_argument("--project-root", default=".", help="Repository root.")
    optimizer_only.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    optimizer_only.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    optimizer_only.add_argument("--random-seed", default=1729, help="Sampler seed.")
    optimizer_only.add_argument(
        "--initial-samples-per-task",
        default=6,
        help="Number of no-reasoning seed candidates scored per pilot task.",
    )
    optimizer_only.add_argument(
        "--proposal-batch-size",
        default=3,
        help="Number of top optimizer-only candidates to retain per pilot task.",
    )
    optimizer_only.add_argument("--output", help="Optional JSON output path.")
    optimizer_only.set_defaults(func=run_optimizer_only_baseline)

    optimizer_proposals = subparsers.add_parser(
        "run-optimizer-proposals",
        help="Fit a deterministic seed surrogate and propose candidates by acquisition score.",
    )
    optimizer_proposals.add_argument("--project-root", default=".", help="Repository root.")
    optimizer_proposals.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    optimizer_proposals.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    optimizer_proposals.add_argument("--random-seed", default=1729, help="Sampler seed.")
    optimizer_proposals.add_argument(
        "--initial-observations-per-task",
        default=3,
        help="Number of scored seed observations used to fit each surrogate.",
    )
    optimizer_proposals.add_argument(
        "--proposal-batch-size",
        default=3,
        help="Number of acquisition-ranked candidates to propose per pilot task.",
    )
    optimizer_proposals.add_argument(
        "--exploration-weight",
        default=0.35,
        help="Upper-confidence-bound exploration weight.",
    )
    optimizer_proposals.add_argument("--output", help="Optional JSON output path.")
    optimizer_proposals.set_defaults(func=run_optimizer_proposals)

    reasoning_only = subparsers.add_parser(
        "run-reasoning-only-baseline",
        help="Run a deterministic retrieval-grounded reasoning-only seed baseline harness.",
    )
    reasoning_only.add_argument("--project-root", default=".", help="Repository root.")
    reasoning_only.add_argument(
        "--tasks-config",
        default="configs/pilot_tasks.yaml",
        help="Pilot task config file.",
    )
    reasoning_only.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/processed/seed_strains.json",
            "data/processed/seed_crop_stress_evidence.json",
            "data/processed/seed_formulation_evidence.json",
            "data/processed/seed_literature_chunks.json",
        ],
        help="Processed artifact JSON files with records lists.",
    )
    reasoning_only.add_argument("--top-k", default=3, help="Hypotheses to retain per type.")
    reasoning_only.add_argument("--output", help="Optional JSON output path.")
    reasoning_only.set_defaults(func=run_reasoning_only_baseline)

    baseline_report = subparsers.add_parser(
        "build-baseline-benchmark-report",
        help="Compare seed random, heuristic, and optimizer-only baseline artifacts.",
    )
    baseline_report.add_argument("--project-root", default=".", help="Repository root.")
    baseline_report.add_argument(
        "--heuristic-report",
        default="benchmarks/reports/seed_heuristic_baselines.json",
        help="Heuristic baseline report artifact.",
    )
    baseline_report.add_argument(
        "--random-candidate-report",
        default="benchmarks/reports/seed_random_candidate_baseline.json",
        help="Random valid candidate baseline artifact.",
    )
    baseline_report.add_argument(
        "--scorecard-report",
        default="data/processed/seed_candidate_scorecards.json",
        help="Candidate scorecard artifact for random valid candidates.",
    )
    baseline_report.add_argument(
        "--optimizer-report",
        default="benchmarks/reports/seed_optimizer_only_baseline.json",
        help="Optimizer-only baseline report artifact.",
    )
    baseline_report.add_argument(
        "--reasoning-report",
        default="benchmarks/reports/seed_reasoning_only_baseline.json",
        help="Optional reasoning-only baseline report artifact.",
    )
    baseline_report.add_argument("--review-threshold", default=0.6, help="Hit-rate threshold.")
    baseline_report.add_argument("--top-k", default=3, help="Top-k value for enrichment metrics.")
    baseline_report.add_argument("--output", help="Optional JSON output path.")
    baseline_report.set_defaults(func=run_baseline_benchmark_report)

    shortlist = subparsers.add_parser(
        "build-candidate-shortlist",
        help="Export research-review candidate shortlists from seed scorecards.",
    )
    shortlist.add_argument("--project-root", default=".", help="Repository root.")
    shortlist.add_argument(
        "--scorecard-report",
        default="data/processed/seed_candidate_scorecards.json",
        help="Candidate scorecard artifact.",
    )
    shortlist.add_argument(
        "--optimizer-report",
        default="benchmarks/reports/seed_optimizer_only_baseline.json",
        help="Optimizer-only baseline artifact.",
    )
    shortlist.add_argument("--top-k", default=3, help="Candidates to retain per task.")
    shortlist.add_argument("--output", help="Optional JSON output path.")
    shortlist.set_defaults(func=run_candidate_shortlist)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
