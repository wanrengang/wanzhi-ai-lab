"""
DeepAgent-Pro HTTP API 路由。

主要能力：
- 对话：非流式 POST /chat、流式 GET /chat/{thread_id}/stream（SSE）
- 会话：线程列表、按 thread_id 拉取历史（LangGraph 检查点）
- 上传：数据文件上传；独立任务 /analyze 异步分析
- 数据源 CRUD、联网搜索代理
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
import time

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import ToolMessage

from deepagent_pro.api.chat_history import (
    list_checkpoint_thread_ids,
    messages_checkpoint_to_rows,
    preview_text_from_rows,
)
from deepagent_pro.api.schemas import (
    ChatHistoryMessage,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ChatThreadListResponse,
    ChatThreadSummary,
    AnalyzeResponse,
    TaskStatus,
    TaskStatusResponse,
    DataSourceCreate,
    DataSourceResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    UploadResponse,
)
from deepagent_pro.api.deps import get_agent, get_datasources, get_tasks, new_task_id
from deepagent_pro.config import get_settings
from deepagent_pro.storage.file_manager import save_upload
from deepagent_pro.tools.web_search import run_web_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


def _tool_call_item_to_dict(tc: object) -> dict[str, object]:
    """将 LangGraph / LangChain 的 tool_call 项转为 dict（元素可能是 dict 或带属性的对象）。"""
    if isinstance(tc, dict):
        name = tc.get("name", "") or ""
        args = tc.get("args", {}) or {}
        tid = tc.get("id") or tc.get("tool_call_id") or ""
        if not isinstance(args, dict):
            args = {}
        return {"name": name, "args": args, "id": str(tid).strip() if tid else ""}
    name = getattr(tc, "name", None) or ""
    args = getattr(tc, "args", None) or {}
    if not isinstance(args, dict):
        args = {}
    tid = getattr(tc, "id", None) or getattr(tc, "tool_call_id", None) or ""
    return {"name": name, "args": args, "id": str(tid).strip() if tid else ""}


def _preview(text: str, max_len: int = 400) -> str:
    """日志里用的短预览：去换行、截断，避免刷屏。"""
    s = (text or "").replace("\n", " ").strip()
    if len(s) <= max_len:
        return s
    return s[:max_len] + "…"


def _tool_content_for_sse(content: object, max_len: int = 16_000) -> str:
    """工具返回内容序列化为字符串；过长则截断，防止 SSE payload 过大。"""
    if isinstance(content, str):
        text = content
    else:
        try:
            text = json.dumps(content, ensure_ascii=False)
        except TypeError:
            text = str(content)
    if len(text) > max_len:
        return text[:max_len] + "\n…(truncated)"
    return text


def _chat_user_content(message: str, file_paths: list[str] | None) -> str:
    """把关联文件路径拼进用户内容（非流式 / SSE 共用）。"""
    content = message
    if file_paths:
        content += "\n\n关联数据文件:\n" + "\n".join(f"- {p}" for p in file_paths)
    return content


def _langgraph_run_config(thread_id: str) -> dict:
    """invoke/stream 用配置；metadata 会进入 LangSmith，便于按 thread_id 过滤。"""
    return {
        "configurable": {"thread_id": thread_id},
        "metadata": {"thread_id": thread_id},
    }


# ── 数据文件上传（供对话 file_paths 使用）──


@router.post("/upload", response_model=UploadResponse)
async def upload_data_file(file: UploadFile = File(...)):
    """上传 CSV/Excel 等数据文件，返回服务器路径；前端在发送对话时把 path 填入 file_paths。"""
    logger.info("upload_start filename=%s", file.filename or "")
    try:
        saved = await save_upload(file)
    except ValueError as e:
        logger.warning("upload_rejected: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.info("upload_done path=%s", saved)
    return UploadResponse(path=str(saved), filename=file.filename or saved.name)


# ── 对话式分析 ──


@router.get("/chat/threads", response_model=ChatThreadListResponse)
async def list_chat_threads():
    """列出检查点中存在的会话线程及首条预览，供前端侧栏展示。"""
    settings = get_settings()
    ids = list_checkpoint_thread_ids(settings.checkpoint_sqlite_path, limit=60)
    agent = get_agent()
    summaries: list[ChatThreadSummary] = []

    def _state_messages(tid: str):
        """在线程池中读检查点状态，避免阻塞事件循环。"""
        return agent.get_state({"configurable": {"thread_id": tid}})

    for tid in ids:
        try:
            snap = await asyncio.to_thread(_state_messages, tid)
        except Exception:
            logger.exception("list_threads_state_failed thread_id=%s", tid)
            summaries.append(ChatThreadSummary(thread_id=tid, preview=""))
            continue
        msgs: list = []
        if snap and getattr(snap, "values", None):
            msgs = snap.values.get("messages") or []
        rows = messages_checkpoint_to_rows(msgs)
        pv = preview_text_from_rows(rows)
        summaries.append(ChatThreadSummary(thread_id=tid, preview=pv))

    return ChatThreadListResponse(threads=summaries)


@router.get("/chat/{thread_id}/history", response_model=ChatHistoryResponse)
async def chat_history(thread_id: str):
    """从 LangGraph 检查点读取该线程的 user/assistant 文本，供前端刷新后恢复展示。"""
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    def _read_state():
        """同步读图状态；由 asyncio.to_thread 包装执行。"""
        return agent.get_state(config)

    try:
        snap = await asyncio.to_thread(_read_state)
    except Exception:
        logger.exception("chat_history_read_failed thread_id=%s", thread_id)
        raise HTTPException(status_code=500, detail="读取对话状态失败") from None

    msgs: list = []
    if snap and getattr(snap, "values", None):
        msgs = snap.values.get("messages") or []
    rows = messages_checkpoint_to_rows(msgs)
    return ChatHistoryResponse(
        thread_id=thread_id,
        messages=[ChatHistoryMessage(role=r["role"], content=r["content"]) for r in rows],
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_analyze(req: ChatRequest):
    """非流式对话：整轮 invoke 结束后一次性返回助手正文 + 工具调用摘要。"""
    logger.info(
        "chat_start thread_id=%s file_paths=%s preview=%s",
        req.thread_id,
        len(req.file_paths or []),
        _preview(req.message),
    )
    t0 = time.perf_counter()
    agent = get_agent()

    content = _chat_user_content(req.message, req.file_paths or None)

    config = _langgraph_run_config(req.thread_id)

    try:
        # LangGraph 同步 invoke 放到线程池，避免阻塞 async 服务
        result = await asyncio.to_thread(
            agent.invoke,
            {"messages": [{"role": "user", "content": content}]},
            config=config,
        )
    except Exception:
        logger.exception("chat_invoke_failed thread_id=%s", req.thread_id)
        raise

    last_msg = result["messages"][-1]
    response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # 遍历完整消息列表，收集本轮工具调用与 ToolMessage 结果（供前端展示）
    tool_calls = []
    tool_results: list[dict] = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                d = _tool_call_item_to_dict(tc)
                tool_calls.append({
                    "name": d["name"],
                    "args": d["args"],
                    "id": d["id"],
                })
        if isinstance(msg, ToolMessage):
            tool_results.append({
                "name": getattr(msg, "name", None) or "",
                "tool_call_id": getattr(msg, "tool_call_id", "") or "",
                "content": _tool_content_for_sse(msg.content, max_len=32_000),
                "status": getattr(msg, "status", "success"),
            })

    ms = (time.perf_counter() - t0) * 1000
    names = [tc["name"] for tc in tool_calls if tc.get("name")]
    logger.info(
        "chat_done thread_id=%s ms=%.1f tool_calls=%s tools=%s response_len=%s",
        req.thread_id,
        ms,
        len(tool_calls),
        names[:20],
        len(response_text or ""),
    )

    return ChatResponse(
        thread_id=req.thread_id,
        response=response_text,
        tool_calls=tool_calls,
        tool_results=tool_results,
    )


# ── SSE 流式响应 ──
# 前端用 EventSource 订阅；事件类型：start / message / tool_call / tool_result / done / stream_error


@router.get("/chat/{thread_id}/stream")
async def chat_stream(
    thread_id: str,
    message: str,
    file_paths: list[str] = Query(default_factory=list),
):
    """流式对话：LangGraph stream_mode=messages，按块推送 AIMessage 与工具相关事件。

    注：多为「消息块」更新，不保证严格逐 token；`file_paths` 可重复 query 传多个路径。
    """
    logger.info(
        "stream_start thread_id=%s file_paths=%s preview=%s",
        thread_id,
        len(file_paths or []),
        _preview(message),
    )
    agent = get_agent()
    config = _langgraph_run_config(thread_id)
    user_content = _chat_user_content(message, file_paths or None)

    async def event_generator():
        """异步生成器：后台线程跑同步 stream，主协程从队列取块并格式化为 SSE。"""
        yield _sse("start", json.dumps({"thread_id": thread_id}))
        t0 = time.perf_counter()
        tool_n = 0
        msg_n = 0

        # 同步迭代器不能在 async 里直接 for，用队列 + 守护线程桥接
        q: queue.Queue[tuple[object, dict] | None] = queue.Queue()
        stream_exc: list[BaseException] = []

        def producer() -> None:
            try:
                for chunk, metadata in agent.stream(
                    {"messages": [{"role": "user", "content": user_content}]},
                    config=config,
                    stream_mode="messages",
                ):
                    q.put((chunk, metadata))
            except BaseException as e:
                stream_exc.append(e)
            finally:
                q.put(None)  # 哨兵，通知消费者结束

        threading.Thread(target=producer, daemon=True).start()

        try:
            while True:
                item = await asyncio.to_thread(q.get)
                if item is None:
                    break
                chunk, metadata = item
                node = metadata.get("langgraph_node", "")  # 当前节点名，便于前端分段
                if isinstance(chunk, ToolMessage):
                    tool_n += 1
                    payload = {
                        "name": getattr(chunk, "name", None) or "",
                        "tool_call_id": getattr(chunk, "tool_call_id", "") or "",
                        "content": _tool_content_for_sse(chunk.content),
                        "status": getattr(chunk, "status", "success"),
                    }
                    logger.info(
                        "stream_tool_result thread_id=%s node=%s name=%s",
                        thread_id,
                        node,
                        payload.get("name"),
                    )
                    yield _sse("tool_result", json.dumps(payload, ensure_ascii=False))
                    continue
                # AIMessage 上挂带的待执行工具调用（含稳定 id，与 ToolMessage 对齐）
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    for tc in chunk.tool_calls:
                        d = _tool_call_item_to_dict(tc)
                        tool_n += 1
                        logger.info(
                            "stream_tool_call thread_id=%s node=%s name=%s",
                            thread_id,
                            node,
                            d.get("name", ""),
                        )
                        yield _sse(
                            "tool_call",
                            json.dumps(
                                {
                                    "name": d.get("name", ""),
                                    "args": d.get("args", {}),
                                    "id": d.get("id", ""),
                                },
                                ensure_ascii=False,
                            ),
                        )
                # 助手文本增量（content 可能为整段或块，取决于模型与 graph）
                if hasattr(chunk, "content") and chunk.content:
                    msg_n += 1
                    yield _sse("message", json.dumps({
                        "node": node,
                        "content": chunk.content,
                    }, ensure_ascii=False))
        except Exception as e:
            logger.exception("stream_failed thread_id=%s", thread_id)
            # 避免 EventSource 的 error 与自定义事件名冲突，使用 stream_error
            yield _sse("stream_error", json.dumps({"error": str(e)}, ensure_ascii=False))
        if stream_exc:
            err = stream_exc[0]
            logger.error("stream_thread_failed thread_id=%s err=%s", thread_id, err)
            yield _sse("stream_error", json.dumps({"error": str(err)}, ensure_ascii=False))

        ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "stream_done thread_id=%s ms=%.1f tool_events=%s message_chunks=%s",
            thread_id,
            ms,
            tool_n,
            msg_n,
        )
        yield _sse("done", json.dumps({"thread_id": thread_id}))

    # X-Accel-Buffering: no → 经 Nginx 反向代理时禁用缓冲，否则 SSE 会攒包不实时
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── 文件上传分析 ──

@router.post("/analyze", response_model=AnalyzeResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    question: str = Form(...),
):
    """multipart 上传文件并投递后台分析任务；立即返回 task_id，结果轮询 GET /analyze/{task_id}。"""
    saved_path = await save_upload(file)
    task_id = new_task_id()
    tasks = get_tasks()
    tasks[task_id] = {"status": TaskStatus.PROCESSING, "result": None, "error": None}

    logger.info(
        "analyze_task_submit task_id=%s file=%s preview=%s",
        task_id,
        saved_path.name,
        _preview(question),
    )
    asyncio.create_task(_run_analysis(task_id, str(saved_path), question))

    return AnalyzeResponse(
        task_id=task_id,
        status="processing",
        message=f"文件已上传至 {saved_path}，分析任务已提交",
    )


@router.get("/analyze/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询异步分析任务是否完成及结果/错误信息。"""
    tasks = get_tasks()
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    return TaskStatusResponse(task_id=task_id, **task)


# ── 数据源管理 ──

@router.post("/datasource", response_model=DataSourceResponse)
async def add_datasource(ds: DataSourceCreate):
    """注册一条数据源（内存存储，进程内生效）。"""
    datasources = get_datasources()
    datasources[ds.name] = {
        "connection_url": ds.connection_url,
        "description": ds.description,
    }
    return DataSourceResponse(
        name=ds.name,
        connection_url=ds.connection_url,
        description=ds.description,
    )


@router.get("/datasource", response_model=list[DataSourceResponse])
async def list_datasources():
    """列出已注册的数据源。"""
    datasources = get_datasources()
    return [
        DataSourceResponse(name=name, **info)
        for name, info in datasources.items()
    ]


# ── 联网搜索 ──


@router.post("/search", response_model=SearchResponse)
async def web_search_api(req: SearchRequest):
    """联网搜索（ddgs 多引擎聚合），返回标题、链接与摘要（无需单独配置搜索 API Key）"""
    logger.info("search_api query=%s max_results=%s", _preview(req.query, 200), req.max_results)
    try:
        rows = await asyncio.to_thread(run_web_search, req.query, req.max_results)
    except Exception as e:
        logger.exception("search_api_failed")
        raise HTTPException(status_code=502, detail=f"搜索服务不可用: {e}") from e

    items = [
        SearchResultItem(title=r["title"], url=r["url"], snippet=r["snippet"])
        for r in rows
    ]
    return SearchResponse(query=req.query.strip(), total=len(items), results=items)


# ── 辅助函数 ──

async def _run_analysis(task_id: str, file_path: str, question: str):
    """与对话独立的异步任务：invoke 智能体后把结果写入内存 tasks 字典。"""
    tasks = get_tasks()
    t0 = time.perf_counter()
    logger.info("analyze_task_begin task_id=%s path=%s", task_id, file_path)
    try:
        agent = get_agent()
        content = f"请分析以下数据文件并回答问题。\n\n文件路径: {file_path}\n问题: {question}"
        thread_id = f"task-{task_id}"
        config = _langgraph_run_config(thread_id)

        result = await asyncio.to_thread(
            agent.invoke,
            {"messages": [{"role": "user", "content": content}]},
            config=config,
        )

        last_msg = result["messages"][-1]
        response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        tasks[task_id] = {"status": TaskStatus.COMPLETED, "result": response_text, "error": None}
        ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "analyze_task_ok task_id=%s ms=%.1f response_len=%s",
            task_id,
            ms,
            len(response_text or ""),
        )
    except Exception as e:
        logger.exception("analyze_task_failed task_id=%s", task_id)
        tasks[task_id] = {"status": TaskStatus.FAILED, "result": None, "error": str(e)}


def _sse(event: str, data: str) -> str:
    """拼一条符合 SSE 规范的帧（事件名 + data 行 + 空行）。"""
    return f"event: {event}\ndata: {data}\n\n"
