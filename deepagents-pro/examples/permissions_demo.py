"""
DeepAgent 权限控制演示

本示例展示如何使用 FilesystemPermission 控制智能体的文件系统访问权限：

1. 只读智能体（Read-only Agent）：禁止所有写操作
2. 工作区隔离（Workspace Isolation）：限制只能访问指定目录
3. 细粒度权限（Fine-grained）：不同目录不同权限
4. 子代理权限继承与覆盖

运行::

    pip install -e .
    python examples/permissions_demo.py

参考文档：https://docs.langchain.com/oss/python/deepagents/permissions
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents import FilesystemPermission

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings

# 测试用虚拟路径前缀
VIRTUAL_PREFIX = "/local/"
DISK_ROOT_READONLY = _REPO_ROOT / "data" / "permissions_demo" / "readonly_workspace"
DISK_ROOT_WRITABLE = _REPO_ROOT / "data" / "permissions_demo" / "writable_workspace"


def _build_composite_backend() -> CompositeBackend:
    """构建复合后端，支持多个虚拟路径前缀。"""
    DISK_ROOT_READONLY.mkdir(parents=True, exist_ok=True)
    DISK_ROOT_WRITABLE.mkdir(parents=True, exist_ok=True)

    # 写入一个示例文件用于测试读取
    sample_file = DISK_ROOT_READONLY / "sample.txt"
    if not sample_file.exists():
        sample_file.write_text("这是只读工作区的示例文件内容。", encoding="utf-8")

    return CompositeBackend(
        default=StateBackend(),
        routes={
            f"{VIRTUAL_PREFIX}readonly/": FilesystemBackend(
                root_dir=str(DISK_ROOT_READONLY.resolve()),
                virtual_mode=True,
            ),
            f"{VIRTUAL_PREFIX}writable/": FilesystemBackend(
                root_dir=str(DISK_ROOT_WRITABLE.resolve()),
                virtual_mode=True,
            ),
        },
    )


# ============== 演示 1：只读智能体 ==============

def build_readonly_agent():
    """创建只读智能体：禁止所有写操作。"""
    backend = _build_composite_backend()

    agent = create_deep_agent(
        name="readonly-agent-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt=(
            "你是只读助手，只能读取文件，不能写入。\n"
            f"文件位于 {VIRTUAL_PREFIX}readonly/ 目录下。\n"
            "请用中文简短回复。"
        ),
        permissions=[
            # 允许读取所有文件
            FilesystemPermission(
                operations=["read"],
                paths=["/**"],
                mode="allow",
            ),
            # 禁止所有写操作
            FilesystemPermission(
                operations=["write"],
                paths=["/**"],
                mode="deny",
            ),
        ],
    )
    return agent


def demo_readonly_agent(agent):
    """演示只读智能体：读取允许，写入被拒绝。"""
    print("\n" + "=" * 60)
    print("【演示 1】只读智能体（Read-only Agent）")
    print("=" * 60)
    print("权限规则：允许读，禁止写\n")

    cfg = {"configurable": {"thread_id": "readonly-demo"}}

    print(">>> 尝试读取文件（应成功）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请读取 {VIRTUAL_PREFIX}readonly/sample.txt 的内容",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")

    print(">>> 尝试写入文件（应被拒绝）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请创建文件 {VIRTUAL_PREFIX}readonly/test.txt，内容为「测试写入」",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")


# ============== 演示 2：工作区隔离 ==============

def build_isolated_agent():
    """创建隔离智能体：只能访问指定工作区。"""
    backend = _build_composite_backend()

    agent = create_deep_agent(
        name="isolated-agent-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt=(
            "你是隔离工作区助手，只能访问 /local/ 目录下的文件。\n"
            "请用中文简短回复。"
        ),
        permissions=[
            # 只允许访问 /local/ 目录
            FilesystemPermission(
                operations=["read", "write"],
                paths=["/local/**"],
                mode="allow",
            ),
            # 禁止访问其他所有路径
            FilesystemPermission(
                operations=["read", "write"],
                paths=["/**"],
                mode="deny",
            ),
        ],
    )
    return agent


def demo_isolated_agent(agent):
    """演示隔离智能体：只能访问授权目录。"""
    print("\n" + "=" * 60)
    print("【演示 2】工作区隔离（Workspace Isolation）")
    print("=" * 60)
    print("权限规则：只允许 /local/**，禁止其他所有路径\n")

    cfg = {"configurable": {"thread_id": "isolated-demo"}}

    print(">>> 尝试访问授权目录（应成功）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请列出 {VIRTUAL_PREFIX}readonly/ 目录下的所有文件",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")

    print(">>> 尝试访问未授权路径（应被拒绝）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请读取 /etc/hosts 文件的内容",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")


# ============== 演示 3：细粒度权限 ==============

def build_finegrained_agent():
    """创建细粒度权限智能体：不同目录不同权限。"""
    backend = _build_composite_backend()

    agent = create_deep_agent(
        name="finegrained-agent-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt=(
            "你是细粒度权限助手。\n"
            f"- {VIRTUAL_PREFIX}readonly/ 目录：只读\n"
            f"- {VIRTUAL_PREFIX}writable/ 目录：可读写\n"
            "请用中文简短回复。"
        ),
        permissions=[
            # 只读目录：允许读，拒绝写
            FilesystemPermission(
                operations=["read"],
                paths=["/local/readonly/**"],
                mode="allow",
            ),
            FilesystemPermission(
                operations=["write"],
                paths=["/local/readonly/**"],
                mode="deny",
            ),
            # 可写目录：允许读写
            FilesystemPermission(
                operations=["read", "write"],
                paths=["/local/writable/**"],
                mode="allow",
            ),
        ],
    )
    return agent


def demo_finegrained_agent(agent):
    """演示细粒度权限：不同目录不同权限。"""
    print("\n" + "=" * 60)
    print("【演示 3】细粒度权限（Fine-grained Permissions）")
    print("=" * 60)
    print("权限规则：\n  - /local/readonly/** → 只读\n  - /local/writable/** → 读写\n")

    cfg = {"configurable": {"thread_id": "finegrained-demo"}}

    print(">>> 读取只读目录（应成功）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请读取 {VIRTUAL_PREFIX}readonly/sample.txt 的内容",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")

    print(">>> 写入只读目录（应被拒绝）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请创建文件 {VIRTUAL_PREFIX}readonly/new.txt，内容为「不应写入」",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")

    print(">>> 写入可写目录（应成功）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请创建文件 {VIRTUAL_PREFIX}writable/note.txt，内容为「这是可写目录」",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")


# ============== 演示 4：使用 glob 模式 ==============

def build_glob_agent():
    """使用 glob 模式的智能体。"""
    backend = _build_composite_backend()

    agent = create_deep_agent(
        name="glob-agent-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt=(
            "你是 Glob 模式演示助手。\n"
            "权限使用 glob 模式匹配路径。\n"
            "请用中文简短回复。"
        ),
        permissions=[
            # 允许访问 /local/ 下所有 .txt 文件
            FilesystemPermission(
                operations=["read"],
                paths=["/local/**/*.txt"],
                mode="allow",
            ),
            # 允许写入 /local/writable/ 下的任意文件
            FilesystemPermission(
                operations=["write"],
                paths=["/local/writable/**"],
                mode="allow",
            ),
            # 拒绝其他所有写操作
            FilesystemPermission(
                operations=["write"],
                paths=["/**"],
                mode="deny",
            ),
        ],
    )
    return agent


def demo_glob_agent(agent):
    """演示 glob 模式路径匹配。"""
    print("\n" + "=" * 60)
    print("【演示 4】Glob 模式路径匹配")
    print("=" * 60)
    print("权限规则：\n  - /local/**/*.txt → 只读\n  - /local/writable/** → 读写\n  - /** → 拒绝写\n")

    cfg = {"configurable": {"thread_id": "glob-demo"}}

    print(">>> 读取 .txt 文件（应成功）...")
    out = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"请读取 {VIRTUAL_PREFIX}readonly/sample.txt",
                }
            ]
        },
        config=cfg,
    )
    last = out["messages"][-1]
    print(f"--- 助手回复 ---\n{getattr(last, 'content', str(last))[:500]}\n")


# ============== 主函数 ==============

def print_concepts() -> None:
    """打印权限系统核心概念。"""
    print(f"""
文件系统权限核心概念
==================

1. FilesystemPermission 对象
   - operations: ["read"] 或 ["write"] 或 ["read", "write"]
   - paths: Glob 模式，如 "/workspace/**", "/*.txt", "{{a,b}}"
   - mode: "allow" 或 "deny"（默认 allow）

2. 评估逻辑：First-match-wins
   第一条匹配的规则决定结果；无匹配则允许。

3. 权限类型
   - 只读智能体：deny 所有写操作
   - 工作区隔离：allow 特定路径，deny 其他
   - 细粒度权限：不同路径不同权限

4. Glob 模式支持
   - ** 匹配任意目录层级
   - * 匹配文件名中的任意字符
   - {{a,b}} 匹配 a 或 b

5. 子代理权限
   子代理继承父代理权限；设置 permissions 字段会完全替换。
""")


def main() -> None:
    print_concepts()

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        exit(1)

    # 演示 1：只读智能体
    print("\n>>> 构建只读智能体（将调用 MiniMax API）...")
    agent = build_readonly_agent()
    demo_readonly_agent(agent)

    # 演示 2：工作区隔离
    print("\n>>> 构建隔离智能体（将调用 MiniMax API）...")
    agent = build_isolated_agent()
    demo_isolated_agent(agent)

    # 演示 3：细粒度权限
    print("\n>>> 构建细粒度权限智能体（将调用 MiniMax API）...")
    agent = build_finegrained_agent()
    demo_finegrained_agent(agent)

    # 演示 4：Glob 模式
    print("\n>>> 构建 Glob 模式智能体（将调用 MiniMax API）...")
    agent = build_glob_agent()
    demo_glob_agent(agent)

    print("\n演示结束。\n")


if __name__ == "__main__":
    main()
