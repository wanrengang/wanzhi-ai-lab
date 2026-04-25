---
name: data-analysis-workflow
description: 在 DeepAgent-Pro 中做表格/SQL 分析时的推荐步骤（先探查再结论，大结果写虚拟文件）。
license: MIT
---

# 数据分析工作流（项目内置 Skill）

## 何时使用

- 用户上传 CSV/Excel 或提供数据库/SQL 需求，需要结构化分析时
- 需要避免一次性把超大工具输出塞进回复时

## 建议步骤

1. **澄清目标**：指标、时间范围、分组维度、输出形式（表/图/报告）。
2. **先探查**：用 `describe_data` / `list_tables` + `describe_table` 了解字段与规模；大表 SQL 必带 `LIMIT`。
3. **再操作**：清洗 → 统计/聚合 → 可视化；每步用工具返回的摘要作答。
4. **长草稿**：需要多轮中间结论时，可用内置 `write_file` 写到虚拟路径（如 `/notes/plan.md`），再用 `read_file` 分页读取，减轻上下文压力。
5. **结论**：中文给出有据结论；若用过 `web_search`，标明来源与时效。

## 与本项目工具的关系

- 数据文件路径以用户消息中的**服务器真实路径**为准（上传接口返回的 path）。
- Skill 正文路径以 **`/skills/...`** 的虚拟路径为准，用 `read_file` 阅读本文件全文时可加大 `limit`。
