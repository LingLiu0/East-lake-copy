# 东湖智库 (East-lake)

> 基于 **llm-wiki** 思想构建：极简、AI 友好、渐进式增长

## 🎯 项目简介

东湖智库是团队知识管理平台，采用纯 Markdown 格式，支持双向链接，便于 AI 理解和检索。

## 📁 目录结构

```
East-lake/
├── index.md           # 知识地图入口
├── concepts/          # 原子化概念
├── projects/          # 项目文档
├── decisions/         # 决策记录（ADR）
├── meetings/          # 会议记录
├── references/        # 外部资源索引
└── templates/         # 文档模板
```

## 🚀 快速开始

### 1. Clone 仓库

```bash
# Clone 到你的 Obsidian vault 目录
git clone https://github.com/huangtao900103/East-lake.git
```

### 2. 在 Obsidian 中打开

1. 打开 Obsidian
2. 选择 "打开文件夹为仓库"
3. 选择 clone 的 `East-lake` 目录

### 3. 安装插件

打开 Obsidian 设置 → 第三方插件 → 浏览并安装：

- **Obsidian Git** - 自动同步
- **Templater** - 模板功能
- **Dataview** - 数据查询

### 4. 配置 Git 自动同步

在 Obsidian Git 插件设置中：
- 自动备份间隔：10 分钟
- 自动拉取间隔：10 分钟
- 启动时自动拉取：开启

## 📝 编辑规范

### 文件命名

- 使用英文短横线：`concept-name.md`
- 原子化：每个文件一个主题

### Front Matter

每个文件必须包含：

```yaml
---
title: 标题
tags: [tag1, tag2]
created: 2025-05-05
updated: 2025-05-05
status: draft | review | stable
---
```

### 双向链接

使用 `[[链接]]` 建立知识网络：

```markdown
相关概念：[[RAG]]、[[Vector-Database]]
应用案例：[[项目A]]
```

## 🔄 协作流程

### 日常编辑

```
编辑 → Obsidian Git 自动 commit → 自动 push
```

### 重要变更

```
创建分支 → 编辑 → 提交 PR → 审核合并
```

## 🤖 AI 功能

### 本地查询

使用 Claude Code CLI 查询知识库：

```bash
cd knowledge-base
claude

> 我们的 RAG 项目用到了哪些技术？
```

### 自动索引

推送到 GitHub 后自动生成：
- 知识图谱（`knowledge-graph.md`）
- 标签索引
- 统计信息

## 📚 相关链接

- [llm-wiki 思想](concepts/llm-wiki.md)
- [决策记录](decisions/)
- [会议记录](meetings/)

## 📄 License

MIT
