"""FastAPI 依赖注入"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from deepagent_pro.agent.core import create_analysis_agent
from deepagent_pro.config import get_settings

logger = logging.getLogger(__name__)


_agent_instance = None
_datasources: dict[str, dict[str, str]] = {}
_tasks: dict[str, dict[str, Any]] = {}


def get_agent():
    """获取智能体单例"""
    global _agent_instance
    if _agent_instance is None:
        logger.info("agent_singleton_init: creating analysis agent")
        _agent_instance = create_analysis_agent()
    return _agent_instance


def get_datasources() -> dict[str, dict[str, str]]:
    return _datasources


def get_tasks() -> dict[str, dict[str, Any]]:
    return _tasks


def new_task_id() -> str:
    return uuid.uuid4().hex[:12]
