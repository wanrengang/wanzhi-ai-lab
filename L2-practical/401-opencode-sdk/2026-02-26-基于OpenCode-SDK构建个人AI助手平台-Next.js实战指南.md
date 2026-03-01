---
title: 基于 OpenCode SDK 构建个人 AI 助手平台 - Next.js 实战指南
tags:
  - OpenCode
  - Next.js
  - AI
  - SDK
  - Web开发
created: 2026-02-26
updated: 2026-02-26
category: 技术实践
status: completed
rating: 5
---

# 基于 OpenCode SDK 构建个人 AI 助手平台 - Next.js 实战指南

## 📖 项目背景

在上一篇文章《OpenCode SDK 深度解析》中，我们了解了 SDK 的核心概念和 API 设计。今天，我们将从实践角度出发，使用 **Next.js** 构建一个完整的 Web 应用，让用户能够通过浏览器随时随地与个人 AI 助手互动。

### 🎯 核心价值

- **零依赖安装**：无需本地安装 OpenCode CLI
- **跨平台访问**：通过浏览器即可访问
- **会话持久化**：所有对话记录保存在服务器
- **实时交互**：流式响应提升用户体验

---

## 🏗️ 技术架构设计

### 整体架构

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Next.js 前端  │ ←──→ │  API Routes      │ ←──→ │ OpenCode Server │
│   (App Router)  │      │  (服务端代理)    │      │   (localhost)   │
└─────────────────┘      └──────────────────┘      └─────────────────┘
    浏览器端                  服务端                    AI 服务
```

### 技术栈选型

| 层级 | 技术 | 说明 |
|-----|------|-----|
| 前端框架 | Next.js 14 | App Router + Server Actions |
| UI 组件 | shadcn/ui | 现代化组件库 |
| 状态管理 | React Hooks | useState + useContext |
| HTTP 客户端 | @opencode-ai/sdk/v2 | 官方 SDK |
| 样式方案 | Tailwind CSS | 实用优先的 CSS 框架 |

---

## 🚀 快速开始

### 1. 创建 Next.js 项目

```bash
npx create-next-app@latest my-ai-assistant \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --import-alias "@/*"

cd my-ai-assistant
npm install @opencode-ai/sdk/v2
```

### 2. 配置环境变量

创建 `.env.local` 文件：

```env
OPENCODE_SERVER_URL=http://localhost:4096
OPENCODE_USERNAME=opencode
OPENCODE_PASSWORD=opencode123
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. 项目结构

```
my-ai-assistant/
├── app/
│   ├── api/
│   │   └── chat/
│   │       └── route.ts          # 聊天 API
│   ├── layout.tsx                # 根布局
│   ├── page.tsx                  # 首页
│   └── globals.css               # 全局样式
├── components/
│   ├── ChatBox.tsx               # 聊天框组件
│   ├── MessageList.tsx           # 消息列表
│   └── InputBar.tsx              # 输入框
├── lib/
│   ├── opencode.ts               # SDK 客户端封装
│   └── utils.ts                  # 工具函数
└── types/
    └── chat.ts                   # 类型定义
```

---

## 💻 核心功能实现

### 1. SDK 客户端封装

创建 `lib/opencode.ts`：

```typescript
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client";

const SERVER_URL = process.env.OPENCODE_SERVER_URL || "http://localhost:4096";
const USERNAME = process.env.OPENCODE_USERNAME || "opencode";
const PASSWORD = process.env.OPENCODE_PASSWORD || "opencode123";

const auth = Buffer.from(`${USERNAME}:${PASSWORD}`).toString('base64');

export const opencodeClient = createOpencodeClient({
  baseUrl: SERVER_URL,
  throwOnError: true,
  headers: {
    'Authorization': `Basic ${auth}`
  }
});

// 获取服务器健康状态
export async function checkHealth() {
  try {
    const health = await opencodeClient.global.health();
    return health.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
}

// 获取当前项目信息
export async function getCurrentProject() {
  try {
    const project = await opencodeClient.project.current();
    return project.data;
  } catch (error) {
    console.error('Failed to get project:', error);
    throw error;
  }
}
```

### 2. 类型定义

创建 `types/chat.ts`：

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}
```

### 3. API Routes - 聊天接口

创建 `app/api/chat/route.ts`：

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { opencodeClient } from '@/lib/opencode';

export async function POST(request: NextRequest) {
  try {
    const { message, sessionId } = await request.json();

    // 创建新会话或使用现有会话
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      const session = await opencodeClient.session.create({
        title: `Web Chat - ${new Date().toLocaleString()}`
      });
      currentSessionId = session.data.id;
    }

    // 发送消息给 AI
    const response = await opencodeClient.session.prompt({
      sessionID: currentSessionId,
      model: {
        providerID: "zai-coding-plan",
        modelID: "glm-4.7"
      },
      parts: [{
        type: "text",
        text: message
      }]
    });

    // 提取 AI 回复
    const aiReply = response.data?.parts?.[0]?.text || '抱歉，我无法回复。';

    return NextResponse.json({
      sessionId: currentSessionId,
      reply: aiReply
    });

  } catch (error: any) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: '处理请求失败' },
      { status: 500 }
    );
  }
}
```

### 4. 聊天框组件

创建 `components/ChatBox.tsx`：

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';
import { Message } from '@/types/chat';

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 发送消息
  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          sessionId
        })
      });

      const data = await response.json();

      if (data.sessionId && !sessionId) {
        setSessionId(data.sessionId);
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.reply,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-10">
            👋 你好！我是你的 AI 助手，有什么可以帮助你的吗？
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                <div className="text-sm font-semibold mb-1">
                  {msg.role === 'user' ? '你' : 'AI 助手'}
                </div>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="输入你的消息..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
        >
          发送
        </button>
      </div>
    </div>
  );
}
```

### 5. 主页面

更新 `app/page.tsx`：

```typescript
import ChatBox from '@/components/ChatBox';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-800">
            🤖 AI 个人助手
          </h1>
          <p className="text-sm text-gray-600">
            基于 OpenCode SDK 构建的智能对话平台
          </p>
        </div>
      </header>
      <ChatBox />
    </main>
  );
}
```

---

## 🎨 样式优化

在 `app/globals.css` 中添加动画：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer utilities {
  .delay-100 {
    animation-delay: 0.1s;
  }
  .delay-200 {
    animation-delay: 0.2s;
  }
}
```

---

## 🚀 运行与测试

### 启动开发服务器

```bash
npm run dev
```

访问 `http://localhost:3000` 即可看到你的 AI 助手界面！

### 功能测试清单

- [ ] 发送消息并获得 AI 回复
- [ ] 会话 ID 保持
- [ ] 加载状态显示
- [ ] 错误处理
- [ ] 响应式布局（移动端适配）

---

## 🔧 进阶功能

### 1. 添加会话历史

创建 `app/api/sessions/route.ts`：

```typescript
import { NextResponse } from 'next/server';
import { opencodeClient } from '@/lib/opencode';

export async function GET() {
  try {
    const sessions = await opencodeClient.session.list();
    return NextResponse.json(sessions.data);
  } catch (error) {
    return NextResponse.json(
      { error: '获取会话列表失败' },
      { status: 500 }
    );
  }
}
```

### 2. 流式响应支持

```typescript
// 使用 Server-Sent Events 实现流式响应
export async function POST(request: NextRequest) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const response = await opencodeClient.session.prompt({
          sessionID: sessionId,
          model: { providerID: "zai-coding-plan", modelID: "glm-4.7" },
          parts: [{ type: "text", text: message }]
        });

        // 模拟流式输出
        const text = response.data?.parts?.[0]?.text || '';
        for (const char of text) {
          controller.enqueue(encoder.encode(char));
          await new Promise(resolve => setTimeout(resolve, 20));
        }

        controller.close();
      } catch (error) {
        controller.error(error);
      }
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
}
```

### 3. 上下文感知聊天

```typescript
// 获取会话历史消息
async function getSessionHistory(sessionId: string) {
  const messages = await opencodeClient.session.messages({
    sessionID: sessionId
  });
  return messages.data;
}

// 在发送新消息前附加历史上下文
const history = await getSessionHistory(sessionId);
const contextPrompt = `
  以下是我们的对话历史：
  ${history.map(m => `${m.role}: ${m.content}`).join('\n')}

  用户的新消息：${message}
`;
```

---

## 🚢 部署指南

### Vercel 部署（推荐）

```bash
npm install -g vercel
vercel
```

**注意事项：**

1. **CORS 配置**：确保 OpenCode 服务器允许跨域请求
2. **环境变量**：在 Vercel 控制台配置环境变量
3. **服务器地址**：使用可公网访问的 OpenCode 服务器地址

### Docker 部署

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

---

## 💡 最佳实践

### 1. 错误处理

```typescript
// 统一错误处理
export function handleApiError(error: any) {
  if (error.error?.[0]?.message) {
    return error.error[0].message;
  }
  return '发生未知错误，请稍后重试';
}
```

### 2. 请求去重

```typescript
// 防止重复提交
const [isSending, setIsSending] = useState(false);

const sendMessage = async () => {
  if (isSending) return;
  setIsSending(true);
  try {
    // ... 发送逻辑
  } finally {
    setIsSending(false);
  }
};
```

### 3. 性能优化

```typescript
// 使用 React.memo 优化组件
export default React.memo(ChatBox);

// 虚拟滚动处理长对话
import { FixedSizeList } from 'react-window';
```

---

## ⚠️ 避坑指南

### 1. CORS 问题

**问题**：浏览器阻止跨域请求

**解决**：
```typescript
// 在 OpenCode 服务器启动时添加 --cors
opencode serve --port 4096 --cors
```

### 2. 认证信息泄露

**问题**：在前端直接暴露密码

**解决**：
- 使用 API Routes 作为代理
- 将敏感信息放在服务端环境变量
- 考虑实现 Token 认证机制

### 3. 会话状态丢失

**问题**：刷新页面后会话 ID 丢失

**解决**：
```typescript
// 使用 localStorage 持久化会话 ID
useEffect(() => {
  const savedSessionId = localStorage.getItem('sessionId');
  if (savedSessionId) {
    setSessionId(savedSessionId);
  }
}, []);

useEffect(() => {
  if (sessionId) {
    localStorage.setItem('sessionId', sessionId);
  }
}, [sessionId]);
```

### 4. 流式响应兼容性

**问题**：不同浏览器对 SSE 支持程度不同

**解决**：
```typescript
// 降级方案：检测浏览器支持
const supportsSSE = typeof EventSource !== 'undefined';

if (!supportsSSE) {
  // 使用传统轮询方式
  const interval = setInterval(async () => {
    const response = await fetch(`/api/messages/${sessionId}`);
    const data = await response.json();
    // 更新消息
  }, 2000);
}
```

---

## 🎯 扩展方向

### 1. 多模态支持
- 图片上传
- 语音输入
- 文件分析

### 2. 协作功能
- 会话分享
- 团队知识库
- 权限管理

### 3. 智能增强
- 意图识别
- 自动任务创建
- 知识图谱构建

### 4. 移动端优化
- PWA 支持
- 原生应用（React Native）
- 桌面应用（Electron）

---

## 📚 相关资源

- [OpenCode SDK 文档](https://github.com/opencode-org/sdk)
- [Next.js 官方文档](https://nextjs.org/docs)
- [shadcn/ui 组件库](https://ui.shadcn.com/)

---

## 结语

通过本教程，你已经学会了如何使用 Next.js 和 OpenCode SDK 构建一个完整的 AI 助手 Web 应用。这个基础架构可以根据你的需求不断扩展，添加更多功能。

**下一步建议：**
1. 添加用户认证系统
2. 实现会话管理功能
3. 集成更多 AI 模型
4. 优化 UI/UX 体验

---

万智创界 - AI技术实战派布道者；关注我，你将获得：
✓ AI前沿动态与趋势
✓ 真实项目案例 + 代码
✓ 工程化实践与避坑
