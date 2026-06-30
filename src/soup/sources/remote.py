"""Loading skills from a remote GitHub or GitLab repository over raw HTTP.

No ``git`` dependency is required: the repository's host API is used to list the
skill directories under ``/skills`` and each ``SKILL.md`` is then fetched from
the host's raw-content endpoint. The default on-disk convention is
``/skills/<skill>/SKILL.md`` and a branch/tag/commit may be chosen with ``ref``.

All network access funnels through :func:`_http_get`, which tests patch so the
suite never touches the network.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from soup.core.exceptions import SkillSourceError
from soup.models.skill import Skill
from soup.sources.skill_md import parse_skill_md

DEFAULT_REF = "main"
DEFAULT_SKILLS_PATH = "skills"

_USER_AGENT = "soup-ai"


def _http_get(url: str) -> str:
    """Fetch ``url`` over HTTP(S) and return the body as text.

    This is the single network seam; tests patch it to avoid real requests.
    """
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body: bytes = response.read()
    except urllib.error.URLError as exc:  # pragma: no cover - network failure path
        msg = f"Failed to fetch {url}: {exc}"
        raise SkillSourceError(msg) from exc
    return body.decode(charset)


@dataclass(frozen=True)
class _Repo:
    host: str
    owner_path: str  # e.g. "owner/repo" or "group/subgroup/project"
    base_path: str = ""  # optional repo-relative subpath encoded in the URL


def _parse_repo_url(url: str) -> _Repo:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    if not host or not path:
        msg = f"Unsupported repository URL: {url!r}"
        raise SkillSourceError(msg)
    parts = [segment for segment in path.split("/") if segment]
    if "github.com" in host:
        # GitHub repository URLs are always owner/repo with an optional subpath.
        if len(parts) < 2:
            msg = f"Unsupported repository URL: {url!r}"
            raise SkillSourceError(msg)
        owner_path = f"{parts[0]}/{parts[1]}"
        base_path = "/".join(parts[2:])
        return _Repo(host=host, owner_path=owner_path, base_path=base_path)
    if "/" not in path:
        msg = f"Unsupported repository URL: {url!r}"
        raise SkillSourceError(msg)
    # For GitLab and other hosts we keep the current interpretation: the full
    # path identifies the project. (Subpath-in-URL parsing is only added for
    # GitHub, where owner/repo boundaries are unambiguous.)
    return _Repo(host=host, owner_path=path)


def is_remote_url(source: str) -> bool:
    """Return whether ``source`` is an ``http(s)://`` URL."""
    return source.startswith(("http://", "https://"))


def load_remote(
    url: str,
    *,
    ref: str | None = None,
    skills_path: str = DEFAULT_SKILLS_PATH,
    options: dict[str, dict[str, Any]] | None = None,
) -> list[Skill]:
    """Load every skill under ``/<skills_path>`` of a remote repository.

    Args:
        url: A GitHub or GitLab repository URL.
        ref: Branch, tag or commit to read from. Defaults to ``"main"``.
        skills_path: Repository-relative folder holding the skill directories.
        options: Per-skill Soup field overrides keyed by skill name.

    Returns:
        The loaded skills in sorted name order (deterministic).

    Raises:
        SkillSourceError: For unsupported hosts or when no skills are found.
    """
    repo = _parse_repo_url(url)
    ref = ref or DEFAULT_REF
    options = options or {}
    effective_skills_path = _resolve_skills_path(repo, skills_path)

    if "github.com" in repo.host:
        names = _list_github(repo, ref, effective_skills_path)
        raw = _github_raw
    elif "gitlab.com" in repo.host or "gitlab" in repo.host:
        names = _list_gitlab(repo, ref, effective_skills_path)
        raw = _gitlab_raw
    else:
        msg = f"Unsupported host {repo.host!r}; only GitHub and GitLab are supported"
        raise SkillSourceError(msg)

    skills: list[Skill] = []
    for name in sorted(names):
        raw_url = raw(repo, ref, f"{effective_skills_path}/{name}/SKILL.md")
        text = _http_get(raw_url)
        skills.append(parse_skill_md(text, dir_name=name, overrides=options.get(name)))

    if not skills:
        msg = f"No skills found under {effective_skills_path!r} in {url}"
        raise SkillSourceError(msg)
    return skills


def _resolve_skills_path(repo: _Repo, skills_path: str) -> str:
    """Resolve the effective skills folder, honoring GitHub URL subpaths.

    Example:
        ``https://github.com/org/repo/skills`` + default ``skills_path='skills'``
        resolves to ``skills`` (not ``skills/skills``).
    """
    if not repo.base_path:
        return skills_path
    if skills_path == DEFAULT_SKILLS_PATH:
        return repo.base_path
    return f"{repo.base_path.rstrip('/')}/{skills_path.lstrip('/')}"


# -- GitHub -----------------------------------------------------------------


def _list_github(repo: _Repo, ref: str, skills_path: str) -> list[str]:
    api = (
        f"https://api.github.com/repos/{repo.owner_path}/contents/"
        f"{urllib.parse.quote(skills_path)}?ref={urllib.parse.quote(ref)}"
    )
    entries = _load_json_list(api)
    return [
        str(entry["name"])
        for entry in entries
        if isinstance(entry, dict) and entry.get("type") == "dir"
    ]


def _github_raw(repo: _Repo, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo.owner_path}/{ref}/{path}"


# -- GitLab -----------------------------------------------------------------


def _list_gitlab(repo: _Repo, ref: str, skills_path: str) -> list[str]:
    encoded = urllib.parse.quote(repo.owner_path, safe="")
    api = (
        f"https://{repo.host}/api/v4/projects/{encoded}/repository/tree"
        f"?path={urllib.parse.quote(skills_path)}&ref={urllib.parse.quote(ref)}&per_page=100"
    )
    entries = _load_json_list(api)
    return [
        str(entry["name"])
        for entry in entries
        if isinstance(entry, dict) and entry.get("type") == "tree"
    ]


def _gitlab_raw(repo: _Repo, ref: str, path: str) -> str:
    return f"https://{repo.host}/{repo.owner_path}/-/raw/{ref}/{path}"


def _load_json_list(url: str) -> list[Any]:
    payload = json.loads(_http_get(url))
    if not isinstance(payload, list):
        msg = f"Expected a JSON list of entries from {url}"
        raise SkillSourceError(msg)
    return payload
