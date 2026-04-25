"""从 LangGraph 检查点状态中抽取可展示的对话轮次（user / assistant 文本）。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from langchain_core.messages import BaseMessage


def list_checkpoint_thread_ids(sqlite_path: str, *, limit: int = 60) -> list[str]:
    """从检查点库列出最近活跃的 thread_id（按 checkpoints.rowid 近似排序）。"""
    p = Path(sqlite_path)
    if not p.is_file():
        return []
    conn = sqlite3.connect(str(p))
    try:
        cur = conn.execute(
            """
            SELECT thread_id FROM checkpoints
            GROUP BY thread_id
            ORDER BY MAX(rowid) DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def preview_text_from_rows(rows: list[dict[str, str]], *, max_len: int = 96) -> str:
    """优先展示首条用户话轮，否则首条助手话轮，作列表摘要。"""
    for prefer in ("user", "assistant"):
        for r in rows:
            if r.get("role") != prefer:
                continue
            t = (r.get("content") or "").strip().replace("\n", " ")
            if not t:
                continue
            return t if len(t) <= max_len else t[: max_len - 1] + "…"
    return ""


def messages_checkpoint_to_rows(messages: list[Any] | None) -> list[dict[str, str]]:
    """把图中的 ``messages`` 列表转成 ``{role, content}``，仅保留 human/ai 文本轮次。"""
    if not messages:
        return []
    rows: list[dict[str, str]] = []
    for m in messages:
        if not isinstance(m, BaseMessage):
            continue
        mt = getattr(m, "type", None)
        if mt == "human":
            role = "user"
        elif mt == "ai":
            role = "assistant"
        else:
            continue
        c = m.content
        if isinstance(c, list):
            parts: list[str] = []
            for block in c:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                else:
                    parts.append(str(block))
            c = "".join(parts)
        elif not isinstance(c, str):
            c = str(c)
        c = (c or "").strip()
        if not c:
            continue
        rows.append({"role": role, "content": c})
    return rows
