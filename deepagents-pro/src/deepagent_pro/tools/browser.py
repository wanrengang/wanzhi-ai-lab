"""精简浏览器自动化：同步 Playwright + aria 快照 ref（依赖可选 `playwright`）。

Playwright 同步 API 基于 greenlet，**必须在创建它的同一线程**上调用。LangGraph /
``asyncio.to_thread`` 可能在不同工作线程执行工具，会导致
``greenlet.error: cannot switch to a different thread``。
因此所有浏览器操作通过 **单线程** ``ThreadPoolExecutor(max_workers=1)`` 串行执行。
"""

from __future__ import annotations

import atexit
import concurrent.futures
import json
import logging
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from langchain.tools import tool

from deepagent_pro.config import get_settings
from deepagent_pro.tools.browser_snapshot import build_role_snapshot_from_aria

logger = logging.getLogger(__name__)

# 唯一 Playwright 所有者线程（与 QwenPaw 在 Windows 上使用单线程池的思路一致）
_browser_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="playwright-sync",
)

atexit.register(lambda: _browser_executor.shutdown(wait=False))

_state: dict[str, Any] = {
    "pw": None,
    "browser": None,
    "context": None,
    "pages": {},
    "refs": {},
    "current_page_id": None,
    "headed": False,
}


def _ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "未安装 Playwright。请执行: pip install playwright && playwright install chromium",
        ) from e
    return sync_playwright


def _parse_allowed_hosts(raw: str) -> list[str]:
    return [h.strip().lower() for h in (raw or "").split(",") if h.strip()]


def _check_url_allowed(url: str) -> None:
    u = (url or "").strip()
    if not u:
        raise ValueError("url 不能为空")
    parsed = urlparse(u)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("仅允许 http/https URL")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("无效的 URL")
    allowed = _parse_allowed_hosts(get_settings().browser_allowed_hosts)
    if not allowed:
        return
    for pat in allowed:
        if host == pat or host.endswith("." + pat):
            return
    raise ValueError(f"主机不在白名单内: {host}（配置 BROWSER_ALLOWED_HOSTS）")


def _stop_unlocked() -> None:
    for _pid, page in list(_state["pages"].items()):
        try:
            page.close()
        except Exception:
            logger.debug("page close failed", exc_info=True)
    _state["pages"].clear()
    _state["refs"].clear()
    _state["current_page_id"] = None
    try:
        if _state["context"] is not None:
            _state["context"].close()
    except Exception:
        logger.debug("context close failed", exc_info=True)
    try:
        if _state["browser"] is not None:
            _state["browser"].close()
    except Exception:
        logger.debug("browser close failed", exc_info=True)
    try:
        if _state["pw"] is not None:
            _state["pw"].stop()
    except Exception:
        logger.debug("playwright stop failed", exc_info=True)
    _state["context"] = None
    _state["browser"] = None
    _state["pw"] = None


def _launch_unlocked(headed: bool) -> None:
    if _state["context"] is not None:
        return
    sync_playwright = _ensure_playwright()
    _state["pw"] = sync_playwright().start()
    _state["headed"] = headed
    _state["browser"] = _state["pw"].chromium.launch(
        headless=not headed,
        args=["--no-sandbox"] if _in_container_hint() else [],
    )
    _state["context"] = _state["browser"].new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=False,
    )


def _in_container_hint() -> bool:
    try:
        return Path("/.dockerenv").exists()
    except OSError:
        return False


def _get_or_create_page(page_id: str):
    if page_id not in _state["pages"]:
        page = _state["context"].new_page()
        _state["pages"][page_id] = page
        _state["refs"][page_id] = {}
    return _state["pages"][page_id]


def _resolve_locator(page, page_id: str, ref: str, selector: str):
    if ref:
        refs = _state["refs"].get(page_id, {})
        info = refs.get(ref)
        if not info:
            raise ValueError(f"未知 ref「{ref}」，请先对该 page_id 执行 snapshot")
        role = str(info.get("role", "button"))
        name = info.get("name")
        nth = info.get("nth")
        loc = page.get_by_role(role, name=name if name else None)
        if nth is not None:
            loc = loc.nth(int(nth))
        return loc
    if selector and selector.strip():
        return page.locator(selector.strip())
    raise ValueError("click/type 需要 ref（来自 snapshot）或 CSS selector")


def _snapshot_page(page, page_id: str) -> dict[str, Any]:
    loc = page.locator("html")
    if not hasattr(loc, "aria_snapshot"):
        raise RuntimeError(
            "当前 Playwright 版本过旧，缺少 locator.aria_snapshot()，请升级: pip install -U playwright",
        )
    raw = loc.aria_snapshot()
    snap, refs = build_role_snapshot_from_aria(
        raw,
        interactive=True,
        compact=True,
        max_depth=24,
    )
    _state["refs"][page_id] = refs
    return {
        "snapshot": snap,
        "refs": refs,
        "ref_keys": list(refs.keys()),
    }


_TOOL_TIMEOUT_S = 600.0


def _browser_use_sync(
    action: str,
    url: str,
    page_id: str,
    ref: str,
    selector: str,
    text: str,
    headed: bool,
    submit: bool,
    full_page: bool,
) -> str:
    """在 Playwright 所属的单 worker 线程内执行。"""
    act = (action or "").strip().lower()
    pid = (page_id or "default").strip() or "default"

    def ok(payload: dict[str, Any]) -> str:
        return json.dumps({"ok": True, **payload}, ensure_ascii=False, indent=2)

    def err(msg: str) -> str:
        return json.dumps({"ok": False, "error": msg}, ensure_ascii=False, indent=2)

    try:
        if act == "stop":
            _stop_unlocked()
            return ok({"message": "浏览器已关闭"})

        if act == "start":
            _launch_unlocked(headed=bool(headed))
            return ok({"message": "浏览器已启动", "headed": bool(headed)})

        if act in ("open", "navigate"):
            u = (url or "").strip()
            _check_url_allowed(u)
            _launch_unlocked(headed=bool(headed))
            page = _get_or_create_page(pid)
            page.goto(u, timeout=90_000, wait_until="domcontentloaded")
            _state["current_page_id"] = pid
            return ok({"page_id": pid, "url": page.url, "title": page.title()})

        if act == "snapshot":
            if _state["context"] is None:
                return err("浏览器未启动；请先 open 或 start")
            if pid not in _state["pages"]:
                return err(f"未知 page_id: {pid}")
            page = _state["pages"][pid]
            data = _snapshot_page(page, pid)
            _state["current_page_id"] = pid
            return ok(
                {
                    "page_id": pid,
                    "url": page.url,
                    "title": page.title(),
                    "snapshot": data["snapshot"],
                    "ref_keys": data["ref_keys"],
                },
            )

        if act == "click":
            if _state["context"] is None:
                return err("浏览器未启动")
            if pid not in _state["pages"]:
                return err(f"未知 page_id: {pid}")
            page = _state["pages"][pid]
            loc = _resolve_locator(page, pid, ref.strip(), selector)
            loc.click(timeout=30_000)
            return ok({"page_id": pid})

        if act == "type":
            if _state["context"] is None:
                return err("浏览器未启动")
            if pid not in _state["pages"]:
                return err(f"未知 page_id: {pid}")
            page = _state["pages"][pid]
            loc = _resolve_locator(page, pid, ref.strip(), selector)
            t = text or ""
            loc.fill(t, timeout=30_000)
            if submit:
                page.keyboard.press("Enter")
            return ok({"page_id": pid})

        if act == "screenshot":
            if _state["context"] is None:
                return err("浏览器未启动")
            if pid not in _state["pages"]:
                return err(f"未知 page_id: {pid}")
            page = _state["pages"][pid]
            settings = get_settings()
            out_dir = Path(settings.browser_screenshots_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            name = f"shot_{int(time.time() * 1000)}.png"
            path = out_dir / name
            page.screenshot(path=str(path), full_page=bool(full_page))
            return ok({"page_id": pid, "path": str(path.resolve())})

        return err(
            f"未知 action: {action}。支持: start, stop, open, navigate, snapshot, click, type, screenshot",
        )
    except Exception as e:
        logger.warning("browser_use 同步逻辑失败: %s", e, exc_info=True)
        return err(str(e))


@tool
def browser_use(
    action: str,
    url: str = "",
    page_id: str = "default",
    ref: str = "",
    selector: str = "",
    text: str = "",
    headed: bool = False,
    submit: bool = False,
    full_page: bool = False,
) -> str:
    """控制无头/有头 Chromium（Playwright）。用于打开网页、截取可访问性快照（含 ref）、点击、输入。

    典型流程：start（可选）→ open 或 navigate 到目标 URL → snapshot 阅读页面与 ref →
    用 ref 调用 click / type → screenshot 保存截图 → stop 释放浏览器。

    Args:
        action: start | stop | open | navigate | snapshot | click | type | screenshot
        url: open/navigate 时必填的 http(s) 地址
        page_id: 标签页标识，默认 default；多任务时用不同 page_id
        ref: 快照中的元素 ref（如 e1）；点击/输入时优先于 selector
        selector: CSS 选择器；当没有 ref 时使用
        text: action=type 时的文本；submit=True 时在输入后按 Enter
        headed: action=start 或首次 open/navigate 时 True 表示有头模式（需本地图形环境）；已在运行时不会切换头/无头
        submit: type 后是否提交（回车）
        full_page: screenshot 是否整页长图
    """
    try:
        fut = _browser_executor.submit(
            _browser_use_sync,
            action,
            url,
            page_id,
            ref,
            selector,
            text,
            headed,
            submit,
            full_page,
        )
        return fut.result(timeout=_TOOL_TIMEOUT_S)
    except concurrent.futures.TimeoutError:
        logger.warning("browser_use 超时（%.0fs）", _TOOL_TIMEOUT_S)
        return json.dumps(
            {"ok": False, "error": f"浏览器操作超时（{_TOOL_TIMEOUT_S:.0f}s）"},
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        logger.warning("browser_use 失败: %s", e, exc_info=True)
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2)
