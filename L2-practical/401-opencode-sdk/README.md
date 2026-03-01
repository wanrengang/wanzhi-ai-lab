# OpenCode SDK 实战系列

> 🟡 L2 - 进阶实战 | 💻 全栈开发 | 🤖 AI 平台

本系列教你如何基于 OpenCode SDK 构建个人 AI 助手平台，包含 Next.js 和 Vue3 两个版本。

---

## 📚 系列教程

### 1. Next.js 版本
- [基于 OpenCode SDK 构建个人 AI 助手平台 - Next.js 实战指南](./2026-02-26-基于OpenCode-SDK构建个人AI助手平台-Next.js实战指南.md)
  - 项目架构
  - 核心功能
  - 完整代码
  - 部署方案

### 2. Vue3 版本
- [基于 OpenCode SDK 构建个人 AI 助手平台 - Vue3 实战指南](./2026-02-26-基于OpenCode-SDK构建个人AI助手平台-Vue3实战指南.md)
  - Vue3 实现
  - Composition API
  - 组件化设计
  - 状态管理

---

## 🎯 项目特点

### 核心功能

| 功能 | 说明 |
|------|------|
| 🤖 AI 对话 | 多模型支持（GPT/Claude/文心） |
| 📝 笔记管理 | CRUD + AI 总结 |
| 🔍 智能搜索 | 向量检索 + 语义搜索 |
| 📊 数据分析 | AI 数据洞察 |
| 🔌 插件系统 | 自定义工具扩展 |

### 技术栈

**Next.js 版本**：
- ⚛️ Next.js 14 (App Router)
- 🎨 Tailwind CSS
- 🔄 Zustand 状态管理
- 🤖 OpenCode SDK

**Vue3 版本**：
- ⚡ Vue 3 + TypeScript
- 🎨 Element Plus
- 📦 Pinia 状态管理
- 🤖 OpenCode SDK

---

## 🚀 快速开始

### Next.js 版本

```bash
# 克隆项目
git clone https://github.com/xxx/ai-assistant-nextjs.git

# 安装依赖
cd ai-assistant-nextjs
npm install

# 配置环境
cp .env.example .env

# 启动开发
npm run dev
```

### Vue3 版本

```bash
# 克隆项目
git clone https://github.com/xxx/ai-assistant-vue3.git

# 安装依赖
cd ai-assistant-vue3
npm install

# 配置环境
cp .env.example .env

# 启动开发
npm run dev
```

---

## 📖 项目结构

```
ai-assistant/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── api/          # API 路由
│   │   ├── chat/         # 对话页面
│   │   └── notes/        # 笔记页面
│   ├── components/       # 组件
│   │   ├── ChatBox.tsx
│   │   ├── NoteEditor.tsx
│   │   └── SearchBar.tsx
│   ├── lib/              # 工具库
│   │   ├── opencode.ts   # OpenCode SDK
│   │   └── db.ts         # 数据库
│   └── store/            # 状态管理
├── public/
└── package.json
```

---

## 💡 核心功能实现

### 1. AI 对话

```typescript
import { OpenCodeClient } from '@/lib/opencode';

const client = new OpenCodeClient({
  apiKey: process.env.OPENCODE_API_KEY,
});

async function chat(message: string) {
  const response = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: message }],
  });
  return response;
}
```

### 2. 笔记 AI 总结

```typescript
async function summarizeNote(note: string) {
  const summary = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [{
      role: 'system',
      content: '请总结以下笔记的核心观点...'
    }, {
      role: 'user',
      content: note
    }],
  });
  return summary;
}
```

### 3. 向量搜索

```typescript
async function searchNotes(query: string) {
  const results = await client.vectors.search({
    query,
    top_k: 5,
  });
  return results;
}
```

---

## 🔧 环境配置

### .env.example

```bash
# OpenCode SDK
OPENCODE_API_KEY=your_api_key_here
OPENCODE_BASE_URL=https://api.opencode.com

# 数据库
DATABASE_URL=postgresql://user:pass@localhost/db

# 向量数据库
VECTOR_DB_URL=http://localhost:8080

# 其他
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## 📊 项目对比

| 特性 | Next.js | Vue3 |
|------|---------|------|
| 学习曲线 | 中 | 低 |
| 生态丰富 | ✅ | ✅ |
| 性能 | 高 | 高 |
| SSR | ✅ | ❌ |
| 开发体验 | 优秀 | 优秀 |

---

## 🚀 部署指南

### Next.js (Vercel)

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel
```

### Vue3 (Netlify)

```bash
# 构建
npm run build

# 部署到 Netlify
netlify deploy --prod
```

---

## 🎓 学习路径

```
第1步：选择技术栈
↓
Next.js 或 Vue3

第2步：跟着教程实现
↓
阅读完整教程 → 复制代码 → 运行测试

第3步：定制功能
↓
添加自定义功能 → 优化用户体验

第4步：部署上线
↓
配置域名 → 正式发布
```

---

## 🔗 相关资源

- **OpenCode 文档**: https://docs.opencode.com
- **Next.js 文档**: https://nextjs.org/docs
- **Vue3 文档**: https://vuejs.org

---

## 💬 交流反馈

- **GitHub Issues**: 提问和反馈
- **公众号**: 万智创界
- **加群交流**: 回复【加群】

---

**发布时间**：2026-02-26
**作者**：万智创界
**难度**：🟡 进阶实战
**预计学习时间**：3-5天
**标签**：#OpenCode #Next.js #Vue3 #全栈开发 #AI平台
