# Test Results

Commands executed:

- `git switch main`
- `git pull --ff-only`
- `git status --short`
- `git log -1 --oneline`
- `python -m pip install jsonschema==4.23.0`
- `python -m pytest -q`
- `docker build -f docker/Dockerfile.worker -t journal-factory-worker:llm0-1 .`
- `python -m journal_factory.llm.host_runner synthetic-smoke --mock --output reports/runs/2026-07-16_llm_0_1_contract_alignment_governance_repair/MODEL_RUN_SUMMARY.mock.json`
- `docker run --rm journal-factory-worker:llm0-1 synthetic-smoke --mock --context 16384 --max-output 1536 --prompt-template auto_jinja`
- `docker compose -f docker-compose.llm.yml config`
- `python -m journal_factory.llm.host_runner validate-public-handoff reports/runs/2026-07-16_llm_0_1_contract_alignment_governance_repair/HANDOFF.json`

Results:

- Base check: PASS, `main` started at `5f5adf3b26e73c88dd1ac0cd1ed9969b1f9b2eab`.
- Pytest: PASS, 35 passed.
- Exact v1 schema tests: PASS.
- Invalid schema tests: PASS.
- ID contract tests: PASS.
- Context-only ID rejection: PASS.
- State disagreement test: PASS.
- Handoff schema tests: PASS.
- Compose source-isolation test: PASS.
- Compose network exposure test: PASS.
- Docker worker build: PASS.
- Mock transport/schema/ID smoke: PASS.

Not run by design:

- Real Gemma 4 E2B model benchmark.
- Auto/Jinja versus manual-template model A/B benchmark.
- LLM-1 shadow classification.
