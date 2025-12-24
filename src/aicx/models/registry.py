"""Provider registry and adapter interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aicx.types import PromptRequest, Response


class ProviderAdapter(Protocol):
    name: str
    supports_json: bool

    def create_chat_completion(self, request: PromptRequest) -> Response:
        ...


@dataclass(frozen=True)
class ProviderRegistry:
    providers: dict[str, ProviderAdapter]

    def get(self, name: str) -> ProviderAdapter:
        if name not in self.providers:
            raise KeyError(f"Unknown provider: {name}")
        return self.providers[name]


def default_registry() -> ProviderRegistry:
    # TODO: register real provider adapters.
    return ProviderRegistry(providers={})
