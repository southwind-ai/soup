"""In-memory storage backend (the default)."""

from __future__ import annotations

from soup.models.harness import Harness
from soup.storage.base import HarnessStorage


class InMemoryStorage(HarnessStorage):
    """Stores harnesses in a plain dict, keyed by name.

    Insertion order is preserved, which gives deterministic output for
    harnesses that are otherwise equal in priority.
    """

    def __init__(self) -> None:
        self._harnesses: dict[str, Harness] = {}

    def add(self, harness: Harness) -> None:
        self._harnesses[harness.name] = harness

    def get(self, name: str) -> Harness | None:
        return self._harnesses.get(name)

    def remove(self, name: str) -> bool:
        return self._harnesses.pop(name, None) is not None

    def all(self) -> list[Harness]:
        return list(self._harnesses.values())

    def clear(self) -> None:
        self._harnesses.clear()
