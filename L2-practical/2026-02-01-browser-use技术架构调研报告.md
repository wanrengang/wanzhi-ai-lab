---
title: browser-use 技术架构调研报告
subtitle: 基于LLM的智能浏览器自动化框架深度解析
author: 万智创界 AI 工作室
project: browser-use
project_url: https://github.com/browser-use/browser-use
version: 0.11.5
tags:
  - 浏览器自动化
  - LLM
  - AI Agent
  - CDP
  - Python
  - 开源项目
  - 架构分析
  - 技术调研
category: 浏览器自动化
status: 已完成
research_type: 技术架构分析
created: 2026-02-01
modified: 2026-02-01
related:
  - "[[Chrome DevTools Protocol 深入技术研究]]"
  - "[[Clawdbot：个人AI助手的下一个形态]]"
keywords:
  - browser-use
  - LLM agent
  - browser automation
  - Chrome DevTools Protocol
  - Playwright
  - Selenium
---

# browser-use 技术架构调研报告

**项目名称**: browser-use
**GitHub地址**: https://github.com/browser-use/browser-use
**调研日期**: 2026-02-01
**版本**: 0.11.5
**调研人**: 小万（AI助手）

---

## 一、项目概述

### 1.1 项目定位
browser-use 是一个**基于 LLM 的智能浏览器自动化框架**，让 AI 代理能够理解和操作网页。与传统自动化工具（如 Selenium、Playwright）不同，它通过大语言模型来理解用户意图并自主规划任务执行步骤。

### 1.2 核心特性
- 🤖 **LLM 驱动**：使用大语言模型自主决策和规划
- 🌐 **多浏览器支持**：基于 CDP (Chrome DevTools Protocol) 控制 Chromium
- 🔌 **多 LLM 提供商**：支持 OpenAI、Anthropic、Google、Groq、Ollama 等
- 🛠️ **可扩展工具系统**：支持自定义工具和操作
- 📊 **云端服务**：提供 Browser Use Cloud 用于生产环境部署
- 🎯 **智能元素定位**：结合 DOM 树和可访问性树精准定位元素

---

## 二、技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户接口层                             │
├─────────────────────────────────────────────────────────────┤
│  CLI  │  Python API  │  Sandbox  │  Cloud API  │  Skills   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        Agent层                              │
├─────────────────────────────────────────────────────────────┤
│  Agent Service  │  Prompts  │  Judge  │  Message Manager    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        Tools层                              │
├─────────────────────────────────────────────────────────────┤
│  Registry  │  Controller  │  Actions  │  Custom Tools       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Browser层                              │
├─────────────────────────────────────────────────────────────┤
│  BrowserSession  │  Profile  │  Cloud  │  Watchdogs        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        DOM层                                │
├─────────────────────────────────────────────────────────────┤
│  DomService  │  Serializer  │  EnhancedSnapshot  │  Views  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                              │
├─────────────────────────────────────────────────────────────┤
│  LLM抽象  │  Config  │  Telemetry  │  FileSystem  │  Utils │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块详解

#### 2.2.1 Agent 模块 (`browser_use/agent`)

**职责**: 任务规划、决策和执行协调

**核心组件**:

1. **Agent Service** (`service.py`)
   - 主要的代理执行引擎
   - 负责任务分解和步骤执行
   - 管理对话历史和状态
   - 集成 Judge 进行结果验证

2. **System Prompts** (`prompts.py`)
   - 为不同任务定制的系统提示词
   - 支持自定义和扩展

3. **Judge** (`judge.py`)
   - 评估任务完成情况
   - 提供成功/失败判断
   - 支持真值验证

4. **Views** (`views.py`)
   - 定义核心数据模型：
     - `AgentSettings`: 代理配置
     - `AgentState`: 运行时状态
     - `AgentOutput`: LLM 输出格式
     - `ActionResult`: 操作结果
     - `AgentHistory`: 历史记录

5. **Message Manager** (`message_manager/`)
   - 管理对话上下文
   - 处理长短期记忆
   - Token 优化

**关键流程**:
```python
# 简化的执行流程
async def run_step():
    # 1. 获取当前浏览器状态
    browser_state = await browser.get_state()

    # 2. 构建 LLM 输入
    input = build_prompt(
        task=task,
        browser_state=browser_state,
        history=history
    )

    # 3. 调用 LLM 获取动作
    output = await llm.predict(input)

    # 4. 执行动作
    result = await tools.execute(output.action)

    # 5. 更新状态
    history.append(result)

    # 6. 判断是否完成
    if result.is_done:
        return result
```

#### 2.2.2 Browser 模块 (`browser_use/browser`)

**职责**: 浏览器会话管理和 CDP 通信

**核心组件**:

1. **BrowserSession** (`session.py`)
   - 基于 CDP 的浏览器控制
   - Tab 管理和切换
   - 视频录制
   - 截图功能
   - Cookie 和认证管理

2. **BrowserProfile** (`profile.py`)
   - 浏览器配置管理
   - 用户数据持久化
   - 代理设置
   - 反爬虫指纹配置

3. **Session Manager** (`session_manager.py`)
   - 多会话管理
   - 资源池管理
   - 生命周期管理

4. **Watchdogs** (`watchdogs/`)
   - 监控浏览器状态
   - 异常检测和恢复
   - 资源清理

**技术特点**:
- 使用 `cdp-use` 库进行 CDP 通信
- 支持 Chrome、Edge 等 Chromium 内核浏览器
- 支持真实浏览器配置文件复用
- Docker 优化配置

#### 2.2.3 DOM 模块 (`browser_use/dom`)

**职责**: DOM 树解析和元素定位

**核心组件**:

1. **DomService** (`service.py`)
   - 获取完整 DOM 树
   - 结合 Accessibility Tree
   - iframe 跨域处理
   - 视口计算

2. **Serializer** (`serializer/`)
   - DOM 树序列化
   - 属性提取
   - 文本内容提取

3. **Enhanced Snapshot** (`enhanced_snapshot.py`)
   - 增强型快照
   - 计算样式提取
   - 位置信息计算

**智能元素定位策略**:
```python
# 多层次元素匹配
1. CSS Selector
2. XPath
3. ARIA 属性
4. 文本内容匹配
5. 位置坐标匹配
6. 可访问性树节点
```

**关键特性**:
- 递归处理 iframe（可配置深度和数量）
- 可访问性树集成（用于无障碍访问）
- 动态属性过滤（减少 token 消耗）
- 元素去重和优先级排序

#### 2.2.4 Tools 模块 (`browser_use/tools`)

**职责**: 可扩展的工具注册和执行系统

**核心组件**:

1. **Tools Service** (`service.py`)
   - 工具注册中心
   - 参数验证
   - 执行协调

2. **Registry** (`registry/`)
   - 动态工具注册
   - 类型安全的参数模型
   - 工具描述生成

3. **内置 Actions**:
   - `search`: 搜索引擎搜索
   - `navigate`: 导航到 URL
   - `click`: 点击元素
   - `type`: 输入文本
   - `scroll`: 滚动页面
   - `extract`: 提取内容
   - `done`: 完成任务
   - `screenshot`: 截图
   - `upload`: 文件上传
   - 等等...

**自定义工具示例**:
```python
from browser_use import Tools

tools = Tools()

@tools.action(description='描述这个工具做什么')
async def custom_tool(param: str) -> str:
    result = await do_something(param)
    return f"结果: {result}"

agent = Agent(
    task="任务描述",
    llm=llm,
    browser=browser,
    tools=tools,  # 传入自定义工具
)
```

#### 2.2.5 LLM 模块 (`browser_use/llm`)

**职责**: 多 LLM 提供商统一抽象

**支持的提供商**:
- OpenAI (`ChatOpenAI`)
- Anthropic (`ChatAnthropic`)
- Google (`ChatGoogle`)
- Groq (`ChatGroq`)
- Ollama (`ChatOllama`)
- Azure OpenAI (`ChatAzureOpenAI`)
- Browser Use Cloud (`ChatBrowserUse`) - 专为浏览器优化
- Vercel (`ChatVercel`)
- Mistral (`ChatMistral`)
- Oracle Cloud (`ChatOCIRaw`)

**核心接口**:
```python
class BaseChatModel(ABC):
    async def predict(
        self,
        messages: list[BaseMessage],
        output_model: type[BaseModel] | None = None,
    ) -> Any: ...

    async def stream(
        self,
        messages: list[BaseMessage],
        output_model: type[BaseModel] | None = None,
    ) -> AsyncIterator[Any]: ...
```

**特色功能**:
- 结构化输出（JSON Schema 强制）
- 流式响应支持
- Token 使用追踪和成本计算
- 自动重试和错误处理
- 多模态支持（文本+图像）

---

## 三、关键设计模式

### 3.1 异步优先
- 全面使用 `async/await`
- 使用 `asyncio` 进行并发控制
- CDP 连接池管理

### 3.2 Pydantic 数据验证
- 所有数据模型继承 `BaseModel`
- 类型安全和自动验证
- JSON Schema 生成用于 LLM 结构化输出

### 3.3 事件驱动架构
- 使用 `bubus` EventBus
- 事件日志和遥测
- 可观测性支持

### 3.4 插件化设计
- 工具系统完全可扩展
- 支持自定义 Actions
- Skill 系统（如 Claude Code 技能）

### 3.5 配置即代码
- 环境变量配置
- `pydantic-settings` 管理配置
- 支持配置文件和迁移

---

## 四、工作流程示例

### 4.1 完整任务执行流程

```
用户任务: "在 GitHub 上找到 browser-use 仓库的 star 数"
│
├─ 1. 初始化 Agent
│   └─ 创建 BrowserSession、LLM、Tools
│
├─ 2. 开始 Step 循环
│   │
│   ├─ 2.1 获取浏览器状态
│   │   ├─ 截图（如果启用视觉）
│   │   ├─ 获取 DOM 树
│   │   └─ 获取可访问性树
│   │
│   ├─ 2.2 构建 Prompt
│   │   ├─ 系统提示词
│   │   ├─ 任务描述
│   │   ├─ 浏览器状态
│   │   └─ 历史对话
│   │
│   ├─ 2.3 调用 LLM
│   │   └─ 获取结构化输出（Action + 思考）
│   │
│   ├─ 2.4 执行 Action
│   │   ├─ 解析参数
│   │   ├─ 定位元素
│   │   ├─ 执行操作
│   │   └─ 返回结果
│   │
│   ├─ 2.5 更新状态
│   │   ├─ 记录历史
│   │   ├─ 更新记忆
│   │   └─ 检查完成条件
│   │
│   └─ 2.6 判断是否继续
│       ├─ 未完成 → 继续下一步
│       └─ 已完成/失败 → 返回结果
│
└─ 3. 输出最终结果
    ├─ 生成摘要
    ├─ 保存历史（可选）
    └─ 生成 GIF（可选）
```

### 4.2 代码示例

```python
from browser_use import Agent, Browser, ChatBrowserUse
import asyncio

async def main():
    # 1. 创建浏览器实例
    browser = Browser()

    # 2. 创建 LLM（使用专为浏览器优化的模型）
    llm = ChatBrowserUse()

    # 3. 创建 Agent
    agent = Agent(
        task="在 GitHub 上找到 browser-use 仓库并告诉我 star 数",
        llm=llm,
        browser=browser,
    )

    # 4. 运行
    history = await agent.run()

    # 5. 查看结果
    print(history.final_result())

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 五、技术栈总结

### 5.1 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | >=3.11 | 运行环境 |
| pydantic | >=2.11.5 | 数据验证 |
| aiohttp | >=3.13.3 | 异步 HTTP |
| cdp-use | >=1.4.4 | CDP 通信 |
| anthropic | >=0.72.1 | Anthropic LLM |
| openai | >=2.7.2 | OpenAI LLM |
| click | >=8.1.8 | CLI 框架 |
| rich | >=14.0.0 | 终端美化 |
| bubus | >=1.5.6 | 事件总线 |

### 5.2 可选依赖

- **CLI**: `textual` - TUI 界面
- **视频**: `imageio[ffmpeg]` - 视频/GIF 生成
- **云服务**: `boto3`, `oci` - AWS/Oracle Cloud
- **代码能力**: `matplotlib`, `pandas`, `numpy` - 数据分析

### 5.3 开发工具

- **测试**: pytest, pytest-asyncio
- **代码质量**: ruff, pyright
- **可观测性**: lmnr, posthog
- **包管理**: uv（推荐）

---

## 六、性能优化策略

### 6.1 Token 优化

1. **DOM 智能裁剪**
   - 只包含可见元素
   - 过滤无关属性
   - 限制 iframe 深度

2. **对话管理**
   - 自动总结长对话
   - 分离长短期记忆
   - Token 使用追踪

3. **视觉策略**
   - `'auto'` 模式：仅在需要时使用视觉
   - `'low'` 详情：减少图像 token
   - 缓存屏幕截图

### 6.2 并发控制

```python
# 配置最大并发动作
agent = Agent(
    ...,
    max_actions_per_step=3,  # 每步最多执行 3 个动作
)
```

### 6.3 缓存策略

- 浏览器会话复用
- CDP 连接池
- LLM 响应缓存（部分提供商）

### 6.4 生产优化

使用 **Browser Use Cloud** 获得：
- 预热浏览器池
- 代理轮换
- 隐身指纹
- 自动扩缩容
- 监控和日志

---

## 七、生产部署方案

### 7.1 本地部署

```bash
# 使用 uv
uv init
uv add browser-use
uv sync

# 设置 .env
echo "BROWSER_USE_API_KEY=your-key" > .env

# 安装浏览器
uvx browser-use install
```

### 7.2 Docker 部署

```dockerfile
FROM python:3.11-slim

# 安装依赖
COPY pyproject.toml .
RUN pip install browser-use[cli]

# 安装 Chromium
RUN apt-get update && \
    apt-get install -y chromium

# 运行
CMD ["python", "your_agent.py"]
```

### 7.3 Cloud API 部署

```python
from browser_use import Browser, sandbox, ChatBrowserUse

@sandbox()
async def my_task(browser: Browser):
    agent = Agent(
        task="任务描述",
        browser=browser,
        llm=ChatBrowserUse(),
    )
    await agent.run()

# 直接调用，基础设施由 Cloud 管理
asyncio.run(my_task())
```

### 7.4 并行执行

```python
import asyncio

async def run_parallel():
    tasks = [
        agent.run() for agent in agents
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 八、优缺点分析

### 8.1 优点

✅ **智能决策**: LLM 自主规划，无需硬编码流程
✅ **灵活性**: 处理复杂、动态网页
✅ **易用性**: 简洁的 API，快速上手
✅ **可扩展**: 支持自定义工具和 Actions
✅ **多 LLM**: 避免供应商锁定
✅ **生产就绪**: 提供云服务和最佳实践
✅ **活跃维护**: 频繁更新，社区活跃

### 8.2 缺点/挑战

⚠️ **成本**: LLM 调用成本高于传统自动化
⚠️ **速度**: LLM 推理延迟（秒级 vs 毫秒级）
⚠️ **可靠性**: 偶尔的幻觉或错误决策
⚠️ **资源消耗**: Chrome 内存占用高
⚠️ **调试**: LLM 决策过程不透明
⚠️ **反爬**: 某些网站需要额外配置绕过

### 8.3 适用场景

**非常适合**:
- 一次性数据抓取任务
- 复杂的表单填写
- 需要理解的页面交互
- 原型验证和 MVP
- 个人自动化助手

**不适合**:
- 高频实时监控（>100次/分钟）
- 超大规模数据采集
- 极低成本场景
- 简单的重复性任务（传统自动化更优）

---

## 九、竞品对比

| 特性 | browser-use | Selenium | Playwright | Puppeteer |
|------|-------------|----------|------------|-----------|
| **驱动方式** | LLM | 代码 | 代码 | 代码 |
| **灵活性** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **易用性** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **速度** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **成本** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **可维护性** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **智能决策** | ✅ | ❌ | ❌ | ❌ |
| **多模态** | ✅ | ❌ | ❌ | ❌ |

---

## 十、总结与建议

### 10.1 技术亮点

1. **创新的 LLM + 浏览器融合**: 将自然语言理解与浏览器控制完美结合
2. **模块化设计**: 清晰的分层，易于理解和扩展
3. **生产级工程**: 完善的配置、监控、错误处理
4. **开发者友好**: 优秀的文档、丰富的示例、活跃的社区

### 10.2 学习价值

对于智能体开发工程师，这个项目展示了：
- 如何设计 LLM 驱动的 Agent 系统
- 如何集成多 LLM 提供商
- 如何进行 DOM 树和可访问性树的结合
- 如何设计可扩展的工具系统
- 如何处理异步和并发
- 如何进行生产环境优化

### 10.3 使用建议

**入门阶段**:
- 从简单的示例开始
- 使用 `ChatBrowserUse` 模型（专为浏览器优化）
- 本地运行，理解工作流程

**进阶阶段**:
- 尝试自定义 Tools
- 调整 Agent Settings（max_actions_per_step, use_vision 等）
- 优化 Prompt（override_system_message）

**生产阶段**:
- 使用 Browser Use Cloud
- 配置监控和日志
- 实现 Agent Pool 和任务队列
- 添加 Judge 验证和容错机制

### 10.4 未来展望

- 更强的推理能力（集成 o1、o3 等推理模型）
- 更低的延迟（模型优化、缓存策略）
- 更好的可靠性（自我纠错、回滚机制）
- 更强的反爬虫能力（指纹模拟、行为模拟）
- 多 Agent 协作（任务分解、并行执行）

---

## 十一、参考资料

- **官方文档**: https://docs.browser-use.com
- **GitHub**: https://github.com/browser-use/browser-use
- **Cloud服务**: https://cloud.browser-use.com
- **博客**: https://browser-use.com/posts
- **Discord社区**: https://link.browser-use.com/discord

---

**报告生成时间**: 2026-02-01
**AI助手**: 小万 🤖
**项目版本**: browser-use v0.11.5
