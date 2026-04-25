"""联网搜索（使用 ddgs 多引擎聚合，避免仅依赖国内不可达的 Bing）"""

from __future__ import annotations

import re

from langchain.tools import tool

# 命中时会在发往搜索引擎的 query 前锚定「本地真实日期」（与 get_current_time 同一时区），
# 缓解模型并行调用 get_current_time 与 web_search 时在搜索词里编造日期的问题。
_TIME_ANCHOR_PATTERNS = (
    "早报",
    "晨报",
    "午报",
    "晚报",
    "今日要闻",
    "今日新闻",
    "今天新闻",
    "今日资讯",
    "早间新闻",
    "新闻简报",
    "要闻速递",
    "morning briefing",
    "daily brief",
    "news briefing",
    "today's news",
    "today news",
)


def _query_needs_date_anchor(query: str) -> bool:
    q = (query or "").strip()
    if not q:
        return False
    low = q.lower()
    for p in _TIME_ANCHOR_PATTERNS:
        if p.lower() in low or p in q:
            return True
    return False


def _anchor_query_with_local_date(query: str) -> str:
    """在时间敏感查询前加上 YYYY-MM-DD，与服务器侧真实「今天」一致。"""
    from deepagent_pro.tools.current_time import local_date_iso_for_search

    q = (query or "").strip()
    if not q or not _query_needs_date_anchor(q):
        return q

    anchor = local_date_iso_for_search()
    # 已有同日锚点则不重复添加
    if anchor in q:
        return q
    # 已有其它 ISO 日期则不再前置（避免双日期堆叠；若模型写错年，用户可依赖提示词纠偏）
    if re.search(r"\b20\d{2}-\d{2}-\d{2}\b", q):
        return q

    return f"{anchor} {q}"


def _normalize_row(r: dict) -> dict[str, str]:
    """统一不同搜索引擎返回的字段名。"""
    title = r.get("title") or r.get("name") or ""
    url = r.get("href") or r.get("url") or ""
    snippet = r.get("body") or r.get("snippet") or ""
    return {
        "title": str(title).strip(),
        "url": str(url).strip(),
        "snippet": str(snippet).strip(),
    }


def run_web_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """执行网页搜索，返回结构化结果列表。"""
    q = _anchor_query_with_local_date((query or "").strip())
    if not q:
        return []

    n = max(1, min(int(max_results), 20))

    from ddgs import DDGS

    # auto：优先 Wikipedia/Grokipedia 等，不强制走 Bing（旧版 duckduckgo-search 8.x 曾锁死 Bing 导致国内全空）
    fallbacks = (
        "auto",
        "duckduckgo,yahoo,wikipedia",
        "mojeek",
    )
    last_err: Exception | None = None

    for backend in fallbacks:
        try:
            with DDGS(timeout=25) as ddgs:
                raw = ddgs.text(q, max_results=n, backend=backend)
            out = [_normalize_row(r) for r in raw]
            out = [r for r in out if r["title"] or r["url"] or r["snippet"]]
            if out:
                return out
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    return []


def _format_results_for_llm(results: list[dict[str, str]]) -> str:
    if not results:
        return "未找到相关网页结果，请尝试换用其他关键词。"
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        lines.append(f"{i}. {title}\n   链接: {url}\n   摘要: {snippet}")
    return "\n\n".join(lines)


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """在互联网上搜索与问题相关的网页摘要，用于补充背景信息、行业数据、术语定义或最新公开资料。

    涉及「今日」「早报」「晨报」等与**当天**强相关的检索时：应先用 ``get_current_time`` 确认时间再在搜索词里写清日期；
    若来不及分步调用，服务端也会对命中关键词的查询自动加上本地真实日期（与 ``get_current_time`` 相同时区），请勿在搜索词中编造日期。

    Args:
        query: 搜索关键词或一句话问题
        max_results: 返回的搜索结果条数，默认 5，最大 20
    """
    try:
        n = max(1, min(int(max_results), 20))
    except (TypeError, ValueError):
        n = 5
    try:
        rows = run_web_search(query, max_results=n)
        return _format_results_for_llm(rows)
    except Exception as e:
        return f"联网搜索失败: {e}"
