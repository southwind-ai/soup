"""Exceptions raised by Soup."""

from __future__ import annotations


class SoupError(Exception):
    """Base class for all Soup errors."""


class MissingDependencyError(SoupError):
    """Raised when a harness references another that is not registered."""

    def __init__(self, harness_name: str, missing: str) -> None:
        self.harness_name = harness_name
        self.missing = missing
        super().__init__(f"Harness {harness_name!r} references unknown harness {missing!r}")
