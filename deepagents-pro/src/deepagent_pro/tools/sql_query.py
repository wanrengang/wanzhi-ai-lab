"""SQL 查询工具 - 数据库交互"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, inspect, text
from langchain.tools import tool


_engines: dict[str, Any] = {}


def get_engine(connection_url: str):
    if connection_url not in _engines:
        _engines[connection_url] = create_engine(connection_url)
    return _engines[connection_url]


@tool
def execute_sql(connection_url: str, query: str, max_rows: int = 100) -> str:
    """在数据库上执行 SQL 查询并返回结果。

    Args:
        connection_url: SQLAlchemy 连接字符串，例如 "sqlite:///data.db" 或 "postgresql://user:pass@host/db"
        query: 要执行的 SQL 查询语句
        max_rows: 最大返回行数
    """
    try:
        engine = get_engine(connection_url)
        with engine.connect() as conn:
            result = conn.execute(text(query))

            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchmany(max_rows)]
                total = len(rows)

                if not rows:
                    return "查询成功，但没有返回数据。"

                header = " | ".join(columns)
                separator = " | ".join(["---"] * len(columns))
                lines = [header, separator]
                for row in rows[:50]:
                    lines.append(" | ".join(str(row.get(c, "")) for c in columns))

                return (
                    f"查询成功，返回 {total} 行 (最多显示 50 行)\n\n"
                    + "\n".join(lines)
                )
            else:
                conn.commit()
                return f"SQL 执行成功，影响 {result.rowcount} 行。"
    except Exception as e:
        return f"SQL 执行失败: {e}"


@tool
def list_tables(connection_url: str) -> str:
    """列出数据库中所有表名。

    Args:
        connection_url: SQLAlchemy 连接字符串
    """
    try:
        engine = get_engine(connection_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if not tables:
            return "数据库中没有找到任何表。"
        return "数据库表列表:\n" + "\n".join(f"  - {t}" for t in tables)
    except Exception as e:
        return f"获取表列表失败: {e}"


@tool
def describe_table(connection_url: str, table_name: str) -> str:
    """描述数据库表的结构（列名、类型、是否可空等）。

    Args:
        connection_url: SQLAlchemy 连接字符串
        table_name: 表名
    """
    try:
        engine = get_engine(connection_url)
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        if not columns:
            return f"表 '{table_name}' 不存在或没有列。"

        lines = [f"=== 表结构: {table_name} ==="]
        lines.append(f"{'列名':<25} {'类型':<20} {'可空':<8} {'默认值'}")
        lines.append("-" * 70)
        for col in columns:
            nullable = "是" if col.get("nullable", True) else "否"
            default = str(col.get("default", "")) or "-"
            lines.append(f"{col['name']:<25} {str(col['type']):<20} {nullable:<8} {default}")

        pk = inspector.get_pk_constraint(table_name)
        if pk and pk.get("constrained_columns"):
            lines.append(f"\n主键: {', '.join(pk['constrained_columns'])}")

        indexes = inspector.get_indexes(table_name)
        if indexes:
            lines.append("\n索引:")
            for idx in indexes:
                unique = " (唯一)" if idx.get("unique") else ""
                lines.append(f"  - {idx['name']}: {', '.join(idx['column_names'])}{unique}")

        return "\n".join(lines)
    except Exception as e:
        return f"获取表结构失败: {e}"
