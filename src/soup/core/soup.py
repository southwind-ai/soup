"""The public :class:`Soup` facade tying the components together."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, overload

from soup.builders.base import ContextBuilder
from soup.builders.markdown import MarkdownContextBuilder
from soup.core.messages import Messages, extract_query, inject_context
from soup.core.pipeline import SelectionPipeline
from soup.core.resolver import DependencyResolver
from soup.models.harness import Harness
from soup.storage.base import HarnessStorage
from soup.storage.memory import InMemoryStorage
from soup.strategies.base import SelectionStrategy
from soup.strategies.bm25 import BM25Strategy


class Soup:
    """A provider-agnostic context router for LLMs.

    Register many small harnesses, then call :meth:`prepare` on whatever you
    already send to your LLM; Soup injects only the relevant context.

    All collaborators are injected and default to sensible implementations, so
    the zero-config path just works while every part stays replaceable::

        soup = Soup()
        soup.register(name="frontend", tags=["react"], instructions="Use React 19.")
        messages = soup.prepare(user_messages)

    Args:
        storage: Backend holding the harnesses. Defaults to in-memory.
        pipeline: A pre-built selection pipeline. If omitted, one is created
            from ``strategies``.
        strategies: Strategies for the default pipeline. Defaults to a BM25
            strategy. Ignored if ``pipeline`` is given.
        builder: Renders selected harnesses. Defaults to Markdown.
        strict_dependencies: Raise if a harness references an unknown one.
        system_role: Role used when injecting context into chat messages.
    """

    def __init__(
        self,
        *,
        storage: HarnessStorage | None = None,
        pipeline: SelectionPipeline | None = None,
        strategies: Sequence[SelectionStrategy] | None = None,
        builder: ContextBuilder | None = None,
        strict_dependencies: bool = True,
        system_role: str = "system",
    ) -> None:
        self._storage = storage or InMemoryStorage()
        if pipeline is not None:
            self._pipeline = pipeline
        else:
            default = strategies if strategies is not None else [BM25Strategy()]
            self._pipeline = SelectionPipeline(list(default))
        self._builder = builder or MarkdownContextBuilder()
        self._resolver = DependencyResolver(self._storage, strict=strict_dependencies)
        self._system_role = system_role

    # -- registration -----------------------------------------------------

    @overload
    def register(self, harness: Harness, /) -> Harness: ...

    @overload
    def register(
        self,
        *,
        name: str,
        instructions: str,
        description: str | None = ...,
        tags: Sequence[str] = ...,
        examples: Sequence[str] = ...,
        priority: int = ...,
        dependencies: Sequence[str] = ...,
        extends: Sequence[str] = ...,
        version: str | None = ...,
        metadata: dict[str, Any] | None = ...,
    ) -> Harness: ...

    def register(self, harness: Harness | None = None, **fields: Any) -> Harness:
        """Register a harness, from an instance or keyword fields.

        Args:
            harness: A pre-built :class:`Harness` (positional).
            **fields: Field values forwarded to :class:`Harness` if no instance
                is given.

        Returns:
            The registered harness.

        Raises:
            ValueError: If both a harness instance and fields are supplied.
        """
        if harness is not None:
            if fields:
                msg = "Pass either a Harness instance or keyword fields, not both"
                raise ValueError(msg)
            obj = harness
        else:
            if fields.get("metadata") is None:
                fields.pop("metadata", None)
            obj = Harness(**fields)
        self._storage.add(obj)
        return obj

    def register_many(self, harnesses: Iterable[Harness]) -> None:
        """Register every harness in ``harnesses``."""
        for harness in harnesses:
            self._storage.add(harness)

    def unregister(self, name: str) -> bool:
        """Remove a harness by name; return whether it existed."""
        return self._storage.remove(name)

    def get(self, name: str) -> Harness | None:
        """Return a registered harness by name, or ``None``."""
        return self._storage.get(name)

    @property
    def harnesses(self) -> list[Harness]:
        """All registered harnesses."""
        return self._storage.all()

    # -- configuration ----------------------------------------------------

    def add_strategy(self, strategy: SelectionStrategy) -> None:
        """Append a selection strategy to the pipeline."""
        self._pipeline.add(strategy)

    # -- selection & rendering -------------------------------------------

    def select(self, query: str) -> list[Harness]:
        """Select and dependency-resolve the harnesses relevant to ``query``."""
        chosen = self._pipeline.select(query, self._storage.all())
        chosen.sort(key=lambda h: h.priority, reverse=True)
        return self._resolver.resolve(chosen)

    def build_context(self, query: str) -> str:
        """Return the rendered context block for ``query`` (may be empty)."""
        return self._builder.build(self.select(query))

    # -- main entry point -------------------------------------------------

    @overload
    def prepare(self, payload: str) -> str: ...

    @overload
    def prepare(self, payload: Messages) -> Messages: ...

    def prepare(self, payload: str | Messages) -> str | Messages:
        """Inject relevant context into ``payload`` and return the same shape.

        Args:
            payload: A string prompt or a list of chat messages.

        Returns:
            A new prompt/message list with the selected context injected. The
            input is never mutated.
        """
        query = extract_query(payload)
        context = self.build_context(query)
        return inject_context(payload, context, system_role=self._system_role)
