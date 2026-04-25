"""文件上传存储管理"""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import UploadFile

from deepagent_pro.config import get_settings

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".tsv"}


async def save_upload(file: UploadFile) -> Path:
    """保存上传文件到本地，返回保存路径。

    文件名添加时间戳前缀防止冲突。
    """
    settings = get_settings()
    upload_dir = settings.upload_path

    original_name = file.filename or "upload"
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}。支持: {', '.join(ALLOWED_EXTENSIONS)}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique = uuid.uuid4().hex[:6]
    safe_name = f"{timestamp}_{unique}{ext}"

    dest = upload_dir / safe_name
    with dest.open("wb") as f:
        content = await file.read()
        f.write(content)

    return dest


def cleanup_old_files(max_age_hours: int = 24) -> int:
    """清理超过指定时间的上传文件，返回删除的文件数。"""
    settings = get_settings()
    upload_dir = settings.upload_path
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    deleted = 0

    for f in upload_dir.iterdir():
        if f.is_file() and f.name != ".gitkeep":
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                deleted += 1

    charts_dir = upload_dir / "charts"
    if charts_dir.exists():
        for f in charts_dir.iterdir():
            if f.is_file():
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    deleted += 1

    return deleted


def list_uploaded_files() -> list[dict]:
    """列出所有已上传的文件"""
    settings = get_settings()
    upload_dir = settings.upload_path
    files = []
    for f in sorted(upload_dir.iterdir()):
        if f.is_file() and f.name != ".gitkeep":
            files.append({
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    return files
