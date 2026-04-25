"""数据加载工具 - CSV / Excel 文件解析"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
from langchain.tools import tool


@tool
def load_csv(file_path: str, nrows: int | None = None) -> str:
    """加载 CSV 文件并返回预览信息。

    Args:
        file_path: CSV 文件路径
        nrows: 可选，只读取前 N 行
    """
    p = Path(file_path)
    if not p.exists():
        return f"错误：文件 '{file_path}' 不存在"
    try:
        df = pd.read_csv(p, nrows=nrows)
        return _summarize_dataframe(df, file_path)
    except Exception as e:
        return f"读取 CSV 失败: {e}"


@tool
def load_excel(file_path: str, sheet_name: str | None = None, nrows: int | None = None) -> str:
    """加载 Excel 文件并返回预览信息。

    Args:
        file_path: Excel (.xlsx) 文件路径
        sheet_name: 可选，指定工作表名称
        nrows: 可选，只读取前 N 行
    """
    p = Path(file_path)
    if not p.exists():
        return f"错误：文件 '{file_path}' 不存在"
    try:
        kwargs: dict = {"nrows": nrows}
        if sheet_name:
            kwargs["sheet_name"] = sheet_name
        df = pd.read_excel(p, **kwargs)
        return _summarize_dataframe(df, file_path)
    except Exception as e:
        return f"读取 Excel 失败: {e}"


@tool
def list_excel_sheets(file_path: str) -> str:
    """列出 Excel 文件中所有工作表名称。

    Args:
        file_path: Excel (.xlsx) 文件路径
    """
    p = Path(file_path)
    if not p.exists():
        return f"错误：文件 '{file_path}' 不存在"
    try:
        xls = pd.ExcelFile(p)
        sheets = xls.sheet_names
        return json.dumps({"file": file_path, "sheets": sheets}, ensure_ascii=False)
    except Exception as e:
        return f"读取 Excel 工作表失败: {e}"


@tool
def clean_data(file_path: str, operations: str) -> str:
    """对数据执行清洗操作并保存结果。

    Args:
        file_path: 数据文件路径 (CSV 或 Excel)
        operations: JSON 字符串描述的清洗操作列表。支持的操作:
            - {"action": "drop_na"} 删除包含空值的行
            - {"action": "drop_na", "columns": ["col1","col2"]} 指定列删除空值行
            - {"action": "fill_na", "value": 0} 用指定值填充空值
            - {"action": "fill_na", "method": "ffill"} 前向填充空值
            - {"action": "drop_duplicates"} 删除重复行
            - {"action": "rename", "mapping": {"old": "new"}} 重命名列
            - {"action": "astype", "column": "col", "dtype": "float"} 转换列类型
    """
    p = Path(file_path)
    if not p.exists():
        return f"错误：文件 '{file_path}' 不存在"

    try:
        ops = json.loads(operations)
    except json.JSONDecodeError:
        return "错误：operations 参数不是合法的 JSON"

    try:
        df = pd.read_csv(p) if p.suffix == ".csv" else pd.read_excel(p)
        rows_before = len(df)

        for op in (ops if isinstance(ops, list) else [ops]):
            action = op.get("action", "")
            if action == "drop_na":
                cols = op.get("columns")
                df = df.dropna(subset=cols) if cols else df.dropna()
            elif action == "fill_na":
                if "method" in op:
                    df = df.fillna(method=op["method"])
                else:
                    df = df.fillna(op.get("value", 0))
            elif action == "drop_duplicates":
                df = df.drop_duplicates()
            elif action == "rename":
                df = df.rename(columns=op.get("mapping", {}))
            elif action == "astype":
                df[op["column"]] = df[op["column"]].astype(op["dtype"])

        out_path = p.with_stem(p.stem + "_cleaned")
        if out_path.suffix == ".csv":
            df.to_csv(out_path, index=False)
        else:
            df.to_excel(out_path, index=False)

        return (
            f"清洗完成。原始行数: {rows_before}, 清洗后行数: {len(df)}。"
            f"结果已保存到: {out_path}"
        )
    except Exception as e:
        return f"数据清洗失败: {e}"


def _summarize_dataframe(df: pd.DataFrame, source: str) -> str:
    """生成 DataFrame 的摘要文本"""
    buf = io.StringIO()
    df.info(buf=buf)
    info_str = buf.getvalue()

    head_str = df.head(10).to_string(max_colwidth=40)

    return (
        f"=== 数据摘要 ({source}) ===\n"
        f"行数: {len(df)}, 列数: {len(df.columns)}\n"
        f"列名: {list(df.columns)}\n\n"
        f"--- 数据类型 ---\n{info_str}\n"
        f"--- 前10行预览 ---\n{head_str}\n"
    )
