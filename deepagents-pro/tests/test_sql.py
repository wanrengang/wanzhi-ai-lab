"""SQL 工具测试"""

import sqlite3
from pathlib import Path

import pytest

from deepagent_pro.tools.sql_query import execute_sql, list_tables, describe_table


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            city TEXT
        )
    """)
    cursor.executemany(
        "INSERT INTO users (name, age, city) VALUES (?, ?, ?)",
        [
            ("Alice", 25, "北京"),
            ("Bob", 30, "上海"),
            ("Charlie", 28, "深圳"),
        ],
    )
    conn.commit()
    conn.close()
    return f"sqlite:///{db_path}"


class TestSQLTools:
    def test_list_tables(self, test_db):
        result = list_tables.invoke({"connection_url": test_db})
        assert "users" in result

    def test_describe_table(self, test_db):
        result = describe_table.invoke({"connection_url": test_db, "table_name": "users"})
        assert "name" in result
        assert "age" in result
        assert "city" in result

    def test_execute_select(self, test_db):
        result = execute_sql.invoke({
            "connection_url": test_db,
            "query": "SELECT * FROM users WHERE age > 25",
        })
        assert "Bob" in result
        assert "Charlie" in result

    def test_execute_count(self, test_db):
        result = execute_sql.invoke({
            "connection_url": test_db,
            "query": "SELECT COUNT(*) as total FROM users",
        })
        assert "3" in result
