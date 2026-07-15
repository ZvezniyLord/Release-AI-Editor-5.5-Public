from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, request


class LLMRuntimeError(RuntimeError):
    """Runtime or transport failure from the local LLM provider."""


@dataclass(frozen=True)
class CompletionResult:
    content: str
    latency_ms: float
    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatClient(Protocol):
    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        seed: int | None,
        max_tokens: int,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult:
        ...


class OpenAICompatibleClient:
    """Provider-neutral client for a local OpenAI-compatible HTTP API."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 120.0,
        authorization: str | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required; do not hardcode an endpoint")
        if not model:
            raise ValueError("model is required; do not hardcode a model filename")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.authorization = authorization

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/models", None)

    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        seed: int | None,
        max_tokens: int,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            body["seed"] = seed
        if response_format is not None:
            body["response_format"] = response_format

        started = time.perf_counter()
        data = self._request("POST", "/v1/chat/completions", body)
        latency_ms = (time.perf_counter() - started) * 1000
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMRuntimeError("OpenAI-compatible response did not contain message content") from exc
        usage = data.get("usage") or {}
        return CompletionResult(
            content=content,
            latency_ms=latency_ms,
            model=data.get("model"),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    def _request(self, method: str, path: str, body: dict[str, Any] | None) -> dict[str, Any]:
        encoded = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.authorization:
            headers["Authorization"] = self.authorization
        req = request.Request(
            f"{self.base_url}{path}",
            data=encoded,
            headers=headers,
            method=method,
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.URLError as exc:
            raise LLMRuntimeError(f"local LLM runtime unavailable: {exc}") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMRuntimeError("local LLM runtime returned non-JSON HTTP response") from exc


class StaticJSONClient:
    """Deterministic test client used only for synthetic smoke and tests."""

    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self._payloads = list(payloads)
        self.calls = 0

    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        seed: int | None,
        max_tokens: int,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult:
        if self.calls >= len(self._payloads):
            payload = self._payloads[-1]
        else:
            payload = self._payloads[self.calls]
        self.calls += 1
        return CompletionResult(
            content=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            latency_ms=1.0,
            model="synthetic-static-json",
            prompt_tokens=128,
            completion_tokens=64,
            total_tokens=192,
        )
