from __future__ import annotations

from pathlib import Path

import pytest

from journal_factory.llm.chunking import ContextOverflowError, Paragraph, chunk_paragraphs
from journal_factory.llm.client import StaticJSONClient
from journal_factory.llm.contracts import (
    IDContractError,
    SchemaValidationError,
    load_skill_schema,
    stable_text_sha256,
    validate_model_payload,
    validate_model_text,
)
from journal_factory.llm.host_runner import SmokeConfig, run_synthetic_smoke
from journal_factory.llm.public_handoff import validate_public_handoff
from journal_factory.llm.synthetic import expected_payload, malformed_payload_cases, synthetic_paragraphs


def test_skill_schema_is_versioned_in_repo() -> None:
    schema = load_skill_schema()
    assert schema["properties"]["schema_version"]["const"] == "paragraph-classification.v1"


def test_invalid_json_fails_closed() -> None:
    with pytest.raises(SchemaValidationError):
        validate_model_text("prose before {not-json}", expected_ids=["P001"])


def test_missing_extra_duplicate_reordered_and_changed_hash_ids_fail_closed() -> None:
    paragraphs = synthetic_paragraphs()
    expected_ids = [paragraph.paragraph_id for paragraph in paragraphs]
    source_hashes = {paragraph.paragraph_id: stable_text_sha256(paragraph.text) for paragraph in paragraphs}
    cases = malformed_payload_cases(paragraphs)

    validate_model_payload(cases["base"], expected_ids=expected_ids, source_hashes=source_hashes)
    for name in ("missing_id", "extra_id", "duplicate_id", "reordered_ids", "changed_hash"):
        with pytest.raises(IDContractError):
            validate_model_payload(cases[name], expected_ids=expected_ids, source_hashes=source_hashes)


def test_context_overflow_rechunks_without_truncation() -> None:
    paragraphs = [Paragraph(f"P{i:03d}", "x" * 200) for i in range(12)]
    chunks = chunk_paragraphs(
        paragraphs,
        max_context_tokens=700,
        max_output_tokens=128,
        prompt_overhead_tokens=128,
        overflow_policy="rechunk",
    )
    assert len(chunks) > 1
    assert [pid for chunk in chunks for pid in chunk.paragraph_ids] == [p.paragraph_id for p in paragraphs]
    with pytest.raises(ContextOverflowError):
        chunk_paragraphs(
            [Paragraph("P999", "x" * 10000)],
            max_context_tokens=1000,
            max_output_tokens=128,
            prompt_overhead_tokens=128,
            overflow_policy="rechunk",
        )


def test_fixed_seed_synthetic_repeatability() -> None:
    paragraphs = synthetic_paragraphs()
    client = StaticJSONClient([expected_payload(paragraphs), expected_payload(paragraphs)])
    summary = run_synthetic_smoke(
        client,
        SmokeConfig(
            model_name="synthetic-static-json",
            model_file_sha256=None,
            runtime="mock",
            model_supported_context=131072,
            context=16384,
            max_output=1536,
            temperature=0.01,
            seed=42,
            threads=12,
            gpu_layers=34,
            concurrency=1,
            prompt_template="auto_jinja",
        ),
    )
    assert summary["status"] == "COMPLETED"
    assert summary["json_valid_rate"] == 1.0
    assert summary["exact_id_valid_rate"] == 1.0
    assert summary["repeatability_result"] == "PASS"


def test_docker_compose_keeps_source_volume_out_of_llm_runtime() -> None:
    compose = Path("docker-compose.llm.yml").read_text(encoding="utf-8")
    worker_block = compose.split("journal-worker:", 1)[1].split("llm-runtime:", 1)[0]
    runtime_block = compose.split("llm-runtime:", 1)[1]
    assert "/workspace/source" in worker_block
    assert "/workspace/source" not in runtime_block
    assert "${MODEL_DIR:?set MODEL_DIR}" in runtime_block
    assert "read_only: true" in runtime_block
    assert "MODEL_FILE" in runtime_block
    assert ".gguf" not in runtime_block


def test_public_handoff_rejects_local_paths_and_secrets() -> None:
    issues = validate_public_handoff(
        {
            "safe": "reports/runs/example/SUMMARY.md",
            "unsafe": "C:" + "\\Users\\Example\\secret.txt",
            "token": "sk-" + "thisisnotapublictoken123456",
        }
    )
    assert {issue["issue"] for issue in issues} == {"absolute_path", "secret_pattern"}
