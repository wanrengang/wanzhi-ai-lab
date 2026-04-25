"""Pydantic 请求 / 响应模型"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ── 对话分析 ──

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    thread_id: str = Field(..., description="对话线程 ID，用于保持多轮对话上下文")
    file_paths: list[str] = Field(default_factory=list, description="关联的数据文件路径列表")


class ChatResponse(BaseModel):
    thread_id: str
    response: str
    tool_calls: list[dict] = Field(default_factory=list, description="工具调用记录")
    tool_results: list[dict] = Field(
        default_factory=list,
        description="工具返回内容（与 tool_calls 对应；长文本可能被截断）",
    )


class ChatHistoryMessage(BaseModel):
    role: str = Field(..., description="user 或 assistant")
    content: str = Field(..., description="该轮文本内容")


class ChatHistoryResponse(BaseModel):
    thread_id: str
    messages: list[ChatHistoryMessage] = Field(
        default_factory=list,
        description="从检查点读取的 human/ai 轮次，用于前端恢复列表",
    )


class ChatThreadSummary(BaseModel):
    thread_id: str
    preview: str = Field(default="", description="首条用户消息或助手回复摘要，供列表展示")


class ChatThreadListResponse(BaseModel):
    threads: list[ChatThreadSummary] = Field(default_factory=list)


# ── 文件分析 ──

class UploadResponse(BaseModel):
    path: str = Field(..., description="服务器上的绝对路径，可在对话中作为 file_paths 传入")
    filename: str = Field(..., description="原始文件名")


class AnalyzeResponse(BaseModel):
    task_id: str
    status: str = "processing"
    message: str = ""


class TaskStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: str | None = None
    error: str | None = None


# ── 数据源管理 ──

class DataSourceCreate(BaseModel):
    name: str = Field(..., description="数据源名称")
    connection_url: str = Field(..., description="SQLAlchemy 连接字符串")
    description: str = Field(default="", description="数据源描述")


class DataSourceResponse(BaseModel):
    name: str
    connection_url: str
    description: str
    status: str = "connected"


# ── 流式响应 ──

class StreamEvent(BaseModel):
    event: str
    data: str


# ── 联网搜索 ──


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="搜索关键词或问题")
    max_results: int = Field(default=5, ge=1, le=20, description="返回条数，1–20")


class SearchResultItem(BaseModel):
    title: str = ""
    url: str = ""
    snippet: str = ""


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResultItem]
