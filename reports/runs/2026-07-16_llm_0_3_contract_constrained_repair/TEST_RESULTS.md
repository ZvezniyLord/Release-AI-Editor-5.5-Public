# LLM-0.3 Test Results

Status: FAILED because LM Studio candidate gates failed.

Executed checks:

- `python -m pytest -q`
  - Result: PASS, 67 passed.
- `docker build -f docker/Dockerfile.worker -t journal-factory-worker:llm0-3 .`
  - Result: PASS.
- `docker compose -f docker-compose.llm.yml config`
  - Result: PASS with dummy local environment values. Generated config was not committed because it contains local paths.
- `python -m journal_factory.llm.host_runner real-benchmark --mock --prompt-version v1.1 --prompt-templates auto_jinja --output .tmp_llm03_mock.json`
  - Result: PASS as harness smoke. The command correctly exited non-zero because mock is not a real benchmark.
- Real LM Studio ablation:
  - v1 baseline: executed, FAILED gates.
  - v1.1 candidate: executed, FAILED gates because `P017` was missing in all 3 repeats.
- Real host Ollama ablation:
  - v1 baseline: executed, FAILED gates.
  - v1.1 candidate: executed, COMPLETED gates in all 3 repeats.
- `docker run --rm -v "${PWD}:/repo" zricethezav/gitleaks:latest detect --source /repo --no-git --redact -v`
  - Result: PASS, no leaks found.
- `python -m journal_factory.llm.host_runner validate-public-handoff reports/runs/2026-07-16_llm_0_3_contract_constrained_repair/HANDOFF.json`
  - Result: PASS.
- Targeted scans for local paths, personal email/phone patterns, secret patterns, and model weight extensions.
  - Result: PASS after review. Matches were expected localhost endpoints, dates, `.gitignore` model-weight patterns, and sanitized benchmark report metrics.

Not executed:

- Prompt promotion: blocked by LM Studio failure.
- Journal generation, A020, formatting cleanup, frontmatter, and TOC: out of scope.
