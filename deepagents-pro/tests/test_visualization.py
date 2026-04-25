"""可视化工具测试"""

from pathlib import Path

import pandas as pd
import pytest

from deepagent_pro.tools.visualization import create_chart, create_heatmap


@pytest.fixture
def chart_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    df = pd.DataFrame({
        "month": ["Jan", "Feb", "Mar", "Apr", "May"],
        "revenue": [1000, 1200, 900, 1500, 1800],
        "cost": [800, 900, 700, 1000, 1100],
    })
    path = tmp_path / "chart_data.csv"
    df.to_csv(path, index=False)
    return str(path)


class TestVisualization:
    def test_create_line_chart(self, chart_csv):
        result = create_chart.invoke({
            "file_path": chart_csv,
            "chart_type": "line",
            "x_column": "month",
            "y_column": "revenue",
            "title": "月度收入趋势",
        })
        assert "图表已生成" in result

    def test_create_bar_chart(self, chart_csv):
        result = create_chart.invoke({
            "file_path": chart_csv,
            "chart_type": "bar",
            "x_column": "month",
            "y_column": "revenue",
        })
        assert "图表已生成" in result

    def test_create_scatter(self, chart_csv):
        result = create_chart.invoke({
            "file_path": chart_csv,
            "chart_type": "scatter",
            "x_column": "revenue",
            "y_column": "cost",
        })
        assert "图表已生成" in result

    def test_unsupported_chart_type(self, chart_csv):
        result = create_chart.invoke({
            "file_path": chart_csv,
            "chart_type": "radar",
            "x_column": "month",
            "y_column": "revenue",
        })
        assert "不支持" in result

    def test_heatmap(self, chart_csv):
        result = create_heatmap.invoke({"file_path": chart_csv})
        assert "热力图已生成" in result
