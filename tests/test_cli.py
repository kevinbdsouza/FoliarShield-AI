from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from foliarshield_ai.cli import main


class CliTests(unittest.TestCase):
    def test_smoke_run_writes_valid_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "smoke.json"

            exit_code = main(["smoke-run", "--output", str(output_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["artifact_id"], "run:local-smoke-001")
            self.assertEqual(payload["random_seed"], 1729)
            self.assertEqual(payload["source_registry_entries"], 10)
            self.assertGreaterEqual(len(payload["records"]), 18)

    def test_ingest_seed_strains_writes_records_and_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "seed-strains.json"
            manifest_path = Path(temp_dir) / "seed-manifest.json"

            exit_code = main(
                [
                    "ingest-seed-strains",
                    "--output",
                    str(output_path),
                    "--manifest-output",
                    str(manifest_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["artifact_id"], "ingest:seed-strains")
            self.assertEqual(payload["input_records"], 3)
            self.assertEqual(payload["taxon_records"], 3)
            self.assertEqual(payload["strain_records"], 3)
            self.assertEqual(manifest["record_count"], 3)

    def test_ingest_crop_stress_writes_records_and_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "seed-leaf-assay-context.json"
            manifest_path = Path(temp_dir) / "seed-leaf-assay-context-manifest.json"

            exit_code = main(
                [
                    "ingest-crop-stress",
                    "--output",
                    str(output_path),
                    "--manifest-output",
                    str(manifest_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["artifact_id"], "ingest:seed-crop-stress")
            self.assertEqual(payload["input_records"], 3)
            self.assertEqual(payload["crop_records"], 3)
            self.assertEqual(payload["evidence_records"], 3)
            self.assertEqual(manifest["record_count"], 3)

    def test_ingest_formulation_writes_records_and_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "seed-formulation.json"
            manifest_path = Path(temp_dir) / "seed-formulation-manifest.json"

            exit_code = main(
                [
                    "ingest-formulation",
                    "--output",
                    str(output_path),
                    "--manifest-output",
                    str(manifest_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["artifact_id"], "ingest:seed-formulation")
            self.assertEqual(payload["input_records"], 3)
            self.assertEqual(payload["material_records"], 3)
            self.assertEqual(payload["evidence_records"], 3)
            self.assertEqual(manifest["record_count"], 3)

    def test_chunk_literature_writes_documents_and_chunks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "seed-literature-chunks.json"
            manifest_path = Path(temp_dir) / "seed-literature-manifest.json"

            exit_code = main(
                [
                    "chunk-literature",
                    "--output",
                    str(output_path),
                    "--manifest-output",
                    str(manifest_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["artifact_id"], "ingest:seed-literature-chunks")
            self.assertEqual(payload["input_records"], 3)
            self.assertEqual(payload["document_records"], 3)
            self.assertGreaterEqual(payload["chunk_records"], 3)
            self.assertEqual(manifest["record_count"], 3)

    def test_data_quality_report_summarizes_processed_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            strains_path = Path(temp_dir) / "seed-strains.json"
            crop_path = Path(temp_dir) / "seed-leaf-assay-context.json"
            formulation_path = Path(temp_dir) / "seed-formulation.json"
            chunks_path = Path(temp_dir) / "seed-literature-chunks.json"
            report_path = Path(temp_dir) / "quality.json"

            self.assertEqual(main(["ingest-seed-strains", "--output", str(strains_path)]), 0)
            self.assertEqual(main(["ingest-crop-stress", "--output", str(crop_path)]), 0)
            self.assertEqual(main(["ingest-formulation", "--output", str(formulation_path)]), 0)
            self.assertEqual(main(["chunk-literature", "--output", str(chunks_path)]), 0)
            exit_code = main(
                [
                    "data-quality-report",
                    "--inputs",
                    str(strains_path),
                    str(crop_path),
                    str(formulation_path),
                    str(chunks_path),
                    "--output",
                    str(report_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertGreaterEqual(payload["record_count"], 35)
            self.assertIn("rice", payload["coverage_by_crop"])
            self.assertIn("cloaked foliar droplet", payload["coverage_by_formulation_material"])
            self.assertIn("duplicate_candidate_summary", payload)

    def test_curation_report_writes_duplicate_and_taxonomy_checks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            strains_path = Path(temp_dir) / "seed-strains.json"
            chunks_path = Path(temp_dir) / "seed-literature-chunks.json"
            report_path = Path(temp_dir) / "curation.json"

            self.assertEqual(main(["ingest-seed-strains", "--output", str(strains_path)]), 0)
            self.assertEqual(main(["chunk-literature", "--output", str(chunks_path)]), 0)
            exit_code = main(
                [
                    "curation-report",
                    "--inputs",
                    str(strains_path),
                    str(chunks_path),
                    "--output",
                    str(report_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["artifact_id"], "curation:seed-data")
            self.assertGreaterEqual(len(payload["taxonomy_normalization"]), 6)
            self.assertIn("duplicate_publications", payload)

    def test_retrieval_extraction_and_graph_commands_write_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            chunks_path = Path(temp_dir) / "seed-literature-chunks.json"
            index_path = Path(temp_dir) / "retrieval-index.json"
            query_path = Path(temp_dir) / "retrieval-query.json"
            extraction_path = Path(temp_dir) / "structured-extractions.json"
            graph_path = Path(temp_dir) / "graph.json"
            review_path = Path(temp_dir) / "review-queue.json"
            gold_path = Path(temp_dir) / "gold-extractions.json"
            evaluation_path = Path(temp_dir) / "extraction-evaluation.json"
            graph_validation_path = Path(temp_dir) / "graph-validation.json"

            self.assertEqual(main(["chunk-literature", "--output", str(chunks_path)]), 0)
            self.assertEqual(
                main(
                    [
                        "build-retrieval-index",
                        "--inputs",
                        str(chunks_path),
                        "--output",
                        str(index_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "query-retrieval",
                        "--index",
                        str(index_path),
                        "--query",
                        "rice foliar retention rainfastness",
                        "--crop",
                        "rice",
                        "--evidence-type",
                        "leaf-assay-context",
                        "--output",
                        str(query_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "extract-evidence",
                        "--inputs",
                        str(chunks_path),
                        "--output",
                        str(extraction_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "build-knowledge-graph",
                        "--inputs",
                        str(chunks_path),
                        "--extractions",
                        str(extraction_path),
                        "--output",
                        str(graph_path),
                    ]
                ),
                0,
            )
            gold_path.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "records": [
                            {
                                "chunk_id": "chunk:document-manual-doc-001-0",
                                "crops": ["rice"],
                                "stressors": ["leaf-retention", "rainfastness"],
                                "organisms": ["Bacillus"],
                                "reported_phenotypes": ["retained intensity proxy"],
                                "materials": [],
                                "encapsulation_architectures": [],
                                "release_or_viability_signals": [],
                                "assay_or_fidelity": ["fast_physical_assay_seed"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                main(
                    [
                        "build-review-queue",
                        "--extractions",
                        str(extraction_path),
                        "--output",
                        str(review_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "evaluate-extractions",
                        "--extractions",
                        str(extraction_path),
                        "--gold",
                        str(gold_path),
                        "--output",
                        str(evaluation_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "validate-knowledge-graph",
                        "--graph",
                        str(graph_path),
                        "--output",
                        str(graph_validation_path),
                    ]
                ),
                0,
            )

            index = json.loads(index_path.read_text(encoding="utf-8"))
            query = json.loads(query_path.read_text(encoding="utf-8"))
            extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            review = json.loads(review_path.read_text(encoding="utf-8"))
            evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
            graph_validation = json.loads(graph_validation_path.read_text(encoding="utf-8"))
            self.assertEqual(index["status"], "ok")
            self.assertEqual(index["embedding_model"], "deterministic-token-hash-v0.1")
            self.assertGreaterEqual(query["result_count"], 1)
            self.assertGreaterEqual(extraction["record_count"], 3)
            self.assertGreaterEqual(graph["node_count"], 4)
            self.assertGreaterEqual(review["queue_count"], 1)
            self.assertEqual(evaluation["gold_example_count"], 1)
            self.assertIn(graph_validation["status"], {"ok", "needs_review"})

    def test_feature_pilot_dataset_and_baseline_commands_write_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            strains_path = Path(temp_dir) / "seed-strains.json"
            crop_path = Path(temp_dir) / "seed-leaf-assay-context.json"
            formulation_path = Path(temp_dir) / "seed-formulation.json"
            chunks_path = Path(temp_dir) / "seed-literature-chunks.json"
            features_path = Path(temp_dir) / "features.json"
            datasets_path = Path(temp_dir) / "pilot-datasets.json"
            baselines_path = Path(temp_dir) / "baselines.json"
            random_path = Path(temp_dir) / "random-candidates.json"
            objectives_path = Path(temp_dir) / "objectives.json"
            scorecards_path = Path(temp_dir) / "scorecards.json"
            optimizer_path = Path(temp_dir) / "optimizer-only.json"
            optimizer_proposals_path = Path(temp_dir) / "optimizer-proposals.json"
            reasoning_path = Path(temp_dir) / "reasoning-only.json"
            benchmark_path = Path(temp_dir) / "baseline-benchmark.json"
            shortlist_path = Path(temp_dir) / "shortlist.json"

            self.assertEqual(main(["ingest-seed-strains", "--output", str(strains_path)]), 0)
            self.assertEqual(main(["ingest-crop-stress", "--output", str(crop_path)]), 0)
            self.assertEqual(main(["ingest-formulation", "--output", str(formulation_path)]), 0)
            self.assertEqual(main(["chunk-literature", "--output", str(chunks_path)]), 0)

            common_inputs = [
                str(strains_path),
                str(crop_path),
                str(formulation_path),
                str(chunks_path),
            ]
            self.assertEqual(
                main(
                    [
                        "build-feature-table",
                        "--inputs",
                        *common_inputs,
                        "--output",
                        str(features_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "run-optimizer-proposals",
                        "--inputs",
                        *common_inputs,
                        "--initial-observations-per-task",
                        "1",
                        "--proposal-batch-size",
                        "2",
                        "--output",
                        str(optimizer_proposals_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "build-pilot-datasets",
                        "--inputs",
                        *common_inputs,
                        "--output",
                        str(datasets_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "run-heuristic-baselines",
                        "--inputs",
                        *common_inputs,
                        "--output",
                        str(baselines_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "sample-random-candidates",
                        "--inputs",
                        *common_inputs,
                        "--samples-per-task",
                        "2",
                        "--output",
                        str(random_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "define-evaluator-objectives",
                        "--output",
                        str(objectives_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "build-candidate-scorecards",
                        "--inputs",
                        *common_inputs,
                        "--samples-per-task",
                        "2",
                        "--output",
                        str(scorecards_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "run-optimizer-only-baseline",
                        "--inputs",
                        *common_inputs,
                        "--initial-samples-per-task",
                        "3",
                        "--proposal-batch-size",
                        "2",
                        "--output",
                        str(optimizer_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "run-reasoning-only-baseline",
                        "--inputs",
                        *common_inputs,
                        "--top-k",
                        "2",
                        "--output",
                        str(reasoning_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "build-baseline-benchmark-report",
                        "--heuristic-report",
                        str(baselines_path),
                        "--random-candidate-report",
                        str(random_path),
                        "--scorecard-report",
                        str(scorecards_path),
                        "--optimizer-report",
                        str(optimizer_path),
                        "--reasoning-report",
                        str(reasoning_path),
                        "--top-k",
                        "2",
                        "--output",
                        str(benchmark_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "build-candidate-shortlist",
                        "--scorecard-report",
                        str(scorecards_path),
                        "--optimizer-report",
                        str(optimizer_path),
                        "--top-k",
                        "2",
                        "--output",
                        str(shortlist_path),
                    ]
                ),
                0,
            )

            features = json.loads(features_path.read_text(encoding="utf-8"))
            datasets = json.loads(datasets_path.read_text(encoding="utf-8"))
            baselines = json.loads(baselines_path.read_text(encoding="utf-8"))
            random_candidates = json.loads(random_path.read_text(encoding="utf-8"))
            objectives = json.loads(objectives_path.read_text(encoding="utf-8"))
            scorecards = json.loads(scorecards_path.read_text(encoding="utf-8"))
            optimizer = json.loads(optimizer_path.read_text(encoding="utf-8"))
            optimizer_proposals = json.loads(
                optimizer_proposals_path.read_text(encoding="utf-8")
            )
            reasoning = json.loads(reasoning_path.read_text(encoding="utf-8"))
            benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
            shortlist = json.loads(shortlist_path.read_text(encoding="utf-8"))
            self.assertEqual(features["status"], "ok")
            self.assertGreaterEqual(features["feature_counts"]["strain_features"], 3)
            self.assertEqual(datasets["task_count"], 2)
            self.assertGreaterEqual(
                datasets["records"][0]["coverage_counts"]["candidate_strains"],
                1,
            )
            self.assertEqual(baselines["task_count"], 2)
            self.assertGreaterEqual(len(baselines["records"][0]["ranked_strains"]), 1)
            self.assertEqual(random_candidates["task_count"], 2)
            self.assertEqual(len(random_candidates["records"][0]["candidate_designs"]), 2)
            self.assertTrue(
                objectives["records"][0]["promotion_policy"]["requires_human_review"]
            )
            self.assertEqual(scorecards["task_count"], 2)
            self.assertIn(
                "uncertainty_intervals",
                scorecards["records"][0]["scorecards"][0],
            )
            self.assertEqual(optimizer["task_count"], 2)
            self.assertEqual(len(optimizer["records"][0]["proposed_candidates"]), 2)
            self.assertEqual(optimizer_proposals["task_count"], 2)
            self.assertIn(
                "surrogate_prediction",
                optimizer_proposals["records"][0]["proposed_candidates"][0],
            )
            self.assertEqual(reasoning["task_count"], 2)
            self.assertGreaterEqual(reasoning["records"][0]["hypothesis_count"], 1)
            self.assertEqual(benchmark["task_count"], 2)
            self.assertIn("optimizer_only", benchmark["records"][0]["metrics"])
            self.assertIn("reasoning_only", benchmark["records"][0]["metrics"])
            self.assertEqual(shortlist["task_count"], 2)
            self.assertLessEqual(shortlist["records"][0]["shortlist_count"], 2)


if __name__ == "__main__":
    unittest.main()
