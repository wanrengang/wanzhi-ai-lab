"""
LangSmithSandbox（``LangSmithSandbox`` 后端）演示 —— 生产向「远程沙箱」执行

``deepagents.backends.LangSmithSandbox`` 包装 **LangSmith** 提供的云端 Sandbox：
文件与 ``execute`` 落在 **隔离环境**，而非你的笔记本进程里。

**本脚本默认不创建沙箱**（需 LangSmith 项目开通 Sandbox、模板等）；加 ``--live`` 且配置好环境变量时才会真实创建/删除沙箱并调用一次模型。

依赖::

    pip install "langsmith[sandbox]"   # 若尚未安装 sandbox 子依赖

环境变量（``--live`` 时）::

    LANGSMITH_API_KEY 或 LANGCHAIN_API_KEY（LangSmith 认证）
    LANGSMITH_SANDBOX_TEMPLATE  必填：你的 Sandbox 模板名称（在 LangSmith 控制台可见）

运行::

    python examples/sandbox_backend_demo.py
    python examples/sandbox_backend_demo.py --live
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent
from deepagents.backends import LangSmithSandbox

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings


def print_docs() -> None:
    print(
        """
LangSmithSandbox 要点
--------------------
• 构造：``LangSmithSandbox(sandbox=<langsmith.sandbox.Sandbox 实例>)``
• Sandbox 通过 ``SandboxClient().create_sandbox(template_name=..., ...)`` 创建
• 适合：生产上需要 **隔离执行**、**审计**、**与 LangSmith 部署联动** 的场景
• 与 LocalShellBackend 对比：后者无隔离，仅适合本机可信开发

以下代码为「典型集成」示意（默认不执行）：

    from langsmith.sandbox import SandboxClient
    from deepagents.backends import LangSmithSandbox

    client = SandboxClient()
    sb = client.create_sandbox(template_name=os.environ["LANGSMITH_SANDBOX_TEMPLATE"])
    try:
        backend = LangSmithSandbox(sb)
        agent = create_deep_agent(
            model=...,
            backend=backend,
            checkpointer=MemorySaver(),
            ...
        )
        agent.invoke(..., config={"configurable": {"thread_id": "sandbox-demo"}})
    finally:
        client.delete_sandbox(sb.name)
"""
    )


def run_live() -> None:
    template = os.environ.get("LANGSMITH_SANDBOX_TEMPLATE", "").strip()
    if not template:
        print("错误：请设置环境变量 LANGSMITH_SANDBOX_TEMPLATE。\n")
        sys.exit(1)

    try:
        from langsmith.sandbox import SandboxClient  # noqa: PLC0415
    except ImportError as e:
        print(f"无法导入 langsmith.sandbox：{e}\n请安装: pip install \"langsmith[sandbox]\"\n")
        sys.exit(1)

    if not (get_settings().minimax_api_key or "").strip():
        print("需要 MINIMAX_API_KEY（模型调用）。\n")
        sys.exit(1)

    client = SandboxClient()
    sb = client.create_sandbox(template_name=template, timeout=120)
    print(f"已创建 Sandbox: name={sb.name!r}")

    try:
        backend = LangSmithSandbox(sb)
        agent = create_deep_agent(
            name="langsmith-sandbox-demo",
            model=build_model(),
            tools=[],
            checkpointer=MemorySaver(),
            backend=backend,
            system_prompt="你是沙箱内演示助手，用中文简短回复。若用户让你写文件，写在沙箱内路径即可。",
        )
        out = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "请在当前环境创建一个文件 /demo_sandbox_hello.txt，内容一行：hello-from-sandbox",
                    }
                ]
            },
            config={"configurable": {"thread_id": "sandbox-thread-1"}},
        )
        last = out["messages"][-1]
        print("\n--- 助手回复 ---\n", getattr(last, "content", str(last))[:2000])
    finally:
        try:
            client.delete_sandbox(sb.name)
            print(f"\n已删除 Sandbox: {sb.name!r}")
        except Exception as e:  # noqa: BLE001
            print(f"\n警告：删除 Sandbox 失败（请手动清理）: {e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="真实创建 LangSmith Sandbox 并调用模型（需模板与 API Key）",
    )
    args = parser.parse_args()
    print_docs()
    if args.live:
        run_live()
    else:
        print(
            "当前为说明模式。若要在云端沙箱跑通一遍，请设置 LANGSMITH_SANDBOX_TEMPLATE 后执行:\n"
            "  python examples/sandbox_backend_demo.py --live\n"
        )


if __name__ == "__main__":
    main()
