"""数据分析工具 - pandas 统计分析封装"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from langchain.tools import tool


def _load(file_path: str) -> pd.DataFrame | str:
    p = Path(file_path)
    if not p.exists():
        return f"错误：文件 '{file_path}' 不存在"
    if p.suffix == ".csv":
        return pd.read_csv(p)
    return pd.read_excel(p)


@tool
def describe_data(file_path: str, columns: str | None = None) -> str:
    """对数据进行描述性统计分析 (count, mean, std, min, 25%, 50%, 75%, max)。

    Args:
        file_path: 数据文件路径 (CSV 或 Excel)
        columns: 可选，逗号分隔的列名，仅分析指定列
    """
    result = _load(file_path)
    if isinstance(result, str):
        return result
    df = result
    try:
        if columns:
            cols = [c.strip() for c in columns.split(",")]
            df = df[cols]
        desc = df.describe(include="all").to_string()
        return f"=== 描述性统计 ({file_path}) ===\n{desc}"
    except Exception as e:
        return f"分析失败: {e}"


@tool
def correlation_analysis(file_path: str, method: str = "pearson") -> str:
    """计算数值列之间的相关性矩阵。

    Args:
        file_path: 数据文件路径
        method: 相关性计算方法 (pearson / spearman / kendall)
    """
    result = _load(file_path)
    if isinstance(result, str):
        return result
    df = result
    try:
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.empty:
            return "没有数值型列可以计算相关性"
        corr = numeric_df.corr(method=method).to_string()
        return f"=== 相关性矩阵 ({method}) ===\n{corr}"
    except Exception as e:
        return f"相关性分析失败: {e}"


@tool
def group_analysis(file_path: str, group_by: str, agg_column: str, agg_func: str = "mean") -> str:
    """按指定列分组并聚合统计。

    Args:
        file_path: 数据文件路径
        group_by: 分组依据的列名
        agg_column: 要聚合的列名
        agg_func: 聚合函数 (mean / sum / count / min / max / median / std)
    """
    result = _load(file_path)
    if isinstance(result, str):
        return result
    df = result
    try:
        grouped = df.groupby(group_by)[agg_column].agg(agg_func)
        return (
            f"=== 分组分析 ===\n"
            f"分组: {group_by}, 聚合: {agg_func}({agg_column})\n\n"
            f"{grouped.to_string()}"
        )
    except Exception as e:
        return f"分组分析失败: {e}"


@tool
def value_counts(file_path: str, column: str, top_n: int = 20) -> str:
    """统计某列的值分布频次。

    Args:
        file_path: 数据文件路径
        column: 要统计的列名
        top_n: 显示前 N 个最常见的值
    """
    result = _load(file_path)
    if isinstance(result, str):
        return result
    df = result
    try:
        vc = df[column].value_counts().head(top_n)
        total = len(df)
        return (
            f"=== 值频次统计: {column} (共 {total} 行) ===\n"
            f"{vc.to_string()}\n\n"
            f"唯一值数量: {df[column].nunique()}, 缺失值: {df[column].isna().sum()}"
        )
    except Exception as e:
        return f"值频次统计失败: {e}"


@tool
def filter_data(file_path: str, query_expr: str, output_path: str | None = None) -> str:
    """使用 pandas query 表达式筛选数据。

    Args:
        file_path: 数据文件路径
        query_expr: pandas query 表达式，例如 "age > 30 and city == '北京'"
        output_path: 可选，筛选结果保存路径
    """
    result = _load(file_path)
    if isinstance(result, str):
        return result
    df = result
    try:
        filtered = df.query(query_expr)
        summary = (
            f"筛选条件: {query_expr}\n"
            f"原始行数: {len(df)}, 筛选后行数: {len(filtered)}\n\n"
            f"--- 前10行 ---\n{filtered.head(10).to_string(max_colwidth=40)}"
        )
        if output_path:
            p = Path(output_path)
            if p.suffix == ".csv":
                filtered.to_csv(p, index=False)
            else:
                filtered.to_excel(p, index=False)
            summary += f"\n\n结果已保存到: {output_path}"
        return summary
    except Exception as e:
        return f"筛选失败: {e}"
