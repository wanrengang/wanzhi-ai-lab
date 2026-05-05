"""
DeepAgent 任务委派（SubAgent）演示

本示例展示 Deep Agents 的多代理编排能力：
1. 定义专业子代理（数据分析师、图表生成器、报告撰写者）
2. 注册子代理到主代理
3. 任务委派：主代理自动拆分任务并分发
4. 上下文隔离：子代理独立执行，主代理只看到摘要
5. 子代理权限覆盖

运行::

    pip install -e .
    python examples/delegation_demo.py

参考文档：https://docs.langchain.com/oss/python/deepagents/
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

from deepagents import create_deep_agent, SubAgent, AsyncSubAgent, FilesystemPermission
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from langgraph.checkpoint.memory import MemorySaver

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings


# ============== 路径转换工具 ==============

UPLOADS_DIR = _REPO_ROOT / "data" / "uploads"


def virtual_to_real_path(virtual_path: str) -> Path:
    """将虚拟路径（如 /data/file.csv）转换为真实文件系统路径。"""
    if virtual_path.startswith("/data/"):
        return UPLOADS_DIR / virtual_path[6:]
    return UPLOADS_DIR / virtual_path.lstrip("/data/")


def ensure_dir(path: Path) -> None:
    """确保目录存在。"""
    path.parent.mkdir(parents=True, exist_ok=True)


# ============== 定义子代理专用工具 ==============

@tool
def analyze_sales_data(file_path: str, output_path: str = "sales_analysis_summary.txt") -> str:
    """分析销售数据，计算关键指标，并保存结果到文件。

    注意：output_path 只是文件名，会自动保存到 data/uploads/ 目录。

    Args:
        file_path: CSV 文件路径（虚拟路径，如 /data/sales_demo.csv）
        output_path: 分析结果输出文件名（不要带路径，只写文件名）

    Returns:
        分析结果摘要（包含文件保存路径）
    """
    try:
        import pandas as pd

        real_file_path = virtual_to_real_path(file_path)
        df = pd.read_csv(str(real_file_path))
        numeric_cols = df.select_dtypes(include='number').columns
        stats = df[numeric_cols].describe()
        total_rows = len(df)

        output_file = virtual_to_real_path(output_path)
        ensure_dir(output_file)

        summary = f"""数据分析报告
================
数据规模：{total_rows} 行 x {len(df.columns)} 列

数值列统计：
{stats.to_string()}

分析时间：{pd.Timestamp.now()}
"""
        output_file.write_text(summary, encoding="utf-8")

        return f"数据分析完成，已保存到：{output_file.resolve()}"
    except Exception as e:
        return f"分析失败: {e}"


@tool
def write_report(title: str, content_summary: str, output_filename: str = "sales_report.md") -> str:
    """撰写数据分析报告（真实写入文件系统）。

    注意：output_filename 只是文件名，会自动保存到 data/uploads/ 目录。

    Args:
        title: 报告标题
        content_summary: 内容摘要
        output_filename: 输出文件名（不要带路径，只写文件名）

    Returns:
        报告撰写结果
    """
    output_file = virtual_to_real_path(output_filename)
    ensure_dir(output_file)

    report_content = f"""# {title}

{content_summary}

---
自动生成报告
"""
    output_file.write_text(report_content, encoding="utf-8")
    return f"报告已写入：{output_file.resolve()}"


@tool
def save_chart(data_path: str, chart_type: str = "折线图", output_filename: str = "sales_chart.png") -> str:
    """保存图表到文件系统（真实写入）。

    注意：output_filename 只是文件名，会自动保存到 data/uploads/ 目录。

    Args:
        data_path: 数据文件路径
        chart_type: 图表类型
        output_filename: 输出文件名（不要带路径，只写文件名）

    Returns:
        图表保存结果
    """
    output_file = virtual_to_real_path(output_filename)
    ensure_dir(output_file)

    # 创建占位文件（实际场景中这里会是真实图表生成）
    chart_content = f"图表类型：{chart_type}\n数据源：{data_path}\n（占位文件）"
    output_file.write_text(chart_content, encoding="utf-8")
    return f"图表已保存：{output_file.resolve()}"


# ============== 定义子代理 ==============

# 数据分析师子代理
data_analyst = SubAgent(
    name="data-analyst",
    description="""数据分析专家。当用户需要数据分析、统计计算、异常检测时使用此代理。
执行完成后返回简洁的分析摘要。""",
    system_prompt="""你是数据分析专家子代理。

工作流程：
1. 使用 analyze_sales_data 分析数据
2. 识别关键指标和异常
3. 返回简洁摘要（不超过 100 字）

注意：
- 只做分析，不生成图表
- 结果要简洁，突出关键发现""",
    tools=[analyze_sales_data],
)

# 图表生成器子代理
chart_generator = SubAgent(
    name="chart-generator",
    description="""图表生成专家。当用户需要生成可视化图表（折线图、柱状图、散点图等）时使用此代理。""",
    system_prompt="""你是图表生成专家子代理。

工作流程：
1. 使用 save_chart 将图表保存到 /data/ 目录
2. 返回图表保存位置

注意：
- 只负责生成图表
- 说明图表的适用场景""",
    tools=[save_chart],
)

# 报告撰写器子代理
report_writer = SubAgent(
    name="report-writer",
    description="""报告撰写专家。当用户需要生成数据分析报告时使用此代理。""",
    system_prompt="""你是报告撰写专家子代理。

工作流程：
1. 根据分析摘要撰写报告
2. 使用 write_report 将报告保存到 /data/ 目录
3. 返回报告结构和位置

注意：
- 报告要结构清晰
- 包含概述、发现、建议""",
    tools=[write_report],
)


# ============== 演示 1：基础任务委派 ==============

def build_basic_delegation_agent():
    """创建支持任务委派的主代理。"""
    # 映射真实目录到虚拟路径
    UPLOADS_DIR = _REPO_ROOT / "data" / "uploads"
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
        name="delegation-demo",
        model=build_model(),
        tools=[],  # 主代理不直接操作工具，委派给子代理
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt="""你是一个数据分析项目管理者。

当用户提出数据分析需求时，你应该：
1. 使用 write_todos 规划任务步骤
2. 将具体任务委派给专业子代理：
   - data-analyst：数据分析
   - chart-generator：图表生成
   - report-writer：报告撰写
3. 收集子代理返回的摘要，整合后回复用户

重要：子代理完成后会返回摘要，不要在主代理中重复执行子代理的工具。""",
        subagents=[data_analyst, chart_generator, report_writer],
    )
    return agent


def demo_basic_delegation(agent):
    """演示基础任务委派。"""
    print("\n" + "=" * 60)
    print("【演示 1】基础任务委派")
    print("=" * 60)
    print("主代理接收任务 → 拆解 → 委派给子代理 → 整合结果\n")

    cfg = {"configurable": {"thread_id": "basic-delegation"}}

    user_input = "分析 /data/sales_demo.csv 数据，生成折线图，并撰写报告，最终回复要包含各子代理的输出文件路径"

    print(f">>> 用户请求: {user_input}\n")

    out = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=cfg,
    )

    last = out["messages"][-1]
    print("--- 主代理最终回复 ---\n")
    print(getattr(last, "content", str(last))[:1500])


# ============== 主函数 ==============

def print_concepts() -> None:
    """打印任务委派核心概念。"""
    print("""
任务委派核心概念
================

1. SubAgent vs AsyncSubAgent
   - SubAgent：串行执行，等一个完成再执行下一个
   - AsyncSubAgent：并行执行，多个同时执行

2. 委派机制
   - 主代理使用 task() 工具调用子代理
   - 子代理由 description 决定被何时调用
   - 执行完成后返回摘要给主代理

3. 上下文隔离
   - 子代理有独立 context
   - 主代理只看到摘要，不看到细节
   - 子代理执行完 context 销毁

4. 权限继承与覆盖
   - 默认：子代理继承父代理权限
   - 覆盖：子代理设置 permissions 字段
   - 覆盖后完全替换，不是合并

5. 适用场景
   - 复杂任务拆解
   - 专业技能分离
   - 并行加速
   - Context 节省
""")


def main() -> None:
    # print_concepts()

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        exit(1)

    # 演示 1：基础任务委派
    print("\n>>> 构建基础委派智能体（将调用 MiniMax API）...")
    agent = build_basic_delegation_agent()
    demo_basic_delegation(agent)

    print("\n演示结束。\n")


if __name__ == "__main__":
    main()
