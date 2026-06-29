"""Abstract storage interface for harnesses.

The core never talks to a concrete backend; it depends only on this protocol.
That keeps the door open for filesystem, YAML, SQL or Redis backends without
touching the core (Dependency Inversion Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from soup.models.harness import Harness


class HarnessStorage(ABC):
    """Read/write store of :class:`~soup.models.harness.Harness` objects.

    Implementations are keyed by harness name; registering a harness with an
    existing name overwrites the previous one.
    """

    @abstractmethod
    def add(self, harness: Harness) -> None:
        """Insert or replace ``harness`` in the store."""

    @abstractmethod
    def get(self, name: str) -> Harness | None:
        """Return the harness named ``name`` or ``None`` if absent."""

    @abstractmethod
    def remove(self, name: str) -> bool:
        """Delete the harness named ``name``.

        Returns:
            ``True`` if a harness was removed, ``False`` if it was not present.
        """

    @abstractmethod
    def all(self) -> list[Harness]:
        """Return every stored harness."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all harnesses."""

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.get(name) is not None

    def __iter__(self) -> Iterator[Harness]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self.all())
