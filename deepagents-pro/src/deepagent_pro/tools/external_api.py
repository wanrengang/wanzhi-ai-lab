"""外部 API 调用工具"""

from __future__ import annotations

import json

import httpx
from langchain.tools import tool


@tool
def http_get(url: str, headers: str | None = None, params: str | None = None) -> str:
    """发送 HTTP GET 请求并返回响应内容。

    Args:
        url: 请求 URL
        headers: 可选，JSON 格式的请求头
        params: 可选，JSON 格式的查询参数
    """
    try:
        h = json.loads(headers) if headers else {}
        p = json.loads(params) if params else {}
        resp = httpx.get(url, headers=h, params=p, timeout=30, follow_redirects=True)
        return _format_response(resp)
    except json.JSONDecodeError:
        return "错误：headers 或 params 不是合法的 JSON 格式"
    except Exception as e:
        return f"HTTP GET 请求失败: {e}"


@tool
def http_post(url: str, body: str, headers: str | None = None) -> str:
    """发送 HTTP POST 请求并返回响应内容。

    Args:
        url: 请求 URL
        body: JSON 格式的请求体
        headers: 可选，JSON 格式的请求头
    """
    try:
        h = json.loads(headers) if headers else {}
        h.setdefault("Content-Type", "application/json")
        b = json.loads(body)
        resp = httpx.post(url, headers=h, json=b, timeout=30, follow_redirects=True)
        return _format_response(resp)
    except json.JSONDecodeError:
        return "错误：body 或 headers 不是合法的 JSON 格式"
    except Exception as e:
        return f"HTTP POST 请求失败: {e}"


def _format_response(resp: httpx.Response) -> str:
    content_type = resp.headers.get("content-type", "")
    body = resp.text[:5000]

    if "json" in content_type:
        try:
            parsed = resp.json()
            body = json.dumps(parsed, ensure_ascii=False, indent=2)[:5000]
        except Exception:
            pass

    return (
        f"状态码: {resp.status_code}\n"
        f"Content-Type: {content_type}\n\n"
        f"响应内容:\n{body}"
    )
