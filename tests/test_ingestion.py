from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from foliarshield_ai.ingestion import (
    build_crop_stress_evidence_records,
    build_curation_report,
    build_data_quality_report,
    build_formulation_evidence_records,
    build_literature_chunks,
    build_literature_documents,
    build_seed_strain_records,
    build_source_manifest,
    normalize_identifier,
    normalize_taxonomy_name,
    read_tabular_records,
)
from foliarshield_ai.schemas import (
    Assay,
    Crop,
    EncapsulationArchitecture,
    EvidenceRecord,
    FormulationMaterial,
    LiteratureChunk,
    LiteratureDocument,
    Strain,
    StressContext,
    Taxon,
    as_artifact_dict,
)


class IngestionTests(unittest.TestCase):
    def test_normalize_identifier_is_stable(self) -> None:
        self.assertEqual(
            normalize_identifier("Azospirillum brasilense Sp7", prefix="strain"),
            "strain:azospirillum-brasilense-sp7",
        )

    def test_normalize_taxonomy_name_is_stable(self) -> None:
        self.assertEqual(
            normalize_taxonomy_name(" bacillus_SUBTILIS  "),
            "Bacillus subtilis",
        )

    def test_read_jsonl_and_build_seed_records(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "seed.jsonl"
            input_path.write_text(
                json.dumps(
                    {
                        "source_record_id": "manual-001",
                        "taxon": "Azospirillum brasilense",
                        "strain_label": "Sp7-like",
                        "phenotype_tags": "drought; root-growth",
                        "confidence": 0.6,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            rows = read_tabular_records(input_path)
            records = build_seed_strain_records(
                rows,
                source_id="source:manual-strain-curation",
                source_license="CC-BY-4.0",
                default_provenance=str(input_path),
            )

            self.assertEqual(len(records), 2)
            self.assertIsInstance(records[0], Taxon)
            self.assertIsInstance(records[1], Strain)
            strain_record = records[1]
            assert isinstance(strain_record, Strain)
            self.assertEqual(strain_record.phenotype_tags, ("drought", "root-growth"))

    def test_build_source_manifest_records_checksum(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "seed.jsonl"
            input_path.write_text('{"taxon":"Bacillus subtilis"}\n', encoding="utf-8")

            manifest = build_source_manifest(
                source_id="source:manual-strain-curation",
                source_url="https://example.org/source",
                source_license="CC-BY-4.0",
                raw_path=input_path,
                content_type="seed_strain_metadata",
                record_count=1,
            )

            self.assertEqual(manifest.record_count, 1)
            self.assertEqual(len(manifest.checksum_sha256 or ""), 64)

    def test_build_crop_stress_evidence_records(self) -> None:
        records = build_crop_stress_evidence_records(
            [
                {
                    "source_record_id": "manual-crop-001",
                    "crop_common_name": "Pearl Millet",
                    "crop_scientific_name": "Pennisetum glaucum",
                    "stressors": ["Drought", "Heat"],
                    "assay_type": "literature-derived stress proxy",
                    "measured_traits": ["root growth", "survival"],
                    "evidence_title": "Seed evidence",
                    "citation": "Project-authored seed record",
                    "claims": ["requires human literature review"],
                    "phenotype_trait": "stress relevance",
                    "phenotype_value": "pilot context",
                    "confidence": 0.5,
                }
            ],
            source_id="source:manual-crop-stress-curation",
            source_license="CC-BY-4.0",
            default_provenance="data/raw/seed_crop_stress_evidence.jsonl",
        )

        self.assertTrue(any(isinstance(record, Crop) for record in records))
        self.assertTrue(any(isinstance(record, StressContext) for record in records))
        self.assertTrue(any(isinstance(record, Assay) for record in records))
        self.assertTrue(any(isinstance(record, EvidenceRecord) for record in records))

    def test_build_formulation_evidence_records(self) -> None:
        records = build_formulation_evidence_records(
            [
                {
                    "source_record_id": "manual-formulation-001",
                    "material_name": "Sodium Alginate",
                    "material_class": "polysaccharide hydrogel",
                    "release_triggers": ["moisture"],
                    "trigger_type": "moisture",
                    "architecture_type": "hydrogel microcapsule",
                    "evidence_title": "Seed formulation",
                    "citation": "Project-authored seed record",
                    "claims": ["requires human literature review"],
                    "confidence": 0.5,
                }
            ],
            source_id="source:manual-material-curation",
            source_license="CC-BY-4.0",
            default_provenance="data/raw/seed_formulation_evidence.jsonl",
        )

        self.assertTrue(any(isinstance(record, FormulationMaterial) for record in records))
        self.assertTrue(any(isinstance(record, EncapsulationArchitecture) for record in records))
        self.assertTrue(any(isinstance(record, EvidenceRecord) for record in records))

    def test_build_literature_chunks_preserves_document_metadata(self) -> None:
        documents = build_literature_documents(
            [
                {
                    "source_record_id": "manual-doc-001",
                    "title": "Seed note",
                    "citation": "Project-authored seed document",
                    "abstract": "First sentence. Second sentence for retrieval chunking.",
                    "evidence_type": "crop-stress",
                    "keywords": ["millet", "drought"],
                    "confidence": 0.5,
                }
            ],
            source_id="source:manual-crop-stress-curation",
            source_license="CC-BY-4.0",
            default_provenance="data/raw/seed_literature_documents.jsonl",
        )
        chunks = build_literature_chunks(documents, max_chars=200)

        self.assertIsInstance(documents[0], LiteratureDocument)
        self.assertIsInstance(chunks[0], LiteratureChunk)
        self.assertEqual(chunks[0].document_id, documents[0].id)
        self.assertEqual(chunks[0].metadata["evidence_type"], "crop-stress")

    def test_build_data_quality_report_summarizes_seed_records(self) -> None:
        records = [
            as_artifact_dict(
                Taxon(
                    id="taxon:azospirillum",
                    source="source:manual-strain-curation",
                    license="CC-BY-4.0",
                    provenance="seed",
                    confidence=0.6,
                    scientific_name="Azospirillum brasilense",
                )
            ),
            as_artifact_dict(
                Crop(
                    id="crop:pearl-millet",
                    source="source:manual-crop-stress-curation",
                    license="CC-BY-4.0",
                    provenance="seed",
                    confidence=0.5,
                    common_name="pearl millet",
                )
            ),
        ]

        report = build_data_quality_report(records)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["coverage_by_crop"]["pearl millet"], 1)
        self.assertEqual(report["coverage_by_microbial_group"]["Azospirillum"], 1)
        self.assertEqual(report["taxonomy_normalization_count"], 1)

    def test_build_curation_report_flags_duplicates(self) -> None:
        records = [
            {
                "record_type": "Taxon",
                "id": "taxon:bacillus-subtilis-a",
                "scientific_name": "Bacillus subtilis",
            },
            {
                "record_type": "Taxon",
                "id": "taxon:bacillus-subtilis-b",
                "scientific_name": "bacillus_subtilis",
            },
            {
                "record_type": "Strain",
                "id": "strain:a",
                "taxon": "Bacillus subtilis",
                "strain_label": "Subtilis-1",
            },
            {
                "record_type": "Strain",
                "id": "strain:b",
                "taxon": "bacillus subtilis",
                "strain_label": "Subtilis-1",
            },
            {
                "record_type": "LiteratureDocument",
                "id": "document:a",
                "title": "Same title",
                "citation": "doi:10.1234/example",
                "source_url": "",
            },
            {
                "record_type": "EvidenceRecord",
                "id": "evidence:b",
                "title": "Different title",
                "citation": "https://doi.org/10.1234/example",
                "source_url": "",
            },
        ]

        report = build_curation_report(records)

        self.assertEqual(len(report["duplicate_taxa"]), 1)
        self.assertEqual(len(report["duplicate_strains"]), 1)
        self.assertEqual(len(report["duplicate_publications"]), 1)
        self.assertIn("evidence:b", report["duplicate_record_ids"])


if __name__ == "__main__":
    unittest.main()
