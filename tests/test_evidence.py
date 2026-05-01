from __future__ import annotations

import unittest
from typing import Any

from foliarshield_ai.evidence import (
    build_evidence_review_queue,
    build_knowledge_graph,
    build_retrieval_index,
    evaluate_structured_extractions,
    extract_structured_evidence,
    query_retrieval_index,
    validate_knowledge_graph,
)


class EvidenceWorkflowTests(unittest.TestCase):
    def test_retrieval_index_scores_and_filters_chunks(self) -> None:
        records: list[dict[str, Any]] = [
            {
                "record_type": "LiteratureChunk",
                "id": "chunk:millet",
                "document_id": "document:millet",
                "citation": "Seed citation",
                "text": "Pearl millet drought and heat retrieval validation text.",
                "metadata": {"evidence_type": "crop-stress", "title": "Millet note"},
                "confidence": 0.5,
                "license": "CC-BY-4.0",
                "provenance": "seed",
            }
        ]

        index = build_retrieval_index(records)
        results = query_retrieval_index(
            index,
            query="millet drought",
            crop="millet",
            evidence_type="crop-stress",
        )

        self.assertEqual(index["chunk_count"], 1)
        self.assertEqual(index["embedding_dimensions"], 32)
        self.assertEqual(len(index["records"][0]["embedding"]), 32)
        self.assertEqual(results["result_count"], 1)
        self.assertEqual(results["results"][0]["chunk_id"], "chunk:millet")
        self.assertEqual(results["results"][0]["citation"], "Seed citation")
        self.assertGreater(results["results"][0]["embedding_score"], 0)

    def test_structured_extraction_marks_review_scaffolding(self) -> None:
        records: list[dict[str, Any]] = [
            {
                "record_type": "Taxon",
                "id": "taxon:bacillus-subtilis",
                "scientific_name": "Bacillus subtilis",
            },
            {
                "record_type": "LiteratureChunk",
                "id": "chunk:liquid-liquid-encapsulation",
                "document_id": "document:liquid-liquid-encapsulation",
                "citation": "Seed citation",
                "text": (
                    "Bacillus subtilis liquid-liquid encapsulation placeholder "
                    "with simulated rainfall release and viability signal."
                ),
                "metadata": {"evidence_type": "formulation"},
                "confidence": 0.52,
            }
        ]

        extractions = extract_structured_evidence(records)
        extraction = extractions["records"][0]

        self.assertIn("liquid-liquid encapsulation", extraction["materials"])
        self.assertIn("Bacillus subtilis", extraction["organisms"])
        self.assertIn("viability signal", extraction["reported_phenotypes"])
        self.assertIn("liquid-liquid encapsulation", extraction["encapsulation_architectures"])
        self.assertIn("placeholder", extraction["review_flags"])
        self.assertLess(extraction["confidence"], 0.52)

    def test_knowledge_graph_adds_seed_nodes_and_edges(self) -> None:
        records: list[dict[str, Any]] = [
            {
                "record_type": "LiteratureChunk",
                "id": "chunk:millet",
                "document_id": "document:millet",
                "citation": "Seed citation",
                "text": "Pearl millet drought text.",
                "metadata": {"evidence_type": "crop-stress"},
                "confidence": 0.5,
                "source": "seed",
                "provenance": "seed",
            }
        ]
        extractions: list[dict[str, Any]] = [
            {
                "chunk_id": "chunk:millet",
                "document_id": "document:millet",
                "citation": "Seed citation",
                "confidence": 0.35,
                "crops": ["pearl millet"],
                "stressors": ["drought"],
                "organisms": ["Azospirillum brasilense"],
                "reported_phenotypes": ["root growth proxy"],
                "materials": [],
                "encapsulation_architectures": [],
                "release_or_viability_signals": [],
            }
        ]

        graph = build_knowledge_graph(records, extraction_records=extractions)

        self.assertGreaterEqual(graph["node_count"], 3)
        self.assertGreaterEqual(graph["edge_count"], 2)
        self.assertTrue(
            any(edge["relation"] == "tested_in" for edge in graph["edges"])
        )
        self.assertTrue(
            any(node["type"] == "OrganismMention" for node in graph["nodes"])
        )

    def test_review_queue_collects_low_confidence_and_flagged_extractions(self) -> None:
        extractions: list[dict[str, Any]] = [
            {
                "chunk_id": "chunk:review",
                "document_id": "document:review",
                "citation": "Seed citation",
                "confidence": 0.35,
                "evidence_type": "crop-stress",
                "crops": ["pearl millet"],
                "stressors": ["drought"],
                "organisms": [],
                "reported_phenotypes": [],
                "materials": [],
                "encapsulation_architectures": [],
                "release_or_viability_signals": [],
                "assay_or_fidelity": [],
                "review_flags": ["placeholder"],
            }
        ]

        queue = build_evidence_review_queue(extractions, min_confidence=0.5)

        self.assertEqual(queue["queue_count"], 1)
        self.assertIn("low_confidence", queue["records"][0]["review_reasons"])
        self.assertIn("manual_correction_template", queue["records"][0])

    def test_extraction_evaluation_reports_field_metrics(self) -> None:
        extractions: list[dict[str, Any]] = [
            {
                "chunk_id": "chunk:gold",
                "crops": ["pearl millet"],
                "stressors": ["drought"],
                "organisms": ["Azospirillum"],
                "reported_phenotypes": [],
                "materials": [],
                "encapsulation_architectures": [],
                "release_or_viability_signals": [],
                "assay_or_fidelity": [],
            }
        ]
        gold: list[dict[str, Any]] = [
            {
                "chunk_id": "chunk:gold",
                "crops": ["pearl millet"],
                "stressors": ["drought", "heat"],
                "organisms": ["Azospirillum"],
                "reported_phenotypes": [],
                "materials": [],
                "encapsulation_architectures": [],
                "release_or_viability_signals": [],
                "assay_or_fidelity": [],
            }
        ]

        report = evaluate_structured_extractions(extractions, gold)

        self.assertEqual(report["gold_example_count"], 1)
        self.assertEqual(report["matched_example_count"], 1)
        self.assertEqual(report["per_field"]["stressors"]["false_negative"], 1)
        self.assertLess(report["micro_average"]["recall"], 1.0)

    def test_graph_validation_detects_dangling_edges(self) -> None:
        graph: dict[str, Any] = {
            "artifact_id": "graph:test",
            "nodes": [{"id": "node:known", "type": "Known"}],
            "edges": [
                {
                    "source": "node:known",
                    "target": "node:missing",
                    "relation": "supports",
                }
            ],
        }

        report = validate_knowledge_graph(graph)

        self.assertEqual(report["status"], "needs_review")
        self.assertEqual(report["dangling_edge_count"], 1)
        self.assertIn("supports", report["relation_counts"])


if __name__ == "__main__":
    unittest.main()
