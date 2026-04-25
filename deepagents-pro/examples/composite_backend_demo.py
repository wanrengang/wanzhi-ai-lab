"""
CompositeBackend 演示 —— 一张路由表：默认后端 + 多前缀

本例 **同时** 挂载：

- **default**：``StateBackend`` → 根路径如 ``/draft.txt``（随 ``thread_id`` 隔离）
- ``/store/`` → ``StoreBackend`` + ``InMemoryStore``（跨 thread）
- ``/disk/`` → ``FilesystemBackend`` → 真实目录 ``data/composite_demo_disk/``

一次对话里可让模型分别写三类路径，观察「谁持久、谁跟会话走、谁落盘」。

运行::

    python examples/composite_backend_demo.py --dry-run
    python examples/composite_backend_demo.py
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
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings

DISK_ROOT = _REPO_ROOT / "data" / "composite_demo_disk"
STORE_NS = ("composite-demo", "ns-1")


def build_agent():
    DISK_ROOT.mkdir(parents=True, exist_ok=True)
    store = InMemoryStore()
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/store/": StoreBackend(
                store=store,
                namespace=lambda _rt: STORE_NS,
            ),
            "/disk/": FilesystemBackend(
                root_dir=str(DISK_ROOT.resolve()),
                virtual_mode=True,
            ),
        },
    )
    agent = create_deep_agent(
        name="composite-backend-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        store=store,
        backend=backend,
        system_prompt=(
            "你是 Composite 路由演示助手，用中文简短回复。\n"
            "1) 写入 /store/long.txt：一行字「长期-Store」。\n"
            "2) 写入 /disk/on_disk.txt：一行字「磁盘-Filesystem」。\n"
            "3) 写入 /draft.txt：一行字「短期-State」。\n"
            "分步调用工具完成；最后汇总三条是否成功。"
        ),
    )
    return agent


def print_routing_table() -> None:
    print(
        f"""
CompositeBackend 路由（本脚本）
------------------------------
  路径前缀          后端                数据落在哪
  ---------------   ------------------  ---------------------------------
  （默认）          StateBackend        当前 thread 的检查点状态
  /store/           StoreBackend        InMemoryStore[{STORE_NS!r}]
  /disk/            FilesystemBackend   {DISK_ROOT.resolve()}
"""
    )


def demo() -> None:
    agent = build_agent()
    tid = "composite-one-shot"
    print("\n>>> 单次 invoke，让模型写三类路径 …\n")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请按系统说明创建三个文件（/store/long.txt、/disk/on_disk.txt、/draft.txt）。",
                }
            ]
        },
        config={"configurable": {"thread_id": tid}},
    )
    print(getattr(out["messages"][-1], "content", str(out["messages"][-1]))[:3000])

    disk_file = DISK_ROOT / "on_disk.txt"
    print("\n--- 验真：磁盘文件（应含「磁盘」）---")
    if disk_file.is_file():
        print(f"{disk_file.resolve()}\n{disk_file.read_text(encoding='utf-8', errors='replace')[:300]}")
    else:
        print(f"未找到 {disk_file}（模型可能未按路径写入）。")

    print(
        "\n提示：再开一个 thread_id 调用，可验证 /store/ 仍可读、/draft.txt 不可见；"
        "本脚本为省 token 只跑一轮。"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    print_routing_table()
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
