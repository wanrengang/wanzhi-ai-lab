"""Deep Agents backend / skills 路径装配。"""

from deepagents.backends import CompositeBackend, StateBackend
from pydantic_settings import BaseSettings, SettingsConfigDict

from deepagent_pro.agent.backend import build_deepagent_backend, parse_skills_sources


class _S(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    skills_enabled: bool = True
    skills_root_dir: str = "./skills"
    skills_sources: str = "/skills/bundled/,/skills/project/,/skills/"
    shell_enabled: bool = False
    shell_root_dir: str = "."


def test_parse_skills_sources_whitespace_falls_back_to_defaults():
    s = _S.model_construct(skills_enabled=True, skills_sources="   ")
    assert parse_skills_sources(s) == ["/skills/bundled/", "/skills/project/", "/skills/"]


def test_parse_skills_sources_custom():
    s = _S(skills_sources="/skills/project/")
    assert parse_skills_sources(s) == ["/skills/project/"]


def test_parse_skills_disabled():
    s = _S(skills_enabled=False)
    assert parse_skills_sources(s) is None


def test_build_backend_disabled():
    s = _S(skills_enabled=False)
    b = build_deepagent_backend(s)
    assert isinstance(b, StateBackend)


def test_build_backend_lists_skill_dir(tmp_path, monkeypatch):
    root = tmp_path / "sk"
    (root / "bundled" / "demo-skill").mkdir(parents=True)
    (root / "bundled" / "demo-skill" / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Test skill for backend ls.\n---\n\n# Demo\n",
        encoding="utf-8",
    )
    (root / "project").mkdir(exist_ok=True)

    s = _S(skills_root_dir=str(root))
    backend = build_deepagent_backend(s)
    assert isinstance(backend, CompositeBackend)
    ls = backend.ls("/skills/bundled/")
    assert not ls.error
    names = {e["path"].rstrip("/").split("/")[-1] for e in (ls.entries or []) if e.get("is_dir")}
    assert "demo-skill" in names
