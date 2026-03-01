---
title: 深入理解 LangChain Sandboxes：安全的 AI Agent 代码执行环境
tags:
  - AI
  - LangChain
  - 技术博客
  - Sandboxes
created: 2026-02-10
updated: 2026-02-10
category: 技术文档
status: completed
rating: 5
---

# 深入理解 LangChain Sandboxes：安全的 AI Agent 代码执行环境

## 引言

随着 AI Agent 的能力不断增强，它们不仅能够生成代码、操作文件系统，还能执行 Shell 命令。然而，这种强大的能力也带来了严峻的安全挑战：**我们如何让 Agent 自由执行代码，同时保护主机系统不受侵害？**

LangChain Deep Agents 引入的 **Sandboxes（沙箱）** 机制，正是为了解决这一核心问题。本文将深入探讨 Sandboxes 的原理、价值以及实践方法。

---

## 一、什么是 Sandboxes

### 核心定义

**Sandboxes 是 LangChain Deep Agents 中的一种特殊 Backend，用于在隔离环境中执行代码**。它为 AI Agent 提供了一个安全的边界，确保 Agent 的所有操作（文件读写、命令执行）都无法突破到主机系统。

### 架构设计

Sandboxes 的核心架构非常优雅：它通过实现 `SandboxBackendProtocol` 接口，只需要实现一个 `execute()` 方法：

```
┌─────────────────┐
│   AI Agent      │
│                 │
│  ┌───────────┐  │
│  │   Tools   │  │
│  │  ls/read  │  │
│  │  /write/  │  │
│  │  execute  │  │
│  └───────────┘  │
└────────┬────────┘
         │ Backend Protocol
┌────────▼────────┐
│   Sandbox       │
│                 │
│  ┌───────────┐  │
│  │ execute()│  │◄── 唯一需要实现的方法
│  └───────────┘  │
│                 │
│  Filesystem     │
│  Bash           │
│  Dependencies   │
└─────────────────┘
```

所有其他文件系统操作（`ls`、`read_file`、`write_file`、`glob`、`grep`）都基于 `execute()` 方法构建，由 `BaseSandbox` 基类自动实现。

### 功能特性

配置 Sandbox 后，Agent 将获得：

- **完整的文件系统工具**：`ls`、`read_file`、`write_file`、`edit_file`、`glob`、`grep`
- **Shell 命令执行**：通过 `execute` 工具运行任意命令
- **安全隔离边界**：保护主机系统免受 Agent 操作影响

---

## 二、解决了什么问题？企业价值何在？

### 1. 安全性：从源头隔离风险

**问题场景**：Agent 生成并执行恶意代码，访问敏感文件，窃取环境变量中的 API 密钥。

**Sandboxes 的解决方案**：
- ✅ 代码在隔离环境中运行，无法访问主机凭证、文件或网络
- ✅ Agent 无法读取本地文件或访问主机环境变量
- ✅ 即使 Agent 被劫持，攻击也被限制在沙箱内部

### 2. 环境一致性：消除"在我机器上能跑"的困扰

**问题场景**：开发人员本地环境配置复杂，依赖版本冲突，导致 Agent 行为不可预测。

**Sandboxes 的解决方案**：
- ✅ 提供干净、一致的执行环境
- ✅ 可使用特定依赖或 OS 配置，无需本地设置
- ✅ 团队成员之间完全一致的执行环境

### 3. 可扩展性：灵活选择云提供商

LangChain Sandboxes 支持多种主流云服务提供商，包括**国际厂商**和**国内云服务商**：

#### 国际厂商

| 提供商 | 适用场景 |
|--------|----------|
| **Modal** | ML/AI 工作负载，GPU 访问 |
| **Daytona** | TypeScript/Python 开发，快速冷启动 |
| **Runloop** | 一次性开发箱，隔离代码执行 |

#### 国内云服务商

| 服务商     | 产品/方案                | 特点与优势                                                                                                                                                                         |
| ------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **阿里云** | AgentRun Sandbox SDK | 🚀 **已开源**，基于阿里云函数计算 FC 构建<br>✅ 支持 LangChain、AgentScope、Dify、RAGFlow 等主流框架<br>🔧 提供三种沙箱：Code Interpreter（代码解释器）、Browser Sandbox（浏览器）、All-in-One（二合一）<br>📦 深度集成通义千问等阿里云 AI 服务 |
| **腾讯云** | All-in-One 沙箱应用      | 🧪 **内测阶段**，基于腾讯云函数计算 SCF<br>✅ 支持 LangChain DeepAgents 集成<br>🌐 提供一体化云端开发环境（VSCode 编辑器、Python/Node.js 运行时、浏览器、Shell 终端）<br>🔐 支持会话级别的实例隔离和安全配置                                |
| **华为云** | FunctionGraph 函数工作流  | ✅ 支持 Python、Node.js、Java 等多种语言<br>⚡ 毫秒级弹性，独创 SnapShot 技术实现秒级冷启动<br>🎯 在 AgentArts 智能体平台中提供代码节点支持<br>💰 按需付费，毫秒级计量粒度                                                           |

#### 国内服务商的额外优势

相比国际厂商，国内云服务商在本土化方面具有独特优势：

- 🇨🇳 **合规性优势**：符合国内数据安全和隐私保护法规（如《数据安全法》、《个人信息保护法》）
- 🌐 **网络延迟**：国内节点，访问速度快，延迟低
- 💬 **中文支持**：提供完善的中文文档和技术支持
- 🔗 **生态集成**：深度集成国内 AI 服务（如通义千问、文心一言、讯飞星火等）
- 💴 **支付便捷**：支持人民币支付，开具国内发票

#### 阿里云 AgentRun 实践示例

```python
# 安装阿里云 AgentRun Sandbox SDK
pip install agentrun-sdk

# 使用阿里云函数计算作为沙箱后端
from agentrun import AgentRunSandbox
from langchain_anthropic import ChatAnthropic
from deepagents import create_deep_agent

# 创建阿里云 FC 沙箱
sandbox = AgentRunSandbox(
    service_name="my-agent-sandbox",
    region="cn-hangzhou"
)

agent = create_deep_agent(
    model=ChatAnthropic(model="claude-sonnet-4-20250514"),
    system_prompt="You are a Python coding assistant with Alibaba Cloud sandbox access.",
    backend=sandbox,
)
```

这种多云支持策略为企业带来了：
- 🔄 **供应商灵活性**：避免被单一供应商锁定
- 💰 **成本优化**：根据任务特点选择最具性价比的服务
- 🚀 **技术选型自由**：为不同场景选择最优方案
- 🏢 **本土化支持**：国内服务商提供合规性和本地化优势

### 4. 开发效率：即开即用

**传统痛点**：
- 本地安装依赖耗时
- 环境配置冲突
- 跨平台兼容性问题

**Sandboxes 优势**：
- ⚡ 无需本地配置环境
- ⚡ 秒级启动隔离环境
- ⚡ 自动处理依赖管理

---

## 三、怎么用？实践指南

### 3.1 安装依赖

以阿里云 AgentRun Sandbox SDK 为例（国内用户推荐）：

```bash
# 基础安装
pip install agentrun-sdk

# 如需 LangChain 集成
pip install agentrun-sdk[langchain]

# 如需浏览器沙箱功能
pip install agentrun-sdk[playwright]

# 完整安装（包含所有功能）
pip install agentrun-sdk[langchain,playwright,server]
```

> **提示**：AgentRun SDK 需要 Python 3.10 或更高版本。

### 3.2 创建并配置 Sandbox

```python
import os
from agentrun.sandbox import Sandbox, TemplateType
from langchain_anthropic import ChatAnthropic
from deepagents import create_deep_agent
from agentrun.integration.langchain import sandbox_toolset

# 1. 配置阿里云认证信息（建议通过环境变量）
os.environ["AGENTRUN_ACCESS_KEY_ID"] = "your-access-key-id"
os.environ["AGENTRUN_ACCESS_KEY_SECRET"] = "your-access-key-secret"
os.environ["AGENTRUN_ACCOUNT_ID"] = "your-account-id"
os.environ["AGENTRUN_REGION"] = "cn-hangzhou"

# 2. 创建 Code Interpreter Sandbox
sandbox = Sandbox.create(
    template_type=TemplateType.CODE_INTERPRETER,  # 代码解释器沙箱
    template_name="your-sandbox-template",         # 在控制台创建的模板名称
    sandbox_idle_timeout_seconds=300               # 空闲超时时间（秒）
)

# 3. 获取沙箱工具集（包含 execute、read_file、write_file 等）
tools = sandbox_toolset(sandbox)

# 4. 创建 Agent 并绑定 Sandbox 工具
agent = create_deep_agent(
    model=ChatAnthropic(model="claude-sonnet-4-20250514"),
    system_prompt="You are a Python coding assistant with sandbox access.",
    tools=tools,  # 传入沙箱工具集
)

# 5. 执行任务
result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "Create a small Python package and run pytest"
        }
    ]
})

# 6. 清理资源
sandbox.delete()
```

> **重要提示**：
> - 使用前需在[阿里云函数计算 AgentRun 控制台](https://agentrun.fc.aliyun.com/)创建服务关联角色
> - 需要先在控制台创建 Sandbox 模板，获取 `template_name`
> - 建议将认证信息存储在 `.env` 文件中，不要硬编码在代码里

### 3.3 文件操作：双平面访问

AgentRun Sandboxes 提供两种文件访问方式，理解其区别至关重要：

#### 方式一：Agent 文件系统工具（运行时）

Agent 在执行过程中使用的工具，通过 `execute()` 方法在沙箱内运行：

```python
# Agent 调用（自动）- 这些工具由 sandbox_toolset() 自动提供
agent.invoke({
    "messages": [
        {"role": "user", "content": "Read /workspace/index.py"}
    ]
})
```

#### 方式二：文件传输 API（应用层）

应用代码调用的方法，用于主机与沙箱之间的文件传输：

```python
# 上传文件到沙箱（执行前）
sandbox.upload_files([
    ("/workspace/index.py", b"print('Hello from AgentRun!')\n"),
    ("/workspace/pyproject.toml", b"[project]\nname = 'my-app'\n"),
])

# 从沙箱下载文件（执行后）
results = sandbox.download_files(["/workspace/index.py", "/output.txt"])
for result in results:
    if result.content is not None:
        print(f"{result.path}: {result.content.decode()}")
```

**使用建议**：
- 📤 **上传**：在 Agent 运行前预填充源代码、配置或数据
- 📥 **下载**：在 Agent 完成后提取生成的代码、构建产物或报告

### 3.4 直接执行命令

除了通过 Agent，你也可以直接调用沙箱的 `execute()` 方法：

```python
# 直接执行 shell 命令
result = sandbox.execute("python --version")
print(result.output)
# 输出: Python 3.11.0

print(f"退出码: {result.exit_code}")
print(f"是否截断: {result.truncated}")
```

返回结果包含：
- `output`: 合并的 stdout/stderr
- `exit_code`: 命令退出码
- `truncated`: 输出是否被截断（超出大小限制时）

### 3.5 进阶：浏览器沙箱使用

AgentRun 还提供了强大的浏览器沙箱功能，让 Agent 能够"上网"：

```python
from agentrun.sandbox import Sandbox, TemplateType
from playwright.sync_api import sync_playwright

# 1. 创建 Browser Sandbox
browser_sandbox = Sandbox.create(
    template_type=TemplateType.BROWSER,
    template_name="your-browser-template",
    sandbox_idle_timeout_seconds=300
)

# 2. 获取 CDP URL（Chrome DevTools Protocol）
cdp_url = browser_sandbox.get_cdp_url()

# 3. 使用 Playwright 连接并操作
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(cdp_url)
    page = browser.contexts[0].pages[0]

    # 访问网页
    page.goto("https://www.example.com")
    title = page.title()

    # 截图
    page.screenshot(path="screenshot.png")

    browser.close()

# 4. 清理资源
browser_sandbox.delete()
```

> **浏览器沙箱应用场景**：
> - 🌐 网页数据抓取和信息提取
> - 📝 自动化表单填写
> - 🔍 可视化调试（通过 VNC 实时查看）
> - 📸 网页截图和 PDF 生成

---

## 四、安全最佳实践

### ⚠️ 核心原则：永不在沙箱中存储密钥

**错误做法**：
```python
# ❌ 危险！密钥可被 Agent 读取并外泄
# 不要通过环境变量将密钥传入沙箱
sandbox = Sandbox.create(
    template_type=TemplateType.CODE_INTERPRETER,
    template_name="my-template",
    environment={
        "API_KEY": "sk-xxx"  # 绝对不要这样做！
    }
)
```

**正确做法**：

**方案一：将密钥保留在沙箱外的工具中**

```python
# ✅ 安全：工具在主机环境中处理认证
from langchain.tools import tool

@tool
def fetch_api_data(query: str) -> str:
    """调用外部 API（密钥在主机环境）"""
    # 密钥存储在主机环境变量中，沙箱无法访问
    api = ExternalAPI(api_key=os.environ["REAL_API_KEY"])
    return api.search(query)

agent = create_deep_agent(
    model=ChatAnthropic(),
    tools=[fetch_api_data],  # Agent 调用工具，但看不到密钥
    tools=sandbox_toolset(sandbox)  # 只传递沙箱工具
)
```

**方案二：使用网络代理注入凭证**

AgentRun 等提供商支持代理模式，自动在请求中附加认证头：

```python
# ✅ 安全：Agent 发送普通请求，代理注入凭证
# 请求在沙箱内: GET https://api.example.com/data
# 代理处理后: GET https://api.example.com/data
#              Authorization: Bearer sk-xxx (自动添加)
```

**方案三：使用阿里云 KMS 密钥管理服务**

```python
# ✅ 最安全：使用阿里云 KMS 管理密钥
from alibabacloud_kms20160120.client import Client as KmsClient

kms_client = KmsClient(...)  # 使用 RAM 角色，无需硬编码密钥

def get_decrypted_key(key_id: str) -> str:
    """从 KMS 获取解密后的密钥"""
    response = kms_client.decrypt(
        ciphertext_blob=KeyBlob(key_id)
    )
    return response.plaintext
```

### 其他安全建议

1. **限制网络访问**：当不需要网络时，在沙箱模板中配置网络策略
   ```python
   sandbox = Sandbox.create(
       template_type=TemplateType.CODE_INTERPRETER,
       template_name="restricted-template",  # 在控制台配置为禁用公网访问
       # 或使用 vpc_config 指定私有网络
   )
   ```

2. **人工审核**：对敏感操作启用 Human-in-the-Loop 审核
   ```python
   from langchain.agents import AgentExecutor

   agent_executor = AgentExecutor(
       agent=agent,
       tools=tools,
       handle_parsing_errors=True,
       max_execution_time=300,
       # 启用人工审核
       verbose=True,
       return_intermediate_steps=True
   )
   ```

3. **输出过滤**：使用中间件过滤敏感模式
   ```python
   from agentrun.middleware import OutputFilter

   # 配置输出过滤器
   filter = OutputFilter(patterns=[
       r"sk-[a-zA-Z0-9]{32,}",  # 过滤 API Key
       r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"  # 过滤信用卡号
   ])
   ```

4. **最小权限原则**：使用 RAM 角色和窄权限策略
   ```python
   # 使用阿里云 RAM 角色，而非 Access Key
   sandbox = Sandbox.create(
       template_type=TemplateType.CODE_INTERPRETER,
       template_name="my-template",
       role_arn="acs:ram::123456789:role/agent-sandbox-role"  # 限制权限的角色
   )
   ```

5. **资源限制**：设置合理的超时和资源配额
   ```python
   sandbox = Sandbox.create(
       template_type=TemplateType.CODE_INTERPRETER,
       template_name="my-template",
       sandbox_idle_timeout_seconds=300,  # 5 分钟空闲超时
       memory_mbs=2048,                   # 限制内存使用
       timeout_seconds=60                 # 单次命令超时
   )
   ```

6. **审计日志**：启用操作审计
   - 在阿里云控制台启用 ActionTrail
   - 配置沙箱操作日志投递到 SLS 或 OSS
   - 定期审计异常命令和文件访问

---

## 五、总结与展望

LangChain Sandboxes 通过**简洁的架构设计**（单一 `execute()` 方法）实现了**强大的隔离能力**，为企业级 AI Agent 应用提供了：

- 🔒 **安全边界**：保护主机系统不受 Agent 操作影响
- 🌐 **环境一致性**：跨团队、跨平台的统一执行环境
- 🔄 **供应商灵活性**：多云支持，避免锁定
- ⚡ **开发效率**：即开即用，无需复杂配置

随着 AI Agent 能力的不断提升，Sandboxes 将成为企业 AI 应用的**基础设施标准**，为 Agent 的安全、可控执行提供坚实保障。

---

## 参考资源

- [LangChain Deep Agents 官方文档](https://docs.langchain.com/oss/python/deepagents)
- [Sandboxes 官方文档](https://docs.langchain.com/oss/python/deepagents/sandboxes)
- [Provider 集成指南](https://docs.langchain.com/oss/python/integrations/providers)
- [安全最佳实践](https://docs.langchain.com/oss/python/deepagents/security)

---

## 相关标签

#AI #LangChain #技术博客 #Sandboxes #代码执行 #安全隔离 #Agent开发

---

> 💡 **万智创界 - AI技术实战派布道者**
>
> 关注我，你将获得：
> - ✅ AI前沿动态与趋势
> - ✅ 真实项目案例 + 代码
> - ✅ 工程化实践与避坑
>
> 让 AI 真正为业务创造价值，从理论到落地，我们一起前行！
