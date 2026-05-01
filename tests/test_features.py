from __future__ import annotations

import unittest
from typing import Any

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


class FeatureWorkflowTests(unittest.TestCase):
    def test_feature_table_builds_seed_proxy_features(self) -> None:
        records = _seed_records()

        table = build_feature_table(records)

        self.assertEqual(table["status"], "ok")
        self.assertEqual(table["feature_counts"]["strain_features"], 2)
        self.assertEqual(table["feature_counts"]["formulation_features"], 1)
        self.assertEqual(table["feature_counts"]["crop_stress_context_features"], 1)
        self.assertEqual(table["feature_counts"]["payload_combination_pair_features"], 1)
        self.assertEqual(table["feature_counts"]["genome_records_linked"], 1)
        self.assertEqual(table["feature_counts"]["protein_or_gene_features_linked"], 1)
        self.assertEqual(table["feature_counts"]["soil_context_records"], 1)
        self.assertTrue(table["strain_features"][0]["stress_response_flag"])
        self.assertEqual(table["strain_features"][0]["genome_accessions"], ["GCF_TEST_000001"])
        self.assertEqual(len(table["strain_features"][0]["genome_marker_embedding"]), 8)
        self.assertIn(
            "osmoprotection marker",
            table["strain_features"][0]["gene_function_summary_terms"],
        )
        self.assertTrue(table["strain_features"][0]["genome_feature_available"])
        self.assertEqual(table["strain_features"][1]["genome_marker_embedding"], [0.0] * 8)
        self.assertFalse(table["strain_features"][1]["genome_feature_available"])
        self.assertEqual(
            table["crop_stress_context_features"][0]["soil_context_ids"],
            ["soil:dryland"],
        )
        self.assertEqual(table["crop_stress_context_features"][0]["soil_ph_range"], [6.2, 7.8])

    def test_pilot_dataset_collects_matching_seed_records(self) -> None:
        datasets = build_pilot_task_datasets(_seed_records(), _pilot_tasks())

        self.assertEqual(datasets["task_count"], 2)
        first = datasets["records"][0]
        self.assertEqual(first["readiness_status"], "needs_review")
        self.assertIn("strain:a", first["matched_record_ids"]["candidate_strains"])
        self.assertIn("evidence:crop", first["matched_record_ids"]["crop_stress_evidence"])
        second = datasets["records"][1]
        self.assertIn("material:alginate", second["matched_record_ids"]["candidate_materials"])

    def test_heuristic_baselines_rank_strains_and_formulations(self) -> None:
        report = build_heuristic_baseline_report(_seed_records(), _pilot_tasks())

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["task_count"], 2)
        first = report["records"][0]
        self.assertEqual(first["ranked_strains"][0]["strain_id"], "strain:a")
        self.assertEqual(first["ranked_payload_combinations"][0]["assembly_rule"], (
            "top_ranked_biosafety_clear_pair_with_genus_diversity_bonus"
        ))
        second = report["records"][1]
        self.assertEqual(second["ranked_formulations"][0]["material_id"], "material:alginate")

    def test_random_candidate_sampler_is_deterministic_and_valid(self) -> None:
        first = build_random_candidate_sampler(
            _seed_records(),
            _pilot_tasks(),
            random_seed=11,
            samples_per_task=3,
        )
        second = build_random_candidate_sampler(
            _seed_records(),
            _pilot_tasks(),
            random_seed=11,
            samples_per_task=3,
        )

        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["records"], second["records"])
        self.assertEqual(first["records"][0]["candidate_designs"][0]["crop"], "millet")
        self.assertTrue(
            first["records"][0]["candidate_designs"][0]["validity_checks"]["biosafety_clear"]
        )
        self.assertEqual(len(first["records"][0]["candidate_designs"]), 3)

    def test_evaluator_objectives_define_weights_by_task(self) -> None:
        objectives = build_evaluator_objectives(_pilot_tasks())

        self.assertEqual(objectives["status"], "ok")
        self.assertEqual(len(objectives["objective_definitions"]), 7)
        first_weights = objectives["records"][0]["objective_weights"]
        second_weights = objectives["records"][1]["objective_weights"]
        self.assertGreater(first_weights["stress_tolerance_proxy"], 0)
        self.assertGreater(
            second_weights["release_profile_fit"],
            first_weights["release_profile_fit"],
        )

    def test_candidate_scorecards_include_uncertainty_and_guardrails(self) -> None:
        scorecards = build_candidate_scorecards(
            _seed_records(),
            _pilot_tasks(),
            random_seed=11,
            samples_per_task=2,
        )

        self.assertEqual(scorecards["status"], "ok")
        first_task = scorecards["records"][0]
        first_card = first_task["scorecards"][0]
        self.assertIn("stress_tolerance_proxy", first_card["objective_scores"])
        self.assertIn("stress_tolerance_proxy", first_card["uncertainty_intervals"])
        self.assertIn(first_card["responsible_use_status"], {"needs_review", "promoted_for_review"})
        self.assertGreaterEqual(first_task["summary"]["mean_overall_score"], 0)

    def test_candidate_search_space_filters_and_counts_feasible_designs(self) -> None:
        search_space = build_candidate_search_space(_seed_records(), _pilot_tasks())

        self.assertEqual(search_space["status"], "ok")
        first = search_space["records"][0]
        self.assertEqual(first["task_id"], "pilot-1")
        self.assertEqual(first["payload_combination_sizes"], [1, 2])
        self.assertEqual(first["feasible_candidate_count"], 3)
        self.assertEqual(len(first["strain_candidates"]), 2)
        self.assertEqual(first["constraint_summary"]["max_payload_combination_size"], 2)
        second = search_space["records"][1]
        self.assertEqual(second["formulation_candidates"][0]["material_id"], "material:alginate")

    def test_candidate_encoding_emits_stable_vectors_and_constraints(self) -> None:
        encoding = build_candidate_encoding_report(_seed_records(), _pilot_tasks())

        self.assertEqual(encoding["status"], "ok")
        first = encoding["records"][0]
        self.assertEqual(first["encoded_candidate_count"], 3)
        row = first["encoded_candidates"][0]
        self.assertEqual(len(row["continuous_vector"]), 11)
        self.assertTrue(row["conditional_constraints_satisfied"]["has_strain"])
        second = encoding["records"][1]
        self.assertTrue(
            second["encoded_candidates"][0]["conditional_constraints_satisfied"][
                "has_required_formulation"
            ]
        )

    def test_optimizer_only_baseline_selects_scored_candidates(self) -> None:
        report = build_optimizer_only_baseline_report(
            _seed_records(),
            _pilot_tasks(),
            random_seed=11,
            initial_samples_per_task=4,
            proposal_batch_size=2,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["task_count"], 2)
        first = report["records"][0]
        self.assertEqual(first["method"], "deterministic_optimizer_only_seed_search")
        self.assertEqual(first["summary"]["search_cost_candidates_scored"], 4)
        self.assertEqual(len(first["proposed_candidates"]), 2)
        self.assertGreaterEqual(
            first["proposed_candidates"][0]["overall_score"],
            first["proposed_candidates"][1]["overall_score"],
        )

    def test_optimizer_proposals_include_surrogate_and_acquisition(self) -> None:
        report = build_optimizer_proposal_report(
            _seed_records(),
            _pilot_tasks(),
            random_seed=11,
            initial_observations_per_task=1,
            proposal_batch_size=2,
        )

        self.assertEqual(report["status"], "ok")
        first = report["records"][0]
        self.assertEqual(first["method"], "deterministic_seed_surrogate_ucb")
        self.assertEqual(first["surrogate_model"]["type"], "inverse_distance_weighted_regression")
        self.assertEqual(first["acquisition_function"]["type"], "upper_confidence_bound")
        self.assertEqual(len(first["initial_observations"]), 1)
        self.assertEqual(len(first["proposed_candidates"]), 2)
        self.assertIn("surrogate_prediction", first["proposed_candidates"][0])
        self.assertIn("acquisition", first["proposed_candidates"][0])

    def test_baseline_benchmark_report_compares_seed_methods(self) -> None:
        records = _seed_records()
        tasks = _pilot_tasks()
        heuristic = build_heuristic_baseline_report(records, tasks)
        random_candidates = build_random_candidate_sampler(
            records,
            tasks,
            random_seed=11,
            samples_per_task=4,
        )
        scorecards = build_candidate_scorecards(
            records,
            tasks,
            random_seed=11,
            samples_per_task=4,
        )
        optimizer = build_optimizer_only_baseline_report(
            records,
            tasks,
            random_seed=11,
            initial_samples_per_task=4,
            proposal_batch_size=2,
        )
        reasoning = build_reasoning_only_baseline_report(records, tasks, top_k=2)

        report = build_baseline_benchmark_report(
            heuristic,
            random_candidates,
            scorecards,
            optimizer,
            reasoning,
            top_k=2,
        )

        self.assertEqual(report["status"], "ok")
        first_metrics = report["records"][0]["metrics"]
        self.assertIn("hit_rate", first_metrics["random_valid_candidates"])
        self.assertIn("top_k_enrichment", first_metrics["optimizer_only"])
        self.assertIn("reasoning_only", first_metrics)
        self.assertIn("optimizer_top_k_lift_over_random", report["records"][0]["comparisons"])

    def test_reasoning_only_baseline_emits_cited_hypotheses(self) -> None:
        report = build_reasoning_only_baseline_report(_seed_records(), _pilot_tasks(), top_k=2)

        self.assertEqual(report["status"], "ok")
        first = report["records"][0]
        self.assertEqual(first["method"], "deterministic_retrieval_grounded_reasoning_only")
        self.assertGreater(first["hypothesis_count"], 0)
        self.assertIn("supporting_evidence_ids", first["hypotheses"][0])
        self.assertGreaterEqual(first["summary"]["evidence_record_count"], 1)

    def test_candidate_shortlist_export_filters_and_ranks_candidates(self) -> None:
        scorecards = build_candidate_scorecards(
            _seed_records(),
            _pilot_tasks(),
            random_seed=11,
            samples_per_task=4,
        )
        optimizer = build_optimizer_only_baseline_report(
            _seed_records(),
            _pilot_tasks(),
            random_seed=11,
            initial_samples_per_task=4,
            proposal_batch_size=3,
        )

        shortlist = build_candidate_shortlist_export(scorecards, optimizer, top_k=2)

        self.assertEqual(shortlist["status"], "ok")
        first = shortlist["records"][0]
        self.assertLessEqual(first["shortlist_count"], 2)
        self.assertEqual(first["shortlist"][0]["rank"], 1)
        self.assertEqual(first["shortlist"][0]["review_decision"], "human_review_required")


def _pilot_tasks() -> list[dict[str, Any]]:
    return [
        {
            "id": "pilot-1",
            "name": "Millet drought payload_combination",
            "crop": "millet",
            "stressors": ["drought", "heat"],
            "outputs": ["ranked_strains", "ranked_payload_combinations"],
            "evaluation_tier": "in_silico",
        },
        {
            "id": "pilot-2",
            "name": "Formulation scoring",
            "crop": "millet",
            "stressors": ["drought", "heat"],
            "formulation_context": ["hydrogel_encapsulation", "controlled_release"],
            "outputs": ["ranked_materials", "release_fit_scores"],
            "evaluation_tier": "in_silico",
        },
    ]


def _seed_records() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "Strain",
            "id": "strain:a",
            "taxon": "Azospirillum brasilense",
            "confidence": 0.7,
            "phenotype_tags": ["drought stress", "root growth"],
            "biosafety_flags": [],
        },
        {
            "record_type": "Strain",
            "id": "strain:b",
            "taxon": "Bacillus subtilis",
            "confidence": 0.6,
            "phenotype_tags": ["heat tolerant spore", "formulation viability"],
            "biosafety_flags": [],
        },
        {
            "record_type": "Genome",
            "id": "genome:a",
            "taxon_id": "taxon:a",
            "strain_id": "strain:a",
            "accession": "GCF_TEST_000001",
            "assembly_level": "scaffold",
            "feature_source": "local-fixture",
        },
        {
            "record_type": "ProteinOrGeneFeature",
            "id": "feature:a-osmoprotection",
            "genome_id": "genome:a",
            "feature_name": "osmoprotection marker",
            "feature_type": "functional_marker",
            "function_label": "stress response proxy",
            "evidence_ids": ["evidence:crop"],
        },
        {
            "record_type": "Crop",
            "id": "crop:millet",
            "common_name": "pearl millet",
            "region_tags": ["india-dryland"],
        },
        {
            "record_type": "StressContext",
            "id": "stress:millet",
            "crop_id": "crop:millet",
            "stressors": ["drought", "heat"],
            "region": "India dryland systems",
            "temperature_c": [32, 42],
        },
        {
            "record_type": "SoilContext",
            "id": "soil:dryland",
            "texture": "loam",
            "ph_range": [6.2, 7.8],
            "organic_matter_level": "low-to-medium",
            "region": "India dryland systems",
        },
        {
            "record_type": "EvidenceRecord",
            "id": "evidence:crop",
            "evidence_type": "crop-stress",
            "title": "Millet drought heat seed note",
            "claims": ["millet drought heat review"],
            "confidence": 0.5,
        },
        {
            "record_type": "FormulationMaterial",
            "id": "material:alginate",
            "material_class": "polysaccharide hydrogel",
            "release_triggers": ["moisture"],
            "viability_notes": "avoid high-temperature processing",
            "confidence": 0.6,
        },
        {
            "record_type": "ReleaseTrigger",
            "id": "trigger:moisture",
            "trigger_type": "moisture",
        },
        {
            "record_type": "EncapsulationArchitecture",
            "id": "architecture:alginate",
            "architecture_type": "hydrogel_microcapsule",
            "material_ids": ["material:alginate"],
            "release_trigger_ids": ["trigger:moisture"],
            "viability_constraints": ["avoid high-temperature processing"],
        },
        {
            "record_type": "EvidenceRecord",
            "id": "evidence:formulation",
            "evidence_type": "formulation",
            "title": "Alginate hydrogel formulation seed note",
            "claims": ["alginate hydrogel review"],
            "confidence": 0.52,
        },
        {
            "record_type": "LiteratureChunk",
            "id": "chunk:millet",
            "text": "Pearl millet drought heat and alginate hydrogel controlled release.",
            "metadata": {"evidence_type": "crop-stress"},
        },
    ]


if __name__ == "__main__":
    unittest.main()
