"""API 端点测试"""

import io
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from deepagent_pro.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "deepagent-pro"


class TestChatHistory:
    def test_history_empty_thread(self, client):
        """无对话的检查点应返回空列表。"""
        resp = client.get("/api/v1/chat/00000000-0000-4000-8000-000000000001/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["thread_id"] == "00000000-0000-4000-8000-000000000001"
        assert data["messages"] == []

    def test_threads_list_ok(self, client):
        resp = client.get("/api/v1/chat/threads")
        assert resp.status_code == 200
        data = resp.json()
        assert "threads" in data
        assert isinstance(data["threads"], list)


class TestDatasource:
    def test_add_datasource(self, client):
        resp = client.post("/api/v1/datasource", json={
            "name": "test-db",
            "connection_url": "sqlite:///test.db",
            "description": "测试数据库",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test-db"

    def test_list_datasources(self, client):
        client.post("/api/v1/datasource", json={
            "name": "demo-db",
            "connection_url": "sqlite:///demo.db",
        })
        resp = client.get("/api/v1/datasource")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestAnalyze:
    def test_upload_csv(self, client, tmp_path):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)

        resp = client.post(
            "/api/v1/analyze",
            files={"file": ("test.csv", buf, "text/csv")},
            data={"question": "描述这份数据"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "processing"

    def test_task_not_found(self, client):
        resp = client.get("/api/v1/analyze/nonexistent")
        assert resp.status_code == 404


class TestSearch:
    @patch("deepagent_pro.api.routes.run_web_search")
    def test_search_ok(self, mock_search, client):
        mock_search.return_value = [
            {
                "title": "示例标题",
                "url": "https://example.com",
                "snippet": "摘要内容",
            }
        ]
        resp = client.post(
            "/api/v1/search",
            json={"query": "测试关键词", "max_results": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "测试关键词"
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "示例标题"

    def test_search_validation(self, client):
        resp = client.post("/api/v1/search", json={"query": ""})
        assert resp.status_code == 422


class TestUpload:
    def test_upload_csv(self, client):
        buf = io.BytesIO(b"a,b\n1,2")
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("sample.csv", buf, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "path" in data and "filename" in data
        assert data["filename"] == "sample.csv"
        assert str(data["path"]).endswith(".csv")
