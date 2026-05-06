git clone https://github.com/huangtao900103/East-lake.git

# 东湖智库 (East-lake)

> 基于 **llm-wiki** 思想构建：极简、AI 友好、渐进式增长

## 🎯 项目简介

东湖智库是团队知识管理平台，采用纯 Markdown 格式，支持双向链接，便于 AI 理解和检索。


## 📁 目录结构与说明

| 目录         | 说明                   |
|--------------|------------------------|
| index.md     | 知识地图入口           |
| concepts/    | 原子化概念，统一模板   |
| projects/    | 项目文档归档           |
| decisions/   | 决策记录（ADR）        |
| meetings/    | 会议纪要               |
| research/    | 研究成果（政策解读、技术分析、专项课题、领导拜访等，AI自动分类分析）|
| references/  | 外部资源索引           |
| templates/   | 文档模板（概念/决策/会议/研究）|


## 🛠️ 推荐工作流与协作规范

1. **内容录入**：所有知识、决策、会议、研究成果等均按模板填写，保持结构统一。
2. **研究成果管理**：将政策解读、技术分析、专项课题、领导拜访材料等放入 research/ 及其子目录，AI可自动分类、分析、生成摘要。
3. **多格式支持**：非Markdown文件（如Word、PPT、PDF）建议放入 research/，可用脚本自动转为Markdown或纯文本，纳入AI处理。
4. **版本管理**：通过 Git 进行版本控制，建议每次修改后提交并推送。
5. **协作建议**：多人协作时建议使用分支和 Pull Request，便于审核和追溯。
6. **目录索引**：每个主目录下建议维护 index.md，自动/手动汇总子内容。


## 🤖 AI 集成与自动化建议

1. **AI自动分类与分析**：所有 research/ 及其子目录下文档，AI可自动识别类别、生成摘要、提炼要点、FAQ等。
2. **AI 检索与问答**：定期将所有文档分块（chunking），生成 embedding，存入向量数据库（如 FAISS、Milvus），结合 RAG 技术实现智能检索与问答。
3. **多格式支持**：通过脚本自动将 Word、PPT、PDF 等文件转为 Markdown 或纯文本，纳入知识库统一管理。
4. **自动摘要与推送**：AI 可定期分析变更，自动生成知识摘要、推送更新通知。
5. **权限与安全**：敏感内容可分区或加密，AI 检索时结合权限系统。

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

### AI 文档自动分析

当 `research/` 目录下文档变更时，AI 自动：
- 识别文档类别（政策解读/技术分析/专项课题/领导拜访等）
- 生成摘要和关键要点
- 提取标签和 FAQ
- 更新 front matter

### 定时知识摘要

每日/每周自动生成知识库变更摘要，保存到 `reports/` 目录

### 外部 API 服务

提供 REST API 供外部系统调用（需部署）：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/search` | POST | 语义搜索 |
| `/graph` | GET | 知识图谱 |
| `/graph/mermaid` | GET | Mermaid 格式图谱 |
| `/stats` | GET | 统计信息 |

部署方式：
```bash
cd api
pip install -r requirements.txt
python main.py
```

## 📚 相关链接

- [llm-wiki 思想](concepts/llm-wiki.md)
- [决策记录](decisions/)
- [会议记录](meetings/)

## 📄 License

MIT
