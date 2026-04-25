"""
FastAPI 应用入口：挂载 CORS、请求日志、REST 路由，并在存在构建产物时托管前端静态资源。

本地开发前端常用 Vite 独立端口；生产或单端口联调时可将 `frontend/dist` 置于项目根下由本服务一并提供。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from deepagent_pro.config import get_settings
from deepagent_pro.logging_setup import RequestLoggingMiddleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """进程启动时：加载配置、初始化日志与上传目录；关闭时暂无清理逻辑。"""
    settings = get_settings()
    setup_logging(settings)
    settings.upload_path  # 触发 mkdir，确保上传目录存在
    yield


app = FastAPI(
    title="DeepAgent-Pro",
    description="智能数据分析平台 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 允许浏览器跨域访问 API（本地前后端分离调试时常用；生产可按域名收紧 allow_origins）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# 路由放在 app 创建之后，避免循环依赖； noqa 忽略 import 非顶部的风格检查
from deepagent_pro.api.routes import router  # noqa: E402

app.include_router(router)


@app.get("/health")
async def health():
    """负载均衡 / 容器探活用的简单健康检查。"""
    return {"status": "ok", "service": "deepagent-pro"}


# 相对本文件定位到仓库根下的 frontend/dist（npm run build 产物）
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    # html=True：未匹配到静态文件时回退 index.html，便于前端路由（SPA）
    app.mount(
        "/",
        StaticFiles(directory=str(_frontend_dist), html=True),
        name="frontend",
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "deepagent_pro.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,  # debug 时热重载，便于开发
    )
