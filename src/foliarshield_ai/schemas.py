"""Minimal domain schemas and validation for MVP candidate records."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from math import isfinite
from typing import Any

OPEN_RELEASE_LICENSES = {
    "Apache-2.0",
    "CC-BY-4.0",
    "CC0-1.0",
    "MIT",
    "ODC-BY-1.0",
    "PDDL-1.0",
    "Public-Domain",
}


class SchemaValidationError(ValueError):
    """Raised when a schema record violates required MVP contracts."""


class ResponsibleUseStatus(StrEnum):
    RESEARCH_ONLY = "research_only"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    PROMOTED_FOR_REVIEW = "promoted_for_review"


class LicenseReviewStatus(StrEnum):
    APPROVED_OPEN = "approved_open"
    MANIFEST_ONLY = "manifest_only"
    PENDING = "pending"
    BLOCKED = "blocked"


class RedistributionMode(StrEnum):
    REDISTRIBUTABLE = "redistributable"
    MANIFEST_ONLY = "manifest_only"
    LOCAL_ONLY = "local_only"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ProvenancedRecord:
    """Common fields required for public, reviewable MVP artifacts."""

    id: str
    source: str
    license: str
    provenance: str
    confidence: float
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    version: str = "0.1"

    def validate_common(self, *, require_open_license: bool = False) -> None:
        missing = [
            name
            for name in ("id", "source", "license", "provenance", "created_at", "version")
            if not str(getattr(self, name)).strip()
        ]
        if missing:
            raise SchemaValidationError(f"Missing required fields: {', '.join(missing)}")
        if not 0 <= self.confidence <= 1:
            raise SchemaValidationError("confidence must be between 0 and 1")
        if require_open_license and self.license not in OPEN_RELEASE_LICENSES:
            raise SchemaValidationError(
                f"license {self.license!r} is not approved for open release"
            )

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)


@dataclass(frozen=True)
class EvidenceRecord(ProvenancedRecord):
    title: str = ""
    citation: str = ""
    evidence_type: str = ""
    claims: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.citation.strip():
            raise SchemaValidationError("EvidenceRecord requires a citation")
        if not self.claims:
            raise SchemaValidationError("EvidenceRecord requires at least one claim")


@dataclass(frozen=True)
class LiteratureDocument(ProvenancedRecord):
    title: str = ""
    citation: str = ""
    abstract: str = ""
    source_url: str = ""
    evidence_type: str = ""
    keywords: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.title.strip():
            raise SchemaValidationError("LiteratureDocument requires title")
        if not self.citation.strip():
            raise SchemaValidationError("LiteratureDocument requires citation")
        if not self.abstract.strip() and not self.source_url.strip():
            raise SchemaValidationError(
                "LiteratureDocument requires abstract text or a source_url"
            )


@dataclass(frozen=True)
class LiteratureChunk(ProvenancedRecord):
    document_id: str = ""
    chunk_index: int = 0
    text: str = ""
    citation: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.document_id.strip():
            raise SchemaValidationError("LiteratureChunk requires document_id")
        if self.chunk_index < 0:
            raise SchemaValidationError("LiteratureChunk chunk_index must be non-negative")
        if not self.text.strip():
            raise SchemaValidationError("LiteratureChunk requires text")
        if not self.citation.strip():
            raise SchemaValidationError("LiteratureChunk requires citation")


@dataclass(frozen=True)
class SourceRegistryEntry(ProvenancedRecord):
    name: str = ""
    source_type: str = ""
    homepage_url: str = ""
    license_url: str = ""
    license_reviewed_on: str = ""
    planned_record_types: tuple[str, ...] = ()
    license_review_status: LicenseReviewStatus = LicenseReviewStatus.PENDING
    redistribution_mode: RedistributionMode = RedistributionMode.MANIFEST_ONLY
    notes: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.name.strip():
            raise SchemaValidationError("SourceRegistryEntry requires name")
        if not self.source_type.strip():
            raise SchemaValidationError("SourceRegistryEntry requires source_type")
        if not self.homepage_url.strip():
            raise SchemaValidationError("SourceRegistryEntry requires homepage_url")
        if self.license_review_status != LicenseReviewStatus.PENDING:
            if not self.license_url.strip():
                raise SchemaValidationError(
                    "Reviewed SourceRegistryEntry records require license_url"
                )
            if not self.license_reviewed_on.strip():
                raise SchemaValidationError(
                    "Reviewed SourceRegistryEntry records require license_reviewed_on"
                )
        if not self.planned_record_types:
            raise SchemaValidationError("SourceRegistryEntry requires planned_record_types")
        if (
            self.license_review_status == LicenseReviewStatus.BLOCKED
            and self.redistribution_mode != RedistributionMode.BLOCKED
        ):
            raise SchemaValidationError("Blocked source licenses require blocked redistribution")
        if (
            self.license_review_status == LicenseReviewStatus.APPROVED_OPEN
            and self.redistribution_mode != RedistributionMode.REDISTRIBUTABLE
        ):
            raise SchemaValidationError("Open-approved sources should be redistributable")


@dataclass(frozen=True)
class SourceManifest(ProvenancedRecord):
    source_id: str = ""
    source_url: str = ""
    retrieval_method: str = ""
    raw_path: str = ""
    content_type: str = ""
    source_license: str = ""
    license_review_status: LicenseReviewStatus = LicenseReviewStatus.PENDING
    redistribution_mode: RedistributionMode = RedistributionMode.MANIFEST_ONLY
    retrieved_at: str = ""
    record_count: int = 0
    checksum_sha256: str | None = None
    transformation_notes: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        missing = [
            name
            for name in (
                "source_id",
                "source_url",
                "retrieval_method",
                "raw_path",
                "content_type",
                "source_license",
                "retrieved_at",
            )
            if not str(getattr(self, name)).strip()
        ]
        if missing:
            raise SchemaValidationError(f"SourceManifest missing fields: {', '.join(missing)}")
        if self.record_count < 0:
            raise SchemaValidationError("SourceManifest record_count must be non-negative")
        if (
            self.license_review_status == LicenseReviewStatus.BLOCKED
            and self.redistribution_mode != RedistributionMode.BLOCKED
        ):
            raise SchemaValidationError("Blocked source manifests require blocked redistribution")
        if (
            self.license_review_status == LicenseReviewStatus.APPROVED_OPEN
            and self.source_license not in OPEN_RELEASE_LICENSES
        ):
            raise SchemaValidationError(
                "Open-approved source manifests require an approved source_license"
            )


@dataclass(frozen=True)
class Taxon(ProvenancedRecord):
    scientific_name: str = ""
    rank: str = "species"
    synonyms: tuple[str, ...] = ()
    taxonomy_authority: str = ""

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.scientific_name.strip():
            raise SchemaValidationError("Taxon requires a scientific name")
        if not self.rank.strip():
            raise SchemaValidationError("Taxon requires a rank")


@dataclass(frozen=True)
class Strain(ProvenancedRecord):
    taxon: str = ""
    strain_label: str = ""
    biosafety_flags: tuple[str, ...] = ()
    phenotype_tags: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.taxon.strip():
            raise SchemaValidationError("Strain requires a taxon")


@dataclass(frozen=True)
class Genome(ProvenancedRecord):
    taxon_id: str = ""
    strain_id: str | None = None
    accession: str = ""
    assembly_level: str = ""
    feature_source: str = ""

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.taxon_id.strip():
            raise SchemaValidationError("Genome requires taxon_id")
        if not self.accession.strip():
            raise SchemaValidationError("Genome requires an accession")


@dataclass(frozen=True)
class ProteinOrGeneFeature(ProvenancedRecord):
    genome_id: str = ""
    feature_name: str = ""
    feature_type: str = ""
    function_label: str = ""
    evidence_ids: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.genome_id.strip():
            raise SchemaValidationError("ProteinOrGeneFeature requires genome_id")
        if not self.feature_name.strip():
            raise SchemaValidationError("ProteinOrGeneFeature requires feature_name")
        if not self.feature_type.strip():
            raise SchemaValidationError("ProteinOrGeneFeature requires feature_type")


@dataclass(frozen=True)
class Phenotype(ProvenancedRecord):
    subject_id: str = ""
    trait: str = ""
    value: str = ""
    assay_id: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.subject_id.strip():
            raise SchemaValidationError("Phenotype requires subject_id")
        if not self.trait.strip():
            raise SchemaValidationError("Phenotype requires trait")
        if not self.value.strip():
            raise SchemaValidationError("Phenotype requires value")


@dataclass(frozen=True)
class Consortium(ProvenancedRecord):
    member_strain_ids: tuple[str, ...] = ()
    ratios: dict[str, float] = field(default_factory=dict)
    qualitative_composition: tuple[str, ...] = ()
    compatibility_notes: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if len(self.member_strain_ids) < 2:
            raise SchemaValidationError("Consortium requires at least two member strains")
        if self.ratios:
            unknown = set(self.ratios) - set(self.member_strain_ids)
            if unknown:
                joined = ", ".join(sorted(unknown))
                raise SchemaValidationError(
                    f"Consortium ratios reference unknown strains: {joined}"
                )
            for strain_id, ratio in self.ratios.items():
                if not isfinite(ratio) or ratio < 0:
                    raise SchemaValidationError(
                        f"Consortium ratio for {strain_id!r} must be finite and non-negative"
                    )
            if sum(self.ratios.values()) <= 0:
                raise SchemaValidationError("Consortium ratios must have a positive total")


@dataclass(frozen=True)
class Crop(ProvenancedRecord):
    common_name: str = ""
    scientific_name: str = ""
    region_tags: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.common_name.strip():
            raise SchemaValidationError("Crop requires common_name")


@dataclass(frozen=True)
class StressContext(ProvenancedRecord):
    stressors: tuple[str, ...] = ()
    crop_id: str | None = None
    region: str = ""
    temperature_c: tuple[float, float] | None = None
    moisture_regime: str = ""

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.stressors:
            raise SchemaValidationError("StressContext requires at least one stressor")
        if self.temperature_c is not None:
            low, high = self.temperature_c
            if not isfinite(low) or not isfinite(high) or low > high:
                raise SchemaValidationError("StressContext temperature_c must be a finite range")


@dataclass(frozen=True)
class SoilContext(ProvenancedRecord):
    texture: str = ""
    ph_range: tuple[float, float] | None = None
    organic_matter_level: str = ""
    region: str = ""

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.texture.strip():
            raise SchemaValidationError("SoilContext requires texture")
        if self.ph_range is not None:
            low, high = self.ph_range
            if not isfinite(low) or not isfinite(high) or low > high or low < 0 or high > 14:
                raise SchemaValidationError("SoilContext ph_range must be a valid pH range")


@dataclass(frozen=True)
class FormulationMaterial(ProvenancedRecord):
    material_class: str = ""
    release_triggers: tuple[str, ...] = ()
    viability_notes: str = ""

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.material_class.strip():
            raise SchemaValidationError("FormulationMaterial requires a material class")


@dataclass(frozen=True)
class ReleaseTrigger(ProvenancedRecord):
    trigger_type: str = ""
    condition: str = ""
    target_release_window: str = ""

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.trigger_type.strip():
            raise SchemaValidationError("ReleaseTrigger requires trigger_type")


@dataclass(frozen=True)
class EncapsulationArchitecture(ProvenancedRecord):
    architecture_type: str = ""
    material_ids: tuple[str, ...] = ()
    release_trigger_ids: tuple[str, ...] = ()
    shell_layers: int = 1
    viability_constraints: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.architecture_type.strip():
            raise SchemaValidationError("EncapsulationArchitecture requires architecture_type")
        if not self.material_ids:
            raise SchemaValidationError("EncapsulationArchitecture requires material_ids")
        if self.shell_layers < 1:
            raise SchemaValidationError("EncapsulationArchitecture shell_layers must be at least 1")


@dataclass(frozen=True)
class Assay(ProvenancedRecord):
    assay_type: str = ""
    fidelity_tier: str = ""
    measured_traits: tuple[str, ...] = ()
    crop_id: str | None = None
    stress_context_id: str | None = None

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.assay_type.strip():
            raise SchemaValidationError("Assay requires assay_type")
        if not self.fidelity_tier.strip():
            raise SchemaValidationError("Assay requires fidelity_tier")
        if not self.measured_traits:
            raise SchemaValidationError("Assay requires at least one measured trait")


@dataclass(frozen=True)
class CandidateDesign(ProvenancedRecord):
    strain_ids: tuple[str, ...] = ()
    consortium_id: str | None = None
    consortium_ratios: dict[str, float] = field(default_factory=dict)
    qualitative_composition: tuple[str, ...] = ()
    crop: str = ""
    stress_context: str = ""
    formulation_material_id: str | None = None
    encapsulation_architecture: str | None = None
    target_release_profile: str | None = None
    evaluation_tier: str = "in_silico"
    responsible_use_status: ResponsibleUseStatus = ResponsibleUseStatus.RESEARCH_ONLY
    biosafety_flags: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.strain_ids:
            raise SchemaValidationError("CandidateDesign requires at least one strain")
        if self.consortium_ratios:
            unknown = set(self.consortium_ratios) - set(self.strain_ids)
            if unknown:
                joined = ", ".join(sorted(unknown))
                raise SchemaValidationError(
                    f"CandidateDesign ratios reference unknown strains: {joined}"
                )
            for strain_id, ratio in self.consortium_ratios.items():
                if not isfinite(ratio) or ratio < 0:
                    raise SchemaValidationError(
                        f"CandidateDesign ratio for {strain_id!r} must be finite and non-negative"
                    )
            if sum(self.consortium_ratios.values()) <= 0:
                raise SchemaValidationError("CandidateDesign ratios must have a positive total")
        if not self.crop.strip():
            raise SchemaValidationError("CandidateDesign requires a crop")
        if not self.stress_context.strip():
            raise SchemaValidationError("CandidateDesign requires a stress context")
        if (
            self.responsible_use_status == ResponsibleUseStatus.PROMOTED_FOR_REVIEW
            and self.biosafety_flags
        ):
            raise SchemaValidationError(
                "Candidate designs with biosafety blockers cannot be promoted"
            )


@dataclass(frozen=True)
class EvaluationResult(ProvenancedRecord):
    candidate_id: str = ""
    objective_scores: dict[str, float] = field(default_factory=dict)
    uncertainty_intervals: dict[str, tuple[float, float]] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    biosafety_flags: tuple[str, ...] = ()
    manufacturability_flags: tuple[str, ...] = ()
    proxy_to_target_risk_notes: tuple[str, ...] = ()
    recommendation_rationale: str = ""

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.candidate_id.strip():
            raise SchemaValidationError("EvaluationResult requires candidate_id")
        if not self.objective_scores:
            raise SchemaValidationError("EvaluationResult requires objective scores")
        for name, score in self.objective_scores.items():
            if not 0 <= score <= 1:
                raise SchemaValidationError(f"objective score {name!r} must be between 0 and 1")
        if not self.evidence_ids:
            raise SchemaValidationError("EvaluationResult requires evidence citations")
        if not self.recommendation_rationale.strip():
            raise SchemaValidationError("EvaluationResult requires a rationale")


@dataclass(frozen=True)
class BenchmarkResult(ProvenancedRecord):
    task_id: str = ""
    run_id: str = ""
    method: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    baseline_metrics: dict[str, float] = field(default_factory=dict)
    candidate_ids: tuple[str, ...] = ()
    artifact_paths: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def validate(self, *, require_open_license: bool = False) -> None:
        self.validate_common(require_open_license=require_open_license)
        if not self.task_id.strip():
            raise SchemaValidationError("BenchmarkResult requires task_id")
        if not self.run_id.strip():
            raise SchemaValidationError("BenchmarkResult requires run_id")
        if not self.method.strip():
            raise SchemaValidationError("BenchmarkResult requires method")
        if not self.metrics:
            raise SchemaValidationError("BenchmarkResult requires at least one metric")
        for collection_name, metric_values in (
            ("metrics", self.metrics),
            ("baseline_metrics", self.baseline_metrics),
        ):
            for name, value in metric_values.items():
                if not name.strip():
                    raise SchemaValidationError(f"{collection_name} contains an empty metric name")
                if not isfinite(value):
                    raise SchemaValidationError(f"{collection_name} metric {name!r} must be finite")


def validate_records(
    records: Sequence[ProvenancedRecord],
    *,
    require_open_license: bool = False,
) -> None:
    """Validate a heterogeneous list of schema records."""

    for record in records:
        record.validate(require_open_license=require_open_license)


def as_artifact_dict(record: ProvenancedRecord) -> dict[str, Any]:
    """Return a JSON-serializable artifact dictionary for simple reports."""

    data = record.__dict__.copy()
    data["record_type"] = type(record).__name__
    for key, value in list(data.items()):
        if isinstance(value, tuple):
            data[key] = list(value)
        elif isinstance(value, StrEnum):
            data[key] = value.value
    return data
