"""子智能体定义"""

from deepagent_pro.agent.prompts import (
    DATA_CLEANER_PROMPT,
    STAT_ANALYZER_PROMPT,
    VIZ_GENERATOR_PROMPT,
    SQL_EXECUTOR_PROMPT,
    REPORT_WRITER_PROMPT,
)
from deepagent_pro.tools.data_loader import load_csv, load_excel, list_excel_sheets, clean_data
from deepagent_pro.tools.data_analysis import (
    describe_data,
    correlation_analysis,
    group_analysis,
    value_counts,
    filter_data,
)
from deepagent_pro.tools.visualization import create_chart, create_heatmap
from deepagent_pro.tools.sql_query import execute_sql, list_tables, describe_table
from deepagent_pro.tools.external_api import http_get, http_post


data_cleaner = {
    "name": "data-cleaner",
    "description": "数据清洗专家。处理 CSV/Excel 文件的数据质量问题：缺失值、重复行、类型转换、列重命名等。",
    "system_prompt": DATA_CLEANER_PROMPT,
    "tools": [load_csv, load_excel, list_excel_sheets, clean_data],
}

stat_analyzer = {
    "name": "stat-analyzer",
    "description": "统计分析专家。对数据进行描述性统计、相关性分析、分组聚合、值频次统计、数据筛选。",
    "system_prompt": STAT_ANALYZER_PROMPT,
    "tools": [describe_data, correlation_analysis, group_analysis, value_counts, filter_data],
}

viz_generator = {
    "name": "viz-generator",
    "description": "数据可视化专家。根据数据生成折线图、柱状图、散点图、饼图、直方图、箱线图和热力图。",
    "system_prompt": VIZ_GENERATOR_PROMPT,
    "tools": [create_chart, create_heatmap],
}

sql_executor = {
    "name": "sql-executor",
    "description": "SQL 查询专家。连接数据库，查看表结构，执行 SQL 查询并解读结果。适用于需要查询数据库的分析任务。",
    "system_prompt": SQL_EXECUTOR_PROMPT,
    "tools": [execute_sql, list_tables, describe_table],
}

report_writer = {
    "name": "report-writer",
    "description": "报告撰写专家。将数据分析结果整理为结构化的中文分析报告，包含概述、发现、可视化引用和结论建议。",
    "system_prompt": REPORT_WRITER_PROMPT,
    "tools": [],
}


ALL_SUBAGENTS = [
    data_cleaner,
    stat_analyzer,
    viz_generator,
    sql_executor,
    report_writer,
]
