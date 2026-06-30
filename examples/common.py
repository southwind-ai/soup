"""Shared skill definitions reused across the provider examples.

Run any example with, e.g.::

    python examples/openai_example.py
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from soup import BM25Strategy, Soup
from soup.strategies.bm25 import _content_terms


def _write_skill_md(
    root: Path,
    skill_name: str,
    *,
    description: str,
    instructions: str,
    metadata: dict[str, str] | None = None,
) -> Path:
    """Create a minimal spec-compliant ``SKILL.md`` under ``root/skill_name``."""
    skill_dir = root / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    metadata = metadata or {}
    metadata_block = ""
    if metadata:
        items = "\n".join(f"  {key}: {value!r}" for key, value in metadata.items())
        metadata_block = f"metadata:\n{items}\n"
    content = (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {description}\n"
        f"{metadata_block}"
        "---\n\n"
        f"{instructions}\n"
    )
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return skill_dir


def build_soup() -> Soup:
    """Return a :class:`Soup` pre-populated with skills registered in multiple ways."""
    soup = Soup()

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

    soup.register(
        name="nextjs",
        version="2.1",
        extends=["react"],
        description="Next.js app-router conventions.",
        tags=["nextjs", "next", "ssr"],
        instructions="Use the App Router and Server Components by default.",
        priority=30,
    )

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

    with TemporaryDirectory(prefix="soup-example-") as tmp:
        temp_root = Path(tmp)
        markdown_skill = _write_skill_md(
            temp_root,
            "markdown-writing",
            description="Markdown writing guidance. Use for docs and markdown tasks.",
            instructions="Use clear headings and concise sections.",
            metadata={"tags": "markdown, docs", "priority": "12"},
        )
        soup.register(markdown_skill, dependencies=["frontend"], version="1.2")

        collection_dir = temp_root / "skills"
        _write_skill_md(
            collection_dir,
            "form-handling",
            description="Form handling best practices. Use for form validation tasks.",
            instructions="Validate on both client and server.",
        )
        _write_skill_md(
            collection_dir,
            "file-uploads",
            description="File upload guidelines. Use for upload/storage tasks.",
            instructions="Enforce size and MIME checks before persistence.",
        )
        soup.register(
            collection_dir,
            options={
                "form-handling": {"dependencies": ["security"], "priority": 18},
                "file-uploads": {"tags": ["files", "uploads"], "version": "2.0"},
            },
        )

    soup.register("https://github.com/southwind-ai/use-whispers/skills", ref="main")

    return soup


def print_selection(soup: Soup, query: str) -> None:
    """Print selected skills, a compact BM25-style explanation, and exclusions."""
    selected = soup.select(query)
    selected_names = {skill.name for skill in selected}
    excluded = [skill.name for skill in soup.skills if skill.name not in selected_names]
    print(f"Query: {query}")
    if not selected:
        print("Selected skills: (none)")
        print("BM25 note: no overlapping lexical terms were found.")
        print("Excluded skills:", ", ".join(excluded) if excluded else "(none)")
        return

    print("Selected skills:", ", ".join(skill.name for skill in selected))
    # Show the BM25 score used for filtering/ranking.
    scores = {skill.name: score for skill, score in BM25Strategy().rank(query, soup.skills)}
    query_terms = set(_content_terms(query))
    print("BM25 ranking (score per selected skill):")
    for skill in selected:
        if skill.name in scores:
            searchable = "\n".join([skill.name, skill.description, *skill.tags])
            overlap = sorted(query_terms & set(_content_terms(searchable)))
            preview = ", ".join(overlap[:8]) + (", ..." if len(overlap) > 8 else "")
            print(f"- {skill.name}: score={scores[skill.name]:.2f} (matched: {preview})")
        else:
            print(f"- {skill.name}: score=  --  (included via extends/dependencies)")

    print("Excluded skills:", ", ".join(excluded) if excluded else "(none)")


if __name__ == "__main__":
    soup = build_soup()
    print_selection(soup, "Help me build a Next.js page with a form")
    print("\n" + "=" * 60 + "\n")
    print_selection(soup, "Write a SQL query to fetch users")
    print("\n" + "=" * 60 + "\n")
    print_selection(soup, "Write this in markdown and bold: Hello World")
    print("\n" + "=" * 60 + "\n")
    print_selection(soup, "Create a Whispers dashboard")
