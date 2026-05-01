"""Deterministic seed feature, pilot-dataset, and baseline helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from hashlib import sha256
from itertools import combinations
from random import Random
from typing import Any, cast

DEFAULT_OBJECTIVE_WEIGHTS = {
    "stress_tolerance_proxy": 0.22,
    "nutrient_use_efficiency_proxy": 0.12,
    "persistence_proxy": 0.12,
    "encapsulation_viability_proxy": 0.16,
    "release_profile_fit": 0.16,
    "manufacturability_proxy": 0.1,
    "evidence_support": 0.12,
}


def build_feature_table(
    records: Iterable[Mapping[str, Any]],
    *,
    artifact_id: str = "features:seed-v0.1",
) -> dict[str, Any]:
    """Build deterministic local feature records for MVP workflow validation."""

    record_list = list(records)
    strain_records = _records_of_type(record_list, "Strain")
    genome_records = _records_of_type(record_list, "Genome")
    protein_feature_records = _records_of_type(record_list, "ProteinOrGeneFeature")
    material_records = _records_of_type(record_list, "FormulationMaterial")
    architecture_records = _records_of_type(record_list, "EncapsulationArchitecture")
    trigger_records = _records_of_type(record_list, "ReleaseTrigger")
    crop_records = _records_of_type(record_list, "Crop")
    stress_records = _records_of_type(record_list, "StressContext")
    soil_records = _records_of_type(record_list, "SoilContext")
    phenotype_records = _records_of_type(record_list, "Phenotype")

    phenotypes_by_subject: dict[str, list[Mapping[str, Any]]] = {}
    for phenotype in phenotype_records:
        phenotypes_by_subject.setdefault(str(phenotype.get("subject_id", "")), []).append(
            phenotype
        )
    genomes_by_strain: dict[str, list[Mapping[str, Any]]] = {}
    for genome in genome_records:
        strain_id = str(genome.get("strain_id", "") or "")
        if strain_id:
            genomes_by_strain.setdefault(strain_id, []).append(genome)
    gene_features_by_genome: dict[str, list[Mapping[str, Any]]] = {}
    for feature in protein_feature_records:
        gene_features_by_genome.setdefault(str(feature.get("genome_id", "")), []).append(feature)

    triggers_by_id = {str(record.get("id", "")): record for record in trigger_records}
    architectures_by_material: dict[str, list[Mapping[str, Any]]] = {}
    for architecture in architecture_records:
        for material_id in _sequence_values(architecture.get("material_ids", [])):
            architectures_by_material.setdefault(material_id, []).append(architecture)

    strain_features = [
        _strain_feature(
            record,
            phenotypes_by_subject.get(str(record.get("id", "")), []),
            genomes_by_strain.get(str(record.get("id", "")), []),
            gene_features_by_genome,
        )
        for record in strain_records
    ]
    formulation_features = [
        _formulation_feature(
            record,
            architectures_by_material.get(str(record.get("id", "")), []),
            triggers_by_id,
        )
        for record in material_records
    ]
    crop_stress_features = [
        _crop_stress_feature(record, crop_records, soil_records)
        for record in stress_records
    ]
    consortium_features = _consortium_pair_features(strain_features)

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "feature_version": "deterministic-seed-features-v0.1",
        "record_count": len(record_list),
        "feature_counts": {
            "strain_features": len(strain_features),
            "consortium_pair_features": len(consortium_features),
            "formulation_features": len(formulation_features),
            "crop_stress_context_features": len(crop_stress_features),
            "genome_records_linked": sum(
                len(genomes_by_strain.get(str(record.get("id", "")), []))
                for record in strain_records
            ),
            "protein_or_gene_features_linked": sum(
                len(gene_features_by_genome.get(str(genome.get("id", "")), []))
                for genome in genome_records
            ),
            "soil_context_records": len(soil_records),
        },
        "strain_features": strain_features,
        "consortium_pair_features": consortium_features,
        "formulation_features": formulation_features,
        "crop_stress_context_features": crop_stress_features,
        "notes": [
            "Seed features are deterministic proxies for local workflow validation.",
            "They are not benchmark-ready biological descriptors until reviewed datasets land.",
        ],
    }


def build_pilot_task_datasets(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    artifact_id: str = "dataset:pilot-tasks-seed-v0.1",
) -> dict[str, Any]:
    """Package processed seed records into explicit pilot-task dataset slices."""

    record_list = list(records)
    datasets = [_pilot_dataset(task, record_list) for task in tasks]
    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_version": "seed-pilot-datasets-v0.1",
        "task_count": len(datasets),
        "records": datasets,
        "notes": [
            "Pilot datasets are assembled from the current local seed fixtures.",
            "Coverage is intentionally small and review-gated before benchmark claims.",
        ],
    }


def build_heuristic_baseline_report(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    artifact_id: str = "baseline:seed-heuristics-v0.1",
) -> dict[str, Any]:
    """Build first-pass heuristic strain, consortium, and formulation baselines."""

    record_list = list(records)
    feature_table = build_feature_table(record_list)
    strain_features = cast(list[dict[str, Any]], feature_table["strain_features"])
    formulation_features = cast(list[dict[str, Any]], feature_table["formulation_features"])
    baseline_records = [
        _baseline_for_task(task, record_list, strain_features, formulation_features)
        for task in tasks
    ]

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_version": "deterministic-heuristics-v0.1",
        "task_count": len(baseline_records),
        "records": baseline_records,
        "notes": [
            "Heuristic baselines are deterministic scaffolds for regression testing.",
            "Scores are proxy features only and must not be interpreted as recommendations.",
        ],
    }


def build_random_candidate_sampler(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    random_seed: int = 1729,
    samples_per_task: int = 4,
    artifact_id: str = "baseline:random-valid-candidates-v0.1",
) -> dict[str, Any]:
    """Sample deterministic random valid candidate designs for baseline comparisons."""

    record_list = list(records)
    feature_table = build_feature_table(record_list)
    strain_features = [
        feature
        for feature in cast(list[dict[str, Any]], feature_table["strain_features"])
        if not bool(feature.get("biosafety_review_required", False))
    ]
    formulation_features = cast(list[dict[str, Any]], feature_table["formulation_features"])
    stress_features = cast(list[dict[str, Any]], feature_table["crop_stress_context_features"])

    rng = Random(random_seed)
    sampled_records = [
        _sample_candidates_for_task(
            task,
            strain_features,
            formulation_features,
            stress_features,
            rng,
            samples_per_task=samples_per_task,
        )
        for task in tasks
    ]

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_version": "deterministic-random-valid-sampler-v0.1",
        "random_seed": random_seed,
        "samples_per_task": samples_per_task,
        "task_count": len(sampled_records),
        "records": sampled_records,
        "notes": [
            "Random candidates are constrained to schema-valid, biosafety-clear seed records.",
            "This is a baseline search scaffold, not a recommendation generator.",
        ],
    }


def build_candidate_search_space(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    max_consortium_size: int = 2,
    artifact_id: str = "optimizer:seed-search-space-v0.1",
) -> dict[str, Any]:
    """Define a deterministic, constraint-filtered seed candidate search space."""

    record_list = list(records)
    feature_table = build_feature_table(record_list)
    strain_features = cast(list[dict[str, Any]], feature_table["strain_features"])
    formulation_features = cast(list[dict[str, Any]], feature_table["formulation_features"])
    stress_features = cast(list[dict[str, Any]], feature_table["crop_stress_context_features"])
    search_records = [
        _search_space_for_task(
            task,
            strain_features,
            formulation_features,
            stress_features,
            max_consortium_size=max_consortium_size,
        )
        for task in tasks
    ]

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "search_space_version": "deterministic-seed-search-space-v0.1",
        "max_consortium_size": max_consortium_size,
        "task_count": len(search_records),
        "records": search_records,
        "notes": [
            "Search spaces are built from seed proxy features and hard guardrail filters.",
            "They define optimizer inputs only; they are not biological recommendations.",
        ],
    }


def build_candidate_encoding_report(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    max_consortium_size: int = 2,
    artifact_id: str = "optimizer:seed-candidate-encoding-v0.1",
) -> dict[str, Any]:
    """Encode search-space candidates into stable numeric and categorical features."""

    record_list = list(records)
    feature_table = build_feature_table(record_list)
    strain_by_id = {
        str(feature.get("strain_id", "")): feature
        for feature in cast(list[dict[str, Any]], feature_table["strain_features"])
    }
    formulation_by_id = {
        str(feature.get("material_id", "")): feature
        for feature in cast(list[dict[str, Any]], feature_table["formulation_features"])
    }
    stress_by_id = {
        str(feature.get("stress_context_id", "")): feature
        for feature in cast(list[dict[str, Any]], feature_table["crop_stress_context_features"])
    }
    search_space = build_candidate_search_space(
        record_list,
        tasks,
        max_consortium_size=max_consortium_size,
    )
    encoded_records = [
        _encoding_for_task(
            task_record,
            strain_by_id,
            formulation_by_id,
            stress_by_id,
            max_consortium_size=max_consortium_size,
        )
        for task_record in cast(list[dict[str, Any]], search_space["records"])
    ]

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "encoding_version": "deterministic-seed-candidate-encoding-v0.1",
        "search_space_artifact_id": search_space["artifact_id"],
        "task_count": len(encoded_records),
        "records": encoded_records,
        "notes": [
            "Encodings combine continuous proxy features with categorical IDs.",
            "They are stable local optimizer inputs until model-backed embeddings land.",
        ],
    }


def build_evaluator_objectives(
    tasks: Sequence[Mapping[str, Any]],
    *,
    artifact_id: str = "evaluator:objectives-v0.1",
) -> dict[str, Any]:
    """Define deterministic MVP objective contracts and default weights."""

    objective_definitions = [
        {
            "objective": "stress_tolerance_proxy",
            "direction": "maximize",
            "description": "Starter proxy for foliar retention and rainfastness relevance.",
            "evidence_basis": ["phenotype_tags", "crop_stress_evidence", "stress_context"],
        },
        {
            "objective": "nutrient_use_efficiency_proxy",
            "direction": "maximize",
            "description": "Starter proxy for payload compatibility and spray-response support.",
            "evidence_basis": ["phenotype_tags", "phenotype_records"],
        },
        {
            "objective": "persistence_proxy",
            "direction": "maximize",
            "description": "Starter proxy for leaf-surface persistence and post-deposition residence.",
            "evidence_basis": ["phenotype_tags", "formulation_persistence_flags"],
        },
        {
            "objective": "encapsulation_viability_proxy",
            "direction": "maximize",
            "description": "Inverse risk proxy for storage and processing viability constraints.",
            "evidence_basis": ["viability_constraints", "viability_notes"],
        },
        {
            "objective": "release_profile_fit",
            "direction": "maximize",
            "description": "Fit between material triggers, architecture, and task release context.",
            "evidence_basis": ["release_triggers", "architecture_types", "task_context"],
        },
        {
            "objective": "manufacturability_proxy",
            "direction": "maximize",
            "description": (
                "Seed proxy for coating, carrier, matrix, and simple material readiness."
            ),
            "evidence_basis": ["material_class", "manufacturability_flags"],
        },
        {
            "objective": "evidence_support",
            "direction": "maximize",
            "description": "Citation and record-confidence proxy for candidate support.",
            "evidence_basis": ["evidence_records", "record_confidence"],
        },
    ]

    task_records = []
    for task in tasks:
        outputs = set(_sequence_values(task.get("outputs", [])))
        weights = dict(DEFAULT_OBJECTIVE_WEIGHTS)
        if "ranked_consortia" in outputs:
            weights["stress_tolerance_proxy"] += 0.04
            weights["nutrient_use_efficiency_proxy"] += 0.03
            weights["release_profile_fit"] -= 0.04
            weights["manufacturability_proxy"] -= 0.03
        if "ranked_materials" in outputs or "release_fit_scores" in outputs:
            weights["release_profile_fit"] += 0.05
            weights["encapsulation_viability_proxy"] += 0.04
            weights["manufacturability_proxy"] += 0.03
            weights["nutrient_use_efficiency_proxy"] -= 0.04
            weights["persistence_proxy"] -= 0.04
            weights["stress_tolerance_proxy"] -= 0.04
        task_records.append(
            {
                "task_id": str(task.get("id", "")),
                "evaluation_tier": str(task.get("evaluation_tier", "in_silico")),
                "objective_weights": _normalize_weights(weights),
                "promotion_policy": {
                    "minimum_overall_score_for_review": 0.6,
                    "minimum_evidence_support_for_review": 0.35,
                    "biosafety_blocker_bypass_allowed": False,
                    "requires_human_review": True,
                },
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "evaluator_version": "deterministic-seed-evaluator-v0.1",
        "objective_definitions": objective_definitions,
        "records": task_records,
        "notes": [
            "Objective weights are explicit seed defaults for local evaluator scaffolding.",
            "Thresholds require domain review before benchmark or shortlist use.",
        ],
    }


def build_candidate_scorecards(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    random_seed: int = 1729,
    samples_per_task: int = 4,
    artifact_id: str = "evaluator:seed-candidate-scorecards-v0.1",
) -> dict[str, Any]:
    """Generate deterministic scorecards for sampled seed candidate designs."""

    record_list = list(records)
    feature_table = build_feature_table(record_list)
    strain_features = {
        str(feature.get("strain_id", "")): feature
        for feature in cast(list[dict[str, Any]], feature_table["strain_features"])
    }
    formulation_features = {
        str(feature.get("material_id", "")): feature
        for feature in cast(list[dict[str, Any]], feature_table["formulation_features"])
    }
    objective_payload = build_evaluator_objectives(tasks)
    weights_by_task = {
        str(record.get("task_id", "")): cast(dict[str, float], record["objective_weights"])
        for record in cast(list[dict[str, Any]], objective_payload["records"])
    }
    sample_payload = build_random_candidate_sampler(
        record_list,
        tasks,
        random_seed=random_seed,
        samples_per_task=samples_per_task,
    )
    evidence_records = _records_of_type(record_list, "EvidenceRecord")

    task_scorecards = []
    for task_record in cast(list[dict[str, Any]], sample_payload["records"]):
        task_id = str(task_record.get("task_id", ""))
        task = next((item for item in tasks if str(item.get("id", "")) == task_id), {})
        weights = weights_by_task.get(task_id, DEFAULT_OBJECTIVE_WEIGHTS)
        scorecards = [
            _score_candidate(
                candidate,
                task,
                strain_features,
                formulation_features,
                evidence_records,
                weights,
            )
            for candidate in cast(list[dict[str, Any]], task_record.get("candidate_designs", []))
        ]
        scorecards.sort(key=lambda item: (-float(item["overall_score"]), str(item["candidate_id"])))
        task_scorecards.append(
            {
                "task_id": task_id,
                "method": "deterministic_seed_scorecard",
                "candidate_count": len(scorecards),
                "scorecards": scorecards,
                "summary": {
                    "blocked_candidates": sum(
                        1 for card in scorecards if card["responsible_use_status"] == "blocked"
                    ),
                    "review_ready_candidates": sum(
                        1
                        for card in scorecards
                        if card["responsible_use_status"] == "promoted_for_review"
                    ),
                    "mean_overall_score": _mean(
                        [float(card["overall_score"]) for card in scorecards]
                    ),
                },
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "evaluator_version": "deterministic-seed-evaluator-v0.1",
        "random_seed": random_seed,
        "samples_per_task": samples_per_task,
        "task_count": len(task_scorecards),
        "objective_artifact_id": objective_payload["artifact_id"],
        "records": task_scorecards,
        "notes": [
            "Scorecards use seed proxy objectives with uncertainty intervals.",
            "Promotion remains research-review only and is blocked by biosafety flags.",
        ],
    }


def build_optimizer_only_baseline_report(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    random_seed: int = 1729,
    initial_samples_per_task: int = 6,
    proposal_batch_size: int = 3,
    artifact_id: str = "baseline:optimizer-only-seed-v0.1",
) -> dict[str, Any]:
    """Run a deterministic optimizer-only baseline over seed candidate features.

    The current MVP does not yet include a Bayesian surrogate model. This harness provides
    the no-reasoning search baseline contract by scoring a reproducible random design pool,
    retaining the best observed candidates, and emitting trace records that later Bayesian
    optimization can replace without changing report consumers.
    """

    candidate_pool = build_candidate_scorecards(
        records,
        tasks,
        random_seed=random_seed,
        samples_per_task=initial_samples_per_task,
    )
    optimizer_records = []
    for task_record in cast(list[dict[str, Any]], candidate_pool["records"]):
        scorecards = list(cast(list[dict[str, Any]], task_record.get("scorecards", [])))
        scorecards.sort(
            key=lambda item: (
                -float(item.get("overall_score", 0.0)),
                _mean_interval_width(
                    cast(Mapping[str, Sequence[float]], item.get("uncertainty_intervals", {}))
                ),
                str(item.get("candidate_id", "")),
            )
        )
        selected = scorecards[:proposal_batch_size]
        trace = [
            {
                "iteration": index + 1,
                "candidate_id": str(card.get("candidate_id", "")),
                "observed_score": float(card.get("overall_score", 0.0)),
                "mean_uncertainty_width": _mean_interval_width(
                    cast(Mapping[str, Sequence[float]], card.get("uncertainty_intervals", {}))
                ),
                "responsible_use_status": str(card.get("responsible_use_status", "")),
            }
            for index, card in enumerate(selected)
        ]
        optimizer_records.append(
            {
                "task_id": str(task_record.get("task_id", "")),
                "method": "deterministic_optimizer_only_seed_search",
                "search_strategy": "score_sorted_random_design_pool",
                "candidate_pool_size": len(scorecards),
                "proposal_batch_size": proposal_batch_size,
                "proposed_candidates": selected,
                "optimization_trace": trace,
                "summary": {
                    "best_score": max(
                        (float(card.get("overall_score", 0.0)) for card in scorecards),
                        default=0.0,
                    ),
                    "review_ready_candidates": sum(
                        1
                        for card in selected
                        if str(card.get("responsible_use_status", "")) == "promoted_for_review"
                    ),
                    "search_cost_candidates_scored": len(scorecards),
                },
                "limitations": [
                    "No language-model reasoning is used.",
                    "No surrogate model or acquisition function is implemented yet.",
                    "Seed proxy scores are workflow fixtures, not biological recommendations.",
                ],
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_version": "deterministic-optimizer-only-seed-v0.1",
        "random_seed": random_seed,
        "initial_samples_per_task": initial_samples_per_task,
        "proposal_batch_size": proposal_batch_size,
        "task_count": len(optimizer_records),
        "records": optimizer_records,
        "notes": [
            "Optimizer-only baseline is a no-reasoning search harness for seed regression tests.",
            (
                "It is intentionally replaceable by Bayesian optimization once "
                "candidate encoding lands."
            ),
        ],
    }


def build_optimizer_proposal_report(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    random_seed: int = 1729,
    initial_observations_per_task: int = 3,
    proposal_batch_size: int = 3,
    exploration_weight: float = 0.35,
    artifact_id: str = "optimizer:seed-surrogate-proposals-v0.1",
) -> dict[str, Any]:
    """Fit a deterministic seed surrogate and propose candidates by acquisition score."""

    record_list = list(records)
    feature_table = build_feature_table(record_list)
    strain_features = {
        str(feature.get("strain_id", "")): feature
        for feature in cast(list[dict[str, Any]], feature_table["strain_features"])
    }
    formulation_features = {
        str(feature.get("material_id", "")): feature
        for feature in cast(list[dict[str, Any]], feature_table["formulation_features"])
    }
    evidence_records = _records_of_type(record_list, "EvidenceRecord")
    objective_payload = build_evaluator_objectives(tasks)
    weights_by_task = {
        str(record.get("task_id", "")): cast(dict[str, float], record["objective_weights"])
        for record in cast(list[dict[str, Any]], objective_payload["records"])
    }
    encoding_payload = build_candidate_encoding_report(record_list, tasks)

    proposal_records = []
    for encoded_task in cast(list[dict[str, Any]], encoding_payload["records"]):
        task_id = str(encoded_task.get("task_id", ""))
        task = next((item for item in tasks if str(item.get("id", "")) == task_id), {})
        weights = weights_by_task.get(task_id, DEFAULT_OBJECTIVE_WEIGHTS)
        encoded_candidates = list(
            cast(list[dict[str, Any]], encoded_task.get("encoded_candidates", []))
        )
        scored_candidates = [
            _score_candidate(
                _encoded_candidate_design(candidate),
                task,
                strain_features,
                formulation_features,
                evidence_records,
                weights,
            )
            | {
                "continuous_vector": [
                    float(value)
                    for value in cast(Sequence[float], candidate.get("continuous_vector", []))
                ],
                "categorical_variables": candidate.get("categorical_variables", {}),
            }
            for candidate in encoded_candidates
        ]
        initial_observations = _initial_observation_batch(
            scored_candidates,
            random_seed=random_seed,
            task_id=task_id,
            initial_observations_per_task=initial_observations_per_task,
        )
        observed_ids = {
            str(candidate.get("candidate_id", "")) for candidate in initial_observations
        }
        proposal_pool = [
            candidate
            for candidate in scored_candidates
            if str(candidate.get("candidate_id", "")) not in observed_ids
        ]
        surrogate_predictions = [
            _surrogate_prediction(candidate, initial_observations)
            for candidate in proposal_pool
        ]
        proposed_candidates = sorted(
            [
                candidate
                | {
                    "surrogate_prediction": prediction,
                    "acquisition": _acquisition_score(
                        prediction,
                        exploration_weight=exploration_weight,
                    ),
                }
                for candidate, prediction in zip(
                    proposal_pool,
                    surrogate_predictions,
                    strict=True,
                )
            ],
            key=lambda item: (
                -float(cast(Mapping[str, Any], item["acquisition"])["value"]),
                str(item.get("candidate_id", "")),
            ),
        )[:proposal_batch_size]
        proposal_records.append(
            {
                "task_id": task_id,
                "method": "deterministic_seed_surrogate_ucb",
                "surrogate_model": {
                    "type": "inverse_distance_weighted_regression",
                    "training_observations": len(initial_observations),
                    "target": "overall_score",
                    "feature_schema": encoded_task.get("continuous_feature_schema", []),
                },
                "acquisition_function": {
                    "type": "upper_confidence_bound",
                    "exploration_weight": exploration_weight,
                    "formula": "predicted_mean + exploration_weight * predictive_uncertainty",
                },
                "candidate_pool_size": len(scored_candidates),
                "proposal_batch_size": proposal_batch_size,
                "initial_observations": [
                    _observation_summary(candidate) for candidate in initial_observations
                ],
                "proposed_candidates": proposed_candidates,
                "summary": {
                    "best_observed_score": max(
                        (
                            float(candidate.get("overall_score", 0.0))
                            for candidate in initial_observations
                        ),
                        default=0.0,
                    ),
                    "best_acquisition_value": max(
                        (
                            float(cast(Mapping[str, Any], candidate["acquisition"])["value"])
                            for candidate in proposed_candidates
                        ),
                        default=0.0,
                    ),
                    "unevaluated_candidate_count": len(proposal_pool),
                },
                "limitations": [
                    "Seed surrogate uses deterministic proxy scores, not assay labels.",
                    "Batch proposals require downstream evaluator feedback before claims.",
                ],
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "optimizer_version": "deterministic-seed-surrogate-ucb-v0.1",
        "random_seed": random_seed,
        "initial_observations_per_task": initial_observations_per_task,
        "proposal_batch_size": proposal_batch_size,
        "encoding_artifact_id": encoding_payload["artifact_id"],
        "objective_artifact_id": objective_payload["artifact_id"],
        "task_count": len(proposal_records),
        "records": proposal_records,
        "notes": [
            "This is the first model-backed optimizer scaffold over encoded seed candidates.",
            "It supports surrogate ranking, acquisition scoring, and batch proposal contracts.",
        ],
    }


def build_reasoning_only_baseline_report(
    records: Iterable[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    *,
    top_k: int = 3,
    artifact_id: str = "baseline:reasoning-only-seed-v0.1",
) -> dict[str, Any]:
    """Build a deterministic retrieval-grounded reasoning-only baseline.

    This is not an LLM agent. It preserves the artifact contract for the later
    reasoning-only ablation by using only evidence-linked heuristic rankings and an
    explicit rule trace, with no optimizer search or random candidate pool.
    """

    record_list = list(records)
    heuristic_report = build_heuristic_baseline_report(record_list, tasks)
    evidence_records = _records_of_type(record_list, "EvidenceRecord")
    literature_chunks = _records_of_type(record_list, "LiteratureChunk")
    records_by_task = []
    for heuristic_record in cast(list[dict[str, Any]], heuristic_report["records"]):
        task_id = str(heuristic_record.get("task_id", ""))
        task = next((item for item in tasks if str(item.get("id", "")) == task_id), {})
        evidence_ids = _task_evidence_ids(task, evidence_records)
        citation_ids = _task_literature_ids(task, literature_chunks)
        strain_hypotheses = [
            _reasoning_hypothesis_from_ranking(
                ranking,
                task,
                evidence_ids,
                citation_ids,
                hypothesis_type="strain",
                rank=index + 1,
            )
            for index, ranking in enumerate(
                cast(list[dict[str, Any]], heuristic_record.get("ranked_strains", []))[:top_k]
            )
        ]
        consortium_hypotheses = [
            _reasoning_hypothesis_from_ranking(
                ranking,
                task,
                evidence_ids,
                citation_ids,
                hypothesis_type="consortium",
                rank=index + 1,
            )
            for index, ranking in enumerate(
                cast(list[dict[str, Any]], heuristic_record.get("ranked_consortia", []))[:top_k]
            )
        ]
        formulation_hypotheses = [
            _reasoning_hypothesis_from_ranking(
                ranking,
                task,
                evidence_ids,
                citation_ids,
                hypothesis_type="formulation",
                rank=index + 1,
            )
            for index, ranking in enumerate(
                cast(list[dict[str, Any]], heuristic_record.get("ranked_formulations", []))[:top_k]
            )
        ]
        hypotheses = [*strain_hypotheses, *consortium_hypotheses, *formulation_hypotheses]
        records_by_task.append(
            {
                "task_id": task_id,
                "method": "deterministic_retrieval_grounded_reasoning_only",
                "hypothesis_count": len(hypotheses),
                "hypotheses": hypotheses,
                "reasoning_trace": [
                    (
                        "Select task-matching evidence and literature chunks by crop, "
                        "stress, and formulation terms."
                    ),
                    (
                        "Rank seed entities with deterministic evidence, relevance, "
                        "and guardrail components."
                    ),
                    "Emit cited research-review hypotheses without optimizer search.",
                ],
                "summary": {
                    "top_hypothesis_score": max(
                        (float(item.get("score", 0.0)) for item in hypotheses),
                        default=0.0,
                    ),
                    "citation_count": len(citation_ids),
                    "evidence_record_count": len(evidence_ids),
                },
                "limitations": [
                    "No candidate-space search is performed.",
                    "No language model reasoning is used in this local seed scaffold.",
                    "Hypotheses are not deployment recommendations.",
                ],
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_version": "deterministic-reasoning-only-seed-v0.1",
        "top_k": top_k,
        "task_count": len(records_by_task),
        "records": records_by_task,
        "notes": [
            (
                "Reasoning-only baseline uses evidence-linked heuristic rankings "
                "without optimizer search."
            ),
            "It is a deterministic ablation scaffold for future tool-using reasoning agents.",
        ],
    }


def build_baseline_benchmark_report(
    heuristic_report: Mapping[str, Any],
    random_candidate_report: Mapping[str, Any],
    scorecard_report: Mapping[str, Any],
    optimizer_report: Mapping[str, Any],
    reasoning_report: Mapping[str, Any] | None = None,
    *,
    review_threshold: float = 0.6,
    top_k: int = 3,
    artifact_id: str = "benchmark:seed-baseline-comparison-v0.1",
) -> dict[str, Any]:
    """Compare available seed baseline artifacts with deterministic proxy metrics."""

    random_scores_by_task = _scorecards_by_task(scorecard_report)
    optimizer_scores_by_task = {
        str(record.get("task_id", "")): cast(
            list[dict[str, Any]],
            record.get("proposed_candidates", []),
        )
        for record in cast(list[dict[str, Any]], optimizer_report.get("records", []))
    }
    heuristic_records_by_task = {
        str(record.get("task_id", "")): record
        for record in cast(list[dict[str, Any]], heuristic_report.get("records", []))
    }
    random_records_by_task = {
        str(record.get("task_id", "")): record
        for record in cast(list[dict[str, Any]], random_candidate_report.get("records", []))
    }
    reasoning_scores_by_task = (
        {
            str(record.get("task_id", "")): cast(
                list[dict[str, Any]],
                record.get("hypotheses", []),
            )
            for record in cast(list[dict[str, Any]], reasoning_report.get("records", []))
        }
        if reasoning_report
        else {}
    )

    task_ids = sorted(
        set(random_scores_by_task)
        | set(optimizer_scores_by_task)
        | set(heuristic_records_by_task)
        | set(random_records_by_task)
        | set(reasoning_scores_by_task)
    )
    records = []
    for task_id in task_ids:
        random_scores = random_scores_by_task.get(task_id, [])
        optimizer_scores = optimizer_scores_by_task.get(task_id, [])
        reasoning_scores = reasoning_scores_by_task.get(task_id, [])
        heuristic_record = heuristic_records_by_task.get(task_id, {})
        heuristic_scores = [
            *cast(list[dict[str, Any]], heuristic_record.get("ranked_strains", [])),
            *cast(list[dict[str, Any]], heuristic_record.get("ranked_consortia", [])),
            *cast(list[dict[str, Any]], heuristic_record.get("ranked_formulations", [])),
        ]
        records.append(
            {
                "task_id": task_id,
                "metrics": {
                    "random_valid_candidates": _candidate_metric_block(
                        random_scores,
                        threshold=review_threshold,
                        top_k=top_k,
                    ),
                    "heuristic_baseline": _ranked_metric_block(
                        heuristic_scores,
                        threshold=review_threshold,
                        top_k=top_k,
                    ),
                    "optimizer_only": _candidate_metric_block(
                        optimizer_scores,
                        threshold=review_threshold,
                        top_k=top_k,
                    ),
                    "reasoning_only": _ranked_metric_block(
                        reasoning_scores,
                        threshold=review_threshold,
                        top_k=top_k,
                    ),
                },
                "comparisons": {
                    "optimizer_top_k_lift_over_random": _top_k_lift(
                        optimizer_scores,
                        random_scores,
                        top_k=top_k,
                    ),
                    "reasoning_top_k_lift_over_heuristic": _ranked_top_k_lift(
                        reasoning_scores,
                        heuristic_scores,
                        top_k=top_k,
                    ),
                    "optimizer_search_cost": len(random_scores),
                    "reasoning_search_cost": len(reasoning_scores),
                    "heuristic_search_cost": len(heuristic_scores),
                },
                "failure_cases": _failure_cases(random_scores, optimizer_scores),
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "benchmark_version": "seed-baseline-comparison-v0.1",
        "review_threshold": review_threshold,
        "top_k": top_k,
        "task_count": len(records),
        "records": records,
        "source_artifacts": {
            "heuristic": str(heuristic_report.get("artifact_id", "")),
            "random_candidates": str(random_candidate_report.get("artifact_id", "")),
            "scorecards": str(scorecard_report.get("artifact_id", "")),
            "optimizer_only": str(optimizer_report.get("artifact_id", "")),
            "reasoning_only": str(reasoning_report.get("artifact_id", ""))
            if reasoning_report
            else "",
        },
        "notes": [
            "Metrics are computed from seed proxy scores for workflow validation.",
            "Hit rate counts candidates at or above the review threshold.",
            "Calibration is a placeholder based on uncertainty width until held-out labels exist.",
        ],
    }


def build_candidate_shortlist_export(
    scorecard_report: Mapping[str, Any],
    optimizer_report: Mapping[str, Any],
    *,
    top_k: int = 3,
    artifact_id: str = "shortlist:seed-candidates-v0.1",
) -> dict[str, Any]:
    """Export review-gated candidate shortlists from scored seed candidates."""

    scorecards_by_task = _scorecards_by_task(scorecard_report)
    optimizer_by_task = {
        str(record.get("task_id", "")): cast(
            list[dict[str, Any]],
            record.get("proposed_candidates", []),
        )
        for record in cast(list[dict[str, Any]], optimizer_report.get("records", []))
    }
    task_ids = sorted(set(scorecards_by_task) | set(optimizer_by_task))
    records = []
    for task_id in task_ids:
        candidates = optimizer_by_task.get(task_id) or scorecards_by_task.get(task_id, [])
        eligible = [
            candidate
            for candidate in candidates
            if str(candidate.get("responsible_use_status", "")) != "blocked"
        ]
        eligible.sort(
            key=lambda item: (
                -float(item.get("overall_score", 0.0)),
                str(item.get("candidate_id", "")),
            )
        )
        shortlist = [
            {
                "rank": index + 1,
                "candidate_id": str(candidate.get("candidate_id", "")),
                "strain_ids": list(_sequence_values(candidate.get("strain_ids", []))),
                "formulation_material_id": candidate.get("formulation_material_id"),
                "overall_score": float(candidate.get("overall_score", 0.0)),
                "objective_scores": dict(
                    cast(Mapping[str, float], candidate.get("objective_scores", {}))
                ),
                "uncertainty_intervals": dict(
                    cast(Mapping[str, Sequence[float]], candidate.get("uncertainty_intervals", {}))
                ),
                "evidence_ids": list(_sequence_values(candidate.get("evidence_ids", []))),
                "biosafety_flags": list(_sequence_values(candidate.get("biosafety_flags", []))),
                "manufacturability_flags": list(
                    _sequence_values(candidate.get("manufacturability_flags", []))
                ),
                "responsible_use_status": str(candidate.get("responsible_use_status", "")),
                "review_decision": "human_review_required",
                "proxy_to_target_risk_notes": list(
                    _sequence_values(candidate.get("proxy_to_target_risk_notes", []))
                ),
                "recommendation_rationale": str(
                    candidate.get("recommendation_rationale", "")
                ),
            }
            for index, candidate in enumerate(eligible[:top_k])
        ]
        records.append(
            {
                "task_id": task_id,
                "shortlist_count": len(shortlist),
                "shortlist": shortlist,
                "excluded_blocked_count": len(candidates) - len(eligible),
                "source_method": "optimizer_only" if task_id in optimizer_by_task else "scorecards",
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "shortlist_version": "seed-candidate-shortlist-v0.1",
        "top_k": top_k,
        "task_count": len(records),
        "records": records,
        "responsible_use_notice": (
            "Shortlisted candidates are research decision-support artifacts only and "
            "require domain, biosafety, regulatory, and experimental review."
        ),
        "source_artifacts": {
            "scorecards": str(scorecard_report.get("artifact_id", "")),
            "optimizer_only": str(optimizer_report.get("artifact_id", "")),
        },
    }


def _pilot_dataset(task: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    task_id = str(task.get("id", ""))
    crop = str(task.get("crop", "")).lower()
    stressors = _sequence_values(task.get("stressors", []))
    outputs = _sequence_values(task.get("outputs", []))
    formulation_context = _sequence_values(task.get("formulation_context", []))

    crop_record_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "Crop")
        if crop and crop in str(record.get("common_name", "")).lower()
    ]
    stress_context_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "StressContext")
        if _overlaps(stressors, _sequence_values(record.get("stressors", [])))
        or any(
            crop_id in crop_record_ids
            for crop_id in _sequence_values(record.get("crop_id", ""))
        )
    ]
    crop_stress_evidence_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "EvidenceRecord")
        if str(record.get("evidence_type", "")).lower() == "crop-stress"
        and _record_mentions(record, (crop, *stressors))
    ]
    formulation_evidence_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "EvidenceRecord")
        if str(record.get("evidence_type", "")).lower() == "formulation"
    ]
    literature_chunk_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "LiteratureChunk")
        if _record_mentions(record, (crop, *stressors, *formulation_context))
    ]
    candidate_strain_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "Strain")
        if _candidate_strain_for_task(record, stressors)
    ]
    candidate_material_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "FormulationMaterial")
        if "ranked_materials" in outputs
        or "ranked_formulations" in outputs
        or _record_mentions(record, formulation_context)
    ]
    matched_ids = {
        "crop_records": crop_record_ids,
        "stress_contexts": stress_context_ids,
        "crop_stress_evidence": crop_stress_evidence_ids,
        "formulation_evidence": formulation_evidence_ids,
        "literature_chunks": literature_chunk_ids,
        "candidate_strains": candidate_strain_ids,
        "candidate_materials": candidate_material_ids,
    }
    weak_evidence_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "EvidenceRecord")
        if str(record.get("id", "")) in {*crop_stress_evidence_ids, *formulation_evidence_ids}
        and float(record.get("confidence", 0.0)) < 0.55
    ]

    return {
        "task_id": task_id,
        "name": str(task.get("name", "")),
        "crop": crop,
        "stressors": list(stressors),
        "evaluation_tier": str(task.get("evaluation_tier", "")),
        "outputs": list(outputs),
        "matched_record_ids": matched_ids,
        "coverage_counts": {key: len(value) for key, value in matched_ids.items()},
        "weak_or_review_gated_evidence_ids": weak_evidence_ids,
        "readiness_status": "needs_review",
        "readiness_notes": [
            "Seed dataset slice is usable for CLI workflow validation.",
            "Evidence count and review status remain below benchmark-readiness thresholds.",
        ],
    }


def _baseline_for_task(
    task: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    strain_features: Sequence[Mapping[str, Any]],
    formulation_features: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    stressors = _sequence_values(task.get("stressors", []))
    crop = str(task.get("crop", "")).lower()
    outputs = _sequence_values(task.get("outputs", []))
    evidence_ids = [
        str(record.get("id", ""))
        for record in _records_of_type(records, "EvidenceRecord")
        if _record_mentions(record, (crop, *stressors))
    ]
    strain_rankings = [
        _score_strain_feature(feature, crop=crop, stressors=stressors, evidence_ids=evidence_ids)
        for feature in strain_features
    ]
    strain_rankings.sort(key=lambda item: (-float(item["score"]), str(item["strain_id"])))

    formulation_rankings: list[dict[str, Any]] = []
    if "ranked_materials" in outputs or "release_fit_scores" in outputs:
        formulation_rankings = [
            _score_formulation_feature(feature, task)
            for feature in formulation_features
        ]
        formulation_rankings.sort(
            key=lambda item: (-float(item["score"]), str(item["material_id"]))
        )

    return {
        "task_id": str(task.get("id", "")),
        "method": "deterministic_seed_heuristic",
        "ranked_strains": strain_rankings,
        "ranked_consortia": _rank_consortia(strain_rankings),
        "ranked_formulations": formulation_rankings,
        "evaluation_caveats": [
            "Scores combine local seed confidence, lexical feature flags, and simple penalties.",
            "Use only for baseline plumbing until reviewed evidence and objective weights land.",
        ],
    }


def _strain_feature(
    record: Mapping[str, Any],
    phenotypes: Sequence[Mapping[str, Any]],
    genomes: Sequence[Mapping[str, Any]],
    gene_features_by_genome: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    taxon = str(record.get("taxon", "")).strip()
    phenotype_tags = _sequence_values(record.get("phenotype_tags", []))
    phenotype_terms = tuple(
        sorted(
            {
                str(value).strip().lower()
                for phenotype in phenotypes
                for value in (phenotype.get("trait", ""), phenotype.get("value", ""))
                if str(value).strip()
            }
        )
    )
    feature_text = " ".join((*phenotype_tags, *phenotype_terms)).lower()
    genome_accessions = tuple(
        str(genome.get("accession", ""))
        for genome in genomes
        if str(genome.get("accession", "")).strip()
    )
    genome_ids = tuple(str(genome.get("id", "")) for genome in genomes)
    assembly_levels = tuple(
        str(genome.get("assembly_level", ""))
        for genome in genomes
        if str(genome.get("assembly_level", "")).strip()
    )
    gene_features = [
        feature
        for genome_id in genome_ids
        for feature in gene_features_by_genome.get(genome_id, [])
    ]
    gene_function_terms = tuple(
        sorted(
            {
                str(value).strip().lower()
                for feature in gene_features
                for value in (
                    feature.get("feature_name", ""),
                    feature.get("feature_type", ""),
                    feature.get("function_label", ""),
                )
                if str(value).strip()
            }
        )
    )
    gene_evidence_ids = tuple(
        sorted(
            {
                evidence_id
                for feature in gene_features
                for evidence_id in _sequence_values(feature.get("evidence_ids", []))
            }
        )
    )
    gene_text = " ".join(gene_function_terms)
    biosafety_flags = _sequence_values(record.get("biosafety_flags", []))
    return {
        "strain_id": str(record.get("id", "")),
        "taxon": taxon,
        "genus": taxon.split()[0] if taxon else "",
        "confidence": float(record.get("confidence", 0.0)),
        "phenotype_tags": list(phenotype_tags),
        "phenotype_terms": list(phenotype_terms),
        "taxonomic_feature": taxon.lower().replace(" ", "_"),
        "genome_accessions": list(genome_accessions),
        "genome_assembly_levels": list(assembly_levels),
        "genome_marker_embedding": _hashed_vector(
            (*genome_accessions, *assembly_levels, taxon) if genome_accessions else (),
            dimensions=8,
        ),
        "gene_function_summary_terms": list(gene_function_terms),
        "gene_feature_count": len(gene_features),
        "gene_evidence_ids": list(gene_evidence_ids),
        "stress_response_flag": int(
            any(term in feature_text for term in ("drought", "heat", "stress"))
            or any(term in gene_text for term in ("osmoprotection", "stress", "heat"))
        ),
        "root_growth_proxy_flag": int("root" in feature_text),
        "nutrient_use_proxy_flag": int(
            "nitrogen" in feature_text
            or "nutrient" in feature_text
            or "nitrogen" in gene_text
            or "nutrient" in gene_text
        ),
        "formulation_viability_proxy_flag": int(
            "spore" in feature_text or "viability" in feature_text
        ),
        "soil_persistence_proxy_flag": int(
            "persistence" in feature_text or "colonization" in gene_text
        ),
        "genome_feature_available": bool(genomes),
        "biosafety_flags": list(biosafety_flags),
        "biosafety_review_required": bool(biosafety_flags),
    }


def _formulation_feature(
    record: Mapping[str, Any],
    architectures: Sequence[Mapping[str, Any]],
    triggers_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    release_triggers = _sequence_values(record.get("release_triggers", []))
    architecture_types = tuple(
        str(architecture.get("architecture_type", ""))
        for architecture in architectures
        if str(architecture.get("architecture_type", "")).strip()
    )
    architecture_ids = tuple(str(architecture.get("id", "")) for architecture in architectures)
    trigger_ids = tuple(
        trigger_id
        for architecture in architectures
        for trigger_id in _sequence_values(architecture.get("release_trigger_ids", []))
    )
    trigger_types = tuple(
        str(triggers_by_id.get(trigger_id, {}).get("trigger_type", ""))
        for trigger_id in trigger_ids
        if str(triggers_by_id.get(trigger_id, {}).get("trigger_type", "")).strip()
    )
    viability_constraints = tuple(
        constraint
        for architecture in architectures
        for constraint in _sequence_values(architecture.get("viability_constraints", []))
    )
    text = " ".join(
        (
            str(record.get("material_class", "")),
            str(record.get("viability_notes", "")),
            *release_triggers,
            *architecture_types,
            *trigger_types,
            *viability_constraints,
        )
    ).lower()
    return {
        "material_id": str(record.get("id", "")),
        "material_class": str(record.get("material_class", "")),
        "confidence": float(record.get("confidence", 0.0)),
        "release_triggers": list(release_triggers),
        "architecture_ids": list(architecture_ids),
        "architecture_types": list(architecture_types),
        "trigger_types": list(trigger_types),
        "water_response_proxy_flag": int(
            any(term in text for term in ("moisture", "hydrogel", "hydration"))
        ),
        "temperature_process_risk_flag": int("temperature" in text or "storage" in text),
        "persistence_proxy_flag": int("persistence" in text or "porous" in text),
        "manufacturability_proxy_flag": int(
            any(term in text for term in ("coating", "matrix", "carrier", "alginate"))
        ),
        "viability_constraints": list(viability_constraints),
    }


def _crop_stress_feature(
    stress_record: Mapping[str, Any],
    crop_records: Sequence[Mapping[str, Any]],
    soil_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    crop_id = str(stress_record.get("crop_id", ""))
    crop_record = next(
        (record for record in crop_records if str(record.get("id", "")) == crop_id),
        {},
    )
    region_text = " ".join(
        (
            str(stress_record.get("region", "")),
            *(_sequence_values(crop_record.get("region_tags", [])) if crop_record else ()),
        )
    ).lower()
    matched_soil_records = [
        record
        for record in soil_records
        if _region_overlap(str(stress_record.get("region", "")), str(record.get("region", "")))
    ]
    temperature = stress_record.get("temperature_c")
    temperature_range = (
        [float(value) for value in temperature]
        if isinstance(temperature, Sequence) and not isinstance(temperature, str)
        else []
    )
    return {
        "stress_context_id": str(stress_record.get("id", "")),
        "crop_id": crop_id,
        "crop": str(crop_record.get("common_name", "")) if crop_record else "",
        "stressors": list(_sequence_values(stress_record.get("stressors", []))),
        "moisture_regime": str(stress_record.get("moisture_regime", "")),
        "temperature_c": temperature_range,
        "soil_context_ids": [str(record.get("id", "")) for record in matched_soil_records],
        "soil_texture_terms": sorted(
            {
                str(record.get("texture", "")).lower()
                for record in matched_soil_records
                if str(record.get("texture", "")).strip()
            }
        ),
        "soil_ph_range": _combined_range(
            record.get("ph_range") for record in matched_soil_records
        ),
        "soil_organic_matter_terms": sorted(
            {
                str(record.get("organic_matter_level", "")).lower()
                for record in matched_soil_records
                if str(record.get("organic_matter_level", "")).strip()
            }
        ),
        "soil_context_available": bool(matched_soil_records),
        "foliar_panel_relevance_score": _foliar_panel_score(region_text),
    }


def _consortium_pair_features(strain_features: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    eligible = [
        feature
        for feature in strain_features
        if not bool(feature.get("biosafety_review_required", False))
    ]
    for left, right in combinations(eligible, 2):
        left_tags = set(_sequence_values(left.get("phenotype_tags", [])))
        right_tags = set(_sequence_values(right.get("phenotype_tags", [])))
        feature_flags = (
            "stress_response_flag",
            "root_growth_proxy_flag",
            "nutrient_use_proxy_flag",
            "formulation_viability_proxy_flag",
            "soil_persistence_proxy_flag",
        )
        complementarity = sum(
            1
            for flag in feature_flags
            if int(left.get(flag, 0)) != int(right.get(flag, 0))
        )
        features.append(
            {
                "consortium_id": f"consortium:pair:{left['strain_id']}+{right['strain_id']}",
                "member_strain_ids": [left["strain_id"], right["strain_id"]],
                "genus_diversity": int(str(left.get("genus", "")) != str(right.get("genus", ""))),
                "shared_phenotype_tag_count": len(left_tags & right_tags),
                "functional_complementarity_score": round(complementarity / len(feature_flags), 3),
                "risk_flags": [],
            }
        )
    return sorted(features, key=lambda item: str(item["consortium_id"]))


def _score_strain_feature(
    feature: Mapping[str, Any],
    *,
    crop: str,
    stressors: Sequence[str],
    evidence_ids: Sequence[str],
) -> dict[str, Any]:
    text = " ".join(_sequence_values(feature.get("phenotype_tags", []))).lower()
    stress_relevance = max(
        _term_fraction(text, stressors),
        float(feature.get("stress_response_flag", 0)),
    )
    evidence_support = min(1.0, float(feature.get("confidence", 0.0)) + 0.08 * len(evidence_ids))
    crop_relevance = 0.5 if crop else 0.0
    biosafety_penalty = 0.45 if bool(feature.get("biosafety_review_required", False)) else 0.0
    score = (
        0.35 * evidence_support
        + 0.3 * stress_relevance
        + 0.15 * crop_relevance
        + 0.2 * float(feature.get("confidence", 0.0))
        - biosafety_penalty
    )
    return {
        "strain_id": str(feature.get("strain_id", "")),
        "taxon": str(feature.get("taxon", "")),
        "score": round(max(0.0, min(1.0, score)), 3),
        "components": {
            "evidence_support": round(evidence_support, 3),
            "stress_relevance": round(stress_relevance, 3),
            "crop_relevance": round(crop_relevance, 3),
            "biosafety_penalty": round(biosafety_penalty, 3),
        },
        "evidence_ids": list(evidence_ids),
        "biosafety_flags": list(_sequence_values(feature.get("biosafety_flags", []))),
    }


def _score_formulation_feature(
    feature: Mapping[str, Any],
    task: Mapping[str, Any],
) -> dict[str, Any]:
    context_terms = (
        *_sequence_values(task.get("formulation_context", [])),
        *_sequence_values(task.get("stressors", [])),
    )
    text = " ".join(
        (
            str(feature.get("material_class", "")),
            *_sequence_values(feature.get("release_triggers", [])),
            *_sequence_values(feature.get("architecture_types", [])),
            *_sequence_values(feature.get("trigger_types", [])),
            *_sequence_values(feature.get("viability_constraints", [])),
        )
    ).lower()
    release_fit = max(
        _term_fraction(text, context_terms),
        float(feature.get("water_response_proxy_flag", 0)),
    )
    viability_risk = min(
        1.0,
        0.25 * len(_sequence_values(feature.get("viability_constraints", [])))
        + 0.25 * float(feature.get("temperature_process_risk_flag", 0)),
    )
    manufacturability = float(feature.get("manufacturability_proxy_flag", 0))
    score = (
        0.45 * release_fit
        + 0.25 * manufacturability
        + 0.2 * float(feature.get("confidence", 0.0))
        + 0.1 * float(feature.get("persistence_proxy_flag", 0))
        - 0.2 * viability_risk
    )
    return {
        "material_id": str(feature.get("material_id", "")),
        "material_class": str(feature.get("material_class", "")),
        "score": round(max(0.0, min(1.0, score)), 3),
        "components": {
            "release_profile_match": round(release_fit, 3),
            "manufacturability_proxy": round(manufacturability, 3),
            "viability_risk": round(viability_risk, 3),
        },
        "viability_constraints": list(_sequence_values(feature.get("viability_constraints", []))),
    }


def _rank_consortia(strain_rankings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    eligible = [
        ranking
        for ranking in strain_rankings
        if not _sequence_values(ranking.get("biosafety_flags", []))
    ][:4]
    ranked: list[dict[str, Any]] = []
    for left, right in combinations(eligible, 2):
        left_genus = str(left.get("taxon", "")).split()[0] if str(left.get("taxon", "")) else ""
        right_genus = str(right.get("taxon", "")).split()[0] if str(right.get("taxon", "")) else ""
        diversity_bonus = 0.05 if left_genus and left_genus != right_genus else 0.0
        ranked.append(
            {
                "member_strain_ids": [left["strain_id"], right["strain_id"]],
                "score": round(
                    min(1.0, (float(left["score"]) + float(right["score"])) / 2 + diversity_bonus),
                    3,
                ),
                "assembly_rule": "top_ranked_biosafety_clear_pair_with_genus_diversity_bonus",
            }
        )
    ranked.sort(key=lambda item: (-float(item["score"]), str(item["member_strain_ids"])))
    return ranked


def _task_evidence_ids(
    task: Mapping[str, Any],
    evidence_records: Sequence[Mapping[str, Any]],
) -> list[str]:
    crop = str(task.get("crop", "")).lower()
    terms = (
        crop,
        *_sequence_values(task.get("stressors", [])),
        *_sequence_values(task.get("formulation_context", [])),
    )
    return [
        str(record.get("id", ""))
        for record in evidence_records
        if _record_mentions(record, terms)
    ]


def _task_literature_ids(
    task: Mapping[str, Any],
    literature_chunks: Sequence[Mapping[str, Any]],
) -> list[str]:
    crop = str(task.get("crop", "")).lower()
    terms = (
        crop,
        *_sequence_values(task.get("stressors", [])),
        *_sequence_values(task.get("formulation_context", [])),
    )
    return [
        str(record.get("id", ""))
        for record in literature_chunks
        if _record_mentions(record, terms)
    ]


def _reasoning_hypothesis_from_ranking(
    ranking: Mapping[str, Any],
    task: Mapping[str, Any],
    evidence_ids: Sequence[str],
    citation_ids: Sequence[str],
    *,
    hypothesis_type: str,
    rank: int,
) -> dict[str, Any]:
    subject_id = (
        str(ranking.get("strain_id", ""))
        or str(ranking.get("material_id", ""))
        or "+".join(_sequence_values(ranking.get("member_strain_ids", [])))
    )
    score = float(ranking.get("score", 0.0))
    components = cast(Mapping[str, Any], ranking.get("components", {}))
    rationale_terms = [
        key
        for key, value in components.items()
        if isinstance(value, (float, int)) and float(value) > 0
    ]
    if not rationale_terms and hypothesis_type == "consortium":
        rationale_terms = ["ranked_member_scores", "genus_diversity_bonus"]
    return {
        "rank": rank,
        "hypothesis_id": f"hypothesis:{task.get('id', '')}:{hypothesis_type}:{rank:03d}",
        "hypothesis_type": hypothesis_type,
        "subject_id": subject_id,
        "score": round(score, 3),
        "task_context": {
            "crop": str(task.get("crop", "")),
            "stressors": list(_sequence_values(task.get("stressors", []))),
            "formulation_context": list(_sequence_values(task.get("formulation_context", []))),
        },
        "supporting_evidence_ids": list(evidence_ids[:5]),
        "supporting_citation_ids": list(citation_ids[:5]),
        "rationale_factors": rationale_terms,
        "responsible_use_status": "research_review_only",
        "claim": (
            f"{subject_id} is a seed reasoning-only candidate for "
            f"{task.get('name', task.get('id', 'the configured task'))}."
        ),
    }


def _search_space_for_task(
    task: Mapping[str, Any],
    strain_features: Sequence[Mapping[str, Any]],
    formulation_features: Sequence[Mapping[str, Any]],
    stress_features: Sequence[Mapping[str, Any]],
    *,
    max_consortium_size: int,
) -> dict[str, Any]:
    task_id = str(task.get("id", ""))
    crop = str(task.get("crop", ""))
    stressors = _sequence_values(task.get("stressors", []))
    outputs = set(_sequence_values(task.get("outputs", [])))
    needs_formulation = bool(
        "ranked_materials" in outputs
        or "release_fit_scores" in outputs
        or "candidate_scorecards" in outputs
    )
    eligible_strains = [
        feature
        for feature in strain_features
        if not bool(feature.get("biosafety_review_required", False))
        and _strain_matches_task_context(feature, stressors)
    ]
    rejected_strains = [
        {
            "strain_id": str(feature.get("strain_id", "")),
            "reason": "biosafety_review_required"
            if bool(feature.get("biosafety_review_required", False))
            else "no_task_context_match",
        }
        for feature in strain_features
        if feature not in eligible_strains
    ]
    eligible_formulations = [
        feature
        for feature in formulation_features
        if (not needs_formulation or _formulation_matches_task_context(feature, task))
        and _sequence_values(feature.get("architecture_ids", []))
    ]
    rejected_formulations = [
        {
            "material_id": str(feature.get("material_id", "")),
            "reason": "missing_architecture"
            if not _sequence_values(feature.get("architecture_ids", []))
            else "no_task_context_match",
        }
        for feature in formulation_features
        if feature not in eligible_formulations
    ]
    stress_context_id = _matching_stress_context_id(stress_features, crop, stressors)
    consortium_sizes = [
        size for size in range(1, max(1, max_consortium_size) + 1) if size <= len(eligible_strains)
    ]
    combinations_count = _combination_count(len(eligible_strains), consortium_sizes)
    formulation_multiplier = len(eligible_formulations) if needs_formulation else 1
    feasible_candidate_count = combinations_count * formulation_multiplier
    constraint_summary = {
        "biosafety_exclusion": "exclude strain features with biosafety_review_required",
        "task_context_filter": (
            "retain strains and formulations with stress or release-context overlap"
        ),
        "formulation_requirement": needs_formulation,
        "architecture_requirement": "formulation candidates must link to at least one architecture",
        "max_consortium_size": max_consortium_size,
    }
    return {
        "task_id": task_id,
        "crop": crop,
        "stressors": list(stressors),
        "stress_context_ids": [stress_context_id] if stress_context_id else [],
        "consortium_sizes": consortium_sizes,
        "strain_candidates": [
            {
                "strain_id": str(feature.get("strain_id", "")),
                "taxon": str(feature.get("taxon", "")),
                "genus": str(feature.get("genus", "")),
                "continuous_feature_keys": [
                    "confidence",
                    "stress_response_flag",
                    "root_growth_proxy_flag",
                    "nutrient_use_proxy_flag",
                    "formulation_viability_proxy_flag",
                    "soil_persistence_proxy_flag",
                ],
            }
            for feature in eligible_strains
        ],
        "formulation_candidates": [
            {
                "material_id": str(feature.get("material_id", "")),
                "material_class": str(feature.get("material_class", "")),
                "architecture_ids": list(_sequence_values(feature.get("architecture_ids", []))),
                "release_triggers": list(_sequence_values(feature.get("release_triggers", []))),
            }
            for feature in eligible_formulations
        ],
        "release_profile_targets": [_target_release_profile(task) or "not_applicable"],
        "constraint_summary": constraint_summary,
        "invalid_combination_filters": [
            "drop biosafety-flagged strains before candidate enumeration",
            "drop formulations without linked architectures",
            "require formulation candidates for formulation-oriented outputs",
            "require at least one crop-stress context or configured stressor label",
        ],
        "rejected_candidates": {
            "strains": rejected_strains,
            "formulations": rejected_formulations,
        },
        "feasible_candidate_count": feasible_candidate_count,
    }


def _encoding_for_task(
    task_record: Mapping[str, Any],
    strain_by_id: Mapping[str, Mapping[str, Any]],
    formulation_by_id: Mapping[str, Mapping[str, Any]],
    stress_by_id: Mapping[str, Mapping[str, Any]],
    *,
    max_consortium_size: int,
) -> dict[str, Any]:
    strain_ids = [
        str(candidate.get("strain_id", ""))
        for candidate in cast(list[dict[str, Any]], task_record.get("strain_candidates", []))
    ]
    formulation_ids = [
        str(candidate.get("material_id", ""))
        for candidate in cast(
            list[dict[str, Any]],
            task_record.get("formulation_candidates", []),
        )
    ]
    stress_context_ids = _sequence_values(task_record.get("stress_context_ids", []))
    stress_context = stress_by_id.get(stress_context_ids[0], {}) if stress_context_ids else {}
    consortium_sizes = [
        int(size)
        for size in cast(list[int], task_record.get("consortium_sizes", []))
        if int(size) > 0
    ]
    candidate_rows: list[dict[str, Any]] = []
    for size in consortium_sizes:
        for strain_group in combinations(strain_ids, size):
            material_choices = formulation_ids or [""]
            for material_id in material_choices:
                formulation = formulation_by_id.get(material_id, {})
                candidate_id = (
                    f"candidate:encoded:{task_record.get('task_id', '')}:"
                    f"{_stable_token((*strain_group, material_id or 'no-material'))}"
                )
                candidate_rows.append(
                    {
                        "candidate_id": candidate_id,
                        "strain_ids": list(strain_group),
                        "formulation_material_id": material_id or None,
                        "continuous_vector": _candidate_continuous_vector(
                            [strain_by_id[strain_id] for strain_id in strain_group],
                            formulation,
                            stress_context,
                            max_consortium_size=max_consortium_size,
                        ),
                        "categorical_variables": {
                            "strain_ids": list(strain_group),
                            "genera": sorted(
                                {
                                    str(strain_by_id[strain_id].get("genus", ""))
                                    for strain_id in strain_group
                                }
                            ),
                            "material_class": str(formulation.get("material_class", "none")),
                            "architecture_ids": list(
                                _sequence_values(formulation.get("architecture_ids", []))
                            ),
                            "stress_context_id": stress_context_ids[0]
                            if stress_context_ids
                            else "",
                        },
                        "conditional_constraints_satisfied": _encoded_constraints_satisfied(
                            strain_group,
                            formulation,
                            requires_formulation=bool(formulation_ids),
                        ),
                    }
                )

    return {
        "task_id": str(task_record.get("task_id", "")),
        "continuous_feature_schema": [
            "mean_strain_confidence",
            "mean_stress_response",
            "mean_nutrient_use",
            "mean_soil_persistence",
            "consortium_size_norm",
            "genus_diversity",
            "formulation_confidence",
            "release_fit_proxy",
            "viability_proxy",
            "manufacturability_proxy",
            "foliar_panel_relevance",
        ],
        "categorical_feature_schema": [
            "strain_ids",
            "genera",
            "material_class",
            "architecture_ids",
            "stress_context_id",
        ],
        "encoded_candidate_count": len(candidate_rows),
        "encoded_candidates": candidate_rows,
        "encoding_notes": [
            "Continuous vectors are normalized seed proxy descriptors.",
            "Categorical variables are preserved for later one-hot or kernel encoding.",
        ],
    }


def _candidate_continuous_vector(
    strains: Sequence[Mapping[str, Any]],
    formulation: Mapping[str, Any],
    stress_context: Mapping[str, Any],
    *,
    max_consortium_size: int,
) -> list[float]:
    genera = {str(strain.get("genus", "")) for strain in strains if str(strain.get("genus", ""))}
    viability_risk = min(
        1.0,
        0.25 * len(_sequence_values(formulation.get("viability_constraints", [])))
        + 0.25 * float(formulation.get("temperature_process_risk_flag", 0.0)),
    )
    vector = [
        _mean([float(strain.get("confidence", 0.0)) for strain in strains]),
        _mean([float(strain.get("stress_response_flag", 0.0)) for strain in strains]),
        _mean([float(strain.get("nutrient_use_proxy_flag", 0.0)) for strain in strains]),
        _mean([float(strain.get("soil_persistence_proxy_flag", 0.0)) for strain in strains]),
        round(len(strains) / max(1, max_consortium_size), 3),
        round(len(genera) / max(1, len(strains)), 3),
        float(formulation.get("confidence", 0.0)) if formulation else 0.0,
        max(
            float(formulation.get("water_response_proxy_flag", 0.0)),
            float(formulation.get("persistence_proxy_flag", 0.0)),
        )
        if formulation
        else 0.0,
        round(1.0 - viability_risk, 3) if formulation else 0.0,
        float(formulation.get("manufacturability_proxy_flag", 0.0)) if formulation else 0.0,
        float(stress_context.get("foliar_panel_relevance_score", 0.0)),
    ]
    return [round(max(0.0, min(1.0, value)), 3) for value in vector]


def _encoded_constraints_satisfied(
    strain_ids: Sequence[str],
    formulation: Mapping[str, Any],
    *,
    requires_formulation: bool,
) -> dict[str, bool]:
    return {
        "has_strain": bool(strain_ids),
        "consortium_size_supported": len(strain_ids) in {1, 2},
        "has_required_formulation": bool(formulation) if requires_formulation else True,
        "formulation_has_architecture": bool(
            _sequence_values(formulation.get("architecture_ids", []))
        )
        if formulation
        else not requires_formulation,
    }


def _strain_matches_task_context(
    feature: Mapping[str, Any],
    stressors: Sequence[str],
) -> bool:
    text = " ".join(
        (
            *_sequence_values(feature.get("phenotype_tags", [])),
            *_sequence_values(feature.get("phenotype_terms", [])),
            *_sequence_values(feature.get("gene_function_summary_terms", [])),
        )
    ).lower()
    return (
        _term_fraction(text, stressors) > 0
        or bool(feature.get("stress_response_flag", False))
        or bool(feature.get("root_growth_proxy_flag", False))
        or bool(feature.get("nutrient_use_proxy_flag", False))
    )


def _formulation_matches_task_context(
    feature: Mapping[str, Any],
    task: Mapping[str, Any],
) -> bool:
    terms = (
        *_sequence_values(task.get("formulation_context", [])),
        *_sequence_values(task.get("stressors", [])),
    )
    text = " ".join(
        (
            str(feature.get("material_class", "")),
            *_sequence_values(feature.get("release_triggers", [])),
            *_sequence_values(feature.get("architecture_types", [])),
            *_sequence_values(feature.get("trigger_types", [])),
        )
    ).lower()
    return _term_fraction(text, terms) > 0 or bool(feature.get("water_response_proxy_flag", False))


def _combination_count(candidate_count: int, sizes: Sequence[int]) -> int:
    total = 0
    for size in sizes:
        if size == 1:
            total += candidate_count
        elif size == 2:
            total += candidate_count * (candidate_count - 1) // 2
    return total


def _sample_candidates_for_task(
    task: Mapping[str, Any],
    strain_features: Sequence[Mapping[str, Any]],
    formulation_features: Sequence[Mapping[str, Any]],
    stress_features: Sequence[Mapping[str, Any]],
    rng: Random,
    *,
    samples_per_task: int,
) -> dict[str, Any]:
    task_id = str(task.get("id", ""))
    crop = str(task.get("crop", ""))
    stressors = _sequence_values(task.get("stressors", []))
    outputs = set(_sequence_values(task.get("outputs", [])))
    needs_formulation = bool(
        formulation_features
        and (
            "ranked_materials" in outputs
            or "release_fit_scores" in outputs
            or "candidate_scorecards" in outputs
        )
    )
    candidates: list[dict[str, Any]] = []
    if not strain_features:
        return {
            "task_id": task_id,
            "candidate_designs": candidates,
            "validity_notes": ["No biosafety-clear strain features were available."],
        }

    stress_context_id = _matching_stress_context_id(stress_features, crop, stressors)
    max_members = min(2, len(strain_features))
    for index in range(samples_per_task):
        member_count = 2 if max_members >= 2 and rng.random() >= 0.35 else 1
        members = rng.sample(list(strain_features), member_count)
        strain_ids = sorted(str(member.get("strain_id", "")) for member in members)
        ratios = {strain_id: round(1.0 / len(strain_ids), 3) for strain_id in strain_ids}
        formulation = rng.choice(list(formulation_features)) if needs_formulation else {}
        material_id = str(formulation.get("material_id", "")) if formulation else None
        architecture_ids = _sequence_values(formulation.get("architecture_ids", []))
        candidate_id = (
            f"candidate:random:{task_id}:{index + 1:03d}:"
            f"{_stable_token((*strain_ids, material_id or 'no-material'))}"
        )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "source": "deterministic_random_valid_sampler",
                "strain_ids": strain_ids,
                "consortium_ratios": ratios,
                "crop": crop,
                "stress_context": stress_context_id or "+".join(stressors),
                "formulation_material_id": material_id,
                "encapsulation_architecture": architecture_ids[0] if architecture_ids else None,
                "target_release_profile": _target_release_profile(task),
                "evaluation_tier": str(task.get("evaluation_tier", "in_silico")),
                "responsible_use_status": "research_only",
                "biosafety_flags": [],
                "validity_checks": {
                    "has_strain": bool(strain_ids),
                    "biosafety_clear": True,
                    "has_crop": bool(crop),
                    "has_stress_context": bool(stress_context_id or stressors),
                    "has_required_formulation": bool(material_id) if needs_formulation else True,
                },
            }
        )
    return {
        "task_id": task_id,
        "candidate_designs": candidates,
        "validity_notes": [
            "Candidates are sampled from local seed feature records.",
            "Equal consortium ratios are placeholders for schema-valid baseline candidates.",
        ],
    }


def _score_candidate(
    candidate: Mapping[str, Any],
    task: Mapping[str, Any],
    strain_features: Mapping[str, Mapping[str, Any]],
    formulation_features: Mapping[str, Mapping[str, Any]],
    evidence_records: Sequence[Mapping[str, Any]],
    weights: Mapping[str, float],
) -> dict[str, Any]:
    strains = [
        strain_features[strain_id]
        for strain_id in _sequence_values(candidate.get("strain_ids", []))
        if strain_id in strain_features
    ]
    formulation = formulation_features.get(str(candidate.get("formulation_material_id", "")), {})
    crop = str(task.get("crop", "")).lower()
    stressors = _sequence_values(task.get("stressors", []))
    evidence_ids = [
        str(record.get("id", ""))
        for record in evidence_records
        if _record_mentions(record, (crop, *stressors))
    ]
    biosafety_flags = tuple(
        flag
        for strain in strains
        for flag in _sequence_values(strain.get("biosafety_flags", []))
    )
    viability_risk = min(
        1.0,
        0.25 * len(_sequence_values(formulation.get("viability_constraints", [])))
        + 0.25 * float(formulation.get("temperature_process_risk_flag", 0.0)),
    )
    objective_scores = {
        "stress_tolerance_proxy": _mean(
            [
                max(
                    float(strain.get("stress_response_flag", 0.0)),
                    _term_fraction(
                        " ".join(_sequence_values(strain.get("phenotype_tags", []))).lower(),
                        stressors,
                    ),
                )
                for strain in strains
            ]
        ),
        "nutrient_use_efficiency_proxy": _mean(
            [float(strain.get("nutrient_use_proxy_flag", 0.0)) for strain in strains]
        ),
        "persistence_proxy": max(
            _mean([float(strain.get("soil_persistence_proxy_flag", 0.0)) for strain in strains]),
            float(formulation.get("persistence_proxy_flag", 0.0)),
        ),
        "encapsulation_viability_proxy": round(1.0 - viability_risk, 3) if formulation else 0.35,
        "release_profile_fit": _candidate_release_fit(formulation, task),
        "manufacturability_proxy": float(formulation.get("manufacturability_proxy_flag", 0.0)),
        "evidence_support": min(
            1.0,
            _mean([float(strain.get("confidence", 0.0)) for strain in strains])
            + float(formulation.get("confidence", 0.0)) * 0.2
            + 0.04 * len(evidence_ids),
        ),
    }
    objective_scores = {
        key: round(max(0.0, min(1.0, value)), 3) for key, value in objective_scores.items()
    }
    overall_score = round(
        sum(objective_scores[name] * float(weights.get(name, 0.0)) for name in objective_scores),
        3,
    )
    uncertainty_width = _uncertainty_width(len(evidence_ids), len(strains), bool(formulation))
    responsible_status = _responsible_status(
        overall_score=overall_score,
        evidence_support=objective_scores["evidence_support"],
        biosafety_flags=biosafety_flags,
    )
    manufacturability_flags = tuple(
        "review_temperature_processing"
        for _ in [None]
        if bool(formulation.get("temperature_process_risk_flag", False))
    )

    return {
        "candidate_id": str(candidate.get("candidate_id", "")),
        "strain_ids": list(_sequence_values(candidate.get("strain_ids", []))),
        "formulation_material_id": candidate.get("formulation_material_id"),
        "overall_score": overall_score,
        "objective_scores": objective_scores,
        "uncertainty_intervals": {
            name: [
                round(max(0.0, score - uncertainty_width), 3),
                round(min(1.0, score + uncertainty_width), 3),
            ]
            for name, score in objective_scores.items()
        },
        "evidence_ids": evidence_ids,
        "biosafety_flags": list(biosafety_flags),
        "manufacturability_flags": list(manufacturability_flags),
        "responsible_use_status": responsible_status,
        "proxy_to_target_risk_notes": [
            "Seed proxy score; no greenhouse or field validation is implied.",
            "Small reviewed-evidence coverage keeps uncertainty intentionally broad.",
        ],
        "recommendation_rationale": (
            "Candidate is retained for research review only."
            if responsible_status != "blocked"
            else "Candidate is blocked because biosafety flags require review."
        ),
    }


def _encoded_candidate_design(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": str(candidate.get("candidate_id", "")),
        "strain_ids": list(_sequence_values(candidate.get("strain_ids", []))),
        "formulation_material_id": candidate.get("formulation_material_id"),
    }


def _initial_observation_batch(
    candidates: Sequence[Mapping[str, Any]],
    *,
    random_seed: int,
    task_id: str,
    initial_observations_per_task: int,
) -> list[dict[str, Any]]:
    shuffled = [dict(candidate) for candidate in candidates]
    Random(f"{random_seed}:{task_id}:initial-observations").shuffle(shuffled)
    return sorted(
        shuffled[: max(0, min(initial_observations_per_task, len(shuffled)))],
        key=lambda item: str(item.get("candidate_id", "")),
    )


def _surrogate_prediction(
    candidate: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not observations:
        return {
            "predicted_mean": 0.0,
            "predictive_uncertainty": 1.0,
            "nearest_observation_distance": 1.0,
        }
    candidate_vector = [
        float(value) for value in cast(Sequence[float], candidate.get("continuous_vector", []))
    ]
    weighted_scores = []
    weights = []
    distances = []
    for observation in observations:
        observation_vector = [
            float(value)
            for value in cast(Sequence[float], observation.get("continuous_vector", []))
        ]
        distance = _euclidean_distance(candidate_vector, observation_vector)
        weight = 1.0 / (distance + 0.05)
        distances.append(distance)
        weights.append(weight)
        weighted_scores.append(weight * float(observation.get("overall_score", 0.0)))

    weight_total = sum(weights)
    predicted_mean = sum(weighted_scores) / weight_total if weight_total else 0.0
    nearest_distance = min(distances, default=1.0)
    observed_spread = max(
        (float(observation.get("overall_score", 0.0)) for observation in observations),
        default=0.0,
    ) - min(
        (float(observation.get("overall_score", 0.0)) for observation in observations),
        default=0.0,
    )
    uncertainty = min(1.0, 0.18 + nearest_distance * 0.45 + observed_spread * 0.3)
    return {
        "predicted_mean": round(max(0.0, min(1.0, predicted_mean)), 3),
        "predictive_uncertainty": round(max(0.0, min(1.0, uncertainty)), 3),
        "nearest_observation_distance": round(nearest_distance, 3),
    }


def _acquisition_score(
    prediction: Mapping[str, Any],
    *,
    exploration_weight: float,
) -> dict[str, Any]:
    value = float(prediction.get("predicted_mean", 0.0)) + exploration_weight * float(
        prediction.get("predictive_uncertainty", 0.0)
    )
    return {
        "name": "upper_confidence_bound",
        "value": round(max(0.0, min(1.5, value)), 3),
    }


def _observation_summary(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": str(candidate.get("candidate_id", "")),
        "strain_ids": list(_sequence_values(candidate.get("strain_ids", []))),
        "formulation_material_id": candidate.get("formulation_material_id"),
        "observed_score": float(candidate.get("overall_score", 0.0)),
        "responsible_use_status": str(candidate.get("responsible_use_status", "")),
    }


def _euclidean_distance(left: Sequence[float], right: Sequence[float]) -> float:
    width = max(len(left), len(right))
    if width == 0:
        return 0.0
    total = 0.0
    for index in range(width):
        left_value = left[index] if index < len(left) else 0.0
        right_value = right[index] if index < len(right) else 0.0
        total += (left_value - right_value) ** 2
    return float(round(total**0.5, 6))


def _normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in weights.values())
    if total <= 0:
        return {key: 0.0 for key in weights}
    return {key: round(max(0.0, value) / total, 3) for key, value in weights.items()}


def _matching_stress_context_id(
    stress_features: Sequence[Mapping[str, Any]],
    crop: str,
    stressors: Sequence[str],
) -> str:
    for feature in stress_features:
        if crop and crop.lower() in str(feature.get("crop", "")).lower():
            return str(feature.get("stress_context_id", ""))
        if _overlaps(stressors, _sequence_values(feature.get("stressors", []))):
            return str(feature.get("stress_context_id", ""))
    return ""


def _target_release_profile(task: Mapping[str, Any]) -> str | None:
    context = _sequence_values(task.get("formulation_context", []))
    if not context:
        return None
    if any("controlled" in item for item in context):
        return "controlled moisture-responsive release"
    return "task-matched formulation release"


def _candidate_release_fit(
    formulation: Mapping[str, Any],
    task: Mapping[str, Any],
) -> float:
    if not formulation:
        return 0.25
    text = " ".join(
        (
            str(formulation.get("material_class", "")),
            *_sequence_values(formulation.get("release_triggers", [])),
            *_sequence_values(formulation.get("architecture_types", [])),
            *_sequence_values(formulation.get("trigger_types", [])),
        )
    ).lower()
    context_terms = (
        *_sequence_values(task.get("formulation_context", [])),
        *_sequence_values(task.get("stressors", [])),
    )
    return max(
        _term_fraction(text, context_terms),
        float(formulation.get("water_response_proxy_flag", 0)),
    )


def _uncertainty_width(evidence_count: int, strain_count: int, has_formulation: bool) -> float:
    width = 0.32
    width -= min(0.12, 0.03 * evidence_count)
    width -= 0.03 if strain_count > 1 else 0.0
    width -= 0.03 if has_formulation else 0.0
    return round(max(0.12, width), 3)


def _responsible_status(
    *,
    overall_score: float,
    evidence_support: float,
    biosafety_flags: Sequence[str],
) -> str:
    if biosafety_flags:
        return "blocked"
    if overall_score >= 0.6 and evidence_support >= 0.35:
        return "promoted_for_review"
    return "needs_review"


def _scorecards_by_task(scorecard_report: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        str(record.get("task_id", "")): cast(list[dict[str, Any]], record.get("scorecards", []))
        for record in cast(list[dict[str, Any]], scorecard_report.get("records", []))
    }


def _candidate_metric_block(
    scorecards: Sequence[Mapping[str, Any]],
    *,
    threshold: float,
    top_k: int,
) -> dict[str, Any]:
    sorted_cards = sorted(
        scorecards,
        key=lambda item: (
            -float(item.get("overall_score", 0.0)),
            str(item.get("candidate_id", "")),
        ),
    )
    top_cards = sorted_cards[:top_k]
    return {
        "candidate_count": len(sorted_cards),
        "hit_rate": _hit_rate(sorted_cards, threshold=threshold),
        "top_k_enrichment": _hit_rate(top_cards, threshold=threshold),
        "mean_score": _mean([float(card.get("overall_score", 0.0)) for card in sorted_cards]),
        "mean_top_k_score": _mean([float(card.get("overall_score", 0.0)) for card in top_cards]),
        "search_cost": len(sorted_cards),
        "calibration_proxy": _calibration_proxy(sorted_cards),
    }


def _ranked_metric_block(
    rankings: Sequence[Mapping[str, Any]],
    *,
    threshold: float,
    top_k: int,
) -> dict[str, Any]:
    sorted_rankings = sorted(
        rankings,
        key=lambda item: (-float(item.get("score", 0.0)), str(item)),
    )
    top_rankings = sorted_rankings[:top_k]
    return {
        "candidate_count": len(sorted_rankings),
        "hit_rate": _hit_rate(sorted_rankings, threshold=threshold, score_key="score"),
        "top_k_enrichment": _hit_rate(top_rankings, threshold=threshold, score_key="score"),
        "mean_score": _mean([float(item.get("score", 0.0)) for item in sorted_rankings]),
        "mean_top_k_score": _mean([float(item.get("score", 0.0)) for item in top_rankings]),
        "search_cost": len(sorted_rankings),
        "calibration_proxy": "not_applicable_without_uncertainty_intervals",
    }


def _hit_rate(
    items: Sequence[Mapping[str, Any]],
    *,
    threshold: float,
    score_key: str = "overall_score",
) -> float:
    if not items:
        return 0.0
    return round(
        sum(1 for item in items if float(item.get(score_key, 0.0)) >= threshold) / len(items),
        3,
    )


def _top_k_lift(
    candidate_scores: Sequence[Mapping[str, Any]],
    baseline_scores: Sequence[Mapping[str, Any]],
    *,
    top_k: int,
) -> float:
    candidate_top = sorted(
        candidate_scores,
        key=lambda item: (
            -float(item.get("overall_score", 0.0)),
            str(item.get("candidate_id", "")),
        ),
    )[:top_k]
    baseline_top = sorted(
        baseline_scores,
        key=lambda item: (
            -float(item.get("overall_score", 0.0)),
            str(item.get("candidate_id", "")),
        ),
    )[:top_k]
    baseline_mean = _mean([float(item.get("overall_score", 0.0)) for item in baseline_top])
    candidate_mean = _mean([float(item.get("overall_score", 0.0)) for item in candidate_top])
    return round(candidate_mean - baseline_mean, 3)


def _ranked_top_k_lift(
    candidate_scores: Sequence[Mapping[str, Any]],
    baseline_scores: Sequence[Mapping[str, Any]],
    *,
    top_k: int,
) -> float:
    candidate_top = sorted(
        candidate_scores,
        key=lambda item: (-float(item.get("score", 0.0)), str(item)),
    )[:top_k]
    baseline_top = sorted(
        baseline_scores,
        key=lambda item: (-float(item.get("score", 0.0)), str(item)),
    )[:top_k]
    candidate_mean = _mean([float(item.get("score", 0.0)) for item in candidate_top])
    baseline_mean = _mean([float(item.get("score", 0.0)) for item in baseline_top])
    return round(candidate_mean - baseline_mean, 3)


def _calibration_proxy(scorecards: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    interval_widths = [
        _mean_interval_width(
            cast(Mapping[str, Sequence[float]], card.get("uncertainty_intervals", {}))
        )
        for card in scorecards
    ]
    return {
        "mean_uncertainty_width": _mean(interval_widths),
        "narrow_interval_fraction": _hit_rate(
            [{"overall_score": 1.0 - width} for width in interval_widths],
            threshold=0.75,
        ),
    }


def _mean_interval_width(intervals: Mapping[str, Sequence[float]]) -> float:
    widths = [
        max(0.0, float(values[1]) - float(values[0]))
        for values in intervals.values()
        if len(values) >= 2
    ]
    return _mean(widths)


def _failure_cases(
    random_scorecards: Sequence[Mapping[str, Any]],
    optimizer_scorecards: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    failures = []
    if not random_scorecards:
        failures.append(
            {
                "case": "empty_random_baseline",
                "detail": "No random valid candidates were available for this task.",
            }
        )
    if not optimizer_scorecards:
        failures.append(
            {
                "case": "empty_optimizer_baseline",
                "detail": "No optimizer-only proposals were available for this task.",
            }
        )
    if optimizer_scorecards and all(
        str(card.get("responsible_use_status", "")) != "promoted_for_review"
        for card in optimizer_scorecards
    ):
        failures.append(
            {
                "case": "no_review_ready_optimizer_candidates",
                "detail": "Optimizer-only proposals did not clear seed review thresholds.",
            }
        )
    return failures


def _stable_token(values: Sequence[str | None]) -> str:
    raw = "|".join(value or "" for value in values)
    return sha256(raw.encode("utf-8")).hexdigest()[:8]


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _hashed_vector(parts: Sequence[str], *, dimensions: int) -> list[float]:
    text = "|".join(part for part in parts if str(part).strip())
    if not text:
        return [0.0 for _ in range(dimensions)]
    digest = sha256(text.encode("utf-8")).digest()
    return [round(digest[index] / 255, 6) for index in range(dimensions)]


def _region_overlap(left: str, right: str) -> bool:
    left_terms = {term for term in left.lower().replace("-", " ").split() if len(term) > 2}
    right_terms = {term for term in right.lower().replace("-", " ").split() if len(term) > 2}
    return bool(left_terms and right_terms and left_terms & right_terms)


def _combined_range(values: Iterable[Any]) -> list[float]:
    lows: list[float] = []
    highs: list[float] = []
    for value in values:
        if isinstance(value, Sequence) and not isinstance(value, str) and len(value) == 2:
            lows.append(float(value[0]))
            highs.append(float(value[1]))
    if not lows or not highs:
        return []
    return [round(min(lows), 3), round(max(highs), 3)]


def _records_of_type(
    records: Sequence[Mapping[str, Any]],
    record_type: str,
) -> list[Mapping[str, Any]]:
    return [record for record in records if str(record.get("record_type", "")) == record_type]


def _candidate_strain_for_task(record: Mapping[str, Any], stressors: Sequence[str]) -> bool:
    if _sequence_values(record.get("biosafety_flags", [])):
        return False
    text = " ".join(_sequence_values(record.get("phenotype_tags", []))).lower()
    return _term_fraction(text, stressors) > 0 or "stress" in text or "root" in text


def _record_mentions(record: Mapping[str, Any], terms: Sequence[str]) -> bool:
    text = " ".join(
        str(value)
        for key, value in record.items()
        if key not in {"created_at", "version"} and not isinstance(value, dict)
    ).lower()
    return any(term and term.lower().replace("_", " ") in text for term in terms)


def _sequence_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def _overlaps(left: Sequence[str], right: Sequence[str]) -> bool:
    normalized_left = {value.lower() for value in left}
    normalized_right = {value.lower() for value in right}
    return bool(normalized_left & normalized_right)


def _term_fraction(text: str, terms: Sequence[str]) -> float:
    normalized_terms = [term.lower().replace("_", " ") for term in terms if term]
    if not normalized_terms:
        return 0.0
    return sum(1 for term in normalized_terms if term in text) / len(normalized_terms)


def _foliar_panel_score(region_text: str) -> float:
    score = 0.0
    if "leaf" in region_text or "foliar" in region_text:
        score += 0.45
    if "contained" in region_text or "laboratory" in region_text:
        score += 0.35
    if "hydrophobic" in region_text or "waxy" in region_text or "moderate" in region_text:
        score += 0.2
    return round(min(1.0, score), 3)
