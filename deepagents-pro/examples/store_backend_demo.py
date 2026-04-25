"""
StoreBackend（LangGraph Store）演示 —— 跨 thread_id 的长期「文件」记忆

与 ``StateBackend`` 不同：数据存在 **BaseStore**（本例 ``InMemoryStore``）里，由 ``namespace``
隔离；**不**跟检查点里的 thread 状态绑在同一份虚拟文件上。

适合：用户偏好、跨会话知识等（生产可换 ``PostgresStore``）。

运行::

    pip install -e .
    python examples/store_backend_demo.py

说明-only::

    python examples/store_backend_demo.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings

STORE_NS = ("demo-store", "user-1")


def build_agent():
    store = InMemoryStore()
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/store/": StoreBackend(
                store=store,
                namespace=lambda _rt: STORE_NS,
            ),
        },
    )
    agent = create_deep_agent(
        name="store-backend-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        store=store,
        backend=backend,
        system_prompt=(
            "你是 Store 演示助手，用中文简短回复。"
            "用户要求保存长期信息时，写入路径必须在 /store/ 下，例如 /store/note.txt。"
            "读取时如实返回文件内容。"
        ),
        memory=["/store/note.txt"],
    )
    return agent


def demo() -> None:
    agent = build_agent()
    cfg_a = {"configurable": {"thread_id": "store-tid-A"}}
    cfg_b = {"configurable": {"thread_id": "store-tid-B"}}

    print("\n>>> 线程 A：写入 /store/note.txt …")
    agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请写入 /store/note.txt，内容：「StoreBackend 跨线程演示」",
                }
            ]
        },
        config=cfg_a,
    )

    print("\n>>> 线程 B：读取 /store/note.txt（不同 thread_id）…")
    out = agent.invoke(
        {"messages": [{"role": "user", "content": "读取 /store/note.txt 全文"}]},
        config=cfg_b,
    )
    text = getattr(out["messages"][-1], "content", str(out["messages"][-1]))
    print("\n--- 助手回复（节选）---\n", text[:1200])
    if "StoreBackend" in text or "跨线程" in text:
        print("\n✓ 若内容正确，说明 Store 与 thread_id 解耦（同一 namespace）。")


def print_info() -> None:
    print(
        """
要点
----
• ``routes`` 里把 ``/store/`` 指到 ``StoreBackend(store=..., namespace=...)``
• ``create_deep_agent(..., store=同一 store 实例)``
• 虚拟路径前缀可改成 ``/memories/`` 等，与项目约定一致即可。
"""
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    print_info()
    if args.dry_run:
        print("已 --dry-run。\n")
        return
    if not (get_settings().minimax_api_key or "").strip():
        print("需要 MINIMAX_API_KEY。\n")
        sys.exit(1)
    demo()
    print("\n完成。\n")


if __name__ == "__main__":
    main()
