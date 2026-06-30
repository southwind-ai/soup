"""Selection strategy interface.

A strategy is a pure function of *(query, candidates) -> selected*. Strategies
are deliberately tiny and composable; the :class:`SelectionPipeline` chains them
together. This is the Open/Closed extension point of Soup -- add new behavior by
adding a strategy, never by editing the core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from soup.models.skill import Skill


class SelectionStrategy(ABC):
    """Selects the skills relevant to a request.

    Implementations must be side-effect free and must not mutate their inputs.
    """

    @abstractmethod
    def select(self, query: str, skills: list[Skill]) -> list[Skill]:
        """Return the subset of ``skills`` relevant to ``query``.

        Args:
            query: The user request text driving the selection.
            skills: The candidate skills to choose from.

        Returns:
            The selected skills (a subset of ``skills``).
        """
