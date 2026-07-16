from __future__ import annotations

import json
from typing import Any

from journal_factory.llm.benchmark import (
    BenchmarkConfig,
    load_benchmark_fixture,
    response_format_for_mode,
    run_real_gemma_benchmark,
)
from journal_factory.llm.client import CompletionResult, LLMRuntimeError, StaticJSONClient
from journal_factory.llm.contracts import load_skill_schema
from journal_factory.llm.synthetic import expected_payload, malformed_payload_cases, synthetic_paragraphs


class ScriptedClient:
    def __init__(self, payloads: list[dict[str, Any] | str]) -> None:
        self.payloads = list(payloads)
        self.calls = 0
        self.response_formats: list[dict[str, Any] | None] = []

    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        seed: int | None,
        max_tokens: int,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult:
        self.response_formats.append(response_format)
        payload = self.payloads[min(self.calls, len(self.payloads) - 1)]
        self.calls += 1
        content = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        return CompletionResult(
            content=content,
            latency_ms=10.0,
            model="google/gemma-4-e2b",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )


class UnavailableClient:
    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        seed: int | None,
        max_tokens: int,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult:
        raise LLMRuntimeError("endpoint unavailable")


def _config(*, real_model: bool = True, prompt_templates: tuple[str, ...] = ("auto_jinja",)) -> BenchmarkConfig:
    return BenchmarkConfig(
        model_identifier="google/gemma-4-e2b",
        runtime="lmstudio-openai-compatible",
        endpoint="http://127.0.0.1:1234",
        model_supported_context=131072,
        context=16384,
        max_output=2048,
        temperature=0.01,
        seed=42,
        threads=12,
        gpu_layers=34,
        concurrency=1,
        prompt_templates=prompt_templates,
        response_format="json_schema",
        repeat_count=1,
        real_model=real_model,
    )


def test_fixture_preserves_v1_business_type_names_and_orcid_service_data() -> None:
    fixture = load_benchmark_fixture()
    block_types = {block["paragraph_ids"][0]: block["block_type"] for block in fixture.expected_blocks}
    assert block_types["P003"] == "service_data"
    assert "orcid" not in block_types.values()
    assert "empty_paragraph" in block_types.values()
    assert "affiliation" in block_types.values()
    assert "main_text" in block_types.values()


def test_response_format_json_schema_uses_versioned_skill_schema() -> None:
    schema = load_skill_schema()
    response_format = response_format_for_mode("json_schema", schema)
    assert response_format is not None
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["schema"]["$id"] == schema["$id"]


def test_real_benchmark_completed_when_scripted_real_client_passes_all_gates() -> None:
    client = ScriptedClient([expected_payload(synthetic_paragraphs())])
    report = run_real_gemma_benchmark(client, _config(real_model=True))
    assert report["status"] == "COMPLETED"
    assert report["metrics"]["valid_output_rate"] == 1.0
    assert report["metrics"]["semantic_exact_rate"] == 1.0
    assert report["gates"]["passed"] is True
    assert client.response_formats[0]["type"] == "json_schema"


def test_mock_transport_cannot_be_reported_as_real_benchmark() -> None:
    client = StaticJSONClient([expected_payload(synthetic_paragraphs())])
    report = run_real_gemma_benchmark(client, _config(real_model=False))
    assert report["status"] == "FAILED"
    assert "MOCK_NOT_REAL_BENCHMARK" in report["blockers"]
    assert report["metrics"]["valid_output_rate"] == 1.0


def test_context_only_id_failure_blocks_benchmark_gates() -> None:
    payload = malformed_payload_cases(synthetic_paragraphs())["context_only_id"]
    client = ScriptedClient([payload])
    report = run_real_gemma_benchmark(client, _config(real_model=True))
    assert report["status"] == "FAILED"
    assert report["metrics"]["id_contract_failures"] == 1
    assert report["metrics"]["context_only_id_failures"] == 1
    assert report["gates"]["passed"] is False


def test_malformed_json_and_state_disagreement_fail_closed() -> None:
    malformed = ScriptedClient(["not valid json"])
    malformed_report = run_real_gemma_benchmark(malformed, _config(real_model=True))
    assert malformed_report["status"] == "FAILED"
    assert malformed_report["metrics"]["json_failures"] == 1

    state_disagreement = malformed_payload_cases(synthetic_paragraphs())["state_disagreement"]
    state_client = ScriptedClient([state_disagreement])
    state_report = run_real_gemma_benchmark(state_client, _config(real_model=True))
    assert state_report["status"] == "FAILED"
    assert state_report["metrics"]["state_failures"] == 1


def test_endpoint_unavailable_is_blocked_not_completed() -> None:
    report = run_real_gemma_benchmark(UnavailableClient(), _config(real_model=True))
    assert report["status"] == "BLOCKED"
    assert report["metrics"]["transport_failures"] == 1
    assert "MODEL_RUNTIME_UNAVAILABLE" in report["blockers"]
