"""Deterministic retrieval, extraction, and graph helpers for starter foliar evidence."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, cast

_TOKEN = re.compile(r"[a-z0-9][a-z0-9-]*")
_STOPWORDS = {
    "a",
    "and",
    "any",
    "as",
    "before",
    "by",
    "can",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "or",
    "so",
    "that",
    "the",
    "this",
    "to",
    "with",
}

_CROP_TERMS = {
    "brassica": "waxy brassica leaf",
    "cabbage": "waxy brassica leaf",
    "rice": "rice",
    "tomato": "tomato",
    "waxy brassica": "waxy brassica leaf",
}
_STRESS_TERMS = {
    "contact-line motion": "contact-line motion",
    "controlled release": "controlled release",
    "leaf retention": "leaf retention",
    "rainfastness": "rainfastness",
    "wash-off": "wash-off",
}
_MATERIAL_TERMS = {
    "cloaked droplet": "cloaked droplet",
    "emulsion": "emulsion",
    "liquid-liquid encapsulation": "liquid-liquid encapsulation",
    "polymer": "polymer additive",
}
_ORGANISM_TERMS = {
    "bacillus subtilis": "Bacillus subtilis",
    "bacillus velezensis": "Bacillus velezensis",
    "bacillus-like": "Bacillus-like payload",
}
_PHENOTYPE_TERMS = {
    "coverage": "spray coverage proxy",
    "evaporation": "evaporation proxy",
    "retained fluorescent intensity": "retained intensity proxy",
    "retained intensity": "retained intensity proxy",
    "sprayability": "sprayability proxy",
    "viability": "viability signal",
    "wash-off": "wash-off proxy",
}
_ARCHITECTURE_TERMS = {
    "cloaked droplet": "cloaked droplet",
    "liquid-liquid encapsulation": "liquid-liquid encapsulation",
    "polymer-emulsion": "polymer-emulsion film",
}
_RELEASE_TERMS = {
    "diffusion": "diffusion",
    "evaporation": "evaporation",
    "leaf deposition": "leaf deposition",
    "release": "release",
    "simulated rainfall": "simulated rainfall",
}
_REVIEW_TERMS = {
    "placeholder",
    "review",
    "reviewed",
    "scaffolding",
    "validation",
}
_EMBEDDING_DIMENSIONS = 32
_EXTRACTION_FIELDS = (
    "crops",
    "stressors",
    "organisms",
    "reported_phenotypes",
    "materials",
    "encapsulation_architectures",
    "release_or_viability_signals",
    "assay_or_fidelity",
)


def tokenize_text(text: str) -> tuple[str, ...]:
    """Return normalized lexical tokens for local retrieval scaffolding."""

    return tuple(
        token
        for token in _TOKEN.findall(text.lower())
        if token not in _STOPWORDS and len(token) > 1
    )


def build_retrieval_index(
    records: Iterable[Mapping[str, Any]],
    *,
    artifact_id: str = "retrieval:index:seed-literature",
) -> dict[str, Any]:
    """Build a tiny deterministic lexical and hashed-vector index from chunks."""

    chunks = [record for record in records if record.get("record_type") == "LiteratureChunk"]
    document_frequency: Counter[str] = Counter()
    token_counts_by_chunk: dict[str, Counter[str]] = {}

    for chunk in chunks:
        chunk_id = str(chunk.get("id", ""))
        token_counts = Counter(tokenize_text(str(chunk.get("text", ""))))
        token_counts_by_chunk[chunk_id] = token_counts
        document_frequency.update(token_counts)

    chunk_count = len(chunks)
    index_records: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_id = str(chunk.get("id", ""))
        token_counts = token_counts_by_chunk[chunk_id]
        total_tokens = sum(token_counts.values()) or 1
        token_weights = {
            token: round(
                (count / total_tokens)
                * math.log((1 + chunk_count) / (1 + document_frequency[token]))
                + 1.0,
                6,
            )
            for token, count in sorted(token_counts.items())
        }
        metadata = dict(cast(Mapping[str, Any], chunk.get("metadata", {})))
        metadata_text = " ".join(str(value) for value in metadata.values())
        index_records.append(
            {
                "chunk_id": chunk_id,
                "document_id": str(chunk.get("document_id", "")),
                "citation": str(chunk.get("citation", "")),
                "text": str(chunk.get("text", "")),
                "metadata": metadata,
                "confidence": float(chunk.get("confidence", 0.0)),
                "license": str(chunk.get("license", "")),
                "provenance": str(chunk.get("provenance", "")),
                "token_weights": token_weights,
                "embedding": _hashed_embedding(f"{chunk.get('text', '')} {metadata_text}"),
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "index_version": "lexical-hashed-embedding-v0.2",
        "embedding_model": "deterministic-token-hash-v0.1",
        "embedding_dimensions": _EMBEDDING_DIMENSIONS,
        "chunk_count": chunk_count,
        "vocabulary": sorted(document_frequency),
        "records": index_records,
        "notes": [
            "Deterministic lexical plus hashed-vector index for local MVP scaffolding.",
            "Replace hashed vectors with model embeddings before benchmark claims.",
        ],
    }


def query_retrieval_index(
    index: Mapping[str, Any],
    *,
    query: str,
    top_k: int = 5,
    crop: str | None = None,
    stress: str | None = None,
    material: str | None = None,
    evidence_type: str | None = None,
) -> dict[str, Any]:
    """Score indexed chunks with lexical overlap and metadata filters."""

    query_tokens = Counter(tokenize_text(query))
    query_embedding = _hashed_embedding(query)
    filters = {
        "crop": crop,
        "stress": stress,
        "material": material,
        "evidence_type": evidence_type,
    }
    results: list[dict[str, Any]] = []
    for record in _index_records(index):
        text = str(record.get("text", ""))
        metadata = cast(Mapping[str, Any], record.get("metadata", {}))
        searchable = f"{text} {' '.join(str(value) for value in metadata.values())}".lower()
        if not _matches_filters(searchable, metadata, filters):
            continue

        token_weights = cast(Mapping[str, Any], record.get("token_weights", {}))
        lexical_score = sum(
            float(token_weights.get(token, 0.0)) * count
            for token, count in query_tokens.items()
        )
        embedding_score = _cosine_similarity(
            query_embedding,
            _float_sequence(record.get("embedding", [])),
        )
        score = lexical_score + embedding_score
        if lexical_score <= 0 and embedding_score <= 0:
            continue
        results.append(
            {
                "chunk_id": str(record.get("chunk_id", "")),
                "document_id": str(record.get("document_id", "")),
                "score": round(score, 6),
                "lexical_score": round(lexical_score, 6),
                "embedding_score": round(embedding_score, 6),
                "citation": str(record.get("citation", "")),
                "evidence_type": str(metadata.get("evidence_type", "")),
                "title": str(metadata.get("title", "")),
                "matched_terms": sorted(token for token in query_tokens if token in token_weights),
                "text": text,
            }
        )

    results.sort(key=lambda result: (-float(result["score"]), str(result["chunk_id"])))
    return {
        "status": "ok",
        "artifact_id": "retrieval:query-results",
        "query": query,
        "filters": {key: value for key, value in filters.items() if value},
        "result_count": min(len(results), top_k),
        "results": results[:top_k],
    }


def build_evidence_review_queue(
    extraction_records: Iterable[Mapping[str, Any]],
    *,
    min_confidence: float = 0.5,
    artifact_id: str = "review:seed-evidence-queue",
) -> dict[str, Any]:
    """Build a human-review queue for weak or flagged structured extractions."""

    queue_records: list[dict[str, Any]] = []
    for extraction in extraction_records:
        reasons = list(_sequence_values(extraction.get("review_flags", [])))
        confidence = float(extraction.get("confidence", 0.0))
        if confidence < min_confidence:
            reasons.append("low_confidence")
        if not str(extraction.get("citation", "")).strip():
            reasons.append("missing_citation")
        if not any(_sequence_values(extraction.get(field, [])) for field in _EXTRACTION_FIELDS):
            reasons.append("no_structured_fields")
        if not reasons:
            continue

        chunk_id = str(extraction.get("chunk_id", ""))
        queue_records.append(
            {
                "review_id": f"review:{_slug(chunk_id)}",
                "chunk_id": chunk_id,
                "document_id": str(extraction.get("document_id", "")),
                "citation": str(extraction.get("citation", "")),
                "confidence": confidence,
                "evidence_type": str(extraction.get("evidence_type", "")),
                "review_reasons": sorted(set(reasons)),
                "extracted_fields": {
                    field: list(_sequence_values(extraction.get(field, [])))
                    for field in _EXTRACTION_FIELDS
                },
                "manual_correction_template": {
                    "chunk_id": chunk_id,
                    "accepted": None,
                    "corrected_fields": {
                        field: list(_sequence_values(extraction.get(field, [])))
                        for field in _EXTRACTION_FIELDS
                    },
                    "reviewer": "",
                    "reviewed_at": "",
                    "review_notes": "",
                },
            }
        )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "min_confidence": min_confidence,
        "queue_count": len(queue_records),
        "records": sorted(queue_records, key=lambda record: str(record["review_id"])),
        "manual_correction_format": {
            "chunk_id": "LiteratureChunk ID under review.",
            "accepted": "Boolean review decision; false requires corrected_fields or notes.",
            "corrected_fields": {field: "List of accepted values." for field in _EXTRACTION_FIELDS},
            "reviewer": "Reviewer name or stable reviewer ID.",
            "reviewed_at": "ISO-8601 review timestamp.",
            "review_notes": "Short rationale for corrections or rejection.",
        },
    }


def evaluate_structured_extractions(
    extraction_records: Iterable[Mapping[str, Any]],
    gold_records: Iterable[Mapping[str, Any]],
    *,
    artifact_id: str = "evaluation:structured-extractions",
) -> dict[str, Any]:
    """Compare structured extraction records with gold examples by field."""

    extractions_by_chunk = {
        str(record.get("chunk_id", "")): record
        for record in extraction_records
        if str(record.get("chunk_id", "")).strip()
    }
    gold_by_chunk = {
        str(record.get("chunk_id", "")): record
        for record in gold_records
        if str(record.get("chunk_id", "")).strip()
    }

    field_counts: dict[str, Counter[str]] = {field: Counter() for field in _EXTRACTION_FIELDS}
    for chunk_id, gold in gold_by_chunk.items():
        extraction = extractions_by_chunk.get(chunk_id, {})
        for field in _EXTRACTION_FIELDS:
            expected = set(_sequence_values(gold.get(field, [])))
            observed = set(_sequence_values(extraction.get(field, [])))
            field_counts[field]["true_positive"] += len(expected & observed)
            field_counts[field]["false_positive"] += len(observed - expected)
            field_counts[field]["false_negative"] += len(expected - observed)

    per_field = {
        field: _precision_recall_summary(counts)
        for field, counts in sorted(field_counts.items())
    }
    total_counts: Counter[str] = Counter()
    for counts in field_counts.values():
        total_counts.update(counts)

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "gold_example_count": len(gold_by_chunk),
        "extraction_count": len(extractions_by_chunk),
        "matched_example_count": len(set(gold_by_chunk) & set(extractions_by_chunk)),
        "missing_gold_chunk_ids": sorted(set(gold_by_chunk) - set(extractions_by_chunk)),
        "extra_extraction_chunk_ids": sorted(set(extractions_by_chunk) - set(gold_by_chunk)),
        "micro_average": _precision_recall_summary(total_counts),
        "per_field": per_field,
    }


def validate_knowledge_graph(
    graph: Mapping[str, Any],
    *,
    artifact_id: str = "validation:seed-knowledge-graph",
) -> dict[str, Any]:
    """Validate graph export shape and identify dangling node references."""

    nodes = [
        cast(Mapping[str, Any], node)
        for node in graph.get("nodes", [])
        if isinstance(node, dict)
    ]
    edges = [
        cast(Mapping[str, Any], edge)
        for edge in graph.get("edges", [])
        if isinstance(edge, dict)
    ]
    node_ids = {str(node.get("id", "")) for node in nodes if str(node.get("id", "")).strip()}
    duplicate_node_ids = sorted(
        node_id for node_id, count in Counter(str(node.get("id", "")) for node in nodes).items()
        if node_id and count > 1
    )
    dangling_edges = [
        {
            "source": str(edge.get("source", "")),
            "target": str(edge.get("target", "")),
            "relation": str(edge.get("relation", "")),
        }
        for edge in edges
        if (
            str(edge.get("source", "")) not in node_ids
            or str(edge.get("target", "")) not in node_ids
        )
    ]
    relation_counts = Counter(str(edge.get("relation", "")) for edge in edges)
    node_type_counts = Counter(str(node.get("type", "")) for node in nodes)
    warnings = []
    if dangling_edges:
        warnings.append("dangling_edges")
    if duplicate_node_ids:
        warnings.append("duplicate_node_ids")
    if not relation_counts:
        warnings.append("empty_edge_set")

    return {
        "status": "ok" if not warnings else "needs_review",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "graph_artifact_id": str(graph.get("artifact_id", "")),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "duplicate_node_ids": duplicate_node_ids,
        "dangling_edge_count": len(dangling_edges),
        "dangling_edges": dangling_edges,
        "warnings": warnings,
    }


def extract_structured_evidence(
    records: Iterable[Mapping[str, Any]],
    *,
    artifact_id: str = "extraction:seed-evidence",
) -> dict[str, Any]:
    """Extract seed claim fields with conservative vocabulary matching."""

    record_list = list(records)
    organism_terms = _organism_terms(record_list)
    phenotype_terms = _phenotype_terms(record_list)
    extractions: list[dict[str, Any]] = []
    for record in record_list:
        if record.get("record_type") != "LiteratureChunk":
            continue
        text = str(record.get("text", ""))
        normalized_text = text.lower()
        metadata = cast(Mapping[str, Any], record.get("metadata", {}))
        extracted = {
            "chunk_id": str(record.get("id", "")),
            "document_id": str(record.get("document_id", "")),
            "citation": str(record.get("citation", "")),
            "confidence": _extraction_confidence(
                normalized_text,
                float(record.get("confidence", 0.0)),
            ),
            "crops": _matched_values(normalized_text, _CROP_TERMS),
            "stressors": _matched_values(normalized_text, _STRESS_TERMS),
            "organisms": _matched_values(normalized_text, organism_terms),
            "reported_phenotypes": _matched_values(normalized_text, phenotype_terms),
            "materials": _matched_values(normalized_text, _MATERIAL_TERMS),
            "encapsulation_architectures": _matched_values(normalized_text, _ARCHITECTURE_TERMS),
            "release_or_viability_signals": _matched_values(normalized_text, _RELEASE_TERMS),
            "assay_or_fidelity": tuple(
                value
                for value in ("literature_seed", "workflow_validation")
                if value.replace("_", " ") in normalized_text or "seed" in normalized_text
            ),
            "review_flags": tuple(
                sorted(term for term in _REVIEW_TERMS if term in normalized_text)
            ),
            "evidence_type": str(metadata.get("evidence_type", "")),
        }
        extractions.append(_json_ready(extracted))

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "extraction_version": "lexical-rules-v0.1",
        "record_count": len(extractions),
        "records": extractions,
        "notes": [
            "Rule-based seed extraction is intentionally conservative.",
            "Records with review_flags should enter human review before benchmark use.",
        ],
    }


def build_knowledge_graph(
    records: Iterable[Mapping[str, Any]],
    *,
    extraction_records: Iterable[Mapping[str, Any]] = (),
    artifact_id: str = "graph:seed-evidence-v0.1",
) -> dict[str, Any]:
    """Build a file-backed graph export from processed seed records and extractions."""

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    record_list = list(records)

    for record in record_list:
        record_id = str(record.get("id", ""))
        record_type = str(record.get("record_type", ""))
        if not record_id or not record_type:
            continue
        nodes[record_id] = {
            "id": record_id,
            "type": record_type,
            "label": _record_label(record),
            "source": str(record.get("source", "")),
            "confidence": float(record.get("confidence", 0.0)),
            "provenance": str(record.get("provenance", "")),
        }
        if record_type == "EvidenceRecord":
            for claim in _sequence_values(record.get("claims", [])):
                claim_id = f"claim:{_slug(claim)}"
                nodes.setdefault(
                    claim_id,
                    {
                        "id": claim_id,
                        "type": "Claim",
                        "label": claim,
                        "source": str(record.get("source", "")),
                        "confidence": float(record.get("confidence", 0.0)),
                        "provenance": record_id,
                    },
                )
        _record_edges(record, edges)

    for extraction in extraction_records:
        chunk_id = str(extraction.get("chunk_id", ""))
        if not chunk_id:
            continue
        for field_name, node_type, relation in (
            ("crops", "CropMention", "tested_in"),
            ("stressors", "StressMention", "tested_in"),
            ("organisms", "OrganismMention", "supports"),
            ("reported_phenotypes", "PhenotypeMention", "supports"),
            ("materials", "MaterialMention", "encapsulated_by"),
            ("encapsulation_architectures", "ArchitectureMention", "encapsulated_by"),
            ("release_or_viability_signals", "ReleaseSignal", "released_under"),
        ):
            for value in _sequence_values(extraction.get(field_name, [])):
                mention_id = f"mention:{node_type.lower()}:{_slug(value)}"
                nodes.setdefault(
                    mention_id,
                    {
                        "id": mention_id,
                        "type": node_type,
                        "label": value,
                        "source": "structured-extraction",
                        "confidence": float(extraction.get("confidence", 0.0)),
                        "provenance": chunk_id,
                    },
                )
                _add_edge(
                    edges,
                    chunk_id,
                    mention_id,
                    relation,
                    evidence_id=chunk_id,
                    confidence=float(extraction.get("confidence", 0.0)),
                )

    return {
        "status": "ok",
        "artifact_id": artifact_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "graph_version": "json-node-edge-v0.1",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": sorted(nodes.values(), key=lambda node: str(node["id"])),
        "edges": sorted(
            edges.values(),
            key=lambda edge: (str(edge["source"]), str(edge["target"])),
        ),
    }


def _index_records(index: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records = index.get("records", [])
    if not isinstance(records, list):
        return []
    return [cast(Mapping[str, Any], record) for record in records if isinstance(record, dict)]


def _hashed_embedding(text: str, *, dimensions: int = _EMBEDDING_DIMENSIONS) -> list[float]:
    counts = Counter(tokenize_text(text))
    vector = [0.0] * dimensions
    for token, count in counts.items():
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % dimensions
        sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
        vector[index] += sign * count
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )


def _float_sequence(value: Any) -> tuple[float, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    return tuple(float(item) for item in value)


def _precision_recall_summary(counts: Counter[str]) -> dict[str, Any]:
    true_positive = counts["true_positive"]
    false_positive = counts["false_positive"]
    false_negative = counts["false_negative"]
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0.0
    recall = true_positive / recall_denominator if recall_denominator else 0.0
    f1_denominator = precision + recall
    f1 = 2 * precision * recall / f1_denominator if f1_denominator else 0.0
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }


def _matches_filters(
    searchable: str,
    metadata: Mapping[str, Any],
    filters: Mapping[str, str | None],
) -> bool:
    evidence_type = filters.get("evidence_type")
    if evidence_type and evidence_type.lower() != str(metadata.get("evidence_type", "")).lower():
        return False
    for key in ("crop", "stress", "material"):
        value = filters.get(key)
        if value and value.lower() not in searchable:
            return False
    return True


def _matched_values(text: str, vocabulary: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(sorted({value for term, value in vocabulary.items() if term in text}))


def _organism_terms(records: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    terms = dict(_ORGANISM_TERMS)
    for record in records:
        if record.get("record_type") == "Taxon":
            name = str(record.get("scientific_name", "")).strip()
        elif record.get("record_type") == "Strain":
            name = str(record.get("taxon", "")).strip()
        else:
            continue
        if name:
            terms[name.lower()] = name
            genus = name.split()[0]
            if genus:
                terms.setdefault(genus.lower(), genus)
    return terms


def _phenotype_terms(records: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    terms = dict(_PHENOTYPE_TERMS)
    for record in records:
        if record.get("record_type") != "Phenotype":
            continue
        for field_name in ("trait", "value"):
            value = str(record.get(field_name, "")).strip()
            if value:
                terms[value.lower()] = value
    return terms


def _extraction_confidence(text: str, source_confidence: float) -> float:
    review_penalty = 0.15 if any(term in text for term in _REVIEW_TERMS) else 0.0
    return round(max(0.0, min(1.0, source_confidence - review_penalty)), 3)


def _json_ready(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: list(value) if isinstance(value, tuple) else value
        for key, value in record.items()
    }


def _record_label(record: Mapping[str, Any]) -> str:
    for field_name in (
        "title",
        "scientific_name",
        "common_name",
        "strain_label",
        "material_class",
        "architecture_type",
        "trigger_type",
        "citation",
        "id",
    ):
        value = str(record.get(field_name, "")).strip()
        if value:
            return value
    return str(record.get("id", ""))


def _record_edges(
    record: Mapping[str, Any],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    record_id = str(record.get("id", ""))
    record_type = str(record.get("record_type", ""))
    confidence = float(record.get("confidence", 0.0))
    if record_type == "Strain":
        taxon_label = str(record.get("taxon", "")).strip()
        if taxon_label:
            _add_edge(
                edges,
                record_id,
                f"taxon:{_slug(taxon_label)}",
                "has_taxon",
                confidence=confidence,
            )
    elif record_type == "Phenotype":
        _add_edge(
            edges,
            record_id,
            str(record.get("subject_id", "")),
            "supports",
            evidence_id=_first_value(record.get("evidence_ids", [])),
            confidence=confidence,
        )
        assay_id = str(record.get("assay_id", "")).strip()
        if assay_id:
            _add_edge(edges, record_id, assay_id, "tested_in", confidence=confidence)
    elif record_type == "Assay":
        for target_key in ("crop_id", "stress_context_id"):
            target = str(record.get(target_key, "")).strip()
            if target:
                _add_edge(edges, record_id, target, "tested_in", confidence=confidence)
    elif record_type == "AssayEndpointSchema":
        assay_id = str(record.get("assay_id", "")).strip()
        if assay_id:
            _add_edge(edges, record_id, assay_id, "defines_endpoint_for", confidence=confidence)
        for objective in _sequence_values(record.get("objective_links", [])):
            _add_edge(
                edges,
                record_id,
                f"objective:{_slug(objective)}",
                "measures",
                confidence=confidence,
            )
    elif record_type == "EncapsulationArchitecture":
        for material_id in _sequence_values(record.get("material_ids", [])):
            _add_edge(edges, record_id, material_id, "encapsulated_by", confidence=confidence)
        for trigger_id in _sequence_values(record.get("release_trigger_ids", [])):
            _add_edge(edges, record_id, trigger_id, "released_under", confidence=confidence)
    elif record_type == "LiteratureChunk":
        _add_edge(
            edges,
            record_id,
            str(record.get("document_id", "")),
            "chunk_of",
            evidence_id=record_id,
            confidence=confidence,
        )
    elif record_type == "EvidenceRecord":
        for claim in _sequence_values(record.get("claims", [])):
            claim_id = f"claim:{_slug(claim)}"
            _add_edge(
                edges,
                record_id,
                claim_id,
                "supports",
                evidence_id=record_id,
                confidence=confidence,
            )


def _add_edge(
    edges: dict[tuple[str, str, str], dict[str, Any]],
    source: str,
    target: str,
    relation: str,
    *,
    evidence_id: str = "",
    confidence: float = 0.0,
) -> None:
    if not source or not target:
        return
    key = (source, target, relation)
    edges[key] = {
        "source": source,
        "target": target,
        "relation": relation,
        "evidence_id": evidence_id,
        "confidence": confidence,
    }


def _sequence_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def _first_value(value: Any) -> str:
    values = _sequence_values(value)
    return values[0] if values else ""


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def merge_processed_records(artifacts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Collect records lists from processed JSON artifacts."""

    merged: list[dict[str, Any]] = []
    for artifact in artifacts:
        records = artifact.get("records", [])
        if isinstance(records, list):
            merged.extend(cast(list[dict[str, Any]], records))
    return merged
