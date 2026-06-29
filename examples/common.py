"""Shared harness definitions reused across the provider examples.

Run any example with, e.g.::

    python examples/openai_example.py
"""

from __future__ import annotations

from soup import Soup


def build_soup() -> Soup:
    """Return a :class:`Soup` pre-populated with a small composition hierarchy."""
    soup = Soup()

    # A general foundation harness...
    soup.register(
        name="frontend",
        description="General frontend engineering guidelines.",
        tags=["frontend", "ui", "web"],
        instructions=(
            "Prioritize accessibility (WCAG AA).\n"
            "Keep components small and composable.\n"
            "Prefer semantic HTML."
        ),
        priority=10,
    )

    # ...specialized by react, which extends frontend...
    soup.register(
        name="react",
        version="1.0",
        extends=["frontend"],
        description="React-specific rules.",
        tags=["react", "jsx", "hooks"],
        instructions=(
            "Use React 19 with function components.\nUse hooks; never class components.\n"
            "Never use CSS modules; use Tailwind."
        ),
        priority=20,
    )

    # ...and further specialized by nextjs, which extends react.
    soup.register(
        name="nextjs",
        version="2.1",
        extends=["react"],
        description="Next.js app-router conventions.",
        tags=["nextjs", "next", "ssr"],
        instructions="Use the App Router and Server Components by default.",
        priority=30,
    )

    # An unrelated backend harness with a dependency.
    soup.register(
        name="sql",
        description="Relational database guidance.",
        tags=["sql", "database", "postgres"],
        instructions="Always use parameterized queries.\nAdd indexes for frequent filters.",
        dependencies=["security"],
        priority=15,
    )
    soup.register(
        name="security",
        description="Security best practices.",
        tags=["security", "auth"],
        instructions="Never log secrets.\nValidate and sanitize all external input.",
        priority=100,
    )

    return soup


if __name__ == "__main__":
    soup = build_soup()
    print(soup.prepare("Help me build a Next.js page with a form"))
    print("\n" + "=" * 60 + "\n")
    print(soup.prepare("Write a SQL query to fetch users"))
