"""
最简单的 Deep Agent 示例

这个示例展示如何创建一个基础的 Deep Agent，包含：
- 最小化的配置（仅模型和工具）
- 简单的工具调用
- 基础的对话能力

对比传统 ReAct Agent，Deep Agent 的优势：
1. 内置 write_todos 规划能力
2. 虚拟文件系统（虽然本例未启用）
3. 自动上下文管理
4. 子代理支持（本例未使用）

运行::
    python examples/00_basics/simple_agent.py --dry-run
    python examples/00_basics/simple_agent.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langchain.tools import tool
from langchain_openai import ChatOpenAI

from deepagents import create_deep_agent
from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings


# ============== 定义工具 ==============

@tool
def calculator(expression: str) -> str:
    """简单的计算器工具，可以计算数学表达式。

    Args:
        expression: 数学表达式，如 "2 + 3 * 4"

    Returns:
        计算结果
    """
    try:
        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息（模拟）。

    Args:
        city: 城市名称

    Returns:
        天气信息
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天，温度 25°C",
        "上海": "多云，温度 28°C",
        "深圳": "阴天，温度 30°C",
    }
    return weather_data.get(city, f"{city}的天气信息暂未获取")


@tool
def current_time() -> str:
    """获取当前时间。"""
    from datetime import datetime

    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"


# ============== 创建 Agent ==============

def create_simple_agent():
    """创建一个简单的 Deep Agent"""
    model = build_model()

    tools = [calculator, get_weather, current_time]

    system_prompt = """\
你是一个简单的演示助手，可以帮助用户：
1. 进行数学计算
2. 查询天气（仅支持北京、上海、深圳）
3. 获取当前时间

请用中文简洁回复。"""

    agent = create_deep_agent(
        name="simple-demo",
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent


# ============== 演示场景 ==============

def demo_basic_usage(agent):
    """演示基础用法"""
    print("\n" + "=" * 60)
    print("【场景 1】计算任务")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "帮我计算 (10 + 5) * 2 - 8"
        }]
    })

    last_message = result["messages"][-1]
    print(f"\n助手回复: {last_message.content}")


def demo_tool_selection(agent):
    """演示工具选择"""
    print("\n" + "=" * 60)
    print("【场景 2】工具选择")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "北京现在的天气怎么样？现在几点了？"
        }]
    })

    last_message = result["messages"][-1]
    print(f"\n助手回复: {last_message.content}")


def demo_planning(agent):
    """演示任务规划（write_todos）"""
    print("\n" + "=" * 60)
    print("【场景 3】任务规划")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": """
            我需要你帮我做以下事情：
            1. 计算一下 (15 + 25) / 4 的结果
            2. 查询上海的天气
            3. 告诉我当前时间
            4. 把这些信息整理成一个简短的报告
            """
        }]
    })

    # 打印完整对话过程（包含 write_todos 规划）
    print("\n--- 完整对话过程 ---")
    for i, msg in enumerate(result["messages"]):
        role = getattr(msg, "type", "unknown") or getattr(msg, "role", "unknown")
        content = getattr(msg, "content", "") or ""
        tool_calls = getattr(msg, "tool_calls", []) or []
        if content:
            print(f"\n[{i}] {role}: {str(content)[:200]}{'...' if len(str(content)) > 200 else ''}")
        if tool_calls:
            for tc in tool_calls:
                tc_name = getattr(tc, "name", "?") or (tc.get("name") if isinstance(tc, dict) else "?")
                tc_args = getattr(tc, "args", {}) or (tc.get("args") if isinstance(tc, dict) else {})
                print(f"[{i}] {role} tool_call: {tc_name} → {str(tc_args)[:150]}")

    last_message = result["messages"][-1]
    print(f"\n最终回复: {last_message.content}")


def print_concepts():
    """打印核心概念"""
    print("""
核心概念
--------
1. Deep Agent vs ReAct Agent
   - ReAct Agent: 简单的"思考 → 行动 → 观察"循环
   - Deep Agent: 内置规划、文件系统、子代理、上下文管理

2. create_deep_agent 参数
   - model: LLM 模型
   - tools: 可用工具列表
   - system_prompt: 系统提示词
   - subagents: 子代理（本例未使用）
   - backend: 文件系统后端（本例使用默认 StateBackend）
   - checkpointer: 状态检查点（本例使用默认 MemorySaver）

3. 工具定义
   - 使用 @tool 装饰器
   - 工具的 docstring 会被 LLM 看到，影响调用决策
   - 参数类型注解很重要

4. Agent 会自动使用 write_todos
   - 对于复杂任务（3步以上）
   - 自动分解为 TODO 列表
   - 逐步执行并跟踪进度
""")


def main():
    parser = argparse.ArgumentParser(description="最简单的 Deep Agent 示例")
    parser.add_argument("--dry-run", action="store_true", help="仅打印说明")
    args = parser.parse_args()

    print_concepts()

    if args.dry_run:
        print("已 --dry-run，跳过模型调用。\n")
        return

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        sys.exit(1)

    print("正在构建简单 Agent（将调用 MiniMax API）…\n")

    agent = create_simple_agent()

    # 运行演示场景
    demo_basic_usage(agent)
    demo_tool_selection(agent)
    demo_planning(agent)

    print("\n演示结束。")


if __name__ == "__main__":
    main()
