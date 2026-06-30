"""Tests for the Soup facade, including register() source dispatch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from soup import (
    BM25Strategy,
    MarkdownContextBuilder,
    SelectionPipeline,
    Skill,
    Soup,
)
from soup.sources import remote
from soup.strategies.base import SelectionStrategy


class _SelectByName(SelectionStrategy):
    def __init__(self, *names: str) -> None:
        self._names = set(names)

    def select(self, query: str, skills: list[Skill]) -> list[Skill]:
        _ = query
        return [s for s in skills if s.name in self._names]


def _write_skill(root: Path, name: str, *, body: str = "Do the thing.", extra: str = "") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = f"name: {name}\ndescription: A {name} skill. Use for {name} tasks.\n{extra}"
    (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}---\n\n{body}\n", encoding="utf-8")
    return skill_dir


# -- code-defined & instance registration ----------------------------------


def test_register_with_kwargs() -> None:
    soup = Soup()
    s = soup.register(name="frontend", description="Frontend. Use for UI.", instructions="React.")
    assert isinstance(s, Skill)
    assert s.name == "frontend"
    assert soup.get("frontend") is s


def test_register_kwargs_requires_description() -> None:
    soup = Soup()
    with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError
        soup.register(name="frontend", instructions="React.")  # type: ignore[call-overload]


def test_register_with_instance() -> None:
    soup = Soup()
    s = Skill(name="x", description="d", instructions="i")
    assert soup.register(s) is s
    assert soup.get("x") == s


def test_register_instance_and_fields_conflict() -> None:
    soup = Soup()
    with pytest.raises(ValueError, match="not both"):
        soup.register(Skill(name="x", description="d", instructions="i"), name="y")  # type: ignore[call-overload]


def test_register_metadata_none_is_dropped() -> None:
    soup = Soup()
    s = soup.register(name="x", description="d", instructions="i", metadata=None)
    assert isinstance(s, Skill)
    assert s.metadata == {}


def test_register_many_and_unregister() -> None:
    soup = Soup()
    soup.register_many(
        [
            Skill(name="a", description="d", instructions="i"),
            Skill(name="b", description="d", instructions="i"),
        ]
    )
    assert {s.name for s in soup.skills} == {"a", "b"}
    assert soup.unregister("a") is True
    assert soup.unregister("a") is False


# -- local source dispatch --------------------------------------------------


def test_register_single_skill_dir(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path, "pdf-processing")
    soup = Soup()
    s = soup.register(str(skill_dir))
    assert isinstance(s, Skill)
    assert s.name == "pdf-processing"
    assert soup.get("pdf-processing") is not None


def test_register_single_skill_dir_with_overrides(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path, "pdf-processing")
    soup = Soup()
    s = soup.register(skill_dir, dependencies=["files"], version="1.0", priority=10)
    assert isinstance(s, Skill)
    assert s.dependencies == ("files",)
    assert s.version == "1.0"
    assert s.priority == 10


def test_register_skills_collection(tmp_path: Path) -> None:
    _write_skill(tmp_path, "pdf-processing")
    _write_skill(tmp_path, "data-analysis")
    (tmp_path / "not-a-skill").mkdir()
    soup = Soup()
    out = soup.register(str(tmp_path))
    assert isinstance(out, list)
    assert {s.name for s in out} == {"pdf-processing", "data-analysis"}


def test_register_collection_with_options(tmp_path: Path) -> None:
    _write_skill(tmp_path, "pdf-processing")
    _write_skill(tmp_path, "data-analysis")
    soup = Soup()
    out = soup.register(
        str(tmp_path),
        options={
            "pdf-processing": {"dependencies": ["files"], "priority": 10},
            "data-analysis": {"version": "2.1"},
        },
    )
    by_name = {s.name: s for s in out}
    assert by_name["pdf-processing"].dependencies == ("files",)
    assert by_name["pdf-processing"].priority == 10
    assert by_name["data-analysis"].version == "2.1"


def test_register_collection_rejects_plain_overrides(tmp_path: Path) -> None:
    _write_skill(tmp_path, "pdf-processing")
    _write_skill(tmp_path, "data-analysis")
    soup = Soup()
    with pytest.raises(ValueError, match="options"):
        soup.register(str(tmp_path), priority=10)


# -- remote source dispatch (HTTP mocked) -----------------------------------


def _github_responses() -> dict[str, str]:
    contents = json.dumps(
        [
            {"name": "pdf-processing", "type": "dir"},
            {"name": "README.md", "type": "file"},
        ]
    )
    skill_md = (
        "---\n"
        "name: pdf-processing\n"
        "description: Extract PDF text. Use for PDF tasks.\n"
        "---\n\nUse pypdf.\n"
    )
    return {
        "https://api.github.com/repos/vercel-labs/skills/contents/skills?ref=main": contents,
        "https://raw.githubusercontent.com/vercel-labs/skills/main/skills/pdf-processing/SKILL.md": skill_md,  # noqa: E501
    }


def test_register_github_url(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = _github_responses()
    monkeypatch.setattr(remote, "_http_get", lambda url: responses[url])
    soup = Soup()
    out = soup.register("https://github.com/vercel-labs/skills", ref="main")
    assert isinstance(out, list)
    assert [s.name for s in out] == ["pdf-processing"]
    assert soup.get("pdf-processing") is not None


def test_register_github_url_with_options(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = _github_responses()
    monkeypatch.setattr(remote, "_http_get", lambda url: responses[url])
    soup = Soup()
    out = soup.register(
        "https://github.com/vercel-labs/skills",
        ref="main",
        options={"pdf-processing": {"priority": 5}},
    )
    assert out[0].priority == 5


def test_register_gitlab_url(monkeypatch: pytest.MonkeyPatch) -> None:
    tree = json.dumps([{"name": "data-analysis", "type": "tree"}, {"name": "x", "type": "blob"}])
    skill_md = (
        "---\nname: data-analysis\ndescription: Analyze data. Use for data.\n---\n\nUse pandas.\n"
    )
    responses = {
        "https://gitlab.com/api/v4/projects/group%2Fproject/repository/tree?path=skills&ref=main&per_page=100": tree,  # noqa: E501
        "https://gitlab.com/group/project/-/raw/main/skills/data-analysis/SKILL.md": skill_md,
    }
    monkeypatch.setattr(remote, "_http_get", lambda url: responses[url])
    soup = Soup()
    out = soup.register("https://gitlab.com/group/project", ref="main")
    assert [s.name for s in out] == ["data-analysis"]


def test_register_remote_rejects_plain_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(remote, "_http_get", lambda url: "[]")
    soup = Soup()
    with pytest.raises(ValueError, match="options"):
        soup.register("https://github.com/vercel-labs/skills", priority=10)


# -- selection & rendering --------------------------------------------------


def test_prepare_string_injects_relevant_only() -> None:
    soup = Soup(strategies=[BM25Strategy(min_score=0.0)])
    soup.register(name="frontend", description="d", instructions="Use React 19.", tags=["react"])
    soup.register(name="sql", description="d", instructions="Use indexes.", tags=["database"])
    out = soup.prepare("help with my react component")
    assert "Use React 19." in out
    assert "Use indexes." not in out


def test_prepare_messages_returns_messages() -> None:
    soup = Soup(strategies=[BM25Strategy(min_score=0.0)])
    soup.register(name="frontend", description="d", instructions="Use React 19.", tags=["react"])
    out = soup.prepare([{"role": "user", "content": "react please"}])
    assert isinstance(out, list)
    assert out[0]["role"] == "system"
    assert "Use React 19." in out[0]["content"]


def test_prepare_no_match_is_passthrough() -> None:
    soup = Soup(strategies=[BM25Strategy(min_score=0.0)])
    soup.register(name="frontend", description="d", instructions="Use React 19.", tags=["react"])
    assert soup.prepare("completely unrelated topic") == "completely unrelated topic"


def test_prepare_resolves_extends() -> None:
    soup = Soup(strategies=[BM25Strategy(min_score=0.0)])
    soup.register(name="frontend", description="d", instructions="Accessibility first.")
    soup.register(
        name="react",
        description="d",
        instructions="Use hooks.",
        tags=["react"],
        extends=["frontend"],
    )
    out = soup.prepare("a react question")
    assert "Accessibility first." in out
    assert "Use hooks." in out
    assert out.index("Accessibility first.") < out.index("Use hooks.")


def test_select_orders_by_priority() -> None:
    # Use zero threshold so this test only exercises priority ordering.
    soup = Soup(strategies=[BM25Strategy(min_score=0.0)])
    soup.register(name="low", description="d", instructions="i", tags=["x"], priority=1)
    soup.register(name="high", description="d", instructions="i", tags=["x"], priority=10)
    selected = soup.select("x")
    assert [s.name for s in selected] == ["high", "low"]


def test_add_strategy() -> None:
    soup = Soup(strategies=[])
    soup.register(name="frontend", description="d", instructions="i", tags=["react"])
    assert soup.select("react") == []
    soup.add_strategy(_SelectByName("frontend"))
    assert [s.name for s in soup.select("react")] == ["frontend"]


def test_custom_pipeline() -> None:
    pipeline = SelectionPipeline([_SelectByName("frontend")])
    soup = Soup(pipeline=pipeline)
    soup.register(name="frontend", description="d", instructions="i", tags=["react"])
    assert [s.name for s in soup.select("react")] == ["frontend"]


def test_custom_builder() -> None:
    soup = Soup(
        strategies=[BM25Strategy(min_score=0.0)],
        builder=MarkdownContextBuilder(heading_level=2),
    )
    soup.register(name="frontend", description="d", instructions="Use React.", tags=["react"])
    out = soup.build_context("react")
    assert out.startswith("## Frontend")


def test_custom_strategy_integration() -> None:
    soup = Soup(strategies=[_SelectByName("frontend")])
    soup.register(name="frontend", description="d", instructions="Use React.")
    soup.register(name="sql", description="d", instructions="Use indexes.")
    out = soup.build_context("anything")
    assert "Use React." in out
    assert "Use indexes." not in out


def test_strict_dependencies_default_raises_on_prepare() -> None:
    from soup import MissingDependencyError

    soup = Soup(strategies=[BM25Strategy(min_score=0.0)])
    soup.register(
        name="frontend", description="d", instructions="i", tags=["react"], dependencies=["ghost"]
    )
    with pytest.raises(MissingDependencyError):
        soup.prepare("react")


def test_non_strict_dependencies() -> None:
    soup = Soup(strategies=[BM25Strategy(min_score=0.0)], strict_dependencies=False)
    soup.register(
        name="frontend",
        description="d",
        instructions="Use React.",
        tags=["react"],
        dependencies=["ghost"],
    )
    out = soup.prepare("react")
    assert "Use React." in out
