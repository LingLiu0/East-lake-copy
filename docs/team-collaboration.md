gh api -X PUT repos/huangtao900103/East-lake/subscription -f subscribed=true
gh api -X PUT repos/huangtao900103/Satellite-HB/subscription -f subscribed=true

# 团队协作指南

本文档说明团队成员如何高效协作，请每位成员仔细阅读。

---

## 一、项目概览

| 项目 | 名称 | 用途 | 地址 |
|------|------|------|------|
| 知识库 | 东湖智库 (East-lake) | 团队知识管理、文档沉淀 | [GitHub](https://github.com/huangtao900103/East-lake) |
| 任务管理 | 卫星互联网 (Satellite-HB) | 任务跟踪、进度管理 | [GitHub](https://github.com/huangtao900103/Satellite-HB) |
| 任务看板 | - | 可视化任务状态 | [Projects](https://github.com/users/huangtao900103/projects/3) |

---

## 二、加入团队

### 步骤 1：获取访问权限

联系管理员获取 GitHub 仓库访问权限（Write 权限）。

### 步骤 2：关注仓库

```bash
# 关注仓库，获取更新通知
gh api -X PUT repos/huangtao900103/East-lake/subscription -f subscribed=true
gh api -X PUT repos/huangtao900103/Satellite-HB/subscription -f subscribed=true
```

### 步骤 3：配置通知

GitHub → Settings → Notifications：
- ☑ Email
- ☑ Web
- ☑ Watching

---

## 三、知识库协作

### 1. 内容录入与模板
- 所有内容均按 templates/ 目录下模板填写，保持结构统一。
- 每个主目录建议维护 index.md，自动/手动汇总子内容。

### 2. 版本管理与协作
- 通过 Git 进行版本管理，建议每次修改后提交并推送。
- 多人协作时建议使用分支和 Pull Request，便于审核和追溯。

### 3. AI协作与自动化建议
- 定期将 Markdown 文档分块（chunking），生成 embedding，存入向量数据库，结合 RAG 技术实现智能检索与问答。
- 可开发脚本自动将 Word、PPT、PDF 等文件转为 Markdown 或纯文本，纳入知识库统一管理。
- AI 可定期分析变更，自动生成知识摘要、推送更新通知。
- 支持 embedding 检索、语义问答、自动化知识地图生成等。

### 4. 权限与安全
- 敏感内容可分区或加密，AI 检索时结合权限系统。

> 知识库采用 Git 分支管理模式，详见 [Git 工作流指南](git-workflow.md)

### 角色分工

| 角色 | 分支权限 | 职责 |
|------|----------|------|
| **Maintainer** | main 直接写入 | 审核合并、维护结构 |
| **Contributor** | 分支 + PR | 创建分支、提交内容 |

### 初始化

```bash
# 1. Clone 仓库
git clone https://github.com/huangtao900103/East-lake.git
cd East-lake

# 2. 配置 Git 信息
git config user.name "你的名字"
git config user.email "你的邮箱"
```

### 安装 Obsidian

1. 下载：https://obsidian.md/download
2. 打开 Obsidian → 「打开文件夹作为仓库」→ 选择 `East-lake` 目录
3. 设置 → 第三方插件 → 关闭安全模式
4. 安装 **Obsidian Git** 插件并启用
5. 配置：自动备份间隔 10 分钟，启动时自动拉取

### 日常编辑规范

| 规则 | 说明 |
|------|------|
| 文件命名 | 英文短横线，如 `feature-design.md` |
| 每日同步 | 上班先 pull，下班确认 push |
| 双向链接 | 使用 `[[文件名]]` 关联其他文档 |
| Front Matter | 必须包含 title, tags, created |

### 编辑流程

**日常笔记**（自动同步）：
```
编辑文档 → Obsidian Git 自动 commit → 自动 push
```

**重要文档**（PR 审核）：
```bash
# 创建分支
git checkout -b feature/new-doc

# 编辑完成后提交
git add .
git commit -m "docs: 添加新文档"
git push -u origin feature/new-doc

# 在 GitHub 创建 PR，等待审核
gh pr create --title "docs: 添加新文档" --body "文档说明"
```

### 冲突处理

```bash
# 拉取时发现冲突
git pull

# 查看冲突文件
git status

# 打开冲突文件，选择保留内容
# <<<<<<< HEAD
# 你的修改
# =======
# 别人的修改
# >>>>>>> origin/master

# 解决后提交
git add .
git commit -m "resolve: 解决文档冲突"
git push
```

---

## 四、任务管理协作

### 创建任务

```bash
# 方式 1：命令行
gh issue create --repo huangtao900103/Satellite-HB \
  --title "[Feature] 功能描述" \
  --body "## 背景
为什么需要这个功能

## 目标
- 目标 1
- 目标 2

## 截止
2025-XX-XX"

# 方式 2：网页
# 访问 https://github.com/huangtao900103/Satellite-HB/issues/new/choose
# 选择模板填写
```

### 任务标题规范

| 前缀 | 类型 | 示例 |
|------|------|------|
| `[Bug]` | 问题修复 | `[Bug] 登录页面无法加载` |
| `[Feature]` | 新功能 | `[Feature] 用户个人主页` |
| `[Task]` | 常规任务 | `[Task] 重构用户模块` |
| `[Doc]` | 文档相关 | `[Doc] 更新 API 文档` |

### AI 自动分类

创建 Issue 后，AI 自动：
- 分析类型（bug/feature/task）
- 评估优先级（P0-P3）
- 添加标签
- 生成摘要评论

### 任务状态流转

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Backlog → Todo → In Progress → Review → Done              │
│    待定      待开始     进行中       审核     完成           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 状态更新命令

```bash
# 开始工作
gh issue edit <编号> --repo huangtao900103/Satellite-HB \
  --add-assignee @me \
  --add-label "status:in-progress"

# 遇到阻塞
gh issue edit <编号> --add-label "status:blocked"

# 提交审核
gh issue edit <编号> --add-label "status:review"

# 完成任务
gh issue close <编号> --repo huangtao900103/Satellite-HB
```

### 任务分配

```bash
# 分配给指定成员
gh issue edit <编号> --repo huangtao900103/Satellite-HB \
  --add-assignee 用户名

# 查看我的任务
gh issue list --repo huangtao900103/Satellite-HB \
  --assignee @me --state open
```

---

## 五、标签体系

### 类型标签

| 标签 | 用途 |
|------|------|
| `bug` | Bug 报告 |
| `feature` | 功能请求 |
| `task` | 常规任务 |
| `documentation` | 文档相关 |
| `question` | 问题咨询 |

### 优先级标签

| 标签 | 含义 | 时限 |
|------|------|------|
| `P0-紧急` | 阻塞其他工作 | 立即处理 |
| `P1-高` | 重要任务 | 本周完成 |
| `P2-中` | 普通任务 | 两周内 |
| `P3-低` | 低优先级 | 有时间再做 |

### 状态标签

| 标签 | 含义 |
|------|------|
| `needs-triage` | 待分类 |
| `status:in-progress` | 进行中 |
| `status:blocked` | 阻塞中 |
| `status:review` | 待审核 |

---

## 六、自动化功能

| 功能 | 触发条件 | 说明 |
|------|----------|------|
| AI Issue 分类 | 创建 Issue | 自动分析类型、优先级、打标签 |
| 周报生成 | 每周一 9:00 | 汇总进展，生成报告到 `reports/` |
| 过期提醒 | 每天 10:00 | 提醒 >7天未更新的进行中任务 |
| PR 描述生成 | 创建 PR | 自动生成描述模板 |
| 知识图谱 | Push 到 main | 自动更新链接关系和统计 |

---

## 七、协作场景示例

### 场景 1：新功能开发

```bash
# 1. 创建任务
gh issue create --repo huangtao900103/Satellite-HB \
  --title "[Feature] 用户搜索功能" \
  --body "## 背景
用户需要快速查找内容

## 目标
- 关键词搜索
- 结果高亮
- 搜索历史

## 截止
2025-05-20"

# 2. AI 自动标记 feature, P2-中

# 3. 领取任务
gh issue edit <编号> --add-assignee @me --add-label "status:in-progress"

# 4. 开发过程中记录技术方案到知识库
# 在东湖智库创建 decisions/XXX-search-feature.md

# 5. 完成开发
gh pr create --repo huangtao900103/Satellite-HB \
  --title "feat: 用户搜索功能" \
  --body "实现 #<编号>"

# 6. Review 通过后合并，关闭任务
gh issue close <编号>
```

### 场景 2：Bug 修复

```bash
# 1. 报告 Bug
gh issue create --repo huangtao900103/Satellite-HB \
  --title "[Bug] 支付金额计算错误" \
  --body "## 复现步骤
1. 添加商品
2. 使用优惠券
3. 结算金额错误

## 期望
100 - 20 = 80

## 实际
显示 120"

# 2. AI 自动标记 bug, P0-紧急

# 3. 开始修复
gh issue edit <编号> --add-assignee @me --add-label "status:in-progress"

# 4. 修复完成后
gh issue close <编号> --comment "已修复：优惠券计算逻辑错误"
```

### 场景 3：知识沉淀

```bash
# 1. 在东湖智库创建文档
# concepts/rag-implementation.md

---
title: RAG 实现方案
tags: [ai, rag, architecture]
created: 2026-05-05
---

# RAG 实现方案

## 背景
...

## 技术选型
...

## 相关文档
- [[LLM 基础]]
- [[向量数据库]]

# 2. Obsidian Git 自动同步到 GitHub
```

---

## 八、常用命令速查

### 知识库操作

```bash
# 同步最新内容
cd ~/East-lake && git pull

# 手动提交
git add .
git commit -m "docs: 更新文档"
git push

# 查看状态
git status
```

### 任务操作

```bash
# 创建任务
gh issue create --repo huangtao900103/Satellite-HB --title "标题" --body "内容"

# 查看任务列表
gh issue list --repo huangtao900103/Satellite-HB --state open

# 查看我的任务
gh issue list --repo huangtao900103/Satellite-HB --assignee @me

# 更新状态
gh issue edit <编号> --repo huangtao900103/Satellite-HB --add-label "status:in-progress"

# 添加评论
gh issue comment <编号> --repo huangtao900103/Satellite-HB --body "进展说明"

# 关闭任务
gh issue close <编号> --repo huangtao900103/Satellite-HB
```

---

## 九、新成员检查清单

### 第一天完成

- [ ] 获取 GitHub 仓库访问权限
- [ ] 关注两个仓库（Watch）
- [ ] 设置 GitHub 通知
- [ ] Clone East-lake 仓库
- [ ] 安装 Obsidian
- [ ] 安装 Obsidian Git 插件
- [ ] 安装 gh CLI 工具

### 第一周完成

- [ ] 阅读所有文档
- [ ] 创建一个测试 Issue
- [ ] 在知识库添加一篇笔记
- [ ] 熟悉任务看板
- [ ] 了解团队当前任务

---

## 十、获取帮助

- **知识库**：https://github.com/huangtao900103/East-lake
- **任务管理**：https://github.com/huangtao900103/Satellite-HB
- **任务看板**：https://github.com/users/huangtao900103/projects/3
- **快速入门**：[docs/quick-start.md](quick-start.md)

---

*最后更新：2026-05-05*
