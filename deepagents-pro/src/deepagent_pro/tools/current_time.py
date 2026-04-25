"""当前时间与用户时区偏好（可持久化到 ``data/user_timezone.json``）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain.tools import tool

from deepagent_pro.config import get_settings

logger = logging.getLogger(__name__)

_PREFS_NAME = "user_timezone.json"


def _prefs_path() -> Path:
    settings = get_settings()
    root = Path(settings.upload_dir).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    return root / _PREFS_NAME


def _read_prefs_iana() -> str | None:
    path = _prefs_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        v = (data.get("iana") or data.get("timezone") or "").strip()
        if not v:
            return None
        ZoneInfo(v)  # validate
        return v
    except (OSError, json.JSONDecodeError, TypeError, ZoneInfoNotFoundError, KeyError):
        logger.warning("Ignoring invalid timezone prefs at %s", path)
        return None


def _effective_iana() -> str:
    from_file = _read_prefs_iana()
    if from_file:
        return from_file
    env_tz = (get_settings().user_timezone or "").strip()
    if env_tz:
        return env_tz
    return "UTC"


def _now_in_tz(iana: str) -> tuple[datetime, str]:
    try:
        return datetime.now(ZoneInfo(iana)), iana
    except (ZoneInfoNotFoundError, KeyError):
        logger.warning("Invalid timezone %r, falling back to UTC", iana)
        return datetime.now(timezone.utc), "UTC"


def local_date_iso_for_search() -> str:
    """与 ``get_current_time`` 相同的用户时区下的本地日期 ``YYYY-MM-DD``。

    供 ``web_search`` 等在构造「今日/早报」类查询时锚定真实日期，避免模型并行调用工具时编造日期。
    """
    iana = _effective_iana()
    now, _ = _now_in_tz(iana)
    return now.strftime("%Y-%m-%d")


@tool
def get_current_time() -> str:
    """获取当前时间，格式 ``%Y-%m-%d %H:%M:%S IANA (Weekday)``。

    例如 ``2026-02-13 19:30:45 Asia/Shanghai (Friday)``。

    当用户询问现在几点、当前日期，或需要时间做说明时调用。
    """
    iana = _effective_iana()
    now, label = _now_in_tz(iana)
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} {label} ({now.strftime('%A')})"


@tool
def set_user_timezone(timezone_name: str) -> str:
    """设置用户时区（IANA 名称，如 ``Asia/Shanghai``、``America/New_York``）。

    仅在用户明确要求修改时区时调用。会写入 ``data/user_timezone.json``，
    优先级高于环境变量 ``USER_TIMEZONE``。
    """
    tz_name = (timezone_name or "").strip()
    if not tz_name:
        return "Error: timezone is empty."

    try:
        now = datetime.now(ZoneInfo(tz_name))
    except (ZoneInfoNotFoundError, KeyError):
        return f"Error: invalid timezone '{tz_name}'."

    path = _prefs_path()
    path.write_text(
        json.dumps({"iana": tz_name}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    time_str = f"{now.strftime('%Y-%m-%d %H:%M:%S')} {tz_name} ({now.strftime('%A')})"
    return f"Timezone set to {tz_name}. Current time: {time_str}"
