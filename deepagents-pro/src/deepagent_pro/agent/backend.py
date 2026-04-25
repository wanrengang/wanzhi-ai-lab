"""Deep Agents 存储后端：默认会话内虚拟文件 + 磁盘上的 Skills 库（``/skills/``）。"""

from __future__ import annotations

from pathlib import Path

from deepagents.backends import CompositeBackend, FilesystemBackend, LocalShellBackend, StateBackend
from deepagents.backends.protocol import BackendProtocol

from deepagent_pro.config import Settings


def build_deepagent_backend(settings: Settings) -> BackendProtocol:
    """构建 Deep Agents backend。

    - 默认使用 ``StateBackend``（会话内虚拟文件，不可执行 shell 命令）
    - 当 ``shell_enabled=True`` 时，改用 ``LocalShellBackend``（提供 `execute` 能力）
    - 当 ``skills_enabled=True`` 时，将 ``/skills/`` 路由到磁盘目录 ``skills_root_dir``
    """

    default_backend: BackendProtocol
    if settings.shell_enabled:
        default_backend = LocalShellBackend(
            root_dir=str(Path(settings.shell_root_dir).resolve()),
            virtual_mode=True,
        )
    else:
        default_backend = StateBackend()

    if not settings.skills_enabled:
        return default_backend

    root = Path(settings.skills_root_dir).resolve()
    (root / "bundled").mkdir(parents=True, exist_ok=True)
    (root / "project").mkdir(parents=True, exist_ok=True)

    skills_fs = FilesystemBackend(
        root_dir=str(root),
        virtual_mode=True,
    )
    return CompositeBackend(
        default=default_backend,
        routes={"/skills/": skills_fs},
    )


def parse_skills_sources(settings: Settings) -> list[str] | None:
    """解析 ``skills_sources``；未启用或未配置时返回 ``None``（不传 ``skills=`` 给 SDK）。"""
    if not settings.skills_enabled:
        return None
    raw = (settings.skills_sources or "").strip()
    if not raw:
        return ["/skills/bundled/", "/skills/project/", "/skills/"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["/skills/bundled/", "/skills/project/", "/skills/"]
