"""Provider-agnostic AI interface.

Modules depend only on the :class:`AIProvider` protocol, never on a concrete SDK.
This keeps the "swap OpenAI ↔ Azure ↔ mock without touching modules" guarantee.

When no credentials are configured the factory returns :class:`MockProvider`,
which is deterministic (hash-seeded) so tests and offline demos are reproducible
and never make network calls.
"""

from __future__ import annotations

import hashlib
import json
import math
import textwrap
from typing import Protocol, runtime_checkable

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("engineergpt.ai")


@runtime_checkable
class AIProvider(Protocol):
    """Minimal surface every provider must implement."""

    name: str

    def complete(self, system: str, user: str, *, temperature: float = 0.2) -> str: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


# ---------------------------------------------------------------------------
# Deterministic mock — no network, reproducible, safe for CI and offline demos.
# ---------------------------------------------------------------------------
class MockProvider:
    name = "mock"

    def complete(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        # Produce a structured, plausible engineering answer echoing key inputs
        # so downstream parsing/tests remain meaningful without an LLM.
        digest = hashlib.sha256((system + user).encode()).hexdigest()[:8]
        preview = textwrap.shorten(user.replace("\n", " "), width=200, placeholder="…")
        return json.dumps(
            {
                "summary": (
                    "Deterministic mock analysis. Configure OPENAI_API_KEY for live "
                    f"model output. Input digest {digest}."
                ),
                "detail": preview,
            }
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_embedding(t) for t in texts]

    @staticmethod
    def _hash_embedding(text: str) -> list[float]:
        dims = settings.embedding_dimensions
        vec = [0.0] * dims
        for token in text.lower().split():
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)  # noqa: S324 - non-crypto use
            vec[h % dims] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


# ---------------------------------------------------------------------------
# OpenAI / Azure OpenAI provider (lazy import so mock mode has zero SDK cost).
# ---------------------------------------------------------------------------
class OpenAIProvider:
    def __init__(self, azure: bool = False) -> None:
        from openai import AzureOpenAI, OpenAI  # local import keeps mock path light

        self.name = settings.openai_chat_model
        self._chat_model = settings.openai_chat_model
        self._embed_model = settings.openai_embedding_model
        self._client: OpenAI | AzureOpenAI
        if azure:
            self._client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
        else:
            self._client = OpenAI(api_key=settings.openai_api_key)

    def complete(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        resp = self._client.chat.completions.create(
            model=self._chat_model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(model=self._embed_model, input=texts)
        return [item.embedding for item in resp.data]


def get_ai_provider() -> AIProvider:
    """Factory used as a FastAPI dependency and by services."""
    if settings.use_mock_ai:
        logger.info("ai_provider_selected", extra={"extra_fields": {"provider": "mock"}})
        return MockProvider()
    try:
        provider = OpenAIProvider(azure=settings.ai_provider == "azure")
        logger.info(
            "ai_provider_selected",
            extra={"extra_fields": {"provider": provider.name}},
        )
        return provider
    except Exception:  # pragma: no cover - defensive: never break requests on AI init
        logger.exception("ai_provider_init_failed_falling_back_to_mock")
        return MockProvider()
