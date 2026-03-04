---
title: "OpenClaw技能配置（1）- GitHub打通指南"
created: 2026-03-04
tags: [OpenClaw, GitHub, 技能配置, 实战教程]
category: 技术博客
status: 已完成
---

## 开篇：为什么这事儿值得写？

最近一直在玩OpenClaw，刚开始装好的时候觉得：“也就那样吧，很多事儿干不了”。后来想明白了——**OpenClaw再强，光有大脑没有手脚，啥活也干不了。**

OpenClaw是大脑，负责思考；技能就是手脚，负责干活。没配置技能的OpenClaw，就像一个聪明人被绑在椅子上——心里明白得很，但啥也做不了。

GitHub技能是我第一个配置的，也是我最常用的。为什么？因为作为一名开发者，我每天都要和GitHub打交道，但有多少时间是花在重复性操作上的？

**配置GitHub技能后：**
- "查下我的PR状态" → 3秒搞定
- "帮我建个Issue，标题是xxx" → 自然语言就行
- Agent 24/7待命，晚上有人提Issue，早上起来已经看到分析报告了

给OpenClaw装上GitHub这双手脚，立马就从"聪明但啥也干不了"变成了"聪明又能干活的助手"。

这就是我想写这篇教程的原因——GitHub技能真的值得你花3分钟配置一下。
---

## 一、GitHub技能的价值

配置GitHub技能后，你再也不用记那些复杂的命令了——用自然语言就能操作仓库："查下我的PR状态"、"帮我建个Issue说xxx"、"把这篇文章保存到知识库"。更重要的是，Agent 24/7待命，凌晨2点CI构建失败它能立即分析日志并生成修复建议，第二天你上班看到的是完整报告，只需要决定采纳还是自己修改。那些每天重复30分钟的查PR、建Issue、看CI状态，现在5分钟搞定。一句话：**把重复劳动交给AI，把创造力留给自己。**

## 二、生成GitHub Token（3步搞定）

### 第一步：打开GitHub设置页面

访问：https://github.com/settings/tokens

如果你是第一次用，会看到"Personal access tokens"页面。

### 第二步：生成新Token

点击"Generate new token"（或者"Generate new token (classic)"，界面可能略有不同）

### 第三步：设置权限

你会看到一堆权限选项，别慌，只需要勾选这几个：

```
✅ repo           // 完整的仓库权限（必须）
✅ read:org       // 读取组织信息（可选，如果你在组织里）
✅ admin:org_hook // 管理webhook（可选，如果需要事件通知）
```

其他的都不用勾选。够用就好，不要给太多权限。

**重要原则：最小权限原则**
- 只给必需的权限
- 不够用可以再加
- 安全第一

### 第四步：生成并复制

点击底部的"Generate token"按钮。

**⚠️ 重要：Token只会显示一次！**
所以赶紧复制，存到安全的地方。

Token格式类似这样：
```
ghp_1234567890abcdefghijklmnopqrstuvwxyz
```

**保存建议：**
- ✅ 用密码管理器（1Password、Bitwarden）
- ✅ 存到环境变量
- ❌ 不要写在记事本里
- ❌ 不要截图保存

---

## 三、安装GitHub技能

### 安装命令

打开终端，执行：

```bash
npx clawhub@latest install github
```

就这么简单，一条命令搞定。

**解释一下：**
- `npx`：npm的包执行器，不需要全局安装
- `clawhub`：OpenClaw的技能管理工具
- `@latest`：使用最新版本
- `install github`：安装GitHub技能

### 配置Token

安装完成后，OpenClaw会提示你配置Token。

**方法1：对话中直接设置（最简单）**

```
你："我的GitHub token是 ghp_xxxxxxxxxxxxx"
OpenClaw："收到，已保存配置。"
```

**方法2：环境变量（推荐）**

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**方法3：配置文件（持久化）**

```bash
# 编辑OpenClaw配置
vim ~/.openclaw/openclaw.json
```

添加这段：
```json
{
  "github": {
    "token": "ghp_your_token_here"
  }
}
```

保存退出，完成。

### 验证配置

配置好了，怎么知道能不能用呢？

**问Agent一句话就行：**
```
你："你能查看我的GitHub仓库吗？"
```

如果Agent能回答出你的仓库列表，那就说明配置成功了！

**你会看到类似的回复：**
```
Agent："可以，你有以下仓库：
      - yourname/project1
      - yourname/project2
      - yourname/project3"
```

**成功了！就这么简单。**

---

## 四、实战Demo：2个常用场景

### Demo 1：查询PR状态

**场景：** 你正在赶项目，好几个PR在提交测试，但你不知道进展如何。

**传统方式：**
```
1. 打开GitHub
2. 进入每个PR页面
3. 查看状态、评论、CI结果
4. 切换到下一个PR
5. 重复...

时间：5-10分钟
```

**用OpenClaw：**
```
你："我最近的5个PR是什么状态？"
```

**Agent 3秒内回复：**
```
✅ PR #123: 添加用户登录功能 - 审查中
✅ PR #124: 修复导航栏bug - 已合并
❌ PR #125: 优化数据库查询 - CI失败
⏳ PR #126: 更新API文档 - 待审核
📝 PR #127: 重构支付模块 - 草稿
```

**3秒搞定，传统方式要10分钟。**


### Demo 2：自动保存文章到GitHub知识库

**场景：** 你用OpenClaw写了一篇技术文章，想自动保存到GitHub知识库仓库。

**传统方式：**
```
1. 复制文章内容
2. 打开GitHub
3. 进入仓库
4. 创建新文件
5. 粘贴内容
6. 填写提交信息
7. 提交

时间：3-5分钟
```

**用OpenClaw：**
```
你：“把这篇文章保存到我的
      knowledge-base仓库，
      文件名是OpenClaw-GitHub指南.md，
      分类放到技术文档/文件夹下”
```

**Agent自动执行：**
```
✅ 正在保存到GitHub...

📝 文件信息：
   仓库：yourname/knowledge-base
   路径：技术文档/OpenClaw-GitHub指南.md
   操作：创建新文件

📦 提交信息：
   Commit: "添加：OpenClaw GitHub配置指南"
   分支：main

✅ 成功推送到远程！

🔗 查看：https://github.com/yourname/knowledge-base/blob/main/技术文档/OpenClaw-GitHub指南.md
```

**30秒 vs 5分钟，还能自动规范化提交信息。**

---

## 五、总结

让我用几句话总结一下：

**1. GitHub Token + OpenClaw = 3分钟配置**
**2. 用自然语言操作，不用记命令**
**3. 24/7待命，你睡觉它工作**
**4. 从简单开始，够用就好**

**最重要的是：**

> **把重复劳动交给AI，把创造力留给自己。**

你是一名开发者，你的时间应该花在：
- 💡 设计架构
- 💡 解决难题
- 💡 创造价值

而不是：
- ❌ 手动查PR状态
- ❌ 重复创建Issue
- ❌ 刷新CI页面

**让AI做这些重复的事，你来做更有价值的事。**

---

🎉 **恭喜！你已经学会了配置OpenClaw的GitHub技能！**

现在就开始试试吧：3分钟配置，终身受益。

---

💡 **万智创界 - AI技术实战派布道者**

> **AI不是魔法，是工程。拒绝炫技，只讲落地实战。**

关注我，你将获得：
- ✅ AI前沿动态与趋势
- ✅ 真实项目案例 + 代码
- ✅ 工程化实践与避坑

让AI真正为业务创造价值，从理论到落地，我们一起前行！
