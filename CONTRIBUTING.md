# 贡献指南

感谢你对万智创界 AI 实验室的关注！我们欢迎各种形式的贡献。

---

## 🤝 如何贡献

### 报告问题

如果你发现了 Bug 或有功能建议：

1. 检查 [Issues](https://github.com/wanrengang/wanzhi-ai-lab/issues) 是否已有类似问题
2. 如果没有，创建新 Issue
3. 使用合适的模板填写信息

### 提交代码

我们欢迎代码贡献！流程如下：

#### 1. Fork 仓库

点击右上角的 Fork 按钮

#### 2. 克隆到本地

```bash
git clone https://github.com/你的用户名/wanzhi-ai-lab.git
cd wanzhi-ai-lab
```

#### 3. 创建分支

```bash
git checkout -b feature/你的功能名
# 或
git checkout -b fix/你要修复的问题
```

#### 4. 做出修改

- 遵循现有代码风格
- 添加必要的注释
- 更新相关文档

#### 5. 提交修改

```bash
git add .
git commit -m "feat: 添加某功能"
# 或
git commit -m "fix: 修复某问题"
```

**Commit 规范**：
- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具

#### 6. 推送到 GitHub

```bash
git push origin feature/你的功能名
```

#### 7. 创建 Pull Request

1. 访问你 Fork 的仓库
2. 点击 "Pull Request" 按钮
3. 填写 PR 模板
4. 等待 review

---

## 📝 代码规范

### Python 代码

- 遵循 PEP 8
- 使用类型提示
- 添加 docstring

**示例**：
```python
from typing import List, Optional

def search_web(query: str, max_results: int = 5) -> List[str]:
    """
    搜索网络信息

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        搜索结果列表

    Raises:
        ValueError: 当 query 为空时
    """
    if not query:
        raise ValueError("Query cannot be empty")

    # 实现代码
    pass
```

### 项目结构

每个项目应包含：

```
project-name/
├── README.md          # 项目说明
├── requirements.txt   # 依赖列表
├── .env.example      # 环境变量模板
├── src/              # 源代码
├── tests/            # 测试
└── docs/             # 文档
```

### README 规范

每个项目必须有 README.md，包含：

```markdown
# 项目标题

> 简短描述

## 功能特性
- 特性1
- 特性2

## 安装
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## 使用
\`\`\`python
python main.py
\`\`\`

## 配置
复制 .env.example 为 .env 并填写配置

## 常见问题
...
```

---

## 🎯 贡献方向

我们特别欢迎以下贡献：

### L1 项目（零基础）

- 新手友好的工具教程
- 应用案例展示
- 常见问题解答

### L2 项目（进阶实战）

- 实战项目代码
- 框架对比分析
- 避坑经验分享

### L3 项目（专业深度）

- 源码分析
- 架构设计
- 性能优化

### 文档改进

- 修正错别字
- 补充说明
- 翻译文档

---

## 📧 联系我们

有问题？通过以下方式联系：

- GitHub Issues: [提问](https://github.com/wanrengang/wanzhi-ai-lab/issues)
- 公众号：万智创界
- 邮箱：365700955@qq.com

---

## ⭐ 成为贡献者

所有贡献者将被添加到 [CONTRIBUTORS.md](CONTRIBUTORS.md)

感谢你的贡献！🎉
