# 附件资源目录

本目录用于存放仓库中的附件资源，包括图片、视频、文档等。

---

## 📁 目录结构

```
assets/
├── images/          # 图片资源
│   ├── screenshots/ # 截图
│   ├── diagrams/    # 图表
│   └── logos/       # Logo
├── videos/          # 视频资源
├── documents/       # 文档资源（PDF等）
└── misc/            # 其他附件
```

---

## 📝 使用说明

### 添加附件

1. 将文件放入对应的子目录
2. 在 Markdown 中使用相对路径引用：
   ```markdown
   ![图片说明](assets/images/screenshot.png)
   ```

### 引用示例

- 图片：`![描述](assets/images/xxx.png)`
- 视频：`[视频](assets/videos/demo.mp4)`
- PDF：`[文档](assets/documents/xxx.pdf)`

---

## 🔍 为什么单独存放附件？

- ✅ **结构清晰**：附件与内容分离
- ✅ **易于管理**：统一管理所有资源
- ✅ **便于复用**：多个文章可共享同一资源
- ✅ **优化加载**：可单独优化资源加载

---

**创建时间**：2026-03-01
**维护者**：万智创界
