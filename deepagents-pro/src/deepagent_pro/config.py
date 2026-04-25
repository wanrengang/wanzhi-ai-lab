from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# pydantic-settings 只会把 .env 里「已声明字段」读进 Settings；LangSmith 等库读的是 os.environ。
# 在导入其它模块前加载项目根目录 .env，保证 LANGCHAIN_* 生效（与从哪一 cwd 启动无关）。
_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MiniMax LLM
    minimax_api_key: str = ""
    minimax_model: str = "MiniMax-M2.5"
    minimax_base_url: str = "https://api.minimax.io/v1"

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/analysis.db"

    # LangGraph 对话检查点（SQLite，重启后同一 thread_id 仍可续聊）
    checkpoint_sqlite_path: str = "./data/checkpoints.sqlite"

    # 文件存储
    upload_dir: str = "./data/uploads"

    # IANA 时区（如 Asia/Shanghai）；空则默认 UTC，可被 ``data/user_timezone.json`` 覆盖
    user_timezone: str = ""

    # Deep Agents Skills（磁盘目录 + 虚拟路径 /skills/...）；关闭设 SKILLS_ENABLED=false
    skills_enabled: bool = True
    skills_root_dir: str = "./skills"
    # 逗号分隔的虚拟源路径，须落在 /skills/ 下，靠后者覆盖同名 skill。
    # 含 ``/skills/`` 时可扫描与 bundled、project 并列的顶层技能目录（如 ``docx/``）。
    skills_sources: str = "/skills/bundled/,/skills/project/,/skills/"

    # Deep Agents Shell 执行（危险：不要在公网环境开启）
    # 开启后会给智能体注入 `execute` 能力（通过 LocalShellBackend），从而能直接运行脚本、pip 等命令。
    shell_enabled: bool = True
    # 作为执行与文件操作的工作目录（建议固定在项目根目录或其子目录）
    shell_root_dir: str = "./data"

    # 服务
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # 日志：LOG_LEVEL=DEBUG|INFO|WARNING；LOG_FILE 默认 ./data/logs/app.log；空/none/off 则仅控制台
    log_level: str = "INFO"
    log_file: str = "./data/logs/app.log"

    # 浏览器工具（browser_use）：逗号分隔主机白名单，留空则仅校验 http/https（生产环境建议配置）
    browser_allowed_hosts: str = ""
    browser_screenshots_dir: str = "./data/browser"

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
