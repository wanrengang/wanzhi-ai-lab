"""数据源查询工具 - 让 Agent 能获取已注册的数据源信息"""

from __future__ import annotations

from typing import Any
from langchain.tools import tool


def get_registered_datasources() -> dict[str, dict[str, str]]:
    """从 API deps 获取已注册的数据源字典"""
    from deepagent_pro.api.deps import get_datasources
    return get_datasources()


@tool
def list_datasources() -> str:
    """列出所有已注册的数据源及其连接字符串。

    使用场景：
    - 用户询问有哪些可用的数据库时
    - 在执行 SQL 查询前需要确认数据源名称时

    Returns:
        数据源列表的字符串描述
    """
    datasources = get_registered_datasources()

    if not datasources:
        return "当前没有注册任何数据源。请先通过 POST /api/v1/datasource 注册数据源。"

    lines = ["已注册的数据源列表：\n"]
    for name, info in datasources.items():
        lines.append(f"  名称: {name}")
        lines.append(f"  连接: {info.get('connection_url', 'N/A')}")
        lines.append(f"  描述: {info.get('description', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


@tool
def get_datasource_url(name: str) -> str:
    """获取指定数据源的连接字符串。

    Args:
        name: 数据源名称

    Returns:
        数据源的连接字符串，如果不存在则返回错误提示
    """
    datasources = get_registered_datasources()

    if name not in datasources:
        available = ", ".join(datasources.keys())
        return f"数据源 '{name}' 不存在。可用的数据源: {available or '(无)'}"

    return datasources[name].get("connection_url", "")
