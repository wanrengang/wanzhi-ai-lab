"""
LocalShellBackend 演示 —— 在受限目录内提供「读文件 + execute」能力（宿主机执行）

**危险**：命令在 **本机**、以 **当前用户权限** 运行，与生产多租户/API 场景不匹配。
仅适合 **本机可信环境**；公网服务请用容器 / LangSmith Sandbox 等隔离方案。

本 demo 将 ``root_dir`` 限制在仓库内 ``data/local_shell_demo/``，避免误扫全盘；
仍可能读写该目录下任意文件、执行任意命令 —— 需显式 ``--accept-risk`` 才调用模型。

运行::

    python examples/local_shell_backend_demo.py --dry-run
    python examples/local_shell_backend_demo.py --accept-risk   # 会调 LLM + 可能在宿主机执行命令
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
from deepagents.backends import LocalShellBackend

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings

WORK_ROOT = _REPO_ROOT / "data" / "local_shell_demo"


def build_agent():
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    # 与主项目 shell_enabled 时一致：虚拟路径映射到单一 root_dir
    backend = LocalShellBackend(
        root_dir=str(WORK_ROOT.resolve()),
        virtual_mode=True,
    )
    return create_deep_agent(
        name="local-shell-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt=(
            f"你是本地 Shell 演示助手，工作区根路径对应宿主机目录：{WORK_ROOT}。"
            "用户让你执行命令时，使用系统提供的 execute 能力；只在该目录内创建/读取文件。"
            "用中文简短回复。"
        ),
    )


def demo() -> None:
    agent = build_agent()
    tid = "shell-demo-1"
    print(f"\n工作目录（真实磁盘）: {WORK_ROOT.resolve()}\n")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请执行一条安全的 shell 命令：在当前工作区创建一个文本文件 "
                        "`shell_demo_marker.txt`，内容为单行：LocalShellBackend-DEMO。"
                        "若已有 execute 工具，请使用它完成。"
                    ),
                }
            ]
        },
        config={"configurable": {"thread_id": tid}},
    )
    last = out["messages"][-1]
    print(getattr(last, "content", str(last))[:2000])
    marker = WORK_ROOT / "shell_demo_marker.txt"
    if marker.is_file():
        print(f"\n✓ 磁盘上已生成: {marker}\n内容: {marker.read_text(encoding='utf-8', errors='replace')[:200]}")
    else:
        print("\n? 未在磁盘找到 shell_demo_marker.txt，请查看模型是否调用了 execute。")


def print_warning() -> None:
    print(
        """
LocalShellBackend 适用场景（摘自 SDK 文档意译）
------------------------------------------
• 本地开发 CLI、可信个人环境
• 不适合：公网 API、多租户、未校验的用户输入

生产替代：StateBackend / StoreBackend / Docker 或 LangSmith Sandbox 等隔离执行环境。
"""
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--accept-risk",
        action="store_true",
        help="确认知晓宿主机执行风险后才调用模型",
    )
    args = parser.parse_args()
    print_warning()
    if args.dry_run:
        print("已 --dry-run。\n")
        return
    if not args.accept_risk:
        print("未加 --accept-risk，不调用模型。若确认在可信环境，请加上该参数再运行。\n")
        sys.exit(0)
    if not (get_settings().minimax_api_key or "").strip():
        print("需要 MINIMAX_API_KEY。\n")
        sys.exit(1)
    demo()
    print("完成。\n")


if __name__ == "__main__":
    main()
