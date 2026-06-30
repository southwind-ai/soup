"""Selection strategies."""

from soup.strategies.base import SelectionStrategy
from soup.strategies.bm25 import BM25Strategy

__all__ = [
    "BM25Strategy",
    "SelectionStrategy",
]
