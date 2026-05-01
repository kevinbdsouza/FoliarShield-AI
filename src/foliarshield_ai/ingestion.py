"""Local ingestion helpers for seed MVP data artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from foliarshield_ai.schemas import (
    Assay,
    Crop,
    EncapsulationArchitecture,
    EvidenceRecord,
    FormulationMaterial,
    LicenseReviewStatus,
    LiteratureChunk,
    LiteratureDocument,
    Phenotype,
    ProvenancedRecord,
    RedistributionMode,
    ReleaseTrigger,
    SourceManifest,
    SourceRegistryEntry,
    Strain,
    StressContext,
    Taxon,
    as_artifact_dict,
    validate_records,
)

_IDENTIFIER_TOKEN = re.compile(r"[^a-z0-9]+")
_DOI_TOKEN = re.compile(r"\b10\.\d{4,9}/[-._;()/:a-z0-9]+\b", re.IGNORECASE)


def normalize_identifier(value: str, *, prefix: str) -> str:
    """Normalize a source label into a stable local identifier."""

    normalized = _IDENTIFIER_TOKEN.sub("-", value.lower()).strip("-")
    if not normalized:
        raise ValueError(f"Cannot build {prefix!r} identifier from an empty value")
    return f"{prefix}:{normalized}"


def normalize_taxonomy_name(value: str) -> str:
    """Return a deterministic scientific-name label for curation comparisons."""

    normalized = re.sub(r"\s+", " ", value.replace("_", " ")).strip()
    if not normalized:
        return ""
    tokens = normalized.split()
    genus = tokens[0][:1].upper() + tokens[0][1:].lower()
    if len(tokens) == 1:
        return genus
    return " ".join([genus, *(token.lower() for token in tokens[1:])])


def read_tabular_records(path: Path) -> list[dict[str, Any]]:
    """Read small seed records from JSONL or CSV using stdlib parsers."""

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as jsonl_file:
            for line_number, line in enumerate(jsonl_file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                raw_record = json.loads(stripped)
                if not isinstance(raw_record, dict):
                    raise ValueError(f"{path}:{line_number} must contain a JSON object")
                records.append(cast(dict[str, Any], raw_record))
        return records

    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as csv_file:
            return [dict(row) for row in csv.DictReader(csv_file)]

    raise ValueError(f"Unsupported seed data format {suffix!r}; expected .jsonl or .csv")


def file_sha256(path: Path) -> str:
    """Return the SHA-256 checksum for a local source file."""

    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_tags(raw_value: Any) -> tuple[str, ...]:
    """Normalize tag fields that may arrive as lists or separated strings."""

    if raw_value is None:
        return ()
    if isinstance(raw_value, list | tuple):
        values = [str(item).strip() for item in raw_value]
    else:
        values = re.split(r"[|;,]", str(raw_value))
        values = [item.strip() for item in values]
    return tuple(value for value in values if value)


def _required_text(
    row: Mapping[str, Any],
    key: str,
    *,
    row_number: int,
    record_kind: str = "seed row",
) -> str:
    value = str(row.get(key, "")).strip()
    if not value:
        raise ValueError(f"{record_kind} {row_number} missing required field {key!r}")
    return value


def _optional_float(row: Mapping[str, Any], key: str) -> float | None:
    raw_value = row.get(key)
    if raw_value is None or str(raw_value).strip() == "":
        return None
    return float(raw_value)


def _normalized_tags(raw_value: Any) -> tuple[str, ...]:
    return tuple(
        normalize_identifier(value, prefix="tag").removeprefix("tag:")
        for value in split_tags(raw_value)
    )


def _dedupe_key(*values: str) -> str:
    joined = " ".join(value.strip().lower() for value in values if value.strip())
    return _IDENTIFIER_TOKEN.sub("-", joined).strip("-")


def build_seed_strain_records(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id: str,
    source_license: str,
    default_provenance: str,
) -> list[Taxon | Strain]:
    """Build validated Taxon and Strain records from seed strain metadata."""

    records: list[Taxon | Strain] = []
    seen_taxa: set[str] = set()
    for row_number, row in enumerate(rows, start=1):
        taxon_name = normalize_taxonomy_name(_required_text(row, "taxon", row_number=row_number))
        source_record_id = _required_text(row, "source_record_id", row_number=row_number)
        confidence = float(row.get("confidence", 0.5))
        provenance = str(row.get("provenance", default_provenance)).strip() or default_provenance
        taxon_id = normalize_identifier(taxon_name, prefix="taxon")
        if taxon_id not in seen_taxa:
            records.append(
                Taxon(
                    id=taxon_id,
                    source=source_id,
                    license=source_license,
                    provenance=provenance,
                confidence=confidence,
                scientific_name=taxon_name,
                    rank=str(row.get("taxon_rank", "species")).strip() or "species",
                    taxonomy_authority=str(row.get("taxonomy_authority", "")).strip(),
                )
            )
            seen_taxa.add(taxon_id)

        strain_label = str(row.get("strain_label", "")).strip()
        strain_seed = f"{source_record_id}-{strain_label or taxon_name}"
        records.append(
            Strain(
                id=normalize_identifier(strain_seed, prefix="strain"),
                source=source_id,
                license=source_license,
                provenance=provenance,
                confidence=confidence,
                taxon=taxon_name,
                strain_label=strain_label,
                phenotype_tags=split_tags(row.get("phenotype_tags")),
                biosafety_flags=split_tags(row.get("biosafety_flags")),
            )
        )
    validate_records(records, require_open_license=True)
    return records


def build_crop_stress_evidence_records(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id: str,
    source_license: str,
    default_provenance: str,
) -> list[Crop | StressContext | Assay | EvidenceRecord | Phenotype]:
    """Build validated crop-stress and plant-microbe evidence records."""

    records: list[Crop | StressContext | Assay | EvidenceRecord | Phenotype] = []
    seen_crops: set[str] = set()
    seen_stress_contexts: set[str] = set()

    for row_number, row in enumerate(rows, start=1):
        source_record_id = _required_text(
            row,
            "source_record_id",
            row_number=row_number,
            record_kind="crop-stress evidence row",
        )
        crop_name = _required_text(
            row,
            "crop_common_name",
            row_number=row_number,
            record_kind="crop-stress evidence row",
        )
        stressors = _normalized_tags(row.get("stressors"))
        measured_traits = _normalized_tags(row.get("measured_traits"))
        claims = split_tags(row.get("claims"))
        confidence = float(row.get("confidence", 0.5))
        provenance = str(row.get("provenance", default_provenance)).strip() or default_provenance

        crop_id = normalize_identifier(crop_name, prefix="crop")
        if crop_id not in seen_crops:
            records.append(
                Crop(
                    id=crop_id,
                    source=source_id,
                    license=source_license,
                    provenance=provenance,
                    confidence=confidence,
                    common_name=crop_name.strip().lower(),
                    scientific_name=str(row.get("crop_scientific_name", "")).strip(),
                    region_tags=_normalized_tags(row.get("region_tags")),
                )
            )
            seen_crops.add(crop_id)

        stress_seed = f"{crop_name}-{'-'.join(stressors)}-{row.get('region', '')}"
        stress_context_id = normalize_identifier(stress_seed, prefix="stress")
        if stress_context_id not in seen_stress_contexts:
            temperature_low = _optional_float(row, "temperature_c_min")
            temperature_high = _optional_float(row, "temperature_c_max")
            temperature_range = (
                (temperature_low, temperature_high)
                if temperature_low is not None and temperature_high is not None
                else None
            )
            records.append(
                StressContext(
                    id=stress_context_id,
                    source=source_id,
                    license=source_license,
                    provenance=provenance,
                    confidence=confidence,
                    stressors=stressors,
                    crop_id=crop_id,
                    region=str(row.get("region", "")).strip(),
                    temperature_c=temperature_range,
                    moisture_regime=str(row.get("moisture_regime", "")).strip(),
                )
            )
            seen_stress_contexts.add(stress_context_id)

        evidence_id = normalize_identifier(source_record_id, prefix="evidence")
        records.append(
            EvidenceRecord(
                id=evidence_id,
                source=source_id,
                license=source_license,
                provenance=provenance,
                confidence=confidence,
                title=_required_text(
                    row,
                    "evidence_title",
                    row_number=row_number,
                    record_kind="crop-stress evidence row",
                ),
                citation=_required_text(
                    row,
                    "citation",
                    row_number=row_number,
                    record_kind="crop-stress evidence row",
                ),
                evidence_type=str(row.get("evidence_type", "crop-stress")).strip()
                or "crop-stress",
                claims=claims,
            )
        )

        assay_id = normalize_identifier(
            f"{source_record_id}-{row.get('assay_type', '')}",
            prefix="assay",
        )
        records.append(
            Assay(
                id=assay_id,
                source=source_id,
                license=source_license,
                provenance=provenance,
                confidence=confidence,
                assay_type=_required_text(
                    row,
                    "assay_type",
                    row_number=row_number,
                    record_kind="crop-stress evidence row",
                ),
                fidelity_tier=str(row.get("fidelity_tier", "literature_seed")).strip()
                or "literature_seed",
                measured_traits=measured_traits,
                crop_id=crop_id,
                stress_context_id=stress_context_id,
            )
        )

        phenotype_trait = str(row.get("phenotype_trait", "")).strip()
        phenotype_value = str(row.get("phenotype_value", "")).strip()
        if phenotype_trait and phenotype_value:
            subject_id = str(row.get("phenotype_subject_id", crop_id)).strip() or crop_id
            records.append(
                Phenotype(
                    id=normalize_identifier(
                        f"{source_record_id}-{phenotype_trait}",
                        prefix="phenotype",
                    ),
                    source=source_id,
                    license=source_license,
                    provenance=provenance,
                    confidence=confidence,
                    subject_id=subject_id,
                    trait=phenotype_trait,
                    value=phenotype_value,
                    assay_id=assay_id,
                    evidence_ids=(evidence_id,),
                )
            )

    validate_records(records, require_open_license=True)
    return records


def build_formulation_evidence_records(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id: str,
    source_license: str,
    default_provenance: str,
) -> list[FormulationMaterial | ReleaseTrigger | EncapsulationArchitecture | EvidenceRecord]:
    """Build validated formulation-material and encapsulation evidence records."""

    records: list[
        FormulationMaterial | ReleaseTrigger | EncapsulationArchitecture | EvidenceRecord
    ] = []
    seen_materials: set[str] = set()

    for row_number, row in enumerate(rows, start=1):
        source_record_id = _required_text(
            row,
            "source_record_id",
            row_number=row_number,
            record_kind="formulation evidence row",
        )
        material_name = _required_text(
            row,
            "material_name",
            row_number=row_number,
            record_kind="formulation evidence row",
        )
        confidence = float(row.get("confidence", 0.5))
        provenance = str(row.get("provenance", default_provenance)).strip() or default_provenance
        material_id = normalize_identifier(material_name, prefix="material")
        trigger_type = _required_text(
            row,
            "trigger_type",
            row_number=row_number,
            record_kind="formulation evidence row",
        )
        trigger_id = normalize_identifier(f"{source_record_id}-{trigger_type}", prefix="trigger")

        if material_id not in seen_materials:
            records.append(
                FormulationMaterial(
                    id=material_id,
                    source=source_id,
                    license=source_license,
                    provenance=provenance,
                    confidence=confidence,
                    material_class=_required_text(
                        row,
                        "material_class",
                        row_number=row_number,
                        record_kind="formulation evidence row",
                    ).strip().lower(),
                    release_triggers=_normalized_tags(row.get("release_triggers")),
                    viability_notes=str(row.get("viability_notes", "")).strip(),
                )
            )
            seen_materials.add(material_id)

        records.append(
            ReleaseTrigger(
                id=trigger_id,
                source=source_id,
                license=source_license,
                provenance=provenance,
                confidence=confidence,
                trigger_type=normalize_identifier(trigger_type, prefix="trigger").removeprefix(
                    "trigger:"
                ),
                condition=str(row.get("trigger_condition", "")).strip(),
                target_release_window=str(row.get("target_release_window", "")).strip(),
            )
        )
        records.append(
            EncapsulationArchitecture(
                id=normalize_identifier(
                    f"{source_record_id}-{row.get('architecture_type', '')}",
                    prefix="architecture",
                ),
                source=source_id,
                license=source_license,
                provenance=provenance,
                confidence=confidence,
                architecture_type=_required_text(
                    row,
                    "architecture_type",
                    row_number=row_number,
                    record_kind="formulation evidence row",
                ).strip().lower().replace(" ", "_"),
                material_ids=(material_id,),
                release_trigger_ids=(trigger_id,),
                shell_layers=int(row.get("shell_layers", 1)),
                viability_constraints=split_tags(row.get("viability_constraints")),
            )
        )
        records.append(
            EvidenceRecord(
                id=normalize_identifier(source_record_id, prefix="evidence"),
                source=source_id,
                license=source_license,
                provenance=provenance,
                confidence=confidence,
                title=_required_text(
                    row,
                    "evidence_title",
                    row_number=row_number,
                    record_kind="formulation evidence row",
                ),
                citation=_required_text(
                    row,
                    "citation",
                    row_number=row_number,
                    record_kind="formulation evidence row",
                ),
                evidence_type=str(row.get("evidence_type", "formulation")).strip()
                or "formulation",
                claims=split_tags(row.get("claims")),
            )
        )

    validate_records(records, require_open_license=True)
    return records


def build_literature_documents(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id: str,
    source_license: str,
    default_provenance: str,
) -> list[LiteratureDocument]:
    """Build validated document metadata records for retrieval chunking."""

    documents: list[LiteratureDocument] = []
    for row_number, row in enumerate(rows, start=1):
        source_record_id = _required_text(
            row,
            "source_record_id",
            row_number=row_number,
            record_kind="literature document row",
        )
        provenance = str(row.get("provenance", default_provenance)).strip() or default_provenance
        documents.append(
            LiteratureDocument(
                id=normalize_identifier(source_record_id, prefix="document"),
                source=source_id,
                license=source_license,
                provenance=provenance,
                confidence=float(row.get("confidence", 0.5)),
                title=_required_text(
                    row,
                    "title",
                    row_number=row_number,
                    record_kind="literature document row",
                ),
                citation=_required_text(
                    row,
                    "citation",
                    row_number=row_number,
                    record_kind="literature document row",
                ),
                abstract=str(row.get("abstract", "")).strip(),
                source_url=str(row.get("source_url", "")).strip(),
                evidence_type=str(row.get("evidence_type", "")).strip(),
                keywords=_normalized_tags(row.get("keywords")),
            )
        )

    validate_records(documents, require_open_license=True)
    return documents


def build_literature_chunks(
    documents: Iterable[LiteratureDocument],
    *,
    max_chars: int = 700,
) -> list[LiteratureChunk]:
    """Chunk document abstracts into deterministic retrieval seed records."""

    if max_chars < 200:
        raise ValueError("max_chars must be at least 200")

    chunks: list[LiteratureChunk] = []
    for document in documents:
        text = document.abstract.strip()
        if not text:
            continue
        current = ""
        chunk_index = 0
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(_chunk_from_document(document, chunk_index, current))
                chunk_index += 1
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(_chunk_from_document(document, chunk_index, current))

    validate_records(chunks, require_open_license=True)
    return chunks


def _chunk_from_document(
    document: LiteratureDocument,
    chunk_index: int,
    text: str,
) -> LiteratureChunk:
    return LiteratureChunk(
        id=normalize_identifier(f"{document.id}-{chunk_index}", prefix="chunk"),
        source=document.source,
        license=document.license,
        provenance=document.provenance,
        confidence=document.confidence,
        document_id=document.id,
        chunk_index=chunk_index,
        text=text,
        citation=document.citation,
        metadata={
            "title": document.title,
            "evidence_type": document.evidence_type,
            "keywords": "|".join(document.keywords),
        },
    )


def build_source_manifest(
    *,
    source_id: str,
    source_url: str,
    source_license: str,
    raw_path: Path,
    content_type: str,
    record_count: int,
    retrieval_method: str = "local_seed_file",
    artifact_raw_path: str | None = None,
    transformation_notes: Sequence[str] | None = None,
) -> SourceManifest:
    """Create a manifest for a raw source artifact imported by local ingestion."""

    artifact_path = artifact_raw_path or str(raw_path)
    manifest = SourceManifest(
        id=normalize_identifier(f"{source_id}-{raw_path.name}", prefix="manifest"),
        source="local-ingestion",
        license=source_license,
        provenance=artifact_path,
        confidence=1.0,
        source_id=source_id,
        source_url=source_url,
        retrieval_method=retrieval_method,
        raw_path=artifact_path,
        content_type=content_type,
        source_license=source_license,
        license_review_status=LicenseReviewStatus.APPROVED_OPEN,
        redistribution_mode=RedistributionMode.REDISTRIBUTABLE,
        retrieved_at=datetime.now(UTC).isoformat(),
        record_count=record_count,
        checksum_sha256=file_sha256(raw_path),
        transformation_notes=tuple(
            transformation_notes
            or (
                f"Parsed local {content_type} records and normalized IDs only.",
                "No biological ranking or recommendation is performed during ingestion.",
            )
        ),
    )
    manifest.validate(require_open_license=True)
    return manifest


def build_curation_report(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build deterministic curation checks for duplicate and taxonomy review."""

    record_list = list(records)
    taxonomy_records: list[dict[str, str]] = []
    taxon_groups: dict[str, list[str]] = {}
    strain_groups: dict[str, list[str]] = {}
    publication_groups: dict[str, list[str]] = {}

    for record in record_list:
        record_id = str(record.get("id", "")).strip()
        record_type = str(record.get("record_type", "")).strip()
        if not record_id:
            continue

        if record_type == "Taxon":
            raw_name = str(record.get("scientific_name", "")).strip()
            normalized_name = normalize_taxonomy_name(raw_name)
            normalized_id = (
                normalize_identifier(normalized_name, prefix="taxon") if normalized_name else ""
            )
            taxonomy_records.append(
                {
                    "record_id": record_id,
                    "record_type": record_type,
                    "raw_name": raw_name,
                    "normalized_name": normalized_name,
                    "normalized_taxon_id": normalized_id,
                }
            )
            if normalized_id:
                taxon_groups.setdefault(normalized_id, []).append(record_id)

        elif record_type == "Strain":
            raw_name = str(record.get("taxon", "")).strip()
            normalized_name = normalize_taxonomy_name(raw_name)
            normalized_taxon_id = (
                normalize_identifier(normalized_name, prefix="taxon") if normalized_name else ""
            )
            strain_label = str(record.get("strain_label", "")).strip()
            taxonomy_records.append(
                {
                    "record_id": record_id,
                    "record_type": record_type,
                    "raw_name": raw_name,
                    "normalized_name": normalized_name,
                    "normalized_taxon_id": normalized_taxon_id,
                }
            )
            strain_key = _dedupe_key(normalized_name, strain_label)
            if strain_key:
                strain_groups.setdefault(strain_key, []).append(record_id)

        elif record_type in {"EvidenceRecord", "LiteratureDocument"}:
            publication_key = _publication_key(record)
            if publication_key:
                publication_groups.setdefault(publication_key, []).append(record_id)

    duplicate_taxa = _duplicate_groups(taxon_groups)
    duplicate_strains = _duplicate_groups(strain_groups)
    duplicate_publications = _duplicate_groups(publication_groups)
    duplicate_record_ids = sorted(
        {
            duplicate_id
            for groups in (duplicate_taxa, duplicate_strains, duplicate_publications)
            for group in groups
            for duplicate_id in group["duplicate_record_ids"]
        }
    )

    return {
        "status": "ok",
        "artifact_id": "curation:seed-data",
        "generated_at": datetime.now(UTC).isoformat(),
        "record_count": len(record_list),
        "taxonomy_normalization": taxonomy_records,
        "duplicate_taxa": duplicate_taxa,
        "duplicate_strains": duplicate_strains,
        "duplicate_publications": duplicate_publications,
        "duplicate_record_ids": duplicate_record_ids,
        "canonical_record_count_after_deduplication": len(record_list) - len(duplicate_record_ids),
        "notes": [
            "Duplicate groups keep the first sorted record ID as the canonical seed record.",
            "Taxonomy normalization is string-level curation.",
            "Authority-backed taxonomy checks are still required before benchmark use.",
        ],
    }


def build_data_quality_report(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize coverage and provenance for processed seed artifacts."""

    record_list = list(records)
    curation_report = build_curation_report(record_list)
    record_types = Counter(str(record.get("record_type", "unknown")) for record in record_list)
    crops = Counter(
        str(record.get("common_name", "")).strip()
        for record in record_list
        if record.get("record_type") == "Crop"
    )
    stressors: Counter[str] = Counter()
    for record in record_list:
        if record.get("record_type") == "StressContext":
            stressors.update(str(stressor) for stressor in record.get("stressors", []))

    microbial_groups: Counter[str] = Counter()
    for record in record_list:
        if record.get("record_type") in {"Taxon", "Strain"}:
            taxon_name = str(record.get("scientific_name") or record.get("taxon", "")).strip()
            if taxon_name:
                microbial_groups[taxon_name.split()[0]] += 1

    formulation_materials = Counter(
        str(record.get("material_class", "")).strip()
        for record in record_list
        if record.get("record_type") == "FormulationMaterial"
    )
    licenses = Counter(str(record.get("license", "")) for record in record_list)
    common_fields = ("id", "source", "license", "provenance", "confidence", "created_at", "version")
    missingness = {
        field_name: sum(1 for record in record_list if not str(record.get(field_name, "")).strip())
        for field_name in common_fields
    }
    provenance_complete = sum(
        1 for record in record_list if str(record.get("provenance", "")).strip()
    )
    weak_or_ambiguous = [
        str(record.get("id"))
        for record in record_list
        if record.get("record_type") == "EvidenceRecord"
        and (
            float(record.get("confidence", 0)) < 0.55
            or any("requires" in str(claim).lower() for claim in record.get("claims", []))
        )
    ]

    return {
        "status": "ok",
        "artifact_id": "quality:seed-data",
        "generated_at": datetime.now(UTC).isoformat(),
        "record_count": len(record_list),
        "record_type_counts": dict(sorted(record_types.items())),
        "coverage_by_crop": dict(sorted(crops.items())),
        "coverage_by_stress_type": dict(sorted(stressors.items())),
        "coverage_by_microbial_group": dict(sorted(microbial_groups.items())),
        "coverage_by_formulation_material": dict(sorted(formulation_materials.items())),
        "missingness_summary": missingness,
        "license_summary": dict(sorted(licenses.items())),
        "provenance_completeness": {
            "records_with_provenance": provenance_complete,
            "records_total": len(record_list),
            "fraction": provenance_complete / len(record_list) if record_list else 0.0,
        },
        "weak_or_ambiguous_evidence_ids": weak_or_ambiguous,
        "taxonomy_normalization_count": len(curation_report["taxonomy_normalization"]),
        "duplicate_candidate_summary": {
            "taxa": len(curation_report["duplicate_taxa"]),
            "strains": len(curation_report["duplicate_strains"]),
            "publications": len(curation_report["duplicate_publications"]),
            "duplicate_record_ids": curation_report["duplicate_record_ids"],
        },
        "notes": [
            "Seed artifacts validate workflow coverage only.",
            "Low-confidence evidence should be human-reviewed before benchmarking.",
        ],
    }


def _publication_key(record: Mapping[str, Any]) -> str:
    searchable = " ".join(
        str(record.get(field_name, ""))
        for field_name in ("citation", "source_url", "title")
    ).lower()
    doi_match = _DOI_TOKEN.search(searchable)
    if doi_match:
        return f"doi:{doi_match.group(0).rstrip('.')}"
    return _dedupe_key(
        str(record.get("title", "")),
        str(record.get("citation", "")),
        str(record.get("source_url", "")),
    )


def _duplicate_groups(groups: Mapping[str, Sequence[str]]) -> list[dict[str, Any]]:
    duplicates: list[dict[str, Any]] = []
    for group_key, record_ids in groups.items():
        unique_ids = sorted(set(record_ids))
        if len(unique_ids) < 2:
            continue
        duplicates.append(
            {
                "dedupe_key": group_key,
                "canonical_record_id": unique_ids[0],
                "duplicate_record_ids": unique_ids[1:],
                "record_ids": unique_ids,
            }
        )
    return sorted(duplicates, key=lambda group: str(group["dedupe_key"]))


def artifact_records(records: Iterable[ProvenancedRecord]) -> list[dict[str, Any]]:
    """Convert validated records to JSON artifact dictionaries."""

    return [as_artifact_dict(record) for record in records]


def registry_by_id(entries: Iterable[SourceRegistryEntry]) -> dict[str, SourceRegistryEntry]:
    """Index source registry entries by stable source ID."""

    return {entry.id: entry for entry in entries}
