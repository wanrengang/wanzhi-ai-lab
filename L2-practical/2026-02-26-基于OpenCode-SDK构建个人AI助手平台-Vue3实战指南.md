---
title: 基于 OpenCode SDK 构建个人 AI 助手平台 - Vue 3 实战指南
tags:
  - OpenCode
  - Vue 3
  - Vite
  - AI
  - SDK
  - Web开发
created: 2026-02-26
updated: 2026-02-26
category: 技术实践
status: completed
rating: 5
description: 从零开始用 Vue 3 + Vite + OpenCode SDK v2 构建完整的 ChatGPT 风格 AI 助手 Web 应用，包含完整代码和实战经验
---

# 基于 OpenCode SDK 构建个人 AI 助手平台 - Vue 3 实战指南

## 📖 核心思想

本文介绍如何使用 **Vue 3 + Vite + OpenCode SDK v2** 从零构建一个**ChatGPT 风格的 AI 助手 Web 应用**。通过完整的前端实战代码，展示如何实现实时对话、Markdown 渲染、思考过程展示、模型选择等核心功能，让开发者快速掌握基于 OpenCode SDK 构建个人 AI 平台的完整流程。

---

## 🎯 为什么需要前端应用？

传统使用 OpenCode 的方式是通过 CLI 或 TUI（终端界面），但这存在一些限制：

- ❌ 需要本地安装 OpenCode CLI
- ❌ 无法跨设备访问
- ❌ 界面不够友好
- ❌ 难以分享对话记录

**通过构建 Web 前端应用**，我们可以实现：

- ✅ **浏览器访问**：任何设备只要有浏览器就能使用
- ✅ **现代化界面**：ChatGPT 风格，支持 Markdown、代码高亮
- ✅ **实时交互**：快速响应，流畅体验
- ✅ **易于分享**：可以部署到公网，随时访问

---
---

## 🏗️ 技术架构设计

### 整体架构

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Vue 3 前端    │ ←──→ │  Vite Dev Server │ ←──→ │ OpenCode Server │
│  (Composition  ) │      │   (带代理配置)    │      │   (localhost)   │
│      API        │      │                  │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
    浏览器端              开发服务器                 AI 服务
```

### 技术栈选型

| 层级 | 技术 | 说明 |
|-----|------|-----|
| 前端框架 | Vue 3 | Composition API + `<script setup>` 语法 |
| 构建工具 | Vite 5 | 快速的开发服务器和构建工具 |
| HTTP 客户端 | @opencode-ai/sdk/v2 | OpenCode 官方 SDK |
| Markdown | marked | 解析 AI 返回的 Markdown 内容 |
| 样式方案 | 原生 CSS | CSS Variables + ChatGPT 风格设计 |

### 为什么选择 Vue 3？

1. **Composition API**：更灵活的代码组织方式
2. **响应式系统**：自动追踪依赖，无需手动优化
3. **单文件组件**：HTML、JS、CSS 封装在一个文件中
4. **轻量级**：相比 React，更小的打包体积
5. **学习曲线平缓**：模板语法直观易懂

---

## ⚠️ 前置条件

在开始之前，你需要确保已经完成以下准备工作：

### 1. 安装 OpenCode CLI

如果你还没有安装 OpenCode CLI，请先安装：

```bash
# 使用 npm 安装
npm install -g @opencode-ai/cli

# 或使用 homebrew（macOS）
brew install opencode

# 验证安装
opencode --version
```

### 2. 启动 OpenCode 服务器

启动一个带密码认证的 OpenCode 服务器：

```bash
# 启动服务器（指定端口和主机）
opencode serve --port 4096 --hostname 0.0.0.0
```

> **⚠️ 重要**：生产环境**必须设置密码认证**！不要跳过这一步。

### 3. 设置密码认证

首次启动时，OpenCode 会提示你设置用户名和密码。建议设置强密码：

```bash
# 启动后会提示设置认证信息
? Enter username: opencode
? Enter password: ********
? Confirm password: ********

✅ OpenCode 服务器已启动
   地址: http://localhost:4096
   状态: 运行中
```

**记住你的用户名和密码**，后面配置前端应用时会用到。

### 4. 验证服务器运行

打开浏览器访问 `http://localhost:4096`，你应该能看到 OpenCode 的欢迎页面或 API 文档。

或者使用命令验证：

```bash
curl http://localhost:4096/health

# 返回：{"status":"ok","version":"x.x.x"}
```

### 5. （可选）配置模型提供商

如果你还没有配置 AI 模型，可以通过 OpenCode 配置文件添加：

```bash
# 编辑配置文件
opencode config edit
```

添加你的 API Keys（如 OpenAI、Claude 等）：

```json
{
  "providers": {
    "openai": {
      "apiKey": "sk-xxx..."
    },
    "anthropic": {
      "apiKey": "sk-ant-xxx..."
    }
  }
}
```

---

## 🚀 快速开始

### 1. 创建项目

使用 Vite 快速创建 Vue 3 项目：

```bash
npm create vite@latest my-ai-assistant -- --template vue
cd my-ai-assistant
npm install
```

### 2. 安装依赖

```bash
# 安装 OpenCode SDK
npm install @opencode-ai/sdk

# 安装 Markdown 解析库
npm install marked
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# OpenCode 服务器地址
VITE_OPENCODE_URL=http://localhost:4096

# 服务器认证信息（如果需要）
VITE_OPENCODE_USERNAME=opencode
VITE_OPENCODE_PASSWORD=opencode123
```

### 4. 配置 Vite 代理

编辑 `vite.config.js`：

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 代理 OpenCode 服务器请求，避免 CORS 问题
      '/api': {
        target: 'http://localhost:4096',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

### 5. 项目结构

```
my-ai-assistant/
├── src/
│   ├── App.vue           # 主应用组件
│   ├── main.js           # 应用入口
│   ├── style.css         # 全局样式
│   └── utils/
│       └── opencode.js   # OpenCode SDK 封装
├── .env                  # 环境变量
├── index.html            # HTML 模板
├── vite.config.js        # Vite 配置
└── package.json          # 依赖配置
```

---

## 💻 核心功能实现

### 1. SDK 客户端封装

创建 `src/utils/opencode.js`：

```javascript
/**
 * OpenCode SDK 客户端封装
 * 提供统一的 API 调用接口，处理认证和错误
 */

import { createOpencodeClient } from '@opencode-ai/sdk/v2/client'

const SERVER_URL = import.meta.env.VITE_OPENCODE_URL || 'http://localhost:4096'
const SERVER_USERNAME = import.meta.env.VITE_OPENCODE_USERNAME || 'opencode'
const SERVER_PASSWORD = import.meta.env.VITE_OPENCODE_PASSWORD || 'opencode123'

// 创建认证头（浏览器环境使用 btoa）
const auth = btoa(`${SERVER_USERNAME}:${SERVER_PASSWORD}`)

// 创建客户端实例
export const client = createOpencodeClient({
  baseUrl: SERVER_URL,
  throwOnError: false,
  headers: {
    'Authorization': `Basic ${auth}`
  }
})

/**
 * 检查服务器健康状态
 */
export async function checkHealth() {
  try {
    const result = await client.global.health()
    if (result.error) {
      throw new Error(result.error[0]?.message || '健康检查失败')
    }
    return result.data
  } catch (error) {
    throw new Error(`无法连接到服务器: ${error.message}`)
  }
}

/**
 * 获取可用模型列表
 */
export async function getProviders() {
  try {
    const result = await client.config.providers()
    if (result.error) {
      throw new Error(result.error[0]?.message || '获取模型列表失败')
    }
    return result.data.providers || []
  } catch (error) {
    console.error('获取模型列表失败:', error)
    return []
  }
}

/**
 * 创建新会话
 */
export async function createSession(title = '新对话') {
  try {
    const result = await client.session.create({
      body: { title }
    })
    if (result.error) {
      throw new Error(result.error[0]?.message || '创建会话失败')
    }
    return result.data
  } catch (error) {
    throw new Error(`创建会话失败: ${error.message}`)
  }
}

/**
 * 发送消息并获取 AI 回复
 */
export async function sendMessage(sessionId, text, model = null) {
  try {
    const requestBody = {
      sessionID: sessionId,
      parts: [{
        type: 'text',
        text
      }]
    }

    // 如果指定了模型，添加到请求中
    if (model) {
      requestBody.model = {
        providerID: model.providerID,
        modelID: model.modelID
      }
    }

    const result = await client.session.prompt(requestBody)

    if (result.error) {
      throw new Error(result.error[0]?.message || '发送消息失败')
    }

    // 返回完整数据，包含 info、parts 等
    return result.data
  } catch (error) {
    throw new Error(`发送消息失败: ${error.message}`)
  }
}

/**
 * 获取会话消息历史
 */
export async function getSessionMessages(sessionId) {
  try {
    const result = await client.session.messages({
      sessionID: sessionId
    })
    if (result.error) {
      throw new Error(result.error[0]?.message || '获取消息历史失败')
    }

    // 转换消息格式
    return (result.data || []).map(msg => ({
      id: msg.id,
      role: msg.info?.role || 'user',
      content: msg.parts
        ?.filter(p => p.type === 'text')
        ?.map(p => p.text)
        ?.join('\n') || '',
      time: msg.time?.created || Date.now()
    }))
  } catch (error) {
    throw new Error(`获取消息历史失败: ${error.message}`)
  }
}
```

### 2. 主应用组件

创建 `src/App.vue`：

```vue
<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-content">
        <h1 class="logo">OpenCode Chat</h1>
        <div class="header-actions">
          <button @click="showSettings = true" class="icon-btn" title="设置">
            ⚙️
          </button>
          <button @click="createNewSession" class="btn-new" title="新建对话">
            + 新对话
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main">
      <!-- 连接状态提示 -->
      <div v-if="!connected" class="status-banner connecting">
        <span class="pulse">🔄</span>
        正在连接服务器...
      </div>

      <div v-else-if="connectionError" class="status-banner error">
        <span>❌</span>
        {{ connectionError }}
      </div>

      <!-- 消息列表 -->
      <div v-else class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">💬</div>
          <h2>开始新的对话</h2>
          <p>向 AI 提问任何问题</p>
          <div class="suggestions">
            <button
              v-for="(suggestion, index) in suggestions"
              :key="index"
              @click="handleSendMessage(suggestion)"
              class="suggestion-btn"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>

        <div v-else class="messages-list">
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message', `message-${message.role}`]"
          >
            <div class="message-content">
              <div class="message-avatar">
                {{ message.role === 'user' ? '👤' : '🤖' }}
              </div>
              <div class="message-text">
                <div v-if="message.role === 'assistant'" class="message-name">
                  AI 助手
                </div>

                <!-- 思考过程 -->
                <div v-if="message.thinking" class="thinking-section">
                  <details class="thinking-details">
                    <summary class="thinking-summary">
                      <span class="thinking-icon">💭</span>
                      <span>思考过程</span>
                    </summary>
                    <div class="thinking-content" v-html="formatMessage(message.thinking)"></div>
                  </details>
                </div>

                <div class="message-body" v-html="formatMessage(message.content)"></div>
                <div v-if="message.time" class="message-time">
                  {{ formatTime(message.time) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 加载指示器 -->
          <div v-if="isLoading" class="message message-assistant">
            <div class="message-content">
              <div class="message-avatar">🤖</div>
              <div class="message-text">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 底部输入区 -->
    <footer class="footer">
      <form @submit.prevent="handleSubmit" class="input-form">
        <div class="input-container">
          <textarea
            v-model="inputText"
            @keydown="handleKeydown"
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
            rows="1"
            ref="inputRef"
            :disabled="isLoading || !connected"
          ></textarea>
          <button
            type="submit"
            :disabled="!inputText.trim() || isLoading || !connected"
            class="send-btn"
          >
            {{ isLoading ? '⏳' : '发送' }}
          </button>
        </div>
      </form>
      <div class="footer-info">
        <span v-if="connected" class="status-ok">✓ 已连接</span>
        <span v-if="currentModel" class="model-info">
          模型: {{ currentModel.modelID }}
        </span>
      </div>
    </footer>

    <!-- 设置对话框 -->
    <div v-if="showSettings" class="modal-overlay" @click="showSettings = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>设置</h2>
          <button @click="showSettings = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="setting-item">
            <label>服务器地址</label>
            <input
              v-model="settings.serverUrl"
              type="text"
              placeholder="http://localhost:4096"
            />
          </div>
          <div class="setting-item">
            <label>模型</label>
            <select v-model="settings.selectedModel" :disabled="availableModels.length === 0">
              <option value="">默认模型</option>
              <option
                v-for="model in availableModels"
                :key="model.id"
                :value="model.id"
              >
                {{ model.name }}
              </option>
            </select>
            <small v-if="availableModels.length === 0" class="text-secondary">
              未检测到可用模型
            </small>
            <small v-else class="text-secondary">
              检测到 {{ availableModels.length }} 个可用模型
            </small>
          </div>
          <div class="setting-item">
            <label>用户名</label>
            <input
              v-model="settings.username"
              type="text"
              placeholder="opencode"
            />
          </div>
          <div class="setting-item">
            <label>密码</label>
            <input
              v-model="settings.password"
              type="password"
              placeholder="•••••••"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="saveSettings" class="btn-primary">保存</button>
          <button @click="showSettings = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import {
  checkHealth,
  createSession,
  sendMessage as sendToAI,
  getSessionMessages,
  getProviders
} from './utils/opencode.js'

// 配置 marked 选项
marked.use({
  breaks: true,  // 支持 GitHub 风格的换行
  gfm: true,     // 启用 GitHub 风格的 Markdown
})

// 状态
const connected = ref(false)
const connectionError = ref(null)
const currentSession = ref(null)
const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)

// 设置
const showSettings = ref(false)
const settings = ref({
  serverUrl: 'http://localhost:4096',
  username: 'opencode',
  password: 'opencode123',
  selectedModel: ''
})
const providers = ref([])
const availableModels = ref([])
const currentModel = ref(null)

// 建议问题
const suggestions = ref([
  '请用一句话介绍 OpenCode',
  '如何使用 OpenCode SDK？',
  'OpenCode 有哪些功能？'
])

// 初始化
onMounted(async () => {
  // 加载保存的设置
  const savedSettings = localStorage.getItem('opencode-settings')
  if (savedSettings) {
    try {
      const parsed = JSON.parse(savedSettings)
      settings.value = { ...settings.value, ...parsed }
    } catch (e) {
      console.error('恢复设置失败:', e)
    }
  }

  await connectToServer()
})

// 连接服务器
async function connectToServer() {
  try {
    connectionError.value = null
    const health = await checkHealth()
    connected.value = true
    console.log('✅ 服务器连接成功', health)

    // 获取可用的模型提供商
    providers.value = await getProviders()
    console.log('✅ 获取模型提供商成功', providers.value)

    // 提取所有可用模型
    availableModels.value = extractModels(providers.value)
    console.log('✅ 可用模型列表', availableModels.value)

    // 如果有保存的模型选择，应用它
    if (settings.value.selectedModel) {
      const model = availableModels.value.find(m => m.id === settings.value.selectedModel)
      if (model) {
        currentModel.value = { providerID: model.providerID, modelID: model.modelID }
      }
    }

    // 创建初始会话
    await createNewSession()
  } catch (error) {
    connected.value = false
    connectionError.value = error.message
    console.error('❌ 连接失败:', error)
  }
}

// 创建新会话
async function createNewSession() {
  try {
    const session = await createSession('Web 聊天会话')
    currentSession.value = session
    messages.value = []
    console.log('✅ 创建会话成功', session.id)

    // 滚动到底部
    await scrollToBottom()
  } catch (error) {
    console.error('❌ 创建会话失败:', error)
    alert('创建会话失败: ' + error.message)
  }
}

// 发送消息
async function handleSendMessage(text) {
  if (!text.trim() || isLoading.value || !connected.value) return

  // 添加用户消息
  const userMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: text,
    time: Date.now()
  }
  messages.value.push(userMessage)

  // 清空输入框
  inputText.value = ''

  // 滚动到底部
  await scrollToBottom()

  // 发送到 AI
  isLoading.value = true
  try {
    // 确定使用的模型
    const modelToUse = settings.value.selectedModel
      ? availableModels.value.find(m => m.id === settings.value.selectedModel)
      : null

    const responseData = await sendToAI(
      currentSession.value.id,
      text,
      modelToUse ? { providerID: modelToUse.providerID, modelID: modelToUse.modelID } : null
    )

    console.log('📦 收到响应数据:', responseData)

    // 从响应中提取内容和思考过程
    let textContent = '(无回复)'
    let thinking = null

    if (responseData && responseData.parts) {
      // 提取思考过程 (type: 'reasoning')
      const reasoningParts = responseData.parts.filter(part => part.type === 'reasoning')
      if (reasoningParts.length > 0) {
        thinking = reasoningParts.map(part => part.text).join('\n\n')
        console.log('💭 发现思考过程:', thinking.substring(0, 100) + '...')
      }

      // 提取最终回复 (type: 'text')
      const textParts = responseData.parts.filter(part => part.type === 'text' && part.text)
      if (textParts.length > 0) {
        textContent = textParts.map(part => part.text).join('\n')
      }
    }

    // 添加 AI 回复
    const aiMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: textContent,
      thinking: thinking,
      time: Date.now()
    }
    messages.value.push(aiMessage)

    console.log('✅ 消息已添加到列表，当前消息数:', messages.value.length)
  } catch (error) {
    console.error('❌ 发送消息失败:', error)
    // 添加错误消息
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `⚠️ 发送失败: ${error.message}`,
      time: Date.now()
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

// 处理表单提交
function handleSubmit() {
  handleSendMessage(inputText.value)
}

// 处理键盘事件
function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSubmit()
  }
}

// 滚动到底部
async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化消息（使用 marked 解析 Markdown）
function formatMessage(text) {
  if (!text) return ''

  try {
    // 使用 marked 解析 Markdown
    const html = marked.parse(text)
    return html
  } catch (error) {
    console.error('Markdown 解析失败:', error)
    // 如果解析失败，返回转义后的纯文本
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>')
  }
}

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 保存设置
function saveSettings() {
  // 保存到 localStorage
  localStorage.setItem('opencode-settings', JSON.stringify(settings.value))

  // 更新当前使用的模型
  if (settings.value.selectedModel) {
    const model = availableModels.value.find(m => m.id === settings.value.selectedModel)
    if (model) {
      currentModel.value = { providerID: model.providerID, modelID: model.modelID }
    }
  } else {
    currentModel.value = null
  }

  showSettings.value = false
}

// 从提供商列表中提取所有模型
function extractModels(providers) {
  const models = []
  let modelIdCounter = 1

  if (!providers || providers.length === 0) {
    return models
  }

  providers.forEach(provider => {
    if (provider.models && provider.models.length > 0) {
      provider.models.forEach(model => {
        models.push({
          id: `model-${modelIdCounter++}`,
          name: `${provider.name} - ${model}`,
          providerID: provider.id,
          modelID: model
        })
      })
    }
  })

  return models.sort((a, b) => a.name.localeCompare(b.name))
}
</script>

<style scoped>
/* 这里放置组件样式，将在下一节完整展示 */
</style>
```

### 3. 全局样式

创建 `src/style.css`（ChatGPT 风格）：

```css
/* 全局样式 - ChatGPT 风格 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --bg-primary: #343541;
  --bg-secondary: #444654;
  --text-primary: #ECECF1;
  --text-secondary: #C5C5D2;
  --accent: #10A37F;
  --accent-hover: #0D8A6A;
  --border: #565869;
  --input-bg: #40414F;
  --user-bubble: #343541;
  --ai-bubble: #444654;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  overflow: hidden;
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(197, 197, 210, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(197, 197, 210, 0.5);
}
```

---

## 🎨 UI/UX 设计要点

### 1. 响应式设计

```css
/* 响应式 */
@media (max-width: 640px) {
  .message-content {
    padding: 0;
  }

  .input-container {
    flex-direction: column;
  }

  .send-btn {
    width: 100%;
  }
}
```

### 2. 动画效果

```css
/* 打字指示器动画 */
.typing-indicator span {
  width: 0.5rem;
  height: 0.5rem;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
```

### 3. Markdown 样式

```css
/* 代码块样式 */
.message-body :deep(pre) {
  background: #1e1e1e;
  border-radius: 0.5rem;
  padding: 1rem;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.message-body :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
  color: #e06c75;
}
```

---

## 🚀 运行与测试

### 启动开发服务器

```bash
npm run dev
```

访问 `http://localhost:5173` 即可看到你的 AI 助手界面！

### 功能测试清单

- [ ] 服务器连接状态显示
- [ ] 发送消息并获得 AI 回复
- [ ] Markdown 渲染（代码块、列表等）
- [ ] 思考过程展示（reasoning）
- [ ] 会话管理（创建新会话）
- [ ] 模型选择
- [ ] 设置保存到 localStorage
- [ ] 响应式布局（移动端适配）



## 💡 最佳实践

### 1. 错误处理

```javascript
try {
  const result = await client.session.prompt(requestBody)
  if (result.error) {
    throw new Error(result.error[0]?.message || '请求失败')
  }
  return result.data
} catch (error) {
  console.error('请求失败:', error)
  // 显示用户友好的错误消息
  throw new Error(`操作失败: ${error.message}`)
}
```

### 2. 性能优化

```javascript
// 使用防抖优化输入
import { debounce } from 'lodash-es'

const debouncedSearch = debounce((query) => {
  // 搜索逻辑
}, 300)

// 虚拟滚动处理长对话
import { FixedSizeList } from 'vue-virtual-scroller'
```

### 3. 安全性

```javascript
// XSS 防护：marked 配置
marked.use({
  sanitize: true,  // 启用 HTML 清理
  sanitizer: (html) => {
    // 自定义清理逻辑
    return DOMPurify.sanitize(html)
  }
})
```

---

## ⚠️ 避坑指南

### 1. CORS 问题

**问题**：浏览器阻止跨域请求

**解决方法 1**：Vite 代理（推荐）
```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:4096',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

**解决方法 2**：服务器端 CORS
```bash
# 启动 OpenCode 时允许 CORS
opencode serve --port 4096 --cors
```

### 2. 认证信息泄露

**问题**：在前端直接暴露密码

**解决方案**：
- ✅ 使用环境变量（`.env` 文件）
- ✅ 生产环境使用服务端代理
- ✅ 实现 Token 认证机制
- ❌ 不要硬编码密码
- ❌ 不要提交 `.env` 到 Git

### 3. SDK 版本问题

**问题**：导入路径错误

**正确导入**：
```javascript
// ✅ 正确（SDK v2）
import { createOpencodeClient } from '@opencode-ai/sdk/v2/client'

// ❌ 错误
import { createOpencodeClient } from '@opencode-ai/sdk'
```

### 4. 响应数据结构

**问题**：AI 返回的数据包含多种类型

**解决方案**：
```javascript
// 提取思考过程 (type: 'reasoning')
const reasoningParts = responseData.parts.filter(part => part.type === 'reasoning')

// 提取最终回复 (type: 'text')
const textParts = responseData.parts.filter(part => part.type === 'text' && part.text)
```

### 5. localStorage 容量限制

**问题**：大量对话历史超出限制

**解决方案**：
```javascript
// 压缩数据
import { compressToUTF16, decompressFromUTF16 } from 'lz-string'

// 只保留最近 N 条消息
const MAX_MESSAGES = 100
if (messages.value.length > MAX_MESSAGES) {
  messages.value = messages.value.slice(-MAX_MESSAGES)
}
```

---

## 🎯 扩展方向

### 1. 多模态支持
- 📷 图片上传和分析
- 🎤 语音输入（Web Speech API）
- 📄 文件上传（PDF、Word 等）

### 2. 协作功能
- 🔗 会话分享链接
- 👥 团队知识库
- 🔐 权限管理

### 3. 智能增强
- 🎯 意图识别
- 📋 自动任务创建
- 🕸️ 知识图谱构建

### 4. 移动端优化
- 📱 PWA 支持
- 📲 原生应用（Capacitor）
- 💻 桌面应用（Electron）

### 5. 高级功能
- 🌊 流式响应（SSE）
- 🎨 代码语法高亮（highlight.js）
- 📊 数据可视化
- 🔍 全文搜索

---

## 📚 相关资源

- [OpenCode SDK 文档](https://github.com/opencode-org/sdk)
- [Vue 3 官方文档](https://vuejs.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Marked 文档](https://marked.js.org/)

---

## 总结

通过本教程，你已经学会了如何使用 Vue 3 和 OpenCode SDK 构建一个完整的 AI 助手 Web 应用。

### 关键要点回顾

1. **Vue 3 Composition API**：更灵活的代码组织
2. **Vite 代理**：解决开发环境 CORS 问题
3. **SDK v2**：使用 `@opencode-ai/sdk/v2/client` 导入
4. **Markdown 渲染**：使用 marked 解析 AI 回复
5. **思考过程**：提取 `reasoning` 类型的 parts
6. **模型选择**：动态获取可用模型列表
7. **设置持久化**：使用 localStorage 保存用户配置

### 下一步建议

1. **添加用户认证**：实现登录注册功能
2. **会话管理**：支持会话列表和切换
3. **流式响应**：使用 SSE 实现实时流式输出
4. **代码高亮**：集成 highlight.js
5. **文件上传**：支持多模态输入

---

万智创界 - AI技术实战派布道者；关注我，你将获得：
✓ AI前沿动态与趋势
✓ 真实项目案例 + 代码
✓ 工程化实践与避坑
