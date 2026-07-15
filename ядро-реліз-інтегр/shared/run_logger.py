from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class RunLogger:
    path: Path

    def _write(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def log(self, event: str, **fields) -> None:
        payload = {"ts": datetime.utcnow().isoformat(timespec="seconds") + "Z", "event": event}
        payload.update(fields)
        self._write(payload)

    def info(self, message: str, **fields) -> None:
        self.log("info", message=message, **fields)


def make_logger(run_dir: Path, *, name: str) -> RunLogger:
    return RunLogger(run_dir / f"{name}_log.jsonl")
