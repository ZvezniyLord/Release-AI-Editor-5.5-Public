from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chunking import Paragraph, chunk_paragraphs
from .client import ChatClient, LLMRuntimeError, StaticJSONClient
from .contracts import (
    IDContractError,
    ModelResponseError,
    ModelStateDisagreementError,
    SchemaValidationError,
    load_skill_schema,
    parse_strict_json,
    reject_forbidden_response_keys,
    validate_exact_id_contract,
    validate_model_state_update,
    validate_schema,
    validate_source_hash,
)
from .templates import PROMPT_VERSION, render_messages


DEFAULT_FIXTURE_PATH = Path("fixtures/synthetic/llm_benchmark/paragraph_classifier_v1.json")


@dataclass(frozen=True)
class BenchmarkFixture:
    fixture_version: str
    article_id: str
    source_hash: str
    input_state: dict[str, bool]
    paragraphs: tuple[Paragraph, ...]
    expected_blocks: tuple[dict[str, Any], ...]
    gates: dict[str, Any]

    @property
    def expected_ids(self) -> list[str]:
        return [paragraph.paragraph_id for paragraph in self.paragraphs if not paragraph.context_only]

    @property
    def context_only_ids(self) -> list[str]:
        return [paragraph.paragraph_id for paragraph in self.paragraphs if paragraph.context_only]


@dataclass(frozen=True)
class BenchmarkConfig:
    model_identifier: str
    runtime: str
    endpoint: str | None
    model_supported_context: int
    context: int
    max_output: int
    temperature: float
    seed: int | None
    threads: int
    gpu_layers: int
    concurrency: int
    prompt_templates: tuple[str, ...]
    response_format: str
    repeat_count: int
    real_model: bool
    model_file_sha256: str | None = None
    docker_image_name: str | None = None
    docker_image_digest: str | None = None


def load_benchmark_fixture(path: Path = DEFAULT_FIXTURE_PATH) -> BenchmarkFixture:
    data = json.loads(path.read_text(encoding="utf-8"))
    paragraphs = tuple(
        Paragraph(
            paragraph_id=item["paragraph_id"],
            text=item["text"],
            context_only=bool(item.get("context_only", False)),
        )
        for item in data["paragraphs"]
    )
    return BenchmarkFixture(
        fixture_version=data["fixture_version"],
        article_id=data["article_id"],
        source_hash=data["source_hash"],
        input_state=dict(data.get("input_state") or {}),
        paragraphs=paragraphs,
        expected_blocks=tuple(dict(item) for item in data["expected_blocks"]),
        gates=dict(data["gates"]),
    )


def response_format_for_mode(mode: str, schema: dict[str, Any]) -> dict[str, Any] | None:
    if mode == "none":
        return None
    if mode == "json_object":
        return {"type": "json_object"}
    if mode == "json_schema":
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "paragraph_classifier_output_v1",
                "strict": True,
                "schema": schema,
            },
        }
    raise ValueError(f"unsupported response_format mode: {mode}")


def _expected_block_type_by_id(fixture: BenchmarkFixture) -> dict[str, str]:
    expected: dict[str, str] = {}
    for block in fixture.expected_blocks:
        for paragraph_id in block["paragraph_ids"]:
            expected[paragraph_id] = block["block_type"]
    return expected


def _actual_block_type_by_id(payload: dict[str, Any]) -> dict[str, str]:
    actual: dict[str, str] = {}
    for block in payload.get("blocks", []):
        block_type = block.get("block_type")
        for paragraph_id in block.get("paragraph_ids", []):
            if isinstance(paragraph_id, str) and isinstance(block_type, str):
                actual[paragraph_id] = block_type
    return actual


def semantic_exact_rate(payload: dict[str, Any], fixture: BenchmarkFixture) -> float:
    expected = _expected_block_type_by_id(fixture)
    if not expected:
        return 0.0
    actual = _actual_block_type_by_id(payload)
    exact = sum(1 for paragraph_id, block_type in expected.items() if actual.get(paragraph_id) == block_type)
    return exact / len(expected)


def _error_code(exc: Exception) -> str:
    message = str(exc)
    if isinstance(exc, SchemaValidationError):
        if "forbidden response key" in message:
            return "FORBIDDEN_RESPONSE_FIELD"
        return "SCHEMA_INVALID"
    if isinstance(exc, IDContractError):
        if "context-only paragraph IDs returned" in message:
            return "CONTEXT_ONLY_ID_RETURNED"
        if "duplicate paragraph IDs" in message:
            return "DUPLICATE_ID"
        if "ID mismatch" in message:
            return "ID_CONTRACT_MISMATCH"
        if "reordered" in message:
            return "ID_ORDER_CHANGED"
        return "ID_CONTRACT_INVALID"
    if isinstance(exc, ModelStateDisagreementError):
        return "MODEL_STATE_DISAGREEMENT"
    return "MODEL_RESPONSE_INVALID"


def evaluate_model_content(
    content: str,
    *,
    fixture: BenchmarkFixture,
    schema: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "json_valid": False,
        "schema_valid": False,
        "id_contract_valid": False,
        "context_only_id_valid": True,
        "state_valid": False,
        "semantic_exact_rate": 0.0,
        "valid_output": False,
        "errors": [],
    }
    try:
        payload = parse_strict_json(content)
        result["json_valid"] = True
    except SchemaValidationError as exc:
        result["errors"].append({"code": _error_code(exc), "message": str(exc)})
        return result

    try:
        reject_forbidden_response_keys(payload)
        validate_schema(payload, schema=schema)
        result["schema_valid"] = True
    except SchemaValidationError as exc:
        result["errors"].append({"code": _error_code(exc), "message": str(exc)})
        if _error_code(exc) == "FORBIDDEN_RESPONSE_FIELD":
            result["forbidden_field_valid"] = False

    try:
        validate_exact_id_contract(
            payload,
            fixture.expected_ids,
            context_only_ids=fixture.context_only_ids,
        )
        validate_source_hash(payload, fixture.source_hash)
        result["id_contract_valid"] = True
    except IDContractError as exc:
        code = _error_code(exc)
        result["errors"].append({"code": code, "message": str(exc)})
        if code == "CONTEXT_ONLY_ID_RETURNED":
            result["context_only_id_valid"] = False

    try:
        validate_model_state_update(payload, input_state=fixture.input_state)
        result["state_valid"] = True
    except ModelStateDisagreementError as exc:
        result["errors"].append({"code": _error_code(exc), "message": str(exc)})

    result["semantic_exact_rate"] = semantic_exact_rate(payload, fixture)
    result["valid_output"] = (
        result["json_valid"]
        and result["schema_valid"]
        and result["id_contract_valid"]
        and result["context_only_id_valid"]
        and result["state_valid"]
    )
    return result


def _aggregate_rates(runs: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(runs)
    if not total:
        return {
            "valid_output_rate": 0.0,
            "semantic_exact_rate": 0.0,
            "schema_failures": 0,
            "id_contract_failures": 0,
            "context_only_id_failures": 0,
            "state_failures": 0,
            "forbidden_field_failures": 0,
            "json_failures": 0,
            "transport_failures": 0,
        }
    latencies = [run["latency_ms"] for run in runs if isinstance(run.get("latency_ms"), (int, float))]
    token_rates = [
        run["tokens_per_second"]
        for run in runs
        if isinstance(run.get("tokens_per_second"), (int, float)) and run["tokens_per_second"] > 0
    ]
    return {
        "valid_output_rate": sum(1 for run in runs if run.get("valid_output")) / total,
        "semantic_exact_rate": statistics.mean(float(run.get("semantic_exact_rate") or 0.0) for run in runs),
        "schema_failures": sum(1 for run in runs if run.get("json_valid") and not run.get("schema_valid")),
        "id_contract_failures": sum(1 for run in runs if run.get("json_valid") and not run.get("id_contract_valid")),
        "context_only_id_failures": sum(
            1 for run in runs if run.get("context_only_id_valid") is False
        ),
        "state_failures": sum(1 for run in runs if run.get("json_valid") and not run.get("state_valid")),
        "forbidden_field_failures": sum(
            1
            for run in runs
            for error in run.get("errors", [])
            if error.get("code") == "FORBIDDEN_RESPONSE_FIELD"
        ),
        "json_failures": sum(1 for run in runs if not run.get("json_valid")),
        "transport_failures": sum(1 for run in runs if run.get("transport_failure")),
        "latency_p50_ms": statistics.median(latencies) if latencies else None,
        "latency_p95_ms": max(latencies) if latencies else None,
        "latency_total_ms": sum(latencies) if latencies else None,
        "tokens_per_second": statistics.mean(token_rates) if token_rates else None,
    }


def gates_pass(metrics: dict[str, Any], gates: dict[str, Any]) -> bool:
    return (
        metrics["valid_output_rate"] >= float(gates["valid_output_rate"])
        and metrics["semantic_exact_rate"] >= float(gates["semantic_exact_rate_min"])
        and metrics["schema_failures"] <= int(gates["schema_failures"])
        and metrics["id_contract_failures"] <= int(gates["id_contract_failures"])
        and metrics["context_only_id_failures"] <= int(gates["context_only_id_failures"])
        and metrics["state_failures"] <= int(gates["state_failures"])
        and metrics["forbidden_field_failures"] <= int(gates["forbidden_field_failures"])
        and metrics["json_failures"] == 0
        and metrics["transport_failures"] == 0
    )


def run_real_gemma_benchmark(
    client: ChatClient,
    config: BenchmarkConfig,
    *,
    fixture_path: Path = DEFAULT_FIXTURE_PATH,
    repo: Path | None = None,
) -> dict[str, Any]:
    schema = load_skill_schema(repo)
    fixture = load_benchmark_fixture(fixture_path)
    chunks = chunk_paragraphs(
        fixture.paragraphs,
        max_context_tokens=config.context,
        max_output_tokens=config.max_output,
        overflow_policy="rechunk",
    )
    response_format = response_format_for_mode(config.response_format, schema)
    runs: list[dict[str, Any]] = []
    started = time.perf_counter()

    for repeat in range(config.repeat_count):
        for prompt_template in config.prompt_templates:
            for chunk in chunks:
                run: dict[str, Any] = {
                    "fixture_version": fixture.fixture_version,
                    "chunk_id": chunk.chunk_id,
                    "repeat": repeat + 1,
                    "prompt_template": prompt_template,
                    "response_format": config.response_format,
                    "expected_decision_id_count": len(
                        [paragraph for paragraph in chunk.paragraphs if not paragraph.context_only]
                    ),
                    "context_only_id_count": len(
                        [paragraph for paragraph in chunk.paragraphs if paragraph.context_only]
                    ),
                }
                messages = render_messages(
                    list(chunk.paragraphs),
                    schema=schema,
                    prompt_template=prompt_template,
                )
                try:
                    call_started = time.perf_counter()
                    completion = client.chat_completion(
                        messages=messages,
                        temperature=config.temperature,
                        seed=config.seed,
                        max_tokens=config.max_output,
                        response_format=response_format,
                    )
                    elapsed = max(time.perf_counter() - call_started, 0.001)
                    run.update(
                        {
                            "latency_ms": completion.latency_ms,
                            "model_reported": completion.model,
                            "prompt_tokens": completion.prompt_tokens,
                            "completion_tokens": completion.completion_tokens,
                            "total_tokens": completion.total_tokens,
                            "tokens_per_second": (
                                completion.total_tokens / elapsed if completion.total_tokens else None
                            ),
                        }
                    )
                    run.update(evaluate_model_content(completion.content, fixture=fixture, schema=schema))
                except LLMRuntimeError as exc:
                    run.update(
                        {
                            "transport_failure": True,
                            "json_valid": False,
                            "schema_valid": False,
                            "id_contract_valid": False,
                            "context_only_id_valid": False,
                            "state_valid": False,
                            "semantic_exact_rate": 0.0,
                            "valid_output": False,
                            "errors": [{"code": "MODEL_RUNTIME_UNAVAILABLE", "message": str(exc)}],
                        }
                    )
                runs.append(run)

    metrics = _aggregate_rates(runs)
    gate_result = gates_pass(metrics, fixture.gates)
    blockers: list[str] = []
    if isinstance(client, StaticJSONClient) or not config.real_model:
        blockers.append("MOCK_NOT_REAL_BENCHMARK")
    if metrics["transport_failures"]:
        blockers.append("MODEL_RUNTIME_UNAVAILABLE")
    if not gate_result:
        blockers.append("REAL_GEMMA_BENCHMARK_GATES_FAILED")

    if "MOCK_NOT_REAL_BENCHMARK" in blockers:
        status = "FAILED"
    elif metrics["transport_failures"]:
        status = "BLOCKED"
    elif gate_result:
        status = "COMPLETED"
    else:
        status = "FAILED"

    return {
        "cycle": "LLM-0.2",
        "status": status,
        "runtime": config.runtime,
        "model_identifier": config.model_identifier,
        "endpoint": config.endpoint,
        "model_file_sha256": config.model_file_sha256,
        "docker_image_name": config.docker_image_name,
        "docker_image_digest": config.docker_image_digest,
        "prompt_path": "skills/journal_builder/prompts/paragraph_classifier/v1/system.txt",
        "schema_path": "skills/journal_builder/schemas/paragraph_classifier_output.v1.schema.json",
        "prompt_version": PROMPT_VERSION,
        "schema_version": "paragraph_classifier_output.v1",
        "fixture_path": fixture_path.as_posix(),
        "fixture_count": 1,
        "benchmark_parameters": {
            "model_supported_context": config.model_supported_context,
            "context": config.context,
            "max_output": config.max_output,
            "temperature": config.temperature,
            "seed": config.seed,
            "threads": config.threads,
            "gpu_layers": config.gpu_layers,
            "concurrency": config.concurrency,
            "prompt_templates": list(config.prompt_templates),
            "response_format": config.response_format,
            "repeat_count": config.repeat_count,
        },
        "validated_operational_context": config.context if status == "COMPLETED" else None,
        "metrics": metrics,
        "gates": fixture.gates | {"passed": gate_result},
        "runs": runs,
        "total_wall_time_ms": (time.perf_counter() - started) * 1000,
        "closed_blockers": ["REAL_GEMMA4_E2B_BENCHMARK_NOT_RUN"],
        "blockers": blockers,
        "open_follow_ups": [
            "Keep v2 classifier schema as candidate until a separate migration decision is approved."
        ],
        "v1_v2_decision": "v1 retained for LLM-0.2; v2 remains candidate and was not promoted.",
    }


def write_benchmark_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
