"""
DeepAgent SubAgent 同步任务委派演示

本示例展示如何使用 SubAgent 实现任务委派：

1. 定义字典风格 SubAgent
2. 任务委派（task 工具）
3. 上下文隔离（子代理执行细节对主代理不可见）
4. 权限继承与覆盖

运行::

    pip install -e .
    python examples/subagent_demo.py

参考文档：https://docs.langchain.com/oss/python/deepagents/subagents
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
import sys
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langchain.tools import tool
from langchain_core.messages import HumanMessage

from deepagents import create_deep_agent, SubAgent, FilesystemPermission
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


# ============== 子代理专用工具 ==============

@tool
def analyze_csv(file_path: str, output_filename: str = "analysis_result.txt") -> str:
    """分析 CSV 文件，计算统计指标并保存结果。

    Args:
        file_path: CSV 文件路径（虚拟路径，如 /data/sales_demo.csv）
        output_filename: 输出文件名

    Returns:
        分析结果
    """
    import pandas as pd

    real_path = virtual_to_real_path(file_path)
    df = pd.read_csv(str(real_path))

    output_file = virtual_to_real_path(output_filename)
    ensure_dir(output_file)

    numeric_cols = df.select_dtypes(include='number').columns
    stats = df[numeric_cols].describe()

    result = f"""CSV 数据分析报告
================
文件：{file_path}
数据规模：{len(df)} 行 x {len(df.columns)} 列

数值列统计：
{stats.to_string()}
"""
    output_file.write_text(result, encoding="utf-8")
    return f"分析完成，已保存到 {output_filename}"


@tool
def create_chart(data_file: str, chart_type: str, output_filename: str = "chart.png") -> str:
    """生成图表并保存。

    Args:
        data_file: 数据文件路径
        chart_type: 图表类型（折线图/柱状图/散点图）
        output_filename: 输出文件名

    Returns:
        图表保存结果
    """
    output_file = virtual_to_real_path(output_filename)
    ensure_dir(output_file)

    content = f"图表类型：{chart_type}\n数据源：{data_file}\n（模拟图表内容）"
    output_file.write_text(content, encoding="utf-8")
    return f"图表已保存到 {output_filename}"


@tool
def write_doc(title: str, content: str, output_filename: str = "document.md") -> str:
    """撰写文档并保存。

    Args:
        title: 文档标题
        content: 文档内容
        output_filename: 输出文件名

    Returns:
        文档保存结果
    """
    output_file = virtual_to_real_path(output_filename)
    ensure_dir(output_file)

    doc = f"# {title}\n\n{content}\n\n---\n自动生成"
    output_file.write_text(doc, encoding="utf-8")
    return f"文档已保存到 {output_filename}"


# ============== SubAgent 定义 ==============

# 数据分析子代理
data_analyst = SubAgent(
    name="data-analyst",
    description="数据分析专家。当用户需要分析 CSV 数据、计算统计指标时使用此代理。",
    system_prompt="""你是数据分析专家子代理。

工作流程：
1. 使用 analyze_csv 工具分析数据
2. 将结果保存到文件
3. 返回简洁摘要（不超过 50 字），包含：分析文件、分析指标数量、结果文件路径

注意：
- 只做数据分析，不要生成图表
- 返回内容要简洁，突出关键指标""",
    tools=[analyze_csv],
)

# 图表生成子代理
chart_maker = SubAgent(
    name="chart-maker",
    description="图表专家。当用户需要生成折线图、柱状图、散点图等可视化图表时使用此代理。",
    system_prompt="""你是图表生成专家子代理。

工作流程：
1. 理解用户需要的图表类型
2. 使用 create_chart 生成图表
3. 返回简洁摘要，包含图表类型和保存路径

注意：
- 只负责生成图表
- 说明图表的适用场景""",
    tools=[create_chart],
)

# 文档撰写子代理
doc_writer = SubAgent(
    name="doc-writer",
    description="文档专家。当用户需要撰写报告、文档、说明文档时使用此代理。",
    system_prompt="""你是文档撰写专家子代理。

工作流程：
1. 理解用户需要的文档类型
2. 使用 write_doc 生成文档
3. 返回简洁摘要，包含文档标题和保存路径

注意：
- 文档要结构清晰
- 突出重点内容""",
    tools=[write_doc],
)


# ============== 主代理构建 ==============

def build_subagent_demo():
    """构建支持任务委派的主代理。"""
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

    # 主代理
    agent = create_deep_agent(
        name="subagent-demo",
        model=build_model(),
        tools=[],  # 主代理不直接操作工具，委派给子代理
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt="""你是数据分析项目协调者。

当用户提出数据分析需求时：
1. 使用 write_todos 规划任务步骤
2. 将具体任务委派给专业子代理：
   - data-analyst：数据分析
   - chart-maker：图表生成
   - doc-writer：文档撰写
3. 通过 task() 工具调用子代理
4. 收集子代理返回的摘要，整合后回复用户

重要：
- 子代理执行完成后只返回摘要，不要重复执行子代理的工具
- 最终回复要清晰展示各子代理的输出文件路径""",
        subagents=[data_analyst, chart_maker, doc_writer],
    )
    return agent


# ============== 演示 ==============

def demo_subagent_delegation():
    """演示子代理委派"""
    print("\n" + "=" * 60)
    print("【演示】SubAgent 任务委派")
    print("=" * 60)
    print("主代理接收任务 → 委派给子代理 → 子代理返回摘要\n")

    agent = build_subagent_demo()
    cfg = {"configurable": {"thread_id": "subagent-demo-1"}}

    user_input = "分析 /data/sales_demo.csv 数据，生成一个销售趋势折线图，并撰写一份分析报告"

    print(f">>> 用户请求: {user_input}\n")

    out = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=cfg,
    )

    last = out["messages"][-1]
    print("--- 主代理最终回复 ---\n")
    print(getattr(last, "content", str(last))[:2000])

    print("\n--- 验证生成的文件 ---")
    for f in UPLOADS_DIR.glob("*"):
        if f.stat().st_size > 0:
            print(f"  {f.name} ({f.stat().st_size} bytes)")


def print_concepts():
    """打印 SubAgent 核心概念"""
    print("""
SubAgent 核心概念
================

1. SubAgent vs AsyncSubAgent
   - SubAgent：同步阻塞，执行完返回摘要
   - AsyncSubAgent：非阻塞，后台任务，可并行

2. SubAgent 字典字段
   - name：唯一标识符
   - description：任务描述（用于主代理决定委派给谁）
   - system_prompt：子代理指令
   - tools：子代理专用工具（可选）
   - permissions：权限覆盖（可选）

3. 任务委派流程
   ① 用户请求 → 主代理
   ② 主代理调用 task() 工具
   ③ 子代理执行（独立 context）
   ④ 子代理返回摘要
   ⑤ 主代理整合结果

4. 上下文隔离
   - 子代理的中间过程主代理不可见
   - 只看到最终摘要
   - 节省主代理 context

5. 适用场景
   - 多步骤复杂任务
   - 专业技能分离
   - Context 节省
   - 并行协调
""")


def main():
    print_concepts()

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        exit(1)

    demo_subagent_delegation()
    print("\n演示结束。\n")


if __name__ == "__main__":
    main()
