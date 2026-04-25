# Deep Agents Demo 目录

本目录包含从基础到进阶的完整学习示例，按学习路径分类。

## 📁 目录结构

```
examples/
├── 00_basics/              # 基础概念
├── 01_backends/            # Backend 体系
├── 02_tools/               # 自定义工具
├── 03_subagents/           # 子代理系统
├── 04_skills/              # Skills 体系
├── 05_integration/         # 综合应用
├── 06_production/          # 生产环境
└── 07_advanced/            # 高级主题
```

## 🚀 学习路径

### Week 1: 基础概念 (00_basics)
从最简单的 Agent 开始，理解核心概念

### Week 2: Backend 与工具 (01_backends, 02_tools)
深入理解存储后端和自定义工具

### Week 3: Multi-Agent (03_subagents, 04_skills)
掌握子代理和 Skills 模式

### Week 4: 生产化 (05_integration, 06_production)
综合应用和生产部署

### Week 5-6: 高级主题 (07_advanced)
性能优化、自定义扩展

## 📖 运行说明

所有 demo 都支持 `--dry-run` 参数查看说明而不调用模型：

```bash
python examples/00_basics/simple_agent.py --dry-run
```

完整运行需要配置 `.env` 文件：

```bash
pip install -e .
python examples/00_basics/simple_agent.py
```

## 📝 详细说明

每个子目录都有独立的 README.md，包含：
- 学习目标
- 前置知识
- 运行步骤
- 关键代码解析
- 练习题
