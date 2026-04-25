"""数据库查询可视化工具 - SQL 查询结果直接生成图表

解决痛点：原来需要「执行 SQL → 导出 CSV → create_chart」三步，
现在一条命令完成「SQL → 图表」。
"""

from __future__ import annotations

import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from langchain.tools import tool
from sqlalchemy import create_engine, text

from deepagent_pro.config import get_settings

plt.rcParams["axes.unicode_minus"] = False

_CHINESE_FONTS = ["SimHei", "Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei", "Noto Sans CJK SC"]
for _font in _CHINESE_FONTS:
    if any(_font.lower() in f.name.lower() for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [_font]
        break


def _output_path(name: str | None = None) -> Path:
    settings = get_settings()
    d = Path(settings.upload_dir) / "charts"
    d.mkdir(parents=True, exist_ok=True)
    fname = name or f"chart_{uuid.uuid4().hex[:8]}.png"
    return d / fname


@tool
def sql_to_chart(
    connection_url: str,
    query: str,
    chart_type: str,
    x_column: str = "",
    y_column: str = "",
    title: str = "",
    output_name: str | None = None,
) -> str:
    """执行 SQL 查询并将结果直接生成为图表。一步完成数据库查询 + 可视化。

    Args:
        connection_url: SQLAlchemy 连接字符串
        query: SQL 查询语句（结果需包含 x_column 和 y_column 指定的列）
        chart_type: 图表类型 (line / bar / scatter / pie / hist / box)
        x_column: X 轴对应的列名（hist 类型可省略）
        y_column: Y 轴对应的列名
        title: 图表标题
        output_name: 可选，输出文件名
    """
    try:
        # 1. 执行 SQL
        engine = create_engine(connection_url)
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)

        if df.empty:
            return "查询成功，但没有返回数据，无法生成图表。"

        rows = len(df)
        cols = list(df.columns)

        # 2. 自动推断列名（用户未指定时取前两列）
        if not x_column and chart_type != "hist":
            x_column = cols[0]
        if not y_column:
            y_column = cols[1] if len(cols) > 1 else cols[0]

        # 校验列名存在
        if x_column and x_column not in cols:
            return f"列 '{x_column}' 不存在。查询返回的列: {cols}"
        if y_column not in cols:
            return f"列 '{y_column}' 不存在。查询返回的列: {cols}"

        # 3. 生成图表
        fig, ax = plt.subplots(figsize=(12, 6))

        if chart_type == "line":
            ax.plot(df[x_column].astype(str), df[y_column], marker="o", markersize=4, linewidth=2)
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)

        elif chart_type == "bar":
            data = df.groupby(x_column)[y_column].sum().sort_values(ascending=False).head(30)
            bars = data.plot(kind="bar", ax=ax, color="#4C78A8")
            # 在柱子上标注数值
            for bar in ax.patches:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f"{height:,.0f}",
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3), textcoords="offset points",
                                ha="center", va="bottom", fontsize=8)

        elif chart_type == "scatter":
            ax.scatter(df[x_column], df[y_column], alpha=0.6, s=60, edgecolors="white", linewidth=0.5)
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)

        elif chart_type == "pie":
            data = df.groupby(x_column)[y_column].sum().head(10)
            data.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90)
            ax.set_ylabel("")

        elif chart_type == "hist":
            ax.hist(df[y_column].dropna(), bins=30, edgecolor="black", alpha=0.7, color="#4C78A8")
            ax.set_xlabel(y_column)
            ax.set_ylabel("频次")

        elif chart_type == "box":
            if x_column:
                df.boxplot(column=y_column, by=x_column, ax=ax)
                plt.suptitle("")
            else:
                ax.boxplot(df[y_column].dropna())
                ax.set_ylabel(y_column)

        else:
            plt.close(fig)
            return f"不支持的图表类型: {chart_type}。支持: line, bar, scatter, pie, hist, box"

        ax.set_title(title or f"{y_column} by {x_column}", fontsize=14, fontweight="bold")
        plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.tight_layout()

        # 4. 保存
        out = _output_path(output_name)
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return (
            f"图表已生成: {out}\n"
            f"数据: {rows} 行 × {len(cols)} 列\n"
            f"列: {', '.join(cols)}\n"
            f"图表类型: {chart_type} | X轴: {x_column or '-'} | Y轴: {y_column}"
        )

    except Exception as e:
        plt.close("all")
        return f"生成图表失败: {e}"
