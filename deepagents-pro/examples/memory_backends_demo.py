"""
DeepAgents 内存模型演示：短期（StateBackend） vs 长期（StoreBackend + LangGraph Store）

本脚本与主应用「数据分析智能体」独立：仅用最小 create_deep_agent（无业务工具），专注展示：

- 默认虚拟根路径下的文件（如 ``/draft.txt``）走 **StateBackend** → 绑定 **当前 thread_id** 的检查点状态，
  换一个新 thread_id 即「新会话」，**读不到**上一线程里的草稿。
- 前缀 ``/memories/`` 路由到 **StoreBackend** + **InMemoryStore** → 数据在 **Store 的命名空间**里持久，
  **同一命名空间**下即使 **thread_id 不同**，仍可读写同一文件（跨会话长期记忆）。

运行前请在项目根目录配置 ``.env``（需 MINIMAX_API_KEY 等，与主项目相同），然后::

    pip install -e .
    python examples/memory_backends_demo.py

若仅想阅读说明、不调用模型::

    python examples/memory_backends_demo.py --dry-run

其它单主题脚本：``store_backend_demo.py``、``local_shell_backend_demo.py``、
``sandbox_backend_demo.py``、``composite_backend_demo.py``；磁盘映射见 ``filesystem_backend_demo.py``。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 支持未执行 pip install -e . 时从仓库根直接运行
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


# 与 Store 中隔离数据：演示用固定命名空间（生产可改为 user_id 等）
DEMO_NAMESPACE = ("demo-user", "memories-fs")


def _build_backend(store: InMemoryStore) -> CompositeBackend:
    """默认 StateBackend + ``/memories/`` → StoreBackend（显式传入同一 store 实例）。"""
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                store=store,
                namespace=lambda _rt: DEMO_NAMESPACE,
            ),
        },
    )


def build_memory_demo_agent():
    """构造带短期/长期分流的演示智能体（内存 Store + 内存检查点）。"""
    store = InMemoryStore()
    checkpointer = MemorySaver()
    backend = _build_backend(store)
    agent = create_deep_agent(
        name="memory-demo",
        model=build_model(),
        tools=[],  # 依赖 Deep Agent 内置的文件类工具即可
        checkpointer=checkpointer,
        store=store,
        backend=backend,
        system_prompt=(
            "你是内存机制演示助手，请始终用中文、简短回复。\n"
            "当用户要求保存长期可复用的信息时，写入路径须位于 /memories/ 下（例如 /memories/preferences.txt）。\n"
            "当用户要求仅本会话使用的草稿时，可写到根路径如 /draft.txt。\n"
            "当用户要求读取文件时，用工具读取并如实概括内容。"
        ),
        # 启动时把该文件注入上下文（若存在）；与「长期记忆」路径一致便于观察
        memory=["/memories/preferences.txt"],
    )
    return agent, store


def print_why_same_agent_two_outcomes() -> None:
    """说明为何两个 demo 共用同一个 agent，现象却不同。"""
    print(
        """
┌─ 为何两次 demo 都用「同一个 build_memory_demo_agent() 实例」？──────────────────
│  智能体只是「路由规则 + 模型」；真正决定数据存在哪里的，是：你访问的「虚拟路径」。
│  同一个 CompositeBackend 里已经写死了：
│    • 路径以 /memories/ 开头  → StoreBackend（外置 Store，按 namespace 存）
│    • 其它路径（如 /draft.txt）→ StateBackend（挂在当前 thread 的检查点状态里）
└────────────────────────────────────────────────────────────────────────────

┌─ 区别不在「是否同一个 agent」，而在「写文件时走了哪条后端」──────────────────────
│
│  demo_long_term_cross_thread
│    读写 /memories/preferences.txt
│    → 走 StoreBackend，数据在 InMemoryStore 的 DEMO_NAMESPACE 里。
│    → 与 configurable.thread_id 无关（同一 namespace 下，换 thread_id 仍是同一块存储）。
│
│  demo_short_term_thread_local
│    读写 /draft.txt
│    → 走默认 StateBackend，数据在「当前 thread_id」对应的图状态里。
│    → 换 thread_id = 换了一份状态快照，看不到上一 thread 里的 /draft.txt。
│
└────────────────────────────────────────────────────────────────────────────
"""
    )


def demo_long_term_cross_thread(agent) -> None:
    """线程 A 写入 /memories/…，线程 B（不同 thread_id）应仍能读到。"""
    print("\n" + "=" * 60)
    print("【长期记忆】/memories/ → StoreBackend + InMemoryStore（跨 thread_id）")
    print("=" * 60)

    cfg_a = {"configurable": {"thread_id": "mem-demo-thread-A"}}
    cfg_b = {"configurable": {"thread_id": "mem-demo-thread-B"}}

    msg_write = (
        "请把下面这句话写入文件 /memories/preferences.txt（覆盖写入即可）："
        "「长期记忆演示：我的代号是 Alpha-7」"
    )
    print("\n>>> 线程 A 发送：写入 /memories/preferences.txt …")
    agent.invoke({"messages": [{"role": "user", "content": msg_write}]}, config=cfg_a)

    msg_read = "请读取 /memories/preferences.txt 的完整内容并复述。这是线程 B，与线程 A 不是同一会话。"
    print("\n>>> 线程 B 发送：读取同一文件 …")
    out = agent.invoke({"messages": [{"role": "user", "content": msg_read}]}, config=cfg_b)
    last = out["messages"][-1]
    text = getattr(last, "content", str(last))
    print("\n--- 助手回复（节选）---\n")
    print(text[:1500])
    if "Alpha-7" in text:
        print("\n✓ 线程 B 能看到线程 A 写入的 Store 内容（长期记忆生效）。")
    else:
        print("\n? 未在回复中检测到预期关键词，请人工查看模型输出是否读到文件。")


def demo_short_term_thread_local(agent) -> None:
    """线程 A 写入 /draft.txt，线程 B 不应看到（StateBackend 随 thread 隔离）。"""
    print("\n" + "=" * 60)
    print("【短期记忆】根路径草稿 → StateBackend（随 thread_id 隔离）")
    print("=" * 60)

    cfg_a = {"configurable": {"thread_id": "draft-demo-thread-A"}}
    cfg_b = {"configurable": {"thread_id": "draft-demo-thread-B"}}

    print("\n>>> 线程 A：写入 /draft.txt …")
    agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请写入 /draft.txt，内容一行：短期草稿仅会话A可见-SECRET",
                }
            ]
        },
        config=cfg_a,
    )

    print("\n>>> 线程 B：尝试读取 /draft.txt …")
    out = agent.invoke(
        {"messages": [{"role": "user", "content": "请读取 /draft.txt，若不存在请明确说文件不存在。"}]},
        config=cfg_b,
    )
    last = out["messages"][-1]
    text = getattr(last, "content", str(last))
    print("\n--- 助手回复（节选）---\n")
    print(text[:1500])
    if "不存在" in text or "没有" in text or "无法" in text:
        print("\n✓ 新线程看不到上一线程的 StateBackend 草稿（与长期 /memories/ 行为不同）。")
    else:
        print("\n? 请根据回复判断：若仍读到 SECRET，再对照 deepagents 版本与文档。")


def print_concepts() -> None:
    """不调用模型时的文字说明。"""
    print(
        """
概念对照（与 ``src/deepagent_pro/agent/backend.py`` 生产配置的关系）
----------------------------------------------------------------------
• 当前主应用默认：CompositeBackend 里 ``/skills/`` → 磁盘 FilesystemBackend；
  默认后端为 StateBackend 或（开启 Shell 时）LocalShellBackend —— **未** 挂载 ``/memories/`` 到 Store。
• 若要在产品中启用「跨会话长期文件记忆」，需要：
    - 提供 ``langgraph.store`` 的实现（开发 InMemoryStore，生产可用 PostgresStore 等）；
    - ``create_deep_agent(..., store=你的 store)``；
    - ``CompositeBackend`` 中为 ``/memories/`` 配置 ``StoreBackend(store=..., namespace=...)``。

本 demo 使用 InMemoryStore + MemorySaver，**进程退出后数据清空**；用于本地理解路由与命名空间行为。
"""
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepAgents 内存路由演示")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印说明，不调用模型",
    )
    args = parser.parse_args()

    print_concepts()

    if args.dry_run:
        print_why_same_agent_two_outcomes()
        print("已 --dry-run，跳过模型调用。\n")
        return

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。无法调用模型。\n")
        sys.exit(1)

    print("正在构建演示智能体（将调用 MiniMax API，共两轮演示、多轮 invoke）…\n")
    print_why_same_agent_two_outcomes()
    agent, _store = build_memory_demo_agent()

    demo_long_term_cross_thread(agent)
    demo_short_term_thread_local(agent)

    print("\n演示结束。\n")


if __name__ == "__main__":
    main()
