# AGENTS.md - 万智创界 AI 实验室开发指南

> 本文档面向 AI 代理和协作者，说明如何在万智创界 AI 实验室知识库中创建和编辑内容。

---

## 📁 项目结构

本项目是一个基于 Markdown 的 AI 技术知识库，采用 Obsidian 管理。

```
wanzhi-ai-lab/
├── L1-zero-basis/     # 🟢 零基础入门 - 无需编程基础的大白话讲解
├── L2-practical/      # 🟡 进阶实战 - 需要编程基础，含完整代码
├── L3-tools/          # 🔴 效率工具 - 前沿 AI 工具分享与实践
├── assets/images/     # 图片资源
└── README.md
```

### 内容分级

| 级别 | 目标受众 | 内容特点 |
|------|----------|----------|
| 🟢 L1 零基础 | 无编程基础 | 大白话讲解 |
| 🟡 L2 进阶 | 有编程基础 | 含完整代码，深度解析 |
| 🔴 L3 工具 | AI 从业者 | 工具使用与实践 |

---

## ✍️ 内容创作规范

### 文件命名

```
YYYY-MM-DD-标题.md
```

**规则**：日期前缀 + 中文标题，避免特殊字符和空格

**示例**：`2026-02-26-基于OpenCode-SDK构建个人AI助手平台-Vue3实战指南.md`

### Frontmatter（必需）

```yaml
---
title: 文章标题
tags:
  - 标签1
  - 标签2
created: 2026-02-26
updated: 2026-02-26
category: 分类
status: completed  # draft/completed/archived
rating: 5  # 1-5
description: 一句话描述文章价值
---
```

**必需字段**：title, tags, created, updated, description

### Markdown 编写

- **标题层级**：H2 主要章节，H3 子章节（H1 已在 frontmatter 定义）
- **H2 标题**：建议使用 emoji 前缀（📖 核心思想、🎯 为什么需要、⚠️ 前置条件等）
- **代码块**：必须使用语言标识符（\`\`\`bash、\`\`\`typescript、\`\`\`python）
- **Wiki 链接**：内部链接使用 Obsidian 语法 `[[文件名]]`
- **列表**：无序列表 `-`，有序列表 `1.`
- **表格**：标准 GitHub Flavored Markdown 语法

---

## 🗣️ 语言与术语规范

- **正文**：简体中文
- **代码注释**：简体中文  
- **技术术语**：英文原文（首次出现时加中文解释）

**常见术语**：OpenCode、LangChain（直接使用）；LLM、Agent（首次中文，后续英文）

---

## 🎨 内容组织

### 文章结构模板

```markdown
---
frontmatter...
---

# 文章标题

> 📖 核心思想/简介（可选）

## 🎯 为什么需要？（问题背景）
## ⚠️ 前置条件
## 🏗️ 技术方案/实现步骤
## 💡 实践要点
## 📚 参考资料
```

### 内容类型

1. **实战教程**（L2）：完整代码 + 分步骤说明 + 截图
2. **调研报告**（L2/L3）：对比表格 + 架构图 + 优劣势分析
3. **工具文档**（L3）：安装步骤 + 配置说明 + 使用示例 + FAQ

---

## 🔄 Git 工作流

### 分支命名

- `feature/xxx` - 功能分支
- `fix/xxx` - 修复分支
- `docs/xxx` - 文档分支

### 提交信息（中文）

```bash
git commit -m "feat: 添加 OpenCode SDK Vue3 实战指南"
git commit -m "docs: 更新 browser-use 工具文档"
git commit -m "fix: 修正代码示例"
```

**提交类型**：feat（新增）、docs（更新）、fix（修复）、chore（资源）、style（格式）

### 提交前检查

- [ ] Frontmatter 完整且格式正确
- [ ] 文件名与标题一致
- [ ] Wiki 链接有效
- [ ] 代码块有语言标识
- [ ] 图片在 `assets/images/`

---

## 📝 质量标准

### 必需项

- ✅ 完整 frontmatter
- ✅ 清晰的章节结构（H2/H3）
- ✅ 可运行的代码示例
- ✅ 适当的截图/图示

### 禁止项

- ❌ 提交明文密钥、密码
- ❌ 提交大文件（> 5MB）
- ❌ 提交临时文件（`.tmp`, `.bak`）
- ❌ 无语言标识的代码块
- ❌ 损坏的 Wiki 链接

---

## 🔧 工具与资源

- **编辑器**：Obsidian（最佳）、VS Code + Markdown 插件
- **图片管理**：存放在 `assets/images/`
- **Markdown 参考**：[Obsidian 官方文档](https://help.obsidian.md/)、[GitHub Flavored Markdown](https://github.github.com/gfm/)

---

## 📞 联系方式

- **公众号**：万智创界
- **邮箱**：365700955@qq.com
- **GitHub**：[@wanrengang](https://github.com/wanrengang)

---

## 🎯 快速检查清单

发布前确认：

- [ ] 文件名：`YYYY-MM-DD-标题.md`
- [ ] Frontmatter 完整
- [ ] 目录级别正确（L1/L2/L3）
- [ ] Wiki 链接语法 `[[...]]`
- [ ] 代码块有语言标识
- [ ] 中文排版规范（中英文间留空格）
- [ ] 提交信息符合规范

---

**最后更新**：2026-03-01  
**维护者**：万智创界 AI 实验室

