"""
FilesystemBackend（本地磁盘）演示

将虚拟路径前缀 ``/local/`` 映射到仓库内真实目录（默认 ``data/fs_backend_demo/``），与
``memory_backends_demo.py`` 中的 Store / State 对照：

- ``/local/...`` → **FilesystemBackend**：读写的是 **本机磁盘上的文件**；同一 ``root_dir`` 下，
  换不同 ``thread_id`` 仍指向同一物理路径，**跨会话可见**；你也可用资源管理器直接打开该目录查看。
- 未挂载的前缀（如 ``/draft.txt``）仍走 **StateBackend**，随 thread 隔离（本脚本可选演示）。

运行::

    pip install -e .
    python examples/filesystem_backend_demo.py

仅打印说明::

    python examples/filesystem_backend_demo.py --dry-run
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

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings

# 虚拟前缀 → 映射到该目录（与主应用 /skills/ 用法一致，virtual_mode=True）
VIRTUAL_PREFIX = "/local/"
# 磁盘目录（相对仓库根）
DISK_ROOT = _REPO_ROOT / "data" / "fs_backend_demo"


def _build_backend() -> CompositeBackend:
    DISK_ROOT.mkdir(parents=True, exist_ok=True)
    return CompositeBackend(
        default=StateBackend(),
        routes={
            VIRTUAL_PREFIX: FilesystemBackend(
                root_dir=str(DISK_ROOT.resolve()),
                virtual_mode=True,
            ),
        },
    )


def build_fs_demo_agent():
    """仅 State + Filesystem 路由，无需 LangGraph Store。"""
    checkpointer = MemorySaver()
    backend = _build_backend()
    agent = create_deep_agent(
        name="filesystem-backend-demo",
        model=build_model(),
        tools=[],
        checkpointer=checkpointer,
        backend=backend,
        system_prompt=(
            "你是文件系统演示助手，用中文简短回复。\n"
            f"当用户要求写入「共享磁盘」文件时，路径必须使用前缀 {VIRTUAL_PREFIX}，"
            f"例如 {VIRTUAL_PREFIX}shared_note.txt。\n"
            "写入后请确认；读取时如实输出文件内容。"
        ),
    )
    return agent


def print_concepts() -> None:
    abs_disk = DISK_ROOT.resolve()
    print(
        f"""
配置说明
--------
• 虚拟路径：以 {VIRTUAL_PREFIX} 开头的路径 → FilesystemBackend
• 真实目录：{abs_disk}
• 例：{VIRTUAL_PREFIX}shared_note.txt 对应磁盘文件：{abs_disk / "shared_note.txt"}

与主项目 ``backend.py`` 中 ``/skills/`` → FilesystemBackend 是同一类用法，只是本 demo 换了一个前缀与目录。
"""
    )


def demo_disk_cross_thread(agent) -> None:
    """线程 A 写入 /local/…，线程 B 读取；最后在 Python 里直接读磁盘文件验真。"""
    fname = "shared_note.txt"
    vpath = f"{VIRTUAL_PREFIX}{fname}"
    cfg_a = {"configurable": {"thread_id": "fs-demo-thread-A"}}
    cfg_b = {"configurable": {"thread_id": "fs-demo-thread-B"}}

    print("\n" + "=" * 60)
    print(f"【FilesystemBackend】{VIRTUAL_PREFIX} → 磁盘目录")
    print("=" * 60)

    print(f"\n>>> 线程 A：写入 {vpath} …")
    agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"请创建或覆盖文件 {vpath}，内容为单行文字："
                        "「磁盘演示：线程A写入，两线程共用一个物理文件」"
                    ),
                }
            ]
        },
        config=cfg_a,
    )

    print(f"\n>>> 线程 B：读取 {vpath}（不同 thread_id）…")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请读取 {vpath} 的完整内容并复述要点。",
                }
            ]
        },
        config=cfg_b,
    )
    last = out["messages"][-1]
    print("\n--- 助手回复（节选）---\n")
    print(getattr(last, "content", str(last))[:1200])

    real = DISK_ROOT / fname
    print("\n--- 验真：Python 直接读磁盘（不经智能体）---")
    if real.is_file():
        text = real.read_text(encoding="utf-8", errors="replace")
        print(f"路径: {real.resolve()}\n内容节选: {text[:500]}")
        print("\n✓ 文件在磁盘上；两线程共用同一 root_dir，故行为与「真实文件夹」一致。")
    else:
        print(f"未找到 {real}，可能模型未按路径写入；请查看助手回复与工具调用。")


def main() -> None:
    parser = argparse.ArgumentParser(description="FilesystemBackend 本地磁盘映射演示")
    parser.add_argument("--dry-run", action="store_true", help="只打印说明")
    args = parser.parse_args()

    print_concepts()

    if args.dry_run:
        print("已 --dry-run，跳过模型调用。\n")
        return

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        sys.exit(1)

    print("正在构建演示智能体（将调用 MiniMax API）…\n")
    agent = build_fs_demo_agent()
    demo_disk_cross_thread(agent)
    print("\n演示结束。\n")


if __name__ == "__main__":
    main()
