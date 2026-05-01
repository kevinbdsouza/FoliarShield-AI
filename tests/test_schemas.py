from __future__ import annotations

import unittest

from foliarshield_ai import (
    Assay,
    BenchmarkResult,
    CandidateDesign,
    Consortium,
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
    ResponsibleUseStatus,
    SchemaValidationError,
    SoilContext,
    SourceManifest,
    SourceRegistryEntry,
    Strain,
    StressContext,
    Taxon,
)


class SchemaValidationTests(unittest.TestCase):
    def test_valid_minimal_records_pass(self) -> None:
        records = [
            Taxon(
                id="taxon:azospirillum-brasilense",
                source="seed-manifest",
                license="CC-BY-4.0",
                provenance="https://example.org/taxon",
                confidence=0.9,
                scientific_name="Azospirillum brasilense",
                rank="species",
            ),
            SourceRegistryEntry(
                id="source:manual-seed",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.8,
                name="Manual seed source",
                source_type="curated-seed-dataset",
                homepage_url="https://example.org/source",
                license_url="https://creativecommons.org/licenses/by/4.0/",
                license_reviewed_on="2026-04-24",
                planned_record_types=("Strain", "EvidenceRecord"),
                license_review_status=LicenseReviewStatus.APPROVED_OPEN,
                redistribution_mode=RedistributionMode.REDISTRIBUTABLE,
            ),
            SourceManifest(
                id="manifest:manual-seed",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=1.0,
                source_id="source:manual-seed",
                source_url="https://example.org/source",
                retrieval_method="local_seed_file",
                raw_path="data/raw/example.jsonl",
                content_type="seed_strain_metadata",
                source_license="CC-BY-4.0",
                license_review_status=LicenseReviewStatus.APPROVED_OPEN,
                redistribution_mode=RedistributionMode.REDISTRIBUTABLE,
                retrieved_at="2026-04-24T00:00:00+00:00",
                record_count=1,
            ),
            Strain(
                id="strain:azospirillum-001",
                source="seed-manifest",
                license="CC-BY-4.0",
                provenance="https://example.org/strain",
                confidence=0.8,
                taxon="Azospirillum brasilense",
            ),
            Genome(
                id="genome:azospirillum-001",
                source="seed-manifest",
                license="CC-BY-4.0",
                provenance="https://example.org/genome",
                confidence=0.7,
                taxon_id="taxon:azospirillum-brasilense",
                strain_id="strain:azospirillum-001",
                accession="GCF_000000001",
            ),
            ProteinOrGeneFeature(
                id="feature:osmoprotection-001",
                source="seed-manifest",
                license="CC-BY-4.0",
                provenance="https://example.org/feature",
                confidence=0.65,
                genome_id="genome:azospirillum-001",
                feature_name="osmoprotection-marker",
                feature_type="functional_marker",
            ),
            Phenotype(
                id="phenotype:drought-proxy-001",
                source="seed-manifest",
                license="CC-BY-4.0",
                provenance="https://example.org/phenotype",
                confidence=0.65,
                subject_id="strain:azospirillum-001",
                trait="drought stress proxy",
                value="positive",
            ),
            Consortium(
                id="consortium:azospirillum-bacillus-001",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.6,
                member_strain_ids=("strain:azospirillum-001", "strain:bacillus-001"),
                ratios={"strain:azospirillum-001": 0.5, "strain:bacillus-001": 0.5},
            ),
            Crop(
                id="crop:millet",
                source="seed-manifest",
                license="CC-BY-4.0",
                provenance="https://example.org/crop",
                confidence=0.8,
                common_name="millet",
                scientific_name="Pennisetum glaucum",
            ),
            StressContext(
                id="stress:drought-heat",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.8,
                stressors=("drought", "heat"),
                crop_id="crop:millet",
                temperature_c=(32.0, 42.0),
            ),
            SoilContext(
                id="soil:dryland-loam",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.7,
                texture="loam",
                ph_range=(6.0, 8.0),
            ),
            FormulationMaterial(
                id="material:alginate",
                source="seed-manifest",
                license="CC-BY-4.0",
                provenance="https://example.org/material",
                confidence=0.7,
                material_class="polysaccharide hydrogel",
            ),
            ReleaseTrigger(
                id="trigger:moisture",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.7,
                trigger_type="moisture",
            ),
            EncapsulationArchitecture(
                id="architecture:alginate-microcapsule",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.7,
                architecture_type="hydrogel_microcapsule",
                material_ids=("material:alginate",),
                release_trigger_ids=("trigger:moisture",),
            ),
            Assay(
                id="assay:pot-trial-proxy",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.65,
                assay_type="pot-trial-proxy",
                fidelity_tier="low",
                measured_traits=("root_growth_proxy",),
            ),
            EvidenceRecord(
                id="evidence:paper-001",
                source="manual-curation",
                license="CC-BY-4.0",
                provenance="https://doi.org/10.0000/example",
                confidence=0.75,
                citation="Example et al. 2026",
                evidence_type="plant-microbe-stress",
                claims=("reported drought-stress growth proxy improvement",),
            ),
            CandidateDesign(
                id="candidate:millet-drought-001",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.6,
                strain_ids=("strain:azospirillum-001", "strain:bacillus-001"),
                consortium_id="consortium:azospirillum-bacillus-001",
                consortium_ratios={"strain:azospirillum-001": 0.5, "strain:bacillus-001": 0.5},
                crop="millet",
                stress_context="drought",
            ),
            EvaluationResult(
                id="eval:millet-drought-001",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=0.6,
                candidate_id="candidate:millet-drought-001",
                objective_scores={"stress_tolerance_proxy": 0.68},
                uncertainty_intervals={"stress_tolerance_proxy": (0.5, 0.8)},
                evidence_ids=("evidence:paper-001",),
                recommendation_rationale="Evidence-supported research candidate.",
            ),
            BenchmarkResult(
                id="benchmark:pilot-1-smoke",
                source="unit-test",
                license="CC-BY-4.0",
                provenance="tests/test_schemas.py",
                confidence=1.0,
                task_id="pilot-1-millet-drought-consortium",
                run_id="run:unit-test",
                method="schema-smoke",
                metrics={"records_validated": 5.0},
                candidate_ids=("candidate:millet-drought-001",),
            ),
        ]

        for record in records:
            record.validate(require_open_license=True)

    def test_missing_provenance_fails(self) -> None:
        record = Strain(
            id="strain:missing-provenance",
            source="seed-manifest",
            license="CC-BY-4.0",
            provenance="",
            confidence=0.8,
            taxon="Bacillus subtilis",
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()

    def test_blocked_source_license_requires_blocked_redistribution(self) -> None:
        record = SourceRegistryEntry(
            id="source:blocked",
            source="unit-test",
            license="All-Rights-Reserved",
            provenance="tests/test_schemas.py",
            confidence=0.2,
            name="Blocked source",
            source_type="closed-dataset",
            homepage_url="https://example.org/blocked",
            license_url="https://example.org/terms",
            license_reviewed_on="2026-04-24",
            planned_record_types=("EvidenceRecord",),
            license_review_status=LicenseReviewStatus.BLOCKED,
            redistribution_mode=RedistributionMode.MANIFEST_ONLY,
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()

    def test_reviewed_source_requires_license_url(self) -> None:
        record = SourceRegistryEntry(
            id="source:reviewed-without-url",
            source="unit-test",
            license="CC-BY-4.0",
            provenance="tests/test_schemas.py",
            confidence=0.8,
            name="Reviewed source without URL",
            source_type="curated-seed-dataset",
            homepage_url="https://example.org/source",
            planned_record_types=("Strain",),
            license_review_status=LicenseReviewStatus.APPROVED_OPEN,
            redistribution_mode=RedistributionMode.REDISTRIBUTABLE,
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()

    def test_open_source_manifest_requires_open_source_license(self) -> None:
        record = SourceManifest(
            id="manifest:bad-license",
            source="unit-test",
            license="CC-BY-4.0",
            provenance="tests/test_schemas.py",
            confidence=1.0,
            source_id="source:manual-seed",
            source_url="https://example.org/source",
            retrieval_method="local_seed_file",
            raw_path="data/raw/example.jsonl",
            content_type="seed_strain_metadata",
            source_license="All-Rights-Reserved",
            license_review_status=LicenseReviewStatus.APPROVED_OPEN,
            redistribution_mode=RedistributionMode.REDISTRIBUTABLE,
            retrieved_at="2026-04-24T00:00:00+00:00",
            record_count=1,
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()

    def test_benchmark_result_requires_finite_metrics(self) -> None:
        record = BenchmarkResult(
            id="benchmark:bad-metric",
            source="unit-test",
            license="CC-BY-4.0",
            provenance="tests/test_schemas.py",
            confidence=1.0,
            task_id="pilot-1-millet-drought-consortium",
            run_id="run:unit-test",
            method="schema-smoke",
            metrics={"score": float("nan")},
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()

    def test_invalid_license_fails_when_open_release_required(self) -> None:
        record = EvidenceRecord(
            id="evidence:closed",
            source="manual-curation",
            license="All-Rights-Reserved",
            provenance="https://example.org/closed",
            confidence=0.7,
            citation="Closed Source 2026",
            claims=("nonredistributable evidence",),
        )

        with self.assertRaises(SchemaValidationError):
            record.validate(require_open_license=True)

    def test_biosafety_blocker_prevents_promotion(self) -> None:
        record = CandidateDesign(
            id="candidate:blocked",
            source="unit-test",
            license="CC-BY-4.0",
            provenance="tests/test_schemas.py",
            confidence=0.3,
            strain_ids=("strain:unknown",),
            crop="chickpea",
            stress_context="heat",
            responsible_use_status=ResponsibleUseStatus.PROMOTED_FOR_REVIEW,
            biosafety_flags=("requires-domain-review",),
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()

    def test_candidate_ratios_must_reference_candidate_strains(self) -> None:
        record = CandidateDesign(
            id="candidate:bad-ratio",
            source="unit-test",
            license="CC-BY-4.0",
            provenance="tests/test_schemas.py",
            confidence=0.4,
            strain_ids=("strain:known",),
            consortium_ratios={"strain:unknown": 1.0},
            crop="millet",
            stress_context="drought",
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()

    def test_context_ranges_must_be_valid(self) -> None:
        record = SoilContext(
            id="soil:bad-ph",
            source="unit-test",
            license="CC-BY-4.0",
            provenance="tests/test_schemas.py",
            confidence=0.7,
            texture="loam",
            ph_range=(8.0, 6.0),
        )

        with self.assertRaises(SchemaValidationError):
            record.validate()


if __name__ == "__main__":
    unittest.main()
