# Oh My OpenCode 项目调研报告

> 调研时间：2026年2月4日
> 项目地址：https://github.com/code-yeongyu/oh-my-opencode
> 当前版本：v3.2.3

---

## 一、项目概述

### 1.1 项目定位

**Oh My OpenCode** 是一个开源的 OpenCode 插件，提供了开箱即用的 AI 智能体编排系统。它是 OpenCode 生态中的"Ubuntu"——将极客才能驾驭的强大工具包装成普通开发者也能轻松使用的生产力倍增器。

### 1.2 核心价值主张

- **从复杂到简单**：OpenCode 功能强大但配置复杂，Oh My OpenCode 让它开箱即用
- **智能体编排**：不仅是单个 AI 助手，而是完整的 AI 开发团队
- **多模型协作**：充分发挥不同 AI 模型的优势，按任务类型智能分配
- **极致生产力**：用户评价显示可节省大量时间，甚至"一夜之间完成人类数月的工作"

### 1.3 项目标语

> "认识 Sisyphus：开箱即用的智能体，像你一样编码。"

---

## 二、解决的核心问题

### 2.1 OpenCode 的痛点

OpenCode 是一个功能极其强大的 AI 编程工具，但存在以下问题：

| 痛点 | 描述 |
|------|------|
| **学习曲线陡峭** | 需要深入理解 LSP、MCP、Hook 等概念才能发挥价值 |
| **配置复杂** | 需要手动配置模型、智能体、工具等多个维度 |
| **缺少最佳实践** | 没有现成的智能体编排模式供参考 |
| **单一模型局限** | 无法充分发挥不同 AI 模型的各自优势 |

### 2.2 Oh My OpenCode 的解决方案

1. **预配置的最佳实践**：内置经过验证的智能体配置
2. **智能体编排系统**：自动将任务分配给最合适的智能体
3. **零配置使用**：默认启用所有功能，"电池已包含"
4. **多模型混合编排**：根据任务类型自动选择最优模型

---

## 三、核心特点

### 3.1 Sisyphus 智能体系统

Sisyphus 是主编排智能体，名为"西西弗斯"（希腊神话中永无止境推石头的英雄），寓意智能体像人类一样坚持不懈地工作。

**Sisyphus 的核心能力：**

```
┌─────────────────────────────────────────────────────────┐
│                    Sisyphus (主编排器)                   │
│                     模型：Opus 4.5 High                 │
└─────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │ 并行探测 │    │ 智能分配 │    │ 持续执行 │
    └─────────┘    └─────────┘    └─────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
    ┌────────────────────▼────────────────────┐
    │         专业子智能体团队                   │
    ├─────────┬─────────┬─────────┬───────────┤
    │ Oracle  │Frontend │Librarian│  Explore  │
    │架构/调试│UI/UX    │文档搜索 │代码库探索 │
    └─────────┴─────────┴─────────┴───────────┘
```

### 3.2 专业子智能体

| 智能体 | 作用 | 推荐模型 |
|--------|------|----------|
| **Oracle** | 架构设计、复杂调试 | GPT 5.2 Medium |
| **Frontend UI/UX Engineer** | 前端开发、UI 设计 | Gemini 3 Pro |
| **Librarian** | 官方文档查询、开源实现搜索 | Claude Sonnet 4.5 |
| **Explore** | 极速代码库探索（上下文感知 Grep）| Grok Code |
| **Prometheus** | 战略规划、需求澄清 | GPT 5.2 系列 |
| **Metis** | 预规划咨询、发现隐藏需求 | 高智商模型 |
| **Momus** | 工作计划审查、质量把控 | 高智商模型 |
| **Atlas** | 总编排器，管理整个开发生命周期 | Sonnet 4.5 |
| **Hephaestus** | 自主深度工作者 | GPT 5.2 Codex Medium |

### 3.3 核心功能特性

#### 1. 完整的 LSP & AST 工具支持
- **LSP 重构**：利用 Language Server Protocol 进行精确、安全的代码重构
- **AST-Grep**：基于抽象语法树的代码搜索和替换
- **LSP 诊断**：实时错误检测和修复建议

#### 2. Todo 继续执行器
> "这就是让 Sisyphus 继续推动巨石的关键。"

- 强制中断的智能体继续执行未完成任务
- 防止任务半途而废
- 确保工作 100% 完成

#### 3. Claude Code 完整兼容层
- Commands（命令系统）
- Agents（智能体系统）
- Skills（技能系统）
- MCP（Model Context Protocol）
- Hooks（钩子系统：PreToolUse、PostToolUse、UserPromptSubmit、Stop）

#### 4. 精选内置 MCP
- **Exa**：网络搜索
- **Context7**：官方文档查询
- **Grep.app**：GitHub 代码搜索

#### 5. 后台任务系统
- 并行运行多个智能体
- 异步任务管理
- 任务通知和监控

#### 6. Ultrawork 模式
- **魔法词**：只需在提示中包含 `ultrawork`（或 `ulw`）
- 自动启用所有功能
- 并行智能体、深度探索、持续执行
- 智能体自动理解其余工作

### 3.4 生产力增强功能

| 功能 | 作用 |
|------|------|
| **Ralph Loop** | 自我参考开发循环，持续工作直到完成 |
| **Comment Checker** | 防止 AI 添加过多注释，保持代码整洁 |
| **Think Mode** | 深度思考模式 |
| **Interactive Bash** | Tmux 集成的交互式终端 |
| **Session Recovery** | 会话恢复机制 |
| **Agent Fallback** | 智能体降级策略 |
| **Preemptive Compaction** | 上下文自动压缩 |

---

## 四、3.0 版本重大更新（编排革命）

**发布日期：2026年1月24日**

### 4.1 核心架构变革：Categories & Skills 系统

v3.0 引入了动态智能体组合系统，彻底改变了智能体的定义和部署方式。

**从硬编码智能体到动态组合**

```
旧方式（v2.x）：
├── Frontend UI/UX Engineer (固定智能体)
├── Backend Engineer (固定智能体)
└── Git Expert (固定智能体)

新方式（v3.0+）：
Category（领域）+ Skill（技能）= 动态智能体

示例：
├── visual-engineering Category + frontend-ui-ux Skill → 前端专家
├── quick Category + git-master Skill → Git 快速操作员
├── deep Category + debugging Skill → 深度调试专家
└── artistry Category + creative-coding Skill → 创意编程师
```

**优势：**
- ✅ 更灵活：可以自由组合任意 Category 和 Skill
- ✅ 可扩展：轻松添加新的 Category 和 Skill
- ✅ 精准匹配：根据任务需求动态生成最优智能体

### 4.2 Prometheus：战略规划师

**新增智能体**，专注于需求澄清和战略规划。

**工作流程：**
```
用户需求 → Prometheus 深度访谈 → 需求澄清 → 咨询专业智能体 → 制定工作计划
```

**核心能力：**
- 对用户进行"面试"，提出深度问题
- 确保所有需求都被明确理解
- 咨询其他专业智能体验证策略
- 输出详细、可执行的工作计划

### 4.3 Atlas：总编排器

**新增核心编排模式**，管理整个开发生命周期。

**工作流程：**
```
/start-work → Atlas 接管 → 分解任务 → 动态分配智能体 → 持续验证 → 完成
```

**核心能力：**
- 混合搭配 Categories 和 Skills
- 为每个子任务部署最合适的智能体
- 执着地验证每个步骤
- 任务失败时自动恢复智能体修复
- 跨提供商优化成本（例如：Sonnet 编排 + GLM 4.7 日常 + Haiku 4.5 快速修复 + GPT 5.2 复杂逻辑）

### 4.4 安装体验重构

**全新交互式 CLI 安装器：**
- 平滑的引导式设置流程
- 自动模型映射（基于订阅状态）
- 原生二进制文件（无需本地运行时）
- 多提供商支持（GitHub Copilot、OpenCode Zen、Z.ai Coding Plan 等）

### 4.5 运行时模糊匹配系统

为处理日益复杂的 Categories 和 Agents，实现了：
- 运行时模型映射模糊匹配
- 确保始终为任务分配最合适的模型
- 自动迁移现有用户配置

---

## 五、3.0 至今的主要更新内容

### 5.1 版本时间线

```
v3.0.0 (2026-01-24) - 编排革命
    ↓
v3.1.x (2026-01-27 ~ 2026-01-30) - 快速迭代期
    ↓
v3.2.0 (2026-02-01) - Hephaestus 诞生
    ↓
v3.2.3 (2026-02-04) - 最新版本
```

### 5.2 v3.1.x 系列重要更新

#### v3.1.0-v3.1.3：系统稳定期
- 增强系统稳定性
- 修复模型选择和缓存问题
- 改进错误处理和恢复机制

#### v3.1.4：用户体验优化
- 新增 Provider 缓存缺失提醒
- 修复 npm 全局安装的版本检测
- 改进模型解析器

#### v3.1.5：配置增强
- Prometheus 自我委派阻止
- delegate_task 权限系统
- 系统 reminder 标签防止误触发

#### v3.1.7：MCP OAuth 2.1 认证
**重大安全更新**：完整的 OAuth 2.1 支持
- RFC 7591（动态客户端注册）
- RFC 9728（受保护资源元数据）
- RFC 8414（授权服务器发现）
- RFC 8707（资源指示器）
- 安全令牌存储
- CLI 命令：`opencode mcp oauth login/logout/status`

同时完成 **LSP 客户端迁移到 vscode-jsonrpc**，提升协议稳定性。

#### v3.1.9：Kimi K2.5 支持
**新增模型提供商**：Moonshot (Kimi)
- 新增 `kimi-k2.5` 到多个智能体的后备链
- 作者评价："在我作为 Atlas 编排器的工作流中，Kimi K2.5 的表现优于 Claude Sonnet 4.5"

**新增 Categories：**
- **deep**：目标导向的自主问题解决
- **artistry**：超越标准模式的创意、非常规方法

#### v3.1.11：系统优化
- Oracle 部署安全审查
- `/stop-continuation` 命令（停止所有继续机制）
- GLM-4.7 Thinking Mode 支持
- 内存泄漏和僵尸进程预防
- Windows LSP 修复

### 5.3 v3.2.0：Hephaestus 诞生 🔨

**新智能体：Hephaestus（赫淮斯托斯）**

在希腊神话中，Hephaestus 是锻造、火焰、金属工艺和工匠之神——为众神打造武器的神圣铁匠。

**为什么叫"Legitimate"（合法的）？**
当 Anthropic 以违反 ToS 为由阻止第三方访问时，社区开始开玩笑地谈论"合法"使用。Hephaestus 拥抱了这个讽刺——他以正确的方式构建事物的工匠。

**核心特征：**
- **目标导向**：给他一个目标，而不是食谱。他自己决定步骤
- **行动前探索**：在写一行代码之前，发起 2-5 个并行 explore/librarian 智能体
- **端到端完成**：不停止，直到任务 100% 完成并有验证证据
- **模式匹配**：搜索现有代码库以匹配项目风格——无 AI 垃圾代码
- **合法精度**：像大师铁匠一样制作代码——外科手术式、极简、精确所需

灵感来源于 [AmpCode's deep mode](https://ampcode.com)。

### 5.4 v3.2.1-v3.2.3：持续优化

#### v3.2.1
- 修复后台智能体并发槽泄漏
- 添加 GitHub Copilot Gemini 模型的 `-preview` 后缀

#### v3.2.2：GPT-5.2 提示优化 + 实验性任务系统

**GPT-5.2 Prompt 优化：**
- Atlas、Sisyphus-Junior、Oracle：基于模型的提示路由
- GPT-5.2 优化提示（XML 结构、冗长度约束、明确决策标准）

**实验性：Claude Code 风格任务系统：**
- 新工具：`TaskCreate`、`TaskGet`、`TaskList`、`TaskUpdate`
- 基于文件的存储：任务存储在 `.sisyphus/tasks/`，兼容 Claude Code schema
- ⚠️ **重要限制**：这是实验性的，**不与 OpenCode 的 Todo UI 同步**
- 启用方式：设置 `experimental.task_system: true`

**其他改进：**
- 更快的探索：`grok-code-fast-1` 作为默认 explore 智能体模型
- 预防性压缩：在 78% 上下文使用时自动总结会话（Anthropic 模型）
- 智能体回退：首次运行无缓存现在正常工作

#### v3.2.3：多提供商网络搜索 + 技能增强

**新功能：**
- **多提供商网络搜索支持**：在 Exa（默认）和 Tavily 之间选择
- **嵌套技能目录**：技能可以组织在子目录中以便更好管理
- **禁用技能支持**：添加 `disabledSkills` 配置选择性地禁用技能

**Bug 修复：**
- 修复 OpenCode Desktop 服务器未授权错误
- 模型选择优化（优先精确模型 ID 匹配）
- Gemini 3 Pro 兼容性改进
- LSP 诊断陈旧数据预防
- 跨平台 Shell 支持

---

## 六、技术架构

### 6.1 技术栈

- **语言**：TypeScript
- **运行时**：Bun（原 Node.js）
- **包管理**：npm
- **平台支持**：Windows、macOS、Linux
- **架构**：插件系统（基于 OpenCode Plugin API）

### 6.2 核心模块

```
oh-my-opencode/
├── src/
│   ├── agents/           # 智能体定义和提示
│   │   ├── sisyphus.ts
│   │   ├── prometheus.ts
│   │   ├── atlas.ts
│   │   ├── oracle.ts
│   │   ├── hephaestus.ts
│   │   └── ...
│   ├── features/         # 功能模块
│   │   ├── background-agent/
│   │   ├── builtin-commands/
│   │   ├── builtin-skills/
│   │   └── sisyphus-swarm/
│   ├── hooks/            # 钩子系统
│   │   ├── todo-continuation-enforcer/
│   │   ├── comment-checker/
│   │   └── ...
│   ├── tools/            # 工具实现
│   │   ├── lsp/
│   │   ├── delegate-task/
│   │   └── session-manager/
│   └── mcp/              # MCP 服务器
├── docs/                 # 文档
│   ├── guide/
│   │   ├── installation.md
│   │   └── overview.md
│   ├── features.md
│   ├── configurations.md
│   └── orchestration-guide.md
└── packages/             # 平台特定二进制
    ├── windows-x64/
    ├── darwin-arm64/
    └── linux-x64/
```

### 6.3 配置系统

**配置文件位置：**
- 项目级：`.opencode/oh-my-opencode.json`
- 用户级：`~/.config/opencode/oh-my-opencode.json`

**支持 JSONC**：支持注释和尾随逗号

**可配置项：**
- 智能体模型和提示
- 后台任务并发限制
- 类别（Categories）定义
- 钩子（Hooks）开关
- MCP 服务器配置
- LSP 配置
- 实验性功能开关

---

## 七、用户评价与影响力

### 7.1 用户评价（来自 README）

> "它让我取消了 Cursor 订阅。开源社区正在发生令人难以置信的事情。"
> — Arthur Guiot

> "如果 Claude Code 能在 7 天内完成人类 3 个月的工作，那么 Sisyphus 只需 1 小时。它会持续工作直到任务完成。它是一个非常自律的智能体。"
> — B, 量化研究员

> "用 Oh My Opencode 仅用一天就清理了 8000 个 eslint 警告"
> — Jacob Ferrari

> "我使用 Ohmyopencode 和 ralph loop 在一夜之间将一个 45k 行的 tauri 应用转换成了 SaaS Web 应用。"
> — James Hargis

> "用了 oh-my-opencode，你再也不会回头了"
> — d0t3ch

> "Oh My OpenCode 真的太疯狂了"
> — YouTube - Darren Builds AI

### 7.2 社区数据（截至 2026-02-04）

- **GitHub Stars**：14,000+
- **npm 下载量**：持续增长
- **贡献者**：活跃的社区贡献
- **Discord 社区**：活跃的讨论和帮助

### 7.3 企业采用

公开信息显示被以下公司/组织使用：
- **Indent**（制作 Spray、vovushop、vreview）
- **Google**
- **Microsoft**

---

## 八、与竞品对比

### 8.1 vs Claude Code

| 特性 | Claude Code | Oh My OpenCode |
|------|-------------|----------------|
| **定位** | Anthropic 官方 AI IDE | OpenCode 插件，编排系统 |
| **模型支持** | Claude 为主 | 多模型混合编排 |
| **智能体系统** | 固定智能体 | 动态 Category+Skill 组合 |
| **可定制性** | 有限 | 高度可定制 |
| **开放性** | 闭源（官方产品）| 开源 |
| **成本** | 订阅制 | 基于现有订阅（ChatGPT/Claude/Gemini）|

### 8.2 vs Cursor

| 特性 | Cursor | Oh My OpenCode |
|------|--------|----------------|
| **定位** | AI 编辑器 | OpenCode 插件 |
| **智能体编排** | 基础 | 高级多智能体编排 |
| **多模型支持** | 有限 | 广泛（GPT/Claude/Gemini/Kimi 等）|
| **可扩展性** | 有限 | 高度可扩展 |
| **价格** | 独立订阅 | 利用现有订阅 |

### 8.3 vs OpenCode 原生

| 特性 | OpenCode 原生 | Oh My OpenCode |
|------|---------------|----------------|
| **学习曲线** | 陡峭 | 平缓（开箱即用）|
| **配置复杂度** | 高 | 低（预配置最佳实践）|
| **智能体编排** | 需手动配置 | 开箱即用的编排系统 |
| **功能完整性** | 基础框架 | 完整的工具链 |

---

## 九、使用场景

### 9.1 典型使用场景

1. **大型项目重构**
   - LSP 重构工具确保安全
   - 模式匹配保持代码风格一致
   - 并行探索加快理解速度

2. **跨技术栈开发**
   - 前端任务 → Frontend UI/UX Engineer (Gemini 3 Pro)
   - 后端逻辑 → GPT 5.2 Codex
   - 文档查询 → Librarian (Claude Sonnet)
   - 代码库探索 → Explore (Grok Code)

3. **复杂问题调试**
   - Oracle 智能体进行架构分析
   - LSP 诊断实时错误检测
   - 上下文感知的深度搜索

4. **快速原型开发**
   - Ultrawork 模式自动启用所有功能
   - 并行智能体加速开发
   - 持续验证确保质量

5. **文档和开源库研究**
   - Librarian 并行查询官方文档和 GitHub 实现
   - Context7 集成官方文档
   - Grep.app 搜索实际使用案例

### 9.2 工作流程示例

**场景：添加新功能**

```bash
# 1. 用户输入需求（包含 "ultrawork"）
用户: "使用 ultrawork 模式添加用户认证功能"

# 2. Sisyphus 自动开始工作
├── Prometheus（如果需要澄清）
│   └── 深度访谈，明确需求
│
├── 并行探索阶段
│   ├── Explore：搜索现有认证实现
│   ├── Librarian：查询最佳实践文档
│   └── Librarian：查找开源实现示例
│
├── Prometheus 制定计划
│   └── 咨询 Oracle 验证架构
│
├── /start-work 激活 Atlas
│   ├── Backend 任务 → GPT 5.2 Codex
│   ├── Frontend UI → Gemini 3 Pro
│   ├── Git 操作 → quick + git-master
│   └── 持续验证每个步骤
│
└── 任务完成
    ├── 运行测试
    ├── 代码审查
    └── 提交 PR
```

---

## 十、安装与配置

### 10.1 快速安装（推荐）

将以下提示复制粘贴到你的 LLM 智能体（Claude Code、AmpCode、Cursor 等）：

```
按照以下说明安装和配置 oh-my-opencode：
https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/refs/heads/master/docs/guide/installation.md
```

### 10.2 手动安装

```bash
npm install -g oh-my-opencode@latest
```

### 10.3 配置

**最小配置（使用默认值）：**

```json
// ~/.config/opencode/oh-my-opencode.json
{
  // 留空使用所有默认配置
}
```

**自定义配置示例：**

```json
{
  "agents": {
    "sisyphus": {
      "model": "claude-opus-4-5-high"
    },
    "oracle": {
      "model": "gpt-5-2-medium"
    }
  },
  "backgroundTask": {
    "maxConcurrentTasks": 5
  },
  "disabledHooks": [
    "comment-checker"
  ]
}
```

---

## 十一、总结与建议

### 11.1 项目优势

1. **开箱即用**：零配置即可获得强大的智能体编排能力
2. **多模型协作**：充分发挥不同 AI 模型的优势
3. **高度可定制**：从 Category 到 Skill，全方位可配置
4. **持续创新**：频繁的更新，快速响应用户需求
5. **开源免费**：基于现有订阅，无需额外付费
6. **社区活跃**：活跃的贡献者和用户社区

### 11.2 适用人群

| 用户类型 | 是否推荐 | 原因 |
|---------|---------|------|
| **OpenCode 用户** | ✅ 强烈推荐 | 完美补充，释放 OpenCode 全部潜力 |
| **Cursor 用户** | ✅ 推荐 | 更强大的多模型编排能力 |
| **Claude Code 用户** | ✅ 推荐 | 兼容层 + 更多功能 |
| **AI 编程初学者** | ✅ 推荐 | 降低使用门槛 |
| **极客开发者** | ✅ 推荐 | 高度可定制，满足深度需求 |
| **仅需要基础 AI 补全** | ❌ 可能过度 | 功能过于强大 |

### 11.3 注意事项

1. **学习曲线**：虽然开箱即用，但要充分发挥威力仍需学习
2. **资源消耗**：多智能体并行会消耗更多 token
3. **依赖订阅**：需要 GPT/Claude/Gemini 等订阅
4. **快速迭代**：项目更新频繁，需要关注新版本

### 11.4 未来展望

从项目发展轨迹看，Oh My OpenCode 正在向以下方向发展：

1. **更智能的编排**：Atlas、Hephaestus 等新智能体持续增强
2. **更多模型支持**：Kimi、GLM 等国产模型集成
3. **更好的用户体验**：安装向导、错误提示、文档完善
4. **企业级功能**：团队协作、权限管理、审计日志
5. **生态扩展**：更多 Skills、Categories、MCP 集成

---

## 十二、相关链接

- **GitHub 仓库**：https://github.com/code-yeongyu/oh-my-opencode
- **官方文档**：https://github.com/code-yeongyu/oh-my-opencode/tree/master/docs
- **发布页面**：https://github.com/code-yeongyu/oh-my-opencode/releases
- **Discord 社区**：https://discord.gg/PUwSMR9XNk
- **作者 X (Twitter)**：[@justsisyphus](https://x.com/justsisyphus)
- **Sisyphus Labs**：https://sisyphuslabs.ai

---

## 附录：版本历史速查

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v3.2.3 | 2026-02-04 | 多提供商网络搜索、嵌套技能目录 |
| v3.2.2 | 2026-02-03 | GPT-5.2 优化、实验性任务系统 |
| v3.2.1 | 2026-02-01 | Bug 修复 |
| v3.2.0 | 2026-02-01 | Hephaestus 智能体 |
| v3.1.11 | 2026-02-01 | Oracle 安全审查、stop-continuation 命令 |
| v3.1.9 | 2026-01-30 | Kimi K2.5 支持、deep/artistry categories |
| v3.1.7 | 2026-01-29 | MCP OAuth 2.1、LSP vscode-jsonrpc 迁移 |
| v3.1.4 | 2026-01-28 | Provider 缓存警告 |
| v3.1.0 | 2026-01-27 | 系统稳定性增强 |
| v3.0.0 | 2026-01-24 | **编排革命**：Categories & Skills、Prometheus、Atlas |

---

*文档生成时间：2026年2月4日*
*项目版本：v3.2.3*
*调研者：AI Agent*
