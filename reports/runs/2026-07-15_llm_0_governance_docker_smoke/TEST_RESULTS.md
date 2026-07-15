# Test Results

Commands executed:

- `git switch main`
- `git pull --ff-only`
- `git status --short`
- `git log -1 --oneline`
- `python -m pytest -q`
- `docker version --format '{{json .}}'`
- `docker build -f docker/Dockerfile.worker -t journal-factory-worker:llm0 .`
- `docker compose -f docker-compose.llm.yml config`
- `docker run --rm journal-factory-worker:llm0 synthetic-smoke --mock --context 16384 --max-output 1536 --prompt-template auto_jinja`
- `python -m journal_factory.llm.host_runner synthetic-smoke --mock --output reports/runs/2026-07-15_llm_0_governance_docker_smoke/MODEL_RUN_SUMMARY.mock.json`
- `python -m journal_factory.llm.host_runner synthetic-smoke --mock --prompt-template manual_chatml --temperature 0.01 --seed 42 --output reports/runs/2026-07-15_llm_0_governance_docker_smoke/MODEL_RUN_SUMMARY.manual_mock.json`
- `python -m journal_factory.llm.host_runner synthetic-smoke --base-url http://localhost:11434 --model gemma2:2b --runtime ollama-openai-compatible --context 8192 --max-output 1536 --temperature 0.01 --seed 42 --threads 12 --gpu-layers 34 --concurrency 1 --prompt-template auto_jinja --output reports/runs/2026-07-15_llm_0_governance_docker_smoke/MODEL_RUN_SUMMARY.ollama_gemma2_probe.json`
- `python -m journal_factory.llm.host_runner validate-public-handoff reports/runs/2026-07-15_llm_0_governance_docker_smoke/MODEL_RUN_SUMMARY.mock.json`

Results:

- Initial branch/base check: PASS, `main` at `14f6469 Add reproducible raw assembly core`, clean before edits.
- Changeset SHA verification: BLOCKED, archive not found.
- Pytest: PASS, 32 passed.
- Invalid JSON fail-closed: PASS via pytest.
- Missing/extra/duplicate/reordered paragraph ID fail-closed: PASS via pytest.
- Source text hash mismatch fail-closed: PASS via pytest.
- Overflow rechunk without truncation: PASS via pytest.
- Fixed-seed repeatability: PASS via pytest and mock smoke.
- Docker worker build: PASS.
- Docker LLM runtime health: BLOCKED for target Gemma 4 E2B runtime.
- Synthetic classifier smoke: PASS in deterministic mock mode, FAIL-CLOSED for non-target local `gemma2:2b` probe.
- Public data/security scan: LIMITED PASS; `git grep` found no actionable secrets or absolute paths in changed public files, but `gitleaks` is unavailable.
