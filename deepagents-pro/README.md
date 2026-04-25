# DeepAgent-Pro: 智能数据分析平台

基于 LangChain Deep Agents SDK 构建的智能数据分析 API 服务。

## 功能特性

- **CSV/Excel 分析** - 上传文件，自然语言提问，获得数据洞察
- **数据库查询** - 连接数据库，自然语言转 SQL 查询
- **外部 API 接入** - 调用外部数据 API 进行分析
- **智能可视化** - 自动生成图表和数据报告
- **对话式分析** - 多轮对话持续深入分析数据
- **流式响应** - SSE 实时推送分析过程
- **Web 控制台** - React + AI SDK：对话与数据分析、**按需联网搜索**（智能体自动调用 `web_search` 工具）、数据源配置

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 MiniMax API Key
```

### 3. 构建前端（可选，用于浏览器访问 UI）

```bash
cd frontend
npm install
npm run build
```

构建完成后，`frontend/dist` 会由 FastAPI 在根路径 `/` 提供静态页面（未构建则无 Web UI，仅 API 可用）。

### 4. 启动服务

```bash
uvicorn deepagent_pro.main:app --reload
```

浏览器访问 **http://localhost:8000/** 即可打开管理界面（需已完成步骤 3）。

### 日志与排障

- 默认 **`LOG_LEVEL=INFO`**，日志同时输出到**终端**与 **`./data/logs/app.log`**（应用日志、HTTP 中间件、以及 uvicorn 访问/错误中与 root 相关的记录均会落盘；单文件约 10MB 轮转，保留多份备份）。
- 可通过 **`LOG_FILE`** 改路径；设为 **`LOG_FILE=`**、**`none`** 或 **`off`** 则仅控制台、不写文件。
- 每条 HTTP 请求会记一行：`method /path status 耗时ms`（logger：`deepagent_pro.http`）。
- 对话相关会记：`chat_start` / `chat_done`、`stream_start` / `stream_done` / `stream_tool_call`、上传与异步 `analyze_task_*`；异常带 **Python 堆栈**（`logger.exception`）。
- 需要更细链路时可设 **`LOG_LEVEL=DEBUG`**（静态资源 `/assets/*` 在 DEBUG 下仍多为精简输出）。

开发前端时可单独启动 Vite 并代理 API：

```bash
cd frontend
npm run dev
```

默认前端开发地址为 **http://127.0.0.1:5173**，已将 `/api` 与 `/health` 代理到 `http://127.0.0.1:8000`，请先在本机启动后端。

### 5. 测试 API

```bash
# 对话式分析
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我分析一下销售数据的趋势", "thread_id": "test-001"}'

# 上传文件分析
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@sales.csv" \
  -F "question=这份数据的主要趋势是什么？"

# 联网搜索
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "pandas 分组聚合 示例", "max_results": 5}'
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/analyze` | 上传文件并提交分析任务 |
| GET | `/api/v1/analyze/{task_id}` | 查询分析任务状态 |
| POST | `/api/v1/chat` | 对话式数据分析 |
| GET | `/api/v1/chat/{thread_id}/stream` | SSE 流式响应 |
| POST | `/api/v1/datasource` | 配置数据库连接 |
| GET | `/api/v1/datasource` | 列出已配置的数据源 |
| POST | `/api/v1/search` | 联网搜索（ddgs 多引擎，返回标题/链接/摘要） |
| POST | `/api/v1/upload` | 上传数据文件，返回服务器路径（供对话 `file_paths`） |

## 架构

- **智能体框架**: Deep Agents SDK + LangChain + LangGraph
- **LLM**: MiniMax (OpenAI 兼容接口)
- **API**: FastAPI + Uvicorn
- **前端**: Vite + React + TypeScript；对话界面使用 [Vercel AI SDK](https://ai-sdk.dev/) 的 `useChat` + 自定义 `ChatTransport` 对接本仓库 FastAPI（`frontend/`）
- **数据处理**: pandas + SQLAlchemy
- **可视化**: matplotlib + plotly

## 许可证

MIT
