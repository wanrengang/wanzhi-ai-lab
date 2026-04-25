"""可视化工具 - 图表生成"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from langchain.tools import tool

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


def _load(file_path: str) -> pd.DataFrame | str:
    p = Path(file_path)
    if not p.exists():
        return f"错误：文件 '{file_path}' 不存在"
    return pd.read_csv(p) if p.suffix == ".csv" else pd.read_excel(p)


@tool
def create_chart(
    file_path: str,
    chart_type: str,
    x_column: str,
    y_column: str,
    title: str = "",
    output_name: str | None = None,
) -> str:
    """根据数据创建图表并保存为图片。

    Args:
        file_path: 数据文件路径
        chart_type: 图表类型 (line / bar / scatter / pie / hist / box)
        x_column: X 轴数据列名
        y_column: Y 轴数据列名
        title: 图表标题
        output_name: 可选，输出文件名
    """
    result = _load(file_path)
    if isinstance(result, str):
        return result
    df = result

    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "line":
            ax.plot(df[x_column], df[y_column], marker="o", markersize=3)
        elif chart_type == "bar":
            data = df.groupby(x_column)[y_column].sum().head(30)
            data.plot(kind="bar", ax=ax)
        elif chart_type == "scatter":
            ax.scatter(df[x_column], df[y_column], alpha=0.6)
        elif chart_type == "pie":
            data = df.groupby(x_column)[y_column].sum().head(10)
            data.plot(kind="pie", ax=ax, autopct="%1.1f%%")
            ax.set_ylabel("")
        elif chart_type == "hist":
            ax.hist(df[y_column].dropna(), bins=30, edgecolor="black", alpha=0.7)
            x_column = y_column
        elif chart_type == "box":
            df.boxplot(column=y_column, by=x_column, ax=ax)
            plt.suptitle("")
        else:
            plt.close(fig)
            return f"不支持的图表类型: {chart_type}。支持: line, bar, scatter, pie, hist, box"

        ax.set_title(title or f"{y_column} by {x_column}")
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        out = _output_path(output_name)
        fig.savefig(out, dpi=150)
        plt.close(fig)

        return f"图表已生成: {out}"
    except Exception as e:
        plt.close("all")
        return f"创建图表失败: {e}"


@tool
def create_heatmap(
    file_path: str,
    title: str = "相关性热力图",
    output_name: str | None = None,
) -> str:
    """生成数值列的相关性热力图。

    Args:
        file_path: 数据文件路径
        title: 图表标题
        output_name: 可选，输出文件名
    """
    result = _load(file_path)
    if isinstance(result, str):
        return result
    df = result

    try:
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.shape[1] < 2:
            return "数值列不足 2 列，无法生成热力图"

        corr = numeric_df.corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
        fig.colorbar(im, ax=ax)

        labels = corr.columns.tolist()
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)

        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)

        ax.set_title(title)
        plt.tight_layout()

        out = _output_path(output_name)
        fig.savefig(out, dpi=150)
        plt.close(fig)

        return f"热力图已生成: {out}"
    except Exception as e:
        plt.close("all")
        return f"创建热力图失败: {e}"
