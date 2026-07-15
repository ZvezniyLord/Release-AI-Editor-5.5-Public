# Multi Chat Execution Plan

Use GitHub as durable state between chats.

Cycle protocol:

1. Read current `main`.
2. Confirm base SHA and scope.
3. Implement only the requested cycle.
4. Run required tests and scans.
5. Commit and push.
6. Return final remote SHA, report paths, test result, blockers, and stop.

Do not continue into the next architectural cycle without an explicit new user
instruction.

Current sequence:

1. LLM-0 foundation.
2. LLM-0.1 contract alignment and governance repair.
3. LLM-0.2 real local Gemma 4 E2B host benchmark.
4. Later shadow classification cycles.
5. Journal style cleanup and body completion only after LLM governance is stable.
