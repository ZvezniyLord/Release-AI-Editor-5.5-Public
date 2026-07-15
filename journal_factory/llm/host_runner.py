from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .benchmark import (
    DEFAULT_FIXTURE_PATH,
    BenchmarkConfig,
    run_real_gemma_benchmark,
)
from .chunking import chunk_paragraphs
from .client import ChatClient, OpenAICompatibleClient, StaticJSONClient
from .contracts import (
    ModelResponseError,
    load_skill_schema,
    parse_strict_json,
    validate_model_payload,
)
from .public_handoff import validate_public_handoff_file
from .synthetic import SOURCE_HASH, expected_payload, synthetic_paragraphs
from .templates import PROMPT_VERSION, render_messages


@dataclass(frozen=True)
class SmokeConfig:
    model_name: str
    model_file_sha256: str | None
    runtime: str
    model_supported_context: int
    context: int
    max_output: int
    temperature: float
    seed: int | None
    threads: int
    gpu_layers: int
    concurrency: int
    prompt_template: str
    flash_attention: bool = True
    gpu_kv_cache: bool = True
    kv_cache_quantization: bool = False
    evaluation_batch: int = 2048
    physical_batch: int = 512


def _client_from_env(args: argparse.Namespace) -> ChatClient:
    if args.mock:
        paragraphs = synthetic_paragraphs()
        return StaticJSONClient([expected_payload(paragraphs)])
    base_url = args.base_url or os.environ.get("LLM_BASE_URL")
    model = args.model or os.environ.get("LLM_MODEL")
    if not base_url or not model:
        raise RuntimeError("LLM_BASE_URL and LLM_MODEL are required for real local host smoke")
    return OpenAICompatibleClient(base_url=base_url, model=model, timeout_seconds=args.timeout)


def run_synthetic_smoke(client: ChatClient, config: SmokeConfig, *, repo: Path | None = None) -> dict[str, Any]:
    schema = load_skill_schema(repo)
    paragraphs = synthetic_paragraphs()
    chunks = chunk_paragraphs(
        paragraphs,
        max_context_tokens=config.context,
        max_output_tokens=config.max_output,
        overflow_policy="rechunk",
    )
    total = 0
    json_valid = 0
    id_valid = 0
    latencies: list[float] = []
    tokens_per_second: list[float] = []
    failures: list[dict[str, str]] = []
    repeatability_payloads: list[dict[str, Any]] = []

    for repeat in range(2):
        for chunk in chunks:
            messages = render_messages(
                list(chunk.paragraphs),
                schema=schema,
                prompt_template=config.prompt_template,
            )
            started = time.perf_counter()
            result = client.chat_completion(
                messages=messages,
                temperature=config.temperature,
                seed=config.seed,
                max_tokens=config.max_output,
                response_format={"type": "json_object"},
            )
            elapsed = max(time.perf_counter() - started, 0.001)
            total += 1
            latencies.append(result.latency_ms)
            if result.total_tokens:
                tokens_per_second.append(result.total_tokens / elapsed)
            decision_ids = [paragraph.paragraph_id for paragraph in chunk.paragraphs if not paragraph.context_only]
            context_only_ids = [paragraph.paragraph_id for paragraph in chunk.paragraphs if paragraph.context_only]
            try:
                payload = parse_strict_json(result.content)
                json_valid += 1
                validate_model_payload(
                    payload,
                    expected_ids=decision_ids,
                    context_only_ids=context_only_ids,
                    expected_source_hash=SOURCE_HASH,
                    input_state={},
                    schema=schema,
                )
                id_valid += 1
                repeatability_payloads.append(payload)
            except ModelResponseError as exc:
                failures.append({"chunk_id": chunk.chunk_id, "error": str(exc)})

    first_half = repeatability_payloads[: len(chunks)]
    second_half = repeatability_payloads[len(chunks) : len(chunks) * 2]
    if failures or not first_half or not second_half:
        repeatability_result = "NOT_RUN"
        deterministic_disagreement_count = 0
    else:
        deterministic_disagreement_count = 0 if first_half == second_half else 1
        repeatability_result = "PASS" if deterministic_disagreement_count == 0 else "FAIL"
    return {
        "status": "COMPLETED" if not failures else "FAILED",
        "model_name": config.model_name,
        "model_file_sha256": config.model_file_sha256,
        "runtime": config.runtime,
        "docker_image_name": None,
        "docker_image_digest": None,
        "model_supported_context": config.model_supported_context,
        "validated_operational_context": config.context if not failures else None,
        "threads": config.threads,
        "gpu_layers": config.gpu_layers,
        "evaluation_batch": config.evaluation_batch,
        "physical_batch": config.physical_batch,
        "concurrency": config.concurrency,
        "prompt_template": config.prompt_template,
        "prompt_version": PROMPT_VERSION,
        "schema_version": "paragraph_classifier_output.v1",
        "temperature": config.temperature,
        "seed": config.seed,
        "json_valid_rate": json_valid / total if total else 0.0,
        "exact_id_valid_rate": id_valid / total if total else 0.0,
        "retry_count": 0,
        "rechunk_count": sum(1 for chunk in chunks if chunk.rechunked),
        "latency_p50_ms": statistics.median(latencies) if latencies else None,
        "latency_p95_ms": max(latencies) if latencies else None,
        "tokens_per_second": statistics.mean(tokens_per_second) if tokens_per_second else None,
        "peak_vram_mb": None,
        "peak_ram_mb": None,
        "repeatability_result": repeatability_result,
        "deterministic_disagreement_count": deterministic_disagreement_count,
        "failures": failures,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_synthetic_smoke(args: argparse.Namespace) -> int:
    client = _client_from_env(args)
    config = SmokeConfig(
        model_name=args.model or os.environ.get("LLM_MODEL") or "synthetic-static-json",
        model_file_sha256=os.environ.get("LLM_MODEL_SHA256"),
        runtime=args.runtime,
        model_supported_context=args.model_supported_context,
        context=args.context,
        max_output=args.max_output,
        temperature=args.temperature,
        seed=args.seed,
        threads=args.threads,
        gpu_layers=args.gpu_layers,
        concurrency=args.concurrency,
        prompt_template=args.prompt_template,
    )
    summary = run_synthetic_smoke(client, config)
    if args.output:
        write_json(Path(args.output), summary)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == "COMPLETED" else 2


def command_real_benchmark(args: argparse.Namespace) -> int:
    client = _client_from_env(args)
    prompt_templates = tuple(item.strip() for item in args.prompt_templates.split(",") if item.strip())
    if not prompt_templates:
        raise RuntimeError("--prompt-templates must contain at least one prompt template")
    config = BenchmarkConfig(
        model_identifier=args.model or os.environ.get("LLM_MODEL") or "synthetic-static-json",
        model_file_sha256=os.environ.get("LLM_MODEL_SHA256"),
        runtime=args.runtime,
        endpoint=None if args.mock else (args.base_url or os.environ.get("LLM_BASE_URL")),
        model_supported_context=args.model_supported_context,
        context=args.context,
        max_output=args.max_output,
        temperature=args.temperature,
        seed=args.seed,
        threads=args.threads,
        gpu_layers=args.gpu_layers,
        concurrency=args.concurrency,
        prompt_templates=prompt_templates,
        response_format=args.response_format,
        repeat_count=args.repeat_count,
        real_model=not args.mock,
        docker_image_name=os.environ.get("LLM_DOCKER_IMAGE_NAME"),
        docker_image_digest=os.environ.get("LLM_DOCKER_IMAGE_DIGEST"),
    )
    summary = run_real_gemma_benchmark(client, config, fixture_path=Path(args.fixture))
    if args.output:
        write_json(Path(args.output), summary)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == "COMPLETED" else 2


def command_health(args: argparse.Namespace) -> int:
    client = _client_from_env(args)
    if not isinstance(client, OpenAICompatibleClient):
        print(json.dumps({"status": "COMPLETED", "runtime": "mock"}, sort_keys=True))
        return 0
    print(json.dumps(client.health(), ensure_ascii=False, sort_keys=True))
    return 0


def command_validate_handoff(args: argparse.Namespace) -> int:
    issues = validate_public_handoff_file(Path(args.path))
    if issues:
        print(json.dumps({"status": "FAILED", "issues": issues}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"status": "COMPLETED", "issues": []}, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="journal-factory-llm")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("synthetic-smoke", "health"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--base-url")
        cmd.add_argument("--model")
        cmd.add_argument("--timeout", type=float, default=120.0)
        cmd.add_argument("--mock", action="store_true")
        cmd.add_argument("--runtime", default="openai-compatible-local")
        if name == "synthetic-smoke":
            cmd.add_argument("--output")
            cmd.add_argument("--model-supported-context", type=int, default=131072)
            cmd.add_argument("--context", type=int, default=16384)
            cmd.add_argument("--max-output", type=int, default=1536)
            cmd.add_argument("--temperature", type=float, default=0.01)
            cmd.add_argument("--seed", type=int, default=42)
            cmd.add_argument("--threads", type=int, default=12)
            cmd.add_argument("--gpu-layers", type=int, default=34)
            cmd.add_argument("--concurrency", type=int, default=1)
            cmd.add_argument("--prompt-template", choices=["auto_jinja", "manual_chatml"], default="auto_jinja")
            cmd.set_defaults(func=command_synthetic_smoke)
        else:
            cmd.set_defaults(func=command_health)
    benchmark = sub.add_parser("real-benchmark")
    benchmark.add_argument("--base-url")
    benchmark.add_argument("--model")
    benchmark.add_argument("--timeout", type=float, default=180.0)
    benchmark.add_argument("--mock", action="store_true")
    benchmark.add_argument("--runtime", default="openai-compatible-local")
    benchmark.add_argument("--output")
    benchmark.add_argument("--fixture", default=str(DEFAULT_FIXTURE_PATH))
    benchmark.add_argument("--model-supported-context", type=int, default=131072)
    benchmark.add_argument("--context", type=int, default=16384)
    benchmark.add_argument("--max-output", type=int, default=2048)
    benchmark.add_argument("--temperature", type=float, default=0.01)
    benchmark.add_argument("--seed", type=int, default=42)
    benchmark.add_argument("--threads", type=int, default=12)
    benchmark.add_argument("--gpu-layers", type=int, default=34)
    benchmark.add_argument("--concurrency", type=int, default=1)
    benchmark.add_argument("--prompt-templates", default="auto_jinja,manual_chatml")
    benchmark.add_argument(
        "--response-format",
        choices=["json_schema", "json_object", "none"],
        default="json_schema",
    )
    benchmark.add_argument("--repeat-count", type=int, default=1)
    benchmark.set_defaults(func=command_real_benchmark)
    validate = sub.add_parser("validate-public-handoff")
    validate.add_argument("path")
    validate.set_defaults(func=command_validate_handoff)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
