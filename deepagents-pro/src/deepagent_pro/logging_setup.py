"""应用日志初始化与 HTTP 请求日志中间件"""

from __future__ import annotations

import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from deepagent_pro.config import Settings

# 单文件上限与备份份数（全部运行日志默认落盘，避免无限增长）
_LOG_MAX_BYTES = 10 * 1024 * 1024
_LOG_BACKUP_COUNT = 14
# 标记本模块添加的轮转文件 handler；reload 时从 root/uvicorn 一并摘掉再 close，避免重复写盘或重复 close
_MARK_ROTATING = "_deepagent_pro_rotating"


def _remove_old_rotating_handlers() -> None:
    loggers = (
        logging.getLogger(),
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.access"),
    )
    seen: list[logging.Handler] = []
    for lg in loggers:
        for h in list(lg.handlers):
            if getattr(h, _MARK_ROTATING, False):
                lg.removeHandler(h)
                if h not in seen:
                    seen.append(h)
    for h in seen:
        try:
            h.close()
        except Exception:
            pass


def _resolved_log_file(settings: Settings) -> Path | None:
    raw = (settings.log_file or "").strip()
    if not raw or raw.lower() in ("none", "false", "off"):
        return None
    return Path(raw)


def setup_logging(settings: Settings) -> None:
    """配置根日志：控制台 + 默认文件（轮转）；uvicorn 单独挂文件（其 logger 不向 root 传播）。"""
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _remove_old_rotating_handlers()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    root.addHandler(stream)

    log_path = _resolved_log_file(settings)
    file_handler: RotatingFileHandler | None = None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=_LOG_MAX_BYTES,
            backupCount=_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        setattr(file_handler, _MARK_ROTATING, True)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
        # uvicorn / uvicorn.access 为 propagate=False，不进入 root；uvicorn.error 无 handlers，会传到 root
        for name in ("uvicorn", "uvicorn.access"):
            logging.getLogger(name).addHandler(file_handler)

    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录每个请求的方法、路径、状态码与耗时（毫秒）。"""

    def __init__(self, app, logger_name: str = "deepagent_pro.http") -> None:
        super().__init__(app)
        self._log = logging.getLogger(logger_name)

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        path = request.url.path
        try:
            response = await call_next(request)
        except Exception:
            self._log.exception("request_failed method=%s path=%s", request.method, path)
            raise
        ms = (time.perf_counter() - start) * 1000
        # 静态资源可降为 DEBUG，需要时把 LOG_LEVEL=DEBUG
        if path.startswith("/assets/") and response.status_code == 200:
            self._log.debug(
                "request method=%s path=%s status=%s ms=%.1f",
                request.method,
                path,
                response.status_code,
                ms,
            )
        else:
            self._log.info(
                "request method=%s path=%s status=%s ms=%.1f",
                request.method,
                path,
                response.status_code,
                ms,
            )
        return response
