"""
DeepAgent Skills 演示 —— 从 Store 动态加载 Skill

本示例展示如何从 URL 加载 Skill 定义并注册到 Agent：

1. 使用 InMemoryStore 存储 Skill 文件
2. 从远程 URL 读取 Skill 内容
3. 将 Skill 注入 Agent 的 /skills/ 路径
4. Agent 可调用 Skill 执行专业任务

运行::

    pip install -e .
    python examples/skills_demo.py

参考文档：https://docs.langchain.com/oss/python/deepagents/skills
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.request import urlopen

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings


# ============== 内置简单 Skill（用于演示） ==============

SIMPLE_SKILL_CONTENT = """# Simple Calculator Skill

## Description
A skill that performs basic arithmetic calculations.

## Instructions
When user asks to calculate something, use this skill.

## Tools
- calculator: Evaluates math expressions

## Triggers
- User mentions "计算", "calculate", math expressions
"""

SEARCH_SKILL_CONTENT = """# Web Search Skill

## Description
A skill for searching the web for information.

## Instructions
When user asks about recent events or needs to look up information, use this skill.

## Tools
- web_search: Searches the web

## Triggers
- User mentions "搜索", "search", "查找"
"""


def seed_skills_to_store(store: InMemoryStore) -> None:
    """将内置 Skill 文件写入 Store。

    Args:
        store: InMemoryStore 实例
    """
    # namespace: ("filesystem",) 存储技能文件
    namespace = ("filesystem",)

    # 写入简单计算 Skill
    store.put(
        namespace=namespace,
        key="/skills/simple-calc/SKILL.md",
        value=create_file_data(SIMPLE_SKILL_CONTENT),
    )

    # 写入搜索 Skill
    store.put(
        namespace=namespace,
        key="/skills/web-search/SKILL.md",
        value=create_file_data(SEARCH_SKILL_CONTENT),
    )

    print("✓ Skills 已写入 Store:")
    print("  - /skills/simple-calc/SKILL.md")
    print("  - /skills/web-search/SKILL.md")


def load_skill_from_url(store: InMemoryStore, url: str, skill_path: str) -> bool:
    """从 URL 加载 Skill 到 Store。

    Args:
        store: InMemoryStore 实例
        url: Skill 文件的原始 URL
        skill_path: Skill 在 store 中的路径

    Returns:
        是否加载成功
    """
    try:
        with urlopen(url) as response:
            content = response.read().decode("utf-8")

        namespace = ("filesystem",)
        store.put(
            namespace=namespace,
            key=skill_path,
            value=create_file_data(content),
        )
        print(f"✓ 从 URL 加载 Skill: {skill_path}")
        return True
    except Exception as e:
        print(f"✗ 加载 Skill 失败: {e}")
        return False


def build_skills_demo_agent(store: InMemoryStore):
    """构建使用 Skills 的 Agent。

    Args:
        store: 包含 Skill 文件的 InMemoryStore
    """
    # 构建 backend：/skills/ 路由到 StoreBackend
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/skills/": StoreBackend(
                store=store,
                namespace=lambda _rt: ("filesystem",),
            ),
        },
    )

    # 创建 Agent，skills 参数指定 Skill 根路径
    agent = create_deep_agent(
        name="skills-demo",
        model=build_model(),
        tools=[],  # 工具由 Skill 提供
        checkpointer=MemorySaver(),
        store=store,
        backend=backend,
        skills=["/skills/"],  # 关键：注册 Skill 路径
        system_prompt="""你是智能助手，可以调用各种 Skills 来完成任务。

Available Skills:
- simple-calc: 简单计算
- web-search: 网络搜索

当用户请求涉及计算或搜索时，主动调用对应 Skill。
请用中文简洁回复。""",
    )
    return agent


# ============== 演示场景 ==============

def demo_builtin_skills():
    """演示内置 Skills（不调用外部 URL）"""
    print("\n" + "=" * 60)
    print("【演示 1】内置 Skills（从 Store 加载）")
    print("=" * 60)

    store = InMemoryStore()
    seed_skills_to_store(store)

    agent = build_skills_demo_agent(store)
    cfg = {"configurable": {"thread_id": "skills-demo-1"}}

    print("\n--- 测试计算 Skill ---")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "请计算 (25 + 15) * 3 / 4"}]},
        config=cfg,
    )
    last = result["messages"][-1]
    print(f"助手回复: {getattr(last, 'content', str(last))[:500]}")


def demo_load_from_url():
    """演示从 URL 加载 Skill（需要网络）"""
    print("\n" + "=" * 60)
    print("【演示 2】从 URL 加载 LangGraph Docs Skill")
    print("=" * 60)

    store = InMemoryStore()

    # 尝试从 GitHub 加载官方示例 Skill
    skill_url = "https://raw.githubusercontent.com/langchain-ai/deepagents/refs/heads/main/libs/cli/examples/skills/langgraph-docs/SKILL.md"

    success = load_skill_from_url(
        store,
        url=skill_url,
        skill_path="/skills/langgraph-docs/SKILL.md",
    )

    if not success:
        print("\n（跳过 URL 加载，网络不可用或 URL 无效）")
        return

    agent = build_skills_demo_agent(store)
    cfg = {"configurable": {"thread_id": "skills-demo-url"}}

    print("\n--- 查询 LangGraph ---")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What is LangGraph?"}]},
        config=cfg,
    )
    last = result["messages"][-1]
    print(f"助手回复: {getattr(last, 'content', str(last))[:500]}")


def print_concepts():
    """打印 Skills 核心概念"""
    print("""
Skills 核心概念
===============

1. Skill 结构
   - SKILL.md: 包含描述、指令、工具触发条件
   - 存储在 StoreBackend 中，按 namespace 隔离
   - 路径格式: /skills/{skill-name}/SKILL.md

2. StoreBackend 路由
   - routes["/skills/"] = StoreBackend(store=store, namespace=...)
   - Agent 通过 /skills/ 路径访问 Skill 定义
   - skills=["/skills/"] 注册可用的 Skill 根路径

3. create_file_data
   - 将字符串内容包装成 Store 需要的 value 格式
   - value["content"] 存储实际 Skill 内容

4. Skill vs Tools
   - Tool: 原子操作（发送邮件、删除文件）
   - Skill: 封装的工作流（包含多个 Tool + 指令）
   - Skill 可以定义触发条件，动态加载

5. 动态加载
   - Skill 内容可以来自：本地文件、URL、数据库
   - 适合：团队共享 Skill、运行时更新 Skill
""")


def main():
    parser = argparse.ArgumentParser(description="DeepAgent Skills 演示")
    parser.add_argument("--dry-run", action="store_true", help="仅打印说明")
    parser.add_argument("--skip-url", action="store_true", help="跳过 URL 加载")
    args = parser.parse_args()

    print_concepts()

    if args.dry_run:
        print("已 --dry-run，跳过执行。\n")
        return

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        sys.exit(1)

    # 演示 1：内置 Skills
    demo_builtin_skills()

    # 演示 2：从 URL 加载（可选）
    if not args.skip_url:
        demo_load_from_url()

    print("\n演示结束。\n")


if __name__ == "__main__":
    main()