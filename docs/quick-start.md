# 团队快速入门指南

## 🚀 5 分钟上手

### 一、知识库配置

#### 1. Clone 仓库

```bash
# Clone 到本地
git clone https://github.com/huangtao900103/East-lake.git
cd East-lake
```

#### 2. 安装 Obsidian

下载地址：https://obsidian.md/download

#### 3. 打开知识库

1. 启动 Obsidian
2. 点击「打开文件夹作为仓库」
3. 选择 `knowledge-base` 目录

#### 4. 安装插件

设置 → 第三方插件 → 关闭安全模式 → 浏览：

| 插件 | 用途 |
|------|------|
| **Obsidian Git** | 自动同步（必装） |
| Templater | 模板插入 |
| Dataview | 数据查询 |

#### 5. 配置 Obsidian Git

```
设置 → Obsidian Git：
- 自动备份间隔：10 分钟
- 自动拉取间隔：10 分钟
- 启动时自动拉取：✓
```

---

### 二、任务管理使用

#### 1. 创建任务

访问 https://github.com/huangtao900103/team-tasks/issues/new/choose

选择模板：
- 🐛 Bug 报告
- ✨ 功能请求
- 📋 任务
- ❓ 问题咨询

#### 2. AI 自动分类

创建 Issue 后，AI 自动：
- 分析类型（bug/feature/task）
- 评估优先级（P0-P3）
- 添加标签
- 生成摘要

#### 3. 查看任务看板

访问 https://github.com/users/huangtao900103/projects/3

拖拽卡片更改状态：
```
Todo → In Progress → Done
```

#### 4. 更新任务状态

```bash
# 开始工作
gh issue edit <编号> --add-label "status:in-progress"

# 标记阻塞
gh issue edit <编号> --add-label "status:blocked"

# 完成任务
gh issue close <编号>
```

---

### 三、常用命令速查

#### Git 操作

```bash
# 同步知识库
cd ~/knowledge-base
git pull

# 手动提交
git add .
git commit -m "更新文档"
git push
```

#### Issue 操作

```bash
# 创建任务
gh issue create --title "任务标题" --body "任务描述"

# 查看任务列表
gh issue list --state open

# 分配任务
gh issue edit <编号> --add-assignee @me

# 添加标签
gh issue edit <编号> --add-label "P1-高"

# 关闭任务
gh issue close <编号>
```

---

### 四、标签说明

#### 类型标签

| 标签 | 颜色 | 用途 |
|------|------|------|
| `bug` | 🔴 | Bug 报告 |
| `feature` | 🔵 | 功能请求 |
| `task` | 🟢 | 常规任务 |
| `question` | 🟣 | 问题咨询 |

#### 优先级标签

| 标签 | 含义 | 时限 |
|------|------|------|
| `P0-紧急` | 阻塞其他工作 | 立即处理 |
| `P1-高` | 重要任务 | 本周完成 |
| `P2-中` | 普通任务 | 两周内 |
| `P3-低` | 低优先级 | 有时间再做 |

#### 状态标签

| 标签 | 含义 |
|------|------|
| `needs-triage` | 待分类 |
| `status:in-progress` | 进行中 |
| `status:blocked` | 阻塞中 |
| `status:review` | 待审核 |

---

### 五、自动化功能

| 功能 | 触发条件 | 说明 |
|------|----------|------|
| AI Issue 分类 | 创建 Issue | 自动打标签、分析优先级 |
| 周报生成 | 每周一 9:00 | 汇总本周进展 |
| 过期提醒 | 每天 10:00 | 提醒 >7天未更新任务 |
| PR 描述生成 | 创建 PR | 自动生成描述模板 |

---

### 六、获取帮助

- 知识库：https://github.com/huangtao900103/knowledge-base
- 任务管理：https://github.com/huangtao900103/team-tasks
- 看板：https://github.com/users/huangtao900103/projects/3

---

## 📋 检查清单

新成员入职请完成：

- [ ] Clone 知识库仓库
- [ ] 安装 Obsidian 并打开知识库
- [ ] 安装 Obsidian Git 插件
- [ ] 配置自动同步
- [ ] 访问任务看板
- [ ] 创建一个测试 Issue

---

*最后更新：2025-05-05*
