"""
进阶练习：Deep Agent 任务规划（write_todos）

本示例展示：
- 流式输出：思考过程实时打印到控制台
- write_todos 的内部机制
- 多步骤任务的规划与执行流程
- 生成的文件真实落盘到 ./output/code_project/

运行::
    python examples/00_basics/planning_demo.py --dry-run
    python examples/00_basics/planning_demo.py
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
from langchain_core.messages import HumanMessage

from deepagents import create_deep_agent
from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings


# ============== 输出目录 ==============
# 生成的文件会真实落盘到此目录
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output" / "code_project"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============== 定义工具 ==============

@tool
def search_code(query: str) -> str:
    """搜索代码库中的相关代码。

    Args:
        query: 搜索关键词

    Returns:
        相关代码片段
    """
    code_database = {
        "排序算法": '''def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)''',
        "数据结构": '''class Stack:
    def __init__(self):
        self.items = []
    def push(self, item):
        self.items.append(item)
    def pop(self):
        return self.items.pop() if self.items else None
    def peek(self):
        return self.items[-1] if self.items else None
    def is_empty(self):
        return len(self.items) == 0''',
        "搜索算法": '''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1''',
    }
    for key, value in code_database.items():
        if key in query:
            return value
    return f"未找到与 '{query}' 相关的代码"


@tool
def write_code(filename: str, content: str) -> str:
    """写入代码到真实文件系统（./output/code_project/）。

    Args:
        filename: 文件名，如 "sort_demo.py"
        content: 代码内容

    Returns:
        写入结果（包含文件路径）
    """
    file_path = OUTPUT_DIR / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ 已写入 {file_path}，共 {len(content)} 字符"


@tool
def run_tests(filename: str) -> str:
    """运行 pytest 测试验证代码正确性。

    Args:
        filename: 测试文件路径

    Returns:
        测试结果
    """
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return f"❌ 测试文件不存在: {file_path}"

    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(file_path), "-v"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(OUTPUT_DIR),
        )
        if result.returncode == 0:
            return f"✅ {result.stdout}"
        else:
            return f"❌ 测试失败:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"⚠️ 无法运行测试: {e}"


@tool
def analyze_performance(code: str) -> str:
    """分析代码的时间/空间复杂度。

    Args:
        code: 代码内容

    Returns:
        复杂度分析结果
    """
    lower = code.lower()
    if "sort" in lower or "bubble" in lower or "quick" in lower:
        return "时间复杂度: O(n log n)，空间复杂度: O(n)"
    if "stack" in lower:
        return "时间复杂度: O(1)，空间复杂度: O(n)"
    if "search" in lower or "binary" in lower:
        return "时间复杂度: O(log n)，空间复杂度: O(1)"
    return "时间复杂度: O(n)，空间复杂度: O(1)"


@tool
def generate_docs(filename: str) -> str:
    """为代码生成文档字符串。

    Args:
        filename: 代码文件路径

    Returns:
        生成的文档
    """
    return f"✅ {filename} 文档已生成，包含：函数说明、参数列表、返回值说明"


def create_planning_agent():
    """创建用于任务规划的 Agent"""
    model = build_model()
    tools = [search_code, write_code, run_tests, analyze_performance, generate_docs]
    system_prompt = """\
你是一个专业的编程助手，擅长任务规划和代码开发。

工作流程：
1. 收到需求后，先用 write_todos 制定详细计划
2. 按计划逐步执行每个子任务
3. 定期更新 TODO 状态（pending → in_progress → completed）
4. 完成后汇总结果

重要：使用 write_code 工具时，filename 只要写文件名（如 sort_demo.py），
文件会自动保存到 ./output/code_project/ 目录。

请用中文回复，保持输出结构清晰。"""
    agent = create_deep_agent(
        name="planning-demo",
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )
    return agent


def print_planning_concepts():
    """打印任务规划的核心概念"""
    print(f"""
核心概念：write_todos 任务规划
------------------------------
1. 触发条件：复杂任务（3步以上）自动启用
2. TODO 结构：{{id, content, status, priority}}
3. 状态流转：pending → in_progress → completed
4. 规划原则：先规划后执行，定期更新进度

流式输出：本 demo 使用 agent.stream() 实时打印思考过程到控制台

文件落盘：生成的文件保存到 {OUTPUT_DIR}
""")



def demo_multi_step_planning(agent):
    """演示多步骤任务规划（流式输出）"""
    print("\n" + "=" * 60)
    print("【演示】完整项目开发流程（流式输出）")
    print("=" * 60)
    print(f"\n📁 文件将保存到: {OUTPUT_DIR}\n")

    user_input = """
我需要你帮我完成一个「排序算法演示项目」的开发：
1. 搜索排序算法的参考代码
2. 编写 sort_demo.py 文件
3. 运行测试验证正确性
4. 分析代码性能
5. 生成项目文档
"""

    print("--- 开始流式执行（实时打印思考过程）---\n")

    # 使用 stream 而非 invoke，实时打印每一步
    # stream_mode="messages" 返回 (msg_chunk, metadata) 元组
    for chunk, _ in agent.stream(
        {"messages": [HumanMessage(content=user_input)]},
        stream_mode="messages",
    ):
        msg_type = getattr(chunk, "type", "?")
        content = getattr(chunk, "content", "") or ""
        tool_calls = getattr(chunk, "tool_calls", None)

        if msg_type == "AIMessageChunk":
            if content:
                # 打印 AI 的思考过程
                print(f"\n[🤔] {content[:300]}{'...' if len(content) > 300 else ''}")
            if tool_calls:
                for tc in tool_calls:
                    tc_name = tc.get("name", "?") or tc.get("name")
                    tc_args = tc.get("args", {}) or {}
                    if tc_name:
                        print(f"  └─ 📌 工具调用: {tc_name}")
                        print(f"      参数: {str(tc_args)[:200]}")

        elif msg_type == "tool":
            # 打印工具执行结果
            print(f"  └─ 🔧 工具返回: {content[:150]}{'...' if len(content) > 150 else ''}")

    print("\n" + "-" * 60)
    if list(OUTPUT_DIR.iterdir()):
        print(f"📂 生成的文件列表:")
        for f in sorted(OUTPUT_DIR.iterdir()):
            print(f"   - {f.name} ({f.stat().st_size} bytes)")
    else:
        print("📂 暂无生成文件（可能文件写入了虚拟文件系统而非真实目录）")


def demo_step_tracking(agent):
    """演示任务进度跟踪（流式输出）"""
    print("\n" + "=" * 60)
    print("【演示】任务进度跟踪（流式输出）")
    print("=" * 60)

    user_input = "帮我开发一个「栈数据结构」的演示程序，包含：搜索模板、编写代码、测试验证"

    print(f"\n📁 文件将保存到: {OUTPUT_DIR}\n")

    for chunk, _ in agent.stream(
        {"messages": [HumanMessage(content=user_input)]},
        stream_mode="messages",
    ):
        msg_type = getattr(chunk, "type", "?")
        content = getattr(chunk, "content", "") or ""
        tool_calls = getattr(chunk, "tool_calls", None)

        if msg_type == "AIMessageChunk":
            if content:
                print(f"\n[🤔] {content[:200]}{'...' if len(content) > 200 else ''}")
            if tool_calls:
                for tc in tool_calls:
                    tc_name = tc.get("name", "?") or tc.get("name")
                    tc_args = tc.get("args", {}) or {}
                    if tc_name:
                        print(f"  └─ 📌 {tc_name}: {str(tc_args)[:150]}")
        elif msg_type == "tool":
            print(f"  └─ 🔧 {content[:100]}{'...' if len(content) > 100 else ''}")


def main():
    parser = argparse.ArgumentParser(description="Deep Agent 任务规划演示")
    parser.add_argument("--dry-run", action="store_true", help="仅打印说明")
    args = parser.parse_args()

    print_planning_concepts()

    if args.dry_run:
        print("已 --dry-run，跳过模型调用。\n")
        return

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        sys.exit(1)

    print("正在构建规划 Agent（将调用 MiniMax API）...\n")

    agent = create_planning_agent()

    demo_multi_step_planning(agent)
    demo_step_tracking(agent)

    print(f"\n✅ 所有生成的文件已保存到: {OUTPUT_DIR}")
    print("演示结束。")


if __name__ == "__main__":
    main()
