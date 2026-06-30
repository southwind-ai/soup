"""The public :class:`Soup` facade tying the components together."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, overload

from soup.builders.base import ContextBuilder
from soup.builders.markdown import MarkdownContextBuilder
from soup.core.messages import Messages, extract_query, inject_context
from soup.core.pipeline import SelectionPipeline
from soup.core.resolver import DependencyResolver
from soup.models.skill import Skill
from soup.sources.local import is_skill_dir, load_skill_dir, load_skills_collection
from soup.sources.remote import is_remote_url, load_remote
from soup.storage.base import SkillStorage
from soup.storage.memory import InMemoryStorage
from soup.strategies.base import SelectionStrategy
from soup.strategies.bm25 import BM25Strategy


class Soup:
    """A provider-agnostic Agent Skills router for LLMs.

    Register many small skills -- defined in code or loaded from ``SKILL.md``
    files (locally or from a GitHub/GitLab repo) -- then call :meth:`prepare` on
    whatever you already send to your LLM; Soup injects only the relevant skill
    instructions.

    All collaborators are injected and default to sensible implementations, so
    the zero-config path just works while every part stays replaceable::

        soup = Soup()
        soup.register(
            name="frontend",
            description="Frontend guidance. Use for UI work.",
            instructions="Use React 19.",
        )
        messages = soup.prepare(user_messages)

    Args:
        storage: Backend holding the skills. Defaults to in-memory.
        pipeline: A pre-built selection pipeline. If omitted, one is created
            from ``strategies``.
        strategies: Strategies for the default pipeline. Defaults to a BM25
            strategy. Ignored if ``pipeline`` is given.
        builder: Renders selected skills. Defaults to Markdown.
        strict_dependencies: Raise if a skill references an unknown one.
        system_role: Role used when injecting context into chat messages.
    """

    def __init__(
        self,
        *,
        storage: SkillStorage | None = None,
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
    def register(self, skill: Skill, /) -> Skill: ...

    @overload
    def register(
        self,
        *,
        name: str,
        description: str,
        instructions: str,
        license: str | None = ...,
        compatibility: str | None = ...,
        allowed_tools: Sequence[str] | str = ...,
        metadata: Mapping[str, Any] | None = ...,
        tags: Sequence[str] | str = ...,
        examples: Sequence[str] | str = ...,
        priority: int = ...,
        dependencies: Sequence[str] | str = ...,
        extends: Sequence[str] | str = ...,
        version: str | None = ...,
    ) -> Skill: ...

    @overload
    def register(
        self,
        source: str | Path,
        /,
        *,
        ref: str | None = ...,
        options: Mapping[str, Mapping[str, Any]] | None = ...,
        version: str | None = ...,
        priority: int = ...,
        tags: Sequence[str] | str = ...,
        examples: Sequence[str] | str = ...,
        dependencies: Sequence[str] | str = ...,
        extends: Sequence[str] | str = ...,
        license: str | None = ...,
        compatibility: str | None = ...,
        allowed_tools: Sequence[str] | str = ...,
        metadata: Mapping[str, Any] | None = ...,
    ) -> Skill | list[Skill]: ...

    def register(
        self,
        source: Skill | str | Path | None = None,
        *,
        ref: str | None = None,
        options: Mapping[str, Mapping[str, Any]] | None = None,
        **fields: Any,
    ) -> Skill | list[Skill]:
        """Register one or more skills, dispatching on the shape of ``source``.

        The single entry point handles every supported source:

        * **Keyword fields** (no ``source``) define a skill in code; ``name``,
          ``description`` and ``instructions`` are required::

              soup.register(name="pdf", description="...", instructions="...")

        * **A :class:`Skill` instance** is registered as-is.
        * **A local skill directory** (contains ``SKILL.md``) loads one skill;
          extra keyword fields override its ``metadata``::

              soup.register("./skills/pdf-processing", dependencies=["files"])

        * **A local skills collection** (a folder of skill directories) loads
          all of them; use ``options`` for per-skill overrides::

              soup.register("./skills", options={"pdf-processing": {"priority": 10}})

        * **A GitHub/GitLab repository URL** loads skills from ``/skills``;
          pick a branch/tag/commit with ``ref`` and override with ``options``::

              soup.register("https://github.com/vercel-labs/skills", ref="main")

        Returns:
            The registered skill (single sources) or the list of registered
            skills (collections and remote repositories).

        Raises:
            ValueError: If incompatible arguments are combined.
        """
        if isinstance(source, Skill):
            if fields or ref is not None or options is not None:
                msg = "Pass either a Skill instance or keyword fields, not both"
                raise ValueError(msg)
            self._storage.add(source)
            return source

        if source is None:
            if ref is not None or options is not None:
                msg = "'ref' and 'options' are only valid when loading from a source"
                raise ValueError(msg)
            if fields.get("metadata") is None:
                fields.pop("metadata", None)
            skill = Skill(**fields)
            self._storage.add(skill)
            return skill

        return self._register_from_source(source, ref=ref, options=options, overrides=fields)

    def _register_from_source(
        self,
        source: str | Path,
        *,
        ref: str | None,
        options: Mapping[str, Mapping[str, Any]] | None,
        overrides: dict[str, Any],
    ) -> Skill | list[Skill]:
        normalized_options = {k: dict(v) for k, v in options.items()} if options else None

        if isinstance(source, str) and is_remote_url(source):
            self._reject_overrides(overrides, "a remote repository")
            skills = load_remote(source, ref=ref, options=normalized_options)
            return self._add_many(skills)

        path = Path(source)
        if is_skill_dir(path):
            skill = load_skill_dir(path, overrides=overrides or None)
            self._storage.add(skill)
            return skill

        self._reject_overrides(overrides, "a skills collection")
        skills = load_skills_collection(path, options=normalized_options)
        return self._add_many(skills)

    @staticmethod
    def _reject_overrides(overrides: dict[str, Any], source_kind: str) -> None:
        if overrides:
            msg = (
                f"Per-skill keyword overrides are not valid for {source_kind}; "
                "use 'options={skill_name: {...}}' instead"
            )
            raise ValueError(msg)

    def _add_many(self, skills: list[Skill]) -> list[Skill]:
        for skill in skills:
            self._storage.add(skill)
        return skills

    def register_many(self, skills: Iterable[Skill]) -> None:
        """Register every skill in ``skills``."""
        for skill in skills:
            self._storage.add(skill)

    def unregister(self, name: str) -> bool:
        """Remove a skill by name; return whether it existed."""
        return self._storage.remove(name)

    def get(self, name: str) -> Skill | None:
        """Return a registered skill by name, or ``None``."""
        return self._storage.get(name)

    @property
    def skills(self) -> list[Skill]:
        """All registered skills."""
        return self._storage.all()

    # -- configuration ----------------------------------------------------

    def add_strategy(self, strategy: SelectionStrategy) -> None:
        """Append a selection strategy to the pipeline."""
        self._pipeline.add(strategy)

    # -- selection & rendering -------------------------------------------

    def select(self, query: str) -> list[Skill]:
        """Select and dependency-resolve the skills relevant to ``query``."""
        chosen = self._pipeline.select(query, self._storage.all())
        chosen.sort(key=lambda s: s.priority, reverse=True)
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
