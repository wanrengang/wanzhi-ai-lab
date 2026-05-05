"""
DeepAgent AsyncSubAgent 异步任务并行委派演示

本示例展示如何使用 AsyncSubAgent 实现真正的后台并行任务：

1. 启动后台任务（start_async_task）
2. 查询任务状态和结果（check_async_task）
3. 列出所有任务（list_async_tasks）
4. 取消任务（cancel_async_task）

运行::

    pip install -e .
    python examples/async_subagent_demo.py

参考文档：https://docs.langchain.com/oss/python/deepagents/async-subagents
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
import sys
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langchain_core.messages import HumanMessage

from deepagents import create_deep_agent, AsyncSubAgent, SubAgent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from langgraph.checkpoint.memory import MemorySaver

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings


# ============== 路径转换工具 ==============

UPLOADS_DIR = _REPO_ROOT / "data" / "uploads"


def virtual_to_real_path(virtual_path: str) -> Path:
    """将虚拟路径转换为真实路径。"""
    if virtual_path.startswith("/data/"):
        return UPLOADS_DIR / virtual_path[6:]
    return UPLOADS_DIR / virtual_path.lstrip("/data/")


def ensure_dir(path: Path) -> None:
    """确保目录存在。"""
    path.parent.mkdir(parents=True, exist_ok=True)


# ============== 异步子代理定义 ==============

# 异步数据分析专家
async_data_expert = AsyncSubAgent(
    name="async-data-expert",
    description="异步数据分析专家，处理数据分析任务",
    graph_id="async_data_graph",
)

# 异步可视化专家
async_viz_expert = AsyncSubAgent(
    name="async-viz-expert",
    description="异步可视化专家，处理图表生成任务",
    graph_id="async_viz_graph",
)


# ============== 同步子代理（用于对比） ==============

def slow_analysis(data: str) -> str:
    """模拟耗时的数据分析（sleep 2秒）"""
    import time
    time.sleep(2)
    return f"数据分析完成，结果：{data[:50]}..."


def slow_chart(data: str) -> str:
    """模拟耗时的图表生成（sleep 3秒）"""
    import time
    time.sleep(3)
    return f"图表生成完成：{data[:30]}..."


# ============== 构建异步任务 Agent ==============

def build_async_agent():
    """构建支持异步任务的主代理。"""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/data/": FilesystemBackend(
                root_dir=str(UPLOADS_DIR.resolve()),
                virtual_mode=True,
            ),
        },
    )

    agent = create_deep_agent(
        name="async-task-demo",
        model=build_model(),
        tools=[slow_analysis, slow_chart],  # 主代理自己的同步工具
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt="""你是任务调度专家，负责启动和管理后台异步任务。

可用异步子代理：
- async-data-expert：异步数据分析
- async-viz-expert：异步可视化

异步任务工具：
- start_async_task(subagent_name, task_description)：启动后台任务，立即返回 task_id
- check_async_task(task_id)：查询任务状态和结果
- list_async_tasks()：列出所有异步任务
- cancel_async_task(task_id)：取消任务

使用流程：
1. 调用 start_async_task 启动多个后台任务
2. 任务立即返回 task_id（不等待完成）
3. 定期调用 check_async_task 查看结果
4. 收集所有结果后整合回复用户

重要：启动任务后要立即返回 task_id，不要等待任务完成！""",
        subagents=[async_data_expert, async_viz_expert],
    )
    return agent


# ============== 演示函数 ==============

def demo_async_task_management(agent):
    """演示异步任务管理：启动、查询、取消、列表"""
    print("\n" + "=" * 60)
    print("【演示】异步任务并行管理")
    print("=" * 60)
    print("启动后台任务 → 不等待 → 查询结果 → 整合回复\n")

    cfg = {"configurable": {"thread_id": "async-demo"}}

    user_input = """请执行以下两个并行任务：
1. 分析 /data/sales_demo.csv 数据
2. 生成销售趋势折线图

请使用 start_async_task 工具启动这两个任务，
然后用 check_async_task 查询结果。"""

    print(f">>> 用户请求: 启动并行任务\n")

    out = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=cfg,
    )

    last = out["messages"][-1]
    print("--- 主代理回复 ---\n")
    print(getattr(last, "content", str(last))[:2000])


def demo_concurrent_vs_sequential():
    """演示并发 vs 串行的效率对比"""
    print("\n" + "=" * 60)
    print("【演示】并发 vs 串行 效率对比")
    print("=" * 60)

    import time

    print("\n--- 串行执行（总耗时 5秒）---")
    start = time.time()
    result1 = slow_analysis("分析数据任务A")
    result2 = slow_chart("图表任务B")
    elapsed = time.time() - start
    print(f"结果1: {result1}")
    print(f"结果2: {result2}")
    print(f"总耗时: {elapsed:.1f}秒")

    print("\n--- 并发执行（总耗时 3秒）---")
    start = time.time()
    import threading
    results = {}
    def task1():
        results['analysis'] = slow_analysis("分析数据任务A")
    def task2():
        results['chart'] = slow_chart("图表任务B")
    t1 = threading.Thread(target=task1)
    t2 = threading.Thread(target=task2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    elapsed = time.time() - start
    print(f"结果1: {results['analysis']}")
    print(f"结果2: {results['chart']}")
    print(f"总耗时: {elapsed:.1f}秒")


def print_concepts():
    """打印 AsyncSubAgent 核心概念"""
    print("""
AsyncSubAgent 核心概念
=====================

1. 异步 vs 同步
   - Sync SubAgent：阻塞等待，执行完一个再执行下一个
   - Async SubAgent：启动后台任务，立即返回，可并行执行

2. 异步任务工具
   - start_async_task：启动后台任务，返回 task_id
   - check_async_task：用 task_id 查询状态和结果
   - list_async_tasks：列出所有任务
   - cancel_async_task：取消任务

3. 执行流程
   ① start_async_task → 立即返回 task_id
   ② 任务在后台运行
   ③ check_async_task(task_id) → 查看状态
   ④ 任务完成 → 返回结果

4. 适用场景
   - 耗时的数据分析
   - 并行爬取多个数据源
   - 生成多个图表
   - 长时间运行的计算任务
""")


def main():
    print_concepts()

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        exit(1)

    print("\n>>> 构建异步任务 Agent（将调用 MiniMax API）...")
    agent = build_async_agent()
    demo_async_task_management(agent)

    # 演示并发 vs 串行效率
    demo_concurrent_vs_sequential()

    print("\n演示结束。\n")


if __name__ == "__main__":
    main()
