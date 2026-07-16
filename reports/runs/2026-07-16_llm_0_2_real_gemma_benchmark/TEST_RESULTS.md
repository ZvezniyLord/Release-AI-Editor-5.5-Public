# LLM-0.2 Test Results

Status: FAILED because real model gates failed.

Executed checks:

- `python -m pytest -q`
  - Result: PASS, 42 passed.
- `docker build -f docker/Dockerfile.worker -t journal-factory-worker:llm0-2 .`
  - Result: PASS.
- `docker compose -f docker-compose.llm.yml config`
  - Result: PASS with dummy local environment values. The generated config was not committed because it contains local absolute paths.
- `python -m journal_factory.llm.host_runner real-benchmark --mock --output .tmp_llm02_mock_benchmark.json`
  - Result: PASS as harness smoke. The command correctly produced `status = FAILED` with `MOCK_NOT_REAL_BENCHMARK`.
- `python -m journal_factory.llm.host_runner health --base-url http://127.0.0.1:1234 --model google/gemma-4-e2b`
  - Result: PASS. Endpoint reported `google/gemma-4-e2b`.
- `python -m journal_factory.llm.host_runner real-benchmark --base-url http://127.0.0.1:1234 --model google/gemma-4-e2b --runtime lmstudio-openai-compatible --context 16384 --max-output 2048 --temperature 0.01 --seed 42 --threads 12 --gpu-layers 34 --concurrency 1 --prompt-templates auto_jinja,manual_chatml --response-format json_schema --repeat-count 1 --output reports/runs/2026-07-16_llm_0_2_real_gemma_benchmark/REAL_GEMMA_BENCHMARK.json`
  - Result: FAIL-CLOSED. Real benchmark executed; gates failed.
- `python -m journal_factory.llm.host_runner real-benchmark --base-url http://127.0.0.1:11434 --model gemma4:e2b --runtime ollama-openai-compatible --context 16384 --max-output 2048 --temperature 0.01 --seed 42 --threads 12 --gpu-layers 34 --concurrency 1 --prompt-templates auto_jinja,manual_chatml --response-format json_schema --repeat-count 1 --output reports/runs/2026-07-16_llm_0_2_real_gemma_benchmark/REAL_GEMMA_BENCHMARK_OLLAMA.json`
  - Result: FAIL-CLOSED. Real benchmark executed; gates failed.
- `docker run --rm -v "${PWD}:/repo" zricethezav/gitleaks:latest detect --source /repo --no-git --redact -v`
  - Result: PASS, no leaks found.
- `python -m journal_factory.llm.host_runner validate-public-handoff reports/runs/2026-07-16_llm_0_2_real_gemma_benchmark/HANDOFF.json`
  - Result: PASS.
- Targeted `rg` scans for secret patterns, local paths, personal email/phone patterns, and model weight extensions.
  - Result: PASS after review. Matches were expected code variables, `.gitignore` model-weight patterns, localhost endpoints, dates, and current benchmark reports.

Not executed:

- Production journal generation: out of scope.
- TOC generation: out of scope.
- LLM-1 shadow classification: out of scope.
