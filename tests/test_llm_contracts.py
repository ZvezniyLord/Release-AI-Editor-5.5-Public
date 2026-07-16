from __future__ import annotations

from pathlib import Path

import pytest

from journal_factory.llm.chunking import ContextOverflowError, Paragraph, chunk_paragraphs
from journal_factory.llm.client import StaticJSONClient
from journal_factory.llm.contracts import (
    IDContractError,
    ModelStateDisagreementError,
    SchemaValidationError,
    deterministic_state_transition,
    load_skill_schema,
    validate_model_payload,
    validate_model_text,
)
from journal_factory.llm.host_runner import SmokeConfig, run_synthetic_smoke
from journal_factory.llm.public_handoff import validate_public_handoff
from journal_factory.llm.synthetic import SOURCE_HASH, expected_payload, malformed_payload_cases, synthetic_paragraphs
from journal_factory.llm.templates import load_system_prompt, render_messages


def _expected_ids() -> list[str]:
    return [paragraph.paragraph_id for paragraph in synthetic_paragraphs() if not paragraph.context_only]


def _context_only_ids() -> list[str]:
    return [paragraph.paragraph_id for paragraph in synthetic_paragraphs() if paragraph.context_only]


def test_v1_skill_schema_uses_current_business_contract_names() -> None:
    schema = load_skill_schema()
    block_types = set(schema["$defs"]["block_type"]["enum"])
    assert {"fragment_status", "state_update", "blocks", "problems", "next_action"} <= set(
        schema["properties"]
    )
    assert "empty_paragraph" in block_types
    assert "affiliation" in block_types
    assert "main_text" in block_types
    assert "service_data" in block_types
    assert "empty" not in block_types
    assert "institution" not in block_types
    assert "body" not in block_types
    assert "orcid" not in block_types


def test_versioned_ukrainian_prompt_is_loaded_from_skill_directory() -> None:
    prompt = load_system_prompt()
    assert "Ти локальний класифікатор фрагментів" in prompt
    assert "empty_paragraph" in prompt
    assert "affiliation" in prompt
    assert "main_text" in prompt
    assert "ORCID у v1 не є окремим block_type" in prompt
    messages = render_messages(synthetic_paragraphs(), schema=load_skill_schema(), prompt_template="auto_jinja")
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == prompt
    assert "properties" not in messages[0]["content"]


def test_invalid_json_fails_closed() -> None:
    with pytest.raises(SchemaValidationError):
        validate_model_text("prose before {not-json}", expected_ids=["P001"])


def test_v1_schema_accepts_exact_contract_and_rejects_old_names() -> None:
    paragraphs = synthetic_paragraphs()
    cases = malformed_payload_cases(paragraphs)

    validate_model_payload(
        cases["base"],
        expected_ids=_expected_ids(),
        context_only_ids=_context_only_ids(),
        expected_source_hash=SOURCE_HASH,
        input_state={},
    )
    for name in ("old_role_name", "orcid_type", "forbidden_text"):
        with pytest.raises(SchemaValidationError):
            validate_model_payload(
                cases[name],
                expected_ids=_expected_ids(),
                context_only_ids=_context_only_ids(),
                expected_source_hash=SOURCE_HASH,
                input_state={},
            )


def test_missing_extra_duplicate_reordered_context_and_hash_ids_fail_closed() -> None:
    paragraphs = synthetic_paragraphs()
    cases = malformed_payload_cases(paragraphs)

    for name in ("missing_id", "extra_id", "duplicate_id", "reordered_ids", "context_only_id", "changed_hash"):
        with pytest.raises(IDContractError):
            validate_model_payload(
                cases[name],
                expected_ids=_expected_ids(),
                context_only_ids=_context_only_ids(),
                expected_source_hash=SOURCE_HASH,
                input_state={},
            )


def test_model_state_disagreement_fails_closed() -> None:
    cases = malformed_payload_cases(synthetic_paragraphs())
    with pytest.raises(ModelStateDisagreementError, match="MODEL_STATE_DISAGREEMENT"):
        validate_model_payload(
            cases["state_disagreement"],
            expected_ids=_expected_ids(),
            context_only_ids=_context_only_ids(),
            expected_source_hash=SOURCE_HASH,
            input_state={},
        )


@pytest.mark.parametrize(
    ("block_type", "state_key"),
    [
        ("section", "section_found"),
        ("doi", "doi_found"),
        ("udc", "udc_found"),
        ("author", "authors_found"),
        ("author_status", "author_status_found"),
        ("affiliation", "affiliation_found"),
        ("city_country", "city_country_found"),
        ("title", "title_found"),
        ("annotation", "annotation_found"),
        ("keywords", "keywords_found"),
        ("main_text", "body_started"),
        ("table_caption", "body_started"),
        ("figure_caption", "body_started"),
        ("formula", "body_started"),
        ("references_heading", "references_started"),
        ("references_item", "references_started"),
        ("service_data", "service_data_found"),
    ],
)
def test_deterministic_state_transition_sets_each_allowed_state(block_type: str, state_key: str) -> None:
    state = deterministic_state_transition(
        {},
        [{"block_type": block_type, "paragraph_ids": ["P001"], "confidence": 1.0, "evidence": []}],
    )
    assert state[state_key] is True


def test_deterministic_state_transition_preserves_true_input_state() -> None:
    state = deterministic_state_transition({"title_found": True}, [])
    assert state["title_found"] is True


@pytest.mark.parametrize(
    ("block_type", "wrong_state_key"),
    [
        ("author_status", "author_status_found"),
        ("references_heading", "references_started"),
        ("service_data", "service_data_found"),
    ],
)
def test_forbidden_state_disagreement_cases_fail_closed(block_type: str, wrong_state_key: str) -> None:
    paragraphs = synthetic_paragraphs()
    payload = expected_payload(paragraphs)
    payload["blocks"] = [
        {
            "block_type": block_type,
            "paragraph_ids": ["P000"],
            "confidence": 1.0,
            "evidence": ["synthetic"],
        }
    ]
    payload["state_update"] = deterministic_state_transition({}, payload["blocks"])
    payload["state_update"][wrong_state_key] = False
    with pytest.raises(ModelStateDisagreementError):
        validate_model_payload(
            payload,
            expected_ids=["P000"],
            context_only_ids=[],
            expected_source_hash=SOURCE_HASH,
            input_state={},
        )


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


def test_mock_transport_schema_id_contract_and_repeatability_only() -> None:
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
    assert summary["model_name"] == "synthetic-static-json"


def test_docker_compose_keeps_source_volume_out_of_llm_runtime_and_port_internal_by_default() -> None:
    compose = Path("docker-compose.llm.yml").read_text(encoding="utf-8")
    worker_block = compose.split("journal-worker:", 1)[1].split("llm-runtime:", 1)[0]
    runtime_block = compose.split("llm-runtime:", 1)[1].split("llm-runtime-debug:", 1)[0]
    debug_block = compose.split("llm-runtime-debug:", 1)[1]
    assert "/workspace/source" in worker_block
    assert "/workspace/source" not in runtime_block
    assert "${MODEL_DIR:?set MODEL_DIR}" in runtime_block
    assert "read_only: true" in runtime_block
    assert "ports:" not in runtime_block
    assert "expose:" in runtime_block
    assert "internal: true" in compose
    assert "127.0.0.1:${LLM_PORT:-8080}:8080" in debug_block


def test_public_handoff_schema_rejects_placeholder_local_paths_and_secret_patterns() -> None:
    valid = {
        "cycle": "LLM-0.1",
        "status": "COMPLETED",
        "base_sha": "5f5adf3b26e73c88dd1ac0cd1ed9969b1f9b2eab",
        "implementation_commit_sha": "5f5adf3b26e73c88dd1ac0cd1ed9969b1f9b2eab",
        "report_commit_sha": None,
        "test_records": [{"name": "pytest", "command": "python -m pytest -q", "result": "PASS"}],
        "report_paths": {
            "summary": "reports/runs/example/SUMMARY.md",
            "handoff": "reports/runs/example/HANDOFF.json",
            "test_results": "reports/runs/example/TEST_RESULTS.md",
            "artifact_manifest": "reports/runs/example/ARTIFACT_MANIFEST.json",
            "defects": "reports/runs/example/DEFECTS.md",
        },
        "model_config_summary": {"real_model_benchmark": "not_run_in_llm_0_1"},
        "artifact_data_classes": ["public_code", "public_docs", "sanitized_reports", "docker_config"],
        "blockers": [],
    }
    assert validate_public_handoff(valid) == []

    invalid = dict(valid)
    invalid["implementation_commit_sha"] = "PENDING_FINAL_COMMIT_SHA_REPORTED_AFTER_PUSH"
    invalid["report_paths"] = dict(valid["report_paths"])
    invalid["report_paths"]["summary"] = "C:" + "\\Users\\Example\\SUMMARY.md"
    invalid["token"] = "sk-" + "thisisnotapublictoken123456"
    issues = validate_public_handoff(invalid)
    issue_codes = {issue["issue"] for issue in issues}
    assert "placeholder_value" in issue_codes
    assert "absolute_path" in issue_codes
    assert "secret_pattern" in issue_codes
    assert any(issue["issue"].startswith("schema:") for issue in issues)
