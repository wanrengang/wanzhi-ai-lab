"""工具函数单元测试"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from deepagent_pro.tools.data_loader import load_csv, load_excel, clean_data
from deepagent_pro.tools.data_analysis import (
    describe_data,
    correlation_analysis,
    group_analysis,
    value_counts,
    filter_data,
)
from deepagent_pro.tools.current_time import get_current_time, set_user_timezone
from deepagent_pro.config import get_settings


@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "age": [25, 30, None, 28, 35],
        "city": ["北京", "上海", "北京", "深圳", "上海"],
        "salary": [10000, 15000, 12000, 18000, 20000],
    })
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def sample_excel(tmp_path):
    df = pd.DataFrame({
        "product": ["A", "B", "C", "A", "B"],
        "sales": [100, 200, 150, 120, 180],
        "quarter": ["Q1", "Q1", "Q2", "Q2", "Q3"],
    })
    path = tmp_path / "sample.xlsx"
    df.to_excel(path, index=False)
    return str(path)


class TestDataLoader:
    def test_load_csv(self, sample_csv):
        result = load_csv.invoke({"file_path": sample_csv})
        assert "行数: 5" in result
        assert "列数: 4" in result
        assert "name" in result

    def test_load_csv_not_found(self):
        result = load_csv.invoke({"file_path": "/nonexistent.csv"})
        assert "不存在" in result

    def test_load_excel(self, sample_excel):
        result = load_excel.invoke({"file_path": sample_excel})
        assert "行数: 5" in result
        assert "product" in result

    def test_clean_data_drop_na(self, sample_csv):
        ops = json.dumps([{"action": "drop_na"}])
        result = clean_data.invoke({"file_path": sample_csv, "operations": ops})
        assert "清洗完成" in result
        assert "原始行数: 5" in result
        assert "cleaned" in result

    def test_clean_data_fill_na(self, sample_csv):
        ops = json.dumps([{"action": "fill_na", "value": 0}])
        result = clean_data.invoke({"file_path": sample_csv, "operations": ops})
        assert "清洗完成" in result


class TestCurrentTime:
    def test_get_current_time_format(self):
        out = get_current_time.invoke({})
        assert len(out) > 10
        assert "(" in out and ")" in out

    def test_set_user_timezone_invalid(self):
        out = set_user_timezone.invoke({"timezone_name": "Not/A/Real/Zone"})
        assert "Error" in out

    def test_set_then_get_shanghai(self, monkeypatch, tmp_path):
        prefs = tmp_path / "user_timezone.json"

        def _fake_prefs_path():
            return prefs

        monkeypatch.setattr(
            "deepagent_pro.tools.current_time._prefs_path",
            _fake_prefs_path,
        )
        set_out = set_user_timezone.invoke({"timezone_name": "Asia/Shanghai"})
        assert "Timezone set to Asia/Shanghai" in set_out
        get_out = get_current_time.invoke({})
        assert "Asia/Shanghai" in get_out

    def test_user_timezone_from_env(self, monkeypatch, tmp_path):
        def _fake_prefs():
            return tmp_path / "user_timezone.json"

        monkeypatch.setattr(
            "deepagent_pro.tools.current_time._prefs_path",
            _fake_prefs,
        )
        monkeypatch.setenv("USER_TIMEZONE", "Europe/London")
        get_settings.cache_clear()
        try:
            out = get_current_time.invoke({})
            assert "Europe/London" in out
        finally:
            get_settings.cache_clear()


class TestDataAnalysis:
    def test_describe_data(self, sample_csv):
        result = describe_data.invoke({"file_path": sample_csv})
        assert "描述性统计" in result
        assert "mean" in result

    def test_describe_data_specific_columns(self, sample_csv):
        result = describe_data.invoke({"file_path": sample_csv, "columns": "age,salary"})
        assert "描述性统计" in result

    def test_correlation(self, sample_csv):
        result = correlation_analysis.invoke({"file_path": sample_csv})
        assert "相关性矩阵" in result

    def test_group_analysis(self, sample_csv):
        result = group_analysis.invoke({
            "file_path": sample_csv,
            "group_by": "city",
            "agg_column": "salary",
            "agg_func": "mean",
        })
        assert "分组分析" in result

    def test_value_counts(self, sample_csv):
        result = value_counts.invoke({"file_path": sample_csv, "column": "city"})
        assert "频次统计" in result
        assert "北京" in result

    def test_filter_data(self, sample_csv):
        result = filter_data.invoke({
            "file_path": sample_csv,
            "query_expr": "salary > 12000",
        })
        assert "筛选条件" in result
