"""Storage backends for harnesses."""

from soup.storage.base import HarnessStorage
from soup.storage.memory import InMemoryStorage

__all__ = ["HarnessStorage", "InMemoryStorage"]
