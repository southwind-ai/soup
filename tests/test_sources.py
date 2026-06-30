"""Tests for the skill source loaders (local filesystem and remote repos)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from soup import SkillSourceError
from soup.sources import (
    is_remote_url,
    is_skill_dir,
    load_remote,
    load_skill_dir,
    load_skills_collection,
    remote,
)


def _write_skill(root: Path, name: str, extra: str = "") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    text = f"---\nname: {name}\ndescription: A {name} skill. Use for {name}.\n{extra}---\n\nBody.\n"
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
    return skill_dir


# -- local ------------------------------------------------------------------


def test_is_skill_dir(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path, "alpha")
    assert is_skill_dir(skill_dir) is True
    assert is_skill_dir(tmp_path) is False


def test_load_skill_dir(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path, "alpha")
    skill = load_skill_dir(skill_dir)
    assert skill.name == "alpha"


def test_load_skill_dir_applies_overrides(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path, "alpha")
    skill = load_skill_dir(skill_dir, overrides={"priority": 7, "tags": ["x"]})
    assert skill.priority == 7
    assert skill.tags == ("x",)


def test_load_skill_dir_not_a_skill(tmp_path: Path) -> None:
    with pytest.raises(SkillSourceError, match="not a skill directory"):
        load_skill_dir(tmp_path)


def test_load_collection(tmp_path: Path) -> None:
    _write_skill(tmp_path, "beta")
    _write_skill(tmp_path, "alpha")
    (tmp_path / "ignore-me").mkdir()
    skills = load_skills_collection(tmp_path)
    assert [s.name for s in skills] == ["alpha", "beta"]  # sorted


def test_load_collection_with_options(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha")
    skills = load_skills_collection(tmp_path, options={"alpha": {"version": "3.0"}})
    assert skills[0].version == "3.0"


def test_load_collection_empty_raises(tmp_path: Path) -> None:
    with pytest.raises(SkillSourceError, match="No skill directories"):
        load_skills_collection(tmp_path)


# -- remote -----------------------------------------------------------------


def test_is_remote_url() -> None:
    assert is_remote_url("https://github.com/a/b") is True
    assert is_remote_url("http://x") is True
    assert is_remote_url("./skills") is False


def test_load_remote_github(monkeypatch: pytest.MonkeyPatch) -> None:
    contents = json.dumps([{"name": "alpha", "type": "dir"}, {"name": "x.md", "type": "file"}])
    skill_md = "---\nname: alpha\ndescription: Alpha skill. Use it.\n---\n\nBody.\n"
    responses = {
        "https://api.github.com/repos/owner/repo/contents/skills?ref=v1.2": contents,
        "https://raw.githubusercontent.com/owner/repo/v1.2/skills/alpha/SKILL.md": skill_md,
    }
    monkeypatch.setattr(remote, "_http_get", lambda url: responses[url])
    skills = load_remote("https://github.com/owner/repo.git", ref="v1.2")
    assert [s.name for s in skills] == ["alpha"]


def test_load_remote_defaults_to_main(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake_get(url: str) -> str:
        seen.append(url)
        if "contents" in url:
            return json.dumps([{"name": "alpha", "type": "dir"}])
        return "---\nname: alpha\ndescription: Alpha skill. Use it.\n---\n\nBody.\n"

    monkeypatch.setattr(remote, "_http_get", fake_get)
    load_remote("https://github.com/owner/repo")
    assert any("ref=main" in url for url in seen)


def test_load_remote_github_with_repo_subpath(monkeypatch: pytest.MonkeyPatch) -> None:
    contents = json.dumps([{"name": "alpha", "type": "dir"}])
    skill_md = "---\nname: alpha\ndescription: Alpha skill. Use it.\n---\n\nBody.\n"
    responses = {
        "https://api.github.com/repos/owner/repo/contents/skills?ref=main": contents,
        "https://raw.githubusercontent.com/owner/repo/main/skills/alpha/SKILL.md": skill_md,
    }
    monkeypatch.setattr(remote, "_http_get", lambda url: responses[url])
    skills = load_remote("https://github.com/owner/repo/skills", ref="main")
    assert [s.name for s in skills] == ["alpha"]


def test_load_remote_unsupported_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(remote, "_http_get", lambda url: "[]")
    with pytest.raises(SkillSourceError, match="Unsupported host"):
        load_remote("https://bitbucket.org/owner/repo", ref="main")


def test_load_remote_bad_url() -> None:
    with pytest.raises(SkillSourceError, match="Unsupported repository URL"):
        load_remote("https://github.com", ref="main")
