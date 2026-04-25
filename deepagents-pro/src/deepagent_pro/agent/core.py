"""主智能体创建 - Deep Agents SDK 封装"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from deepagents import create_deep_agent

from deepagent_pro.config import get_settings
from deepagent_pro.agent.backend import build_deepagent_backend, parse_skills_sources
from deepagent_pro.agent.prompts import MAIN_AGENT_PROMPT
from deepagent_pro.agent.subagents import ALL_SUBAGENTS
from deepagent_pro.tools.data_loader import load_csv, load_excel, list_excel_sheets, clean_data
from deepagent_pro.tools.data_analysis import (
    describe_data,
    correlation_analysis,
    group_analysis,
    value_counts,
    filter_data,
)
from deepagent_pro.tools.visualization import create_chart, create_heatmap
from deepagent_pro.tools.sql_query import execute_sql, list_tables, describe_table
from deepagent_pro.tools.external_api import http_get, http_post
from deepagent_pro.tools.github_info import github_repo_info
from deepagent_pro.tools.web_search import web_search
from deepagent_pro.tools.browser import browser_use
from deepagent_pro.tools.current_time import get_current_time, set_user_timezone
from deepagent_pro.tools.datasource import list_datasources, get_datasource_url
from deepagent_pro.tools.sql_visualization import sql_to_chart


MAIN_TOOLS = [
    load_csv,
    load_excel,
    list_excel_sheets,
    clean_data,
    describe_data,
    correlation_analysis,
    group_analysis,
    value_counts,
    filter_data,
    create_chart,
    create_heatmap,
    execute_sql,
    list_tables,
    describe_table,
    http_get,
    http_post,
    github_repo_info,
    web_search,
    browser_use,
    get_current_time,
    set_user_timezone,
    list_datasources,
    get_datasource_url,
    sql_to_chart,
]


def build_model() -> ChatOpenAI:
    """构建 MiniMax LLM 实例（通过 OpenAI 兼容接口）"""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.minimax_model,
        openai_api_key=settings.minimax_api_key,
        openai_api_base=settings.minimax_base_url,
        temperature=0.3,
        max_retries=3,
        request_timeout=120,
    )


def _build_checkpointer() -> SqliteSaver:
    """磁盘 SQLite 检查点：同一 thread_id 跨请求、跨进程重启保留对话状态。"""
    settings = get_settings()
    path = Path(settings.checkpoint_sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    return SqliteSaver(conn)


def create_analysis_agent():
    """创建数据分析智能体。

    使用 SqliteSaver 持久化检查点：同一 ``thread_id`` 多轮合并，且**重启服务**后仍可续聊
    （见 ``checkpoint_sqlite_path``）。若需仅内存可改为 MemorySaver。
    """
    model = build_model()
    checkpointer = _build_checkpointer()
    settings = get_settings()
    backend = build_deepagent_backend(settings)
    skills_sources = parse_skills_sources(settings)

    agent = create_deep_agent(
        name="deepagent-pro",
        model=model,
        tools=MAIN_TOOLS,
        system_prompt=MAIN_AGENT_PROMPT,
        subagents=ALL_SUBAGENTS,
        checkpointer=checkpointer,
        backend=backend,
        skills=skills_sources,
    )

    return agent
