# CLAUDE.md - East-lake Wiki 维护规则

> 本文件定义了 East-lake 知识库的维护规范，供 LLM Agent 使用

## 项目概述

**East-lake** - 基于 Karpathy llm-wiki 方法的 AI 驱动知识管理系统

## 目录结构

```
.
├── .claude/                 # Claude Code 配置
├── .claudian/               # Claudian 插件配置
├── .github/                 # GitHub Actions 工作流
├── .obsidian/               # Obsidian 配置
│
├── api/                     # API 服务
│
├── docs/                    # 文档
│
├── raw/                     # 原始资料（不可变）
│   ├── clippings/           # Web Clipper 收藏（推荐）
│   └── articles/            # 网页文章/文档
│
├── templates/               # AI生成物模板（人工维护）
│
├── wiki/                    # LLM 编译产物（由 LLM 维护）
│   ├── indexes/             # 索引文件
│   │   ├── index.md         # 内容目录
│   │   ├── log.md           # 操作日志
│   │   └── knowledge-graph.md # 知识图谱
│   ├── concepts/            # 概念条目
│   └── summaries/           # 摘要
│
└── scripts/                 # 核心脚本
    ├── obsidian.py          # 统一入口
    └── fetch_policy.py      # 政策简报获取
```

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| Markdown | `.md` | 完整解析，支持 front matter |
| 文本 | `.txt` | 纯文本处理 |
| PDF | `.pdf` | 文本提取 |
| Word | `.docx` | 文档解析 |
| PPT | `.ppt`, `.pptx` | 演示文稿解析 |
| 网页 | `.html`, `.htm` | HTML 解析 |

## 核心原则

### 1. 原始资料不动原则
- `raw/` 目录下的文件是**不可变的**
- LLM 只读取，不修改
- 这是知识的唯一真实来源

### 2. Wiki 编译原则
- `wiki/` 目录由 LLM 完全维护
- 每次摄入新来源，LLM 必须：
  - 生成摘要 → `wiki/summaries/`
  - 提取概念 → `wiki/concepts/`
  - 更新索引 → `wiki/indexes/index.md`
  - 添加日志 → `wiki/indexes/log.md`
  - 更新知识图谱 → `wiki/indexes/knowledge-graph.md`

### 3. 交叉链接原则
- 知识条目之间使用 `[[链接]]` 建立双向链接
- 新概念自动关联已有概念
- 矛盾点需要标注

## 操作规范

### Ingest（摄入）

当添加新来源到 `raw/`：

1. 读取来源内容
2. 生成摘要（200字以内）
3. 提取关键概念（3-5个）
4. 更新 `index.md`
5. 更新 `knowledge-graph.md`
6. 在 `log.md` 记录

### Query（查询）

回答问题时：
1. 先读 `index.md` 定位相关页面
2. 读取相关页面内容
3. 合成答案，标注来源
4. **重要**：将高质量答案存回 wiki

### Lint（维护）

定期检查 wiki 健康度：
```bash
python3 scripts/obsidian.py ai lint
```

检查内容：
- 孤立页面（无 inbound 链接）
- 过时内容
- 缺失链接
- 未编译的原始文件

## 常用命令

```bash
# 查看状态
python3 scripts/obsidian.py status

# 编译知识库
python3 scripts/obsidian.py ai compile

# 生成知识图谱
python3 scripts/obsidian.py ai graph

# 健康检查
python3 scripts/obsidian.py ai lint

# 提问
python3 scripts/obsidian.py ask "问题"

# 获取政策简报
python3 scripts/fetch_policy.py               # 获取当天
python3 scripts/fetch_policy.py --date 2026-05-07  # 获取指定日期
python3 scripts/fetch_policy.py --daily       # 每日自动
```

## Obsidian 配置

### 已安装插件

项目已配置以下 Obsidian 社区插件：

| 插件 | 用途 |
|------|------|
| [obsidian-git](https://github.com/denolehov/obsidian-git) | 自动备份到 Git 仓库 |
| [Templater](https://github.com/SilentVoid13/Templater) | 高级模板功能 |
| [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | 数据查询和索引 |
| [BRAT](https://github.com/TfTHacker/obsidian42-brat) | 插件测试 |
| [Claudian](https://github.com/YishenTu/claudian) | AI 问答集成 |

### Claudian 安装

推荐通过 BRAT 插件安装 Claudian：

1. **安装 BRAT**：Obsidian → 设置 → 社区插件 → 搜索 "BRAT" 安装
2. **安装 Claudian**：
   - 命令面板 → "BRAT: Add a beta plugin"
   - 输入 `https://github.com/YishenTu/claudian`
3. **配置 API Key**：设置 `ANTHROPIC_API_KEY` 环境变量

### 基础设置

```json
{
  "attachmentFolderPath": "attachments",
  "newFileLocation": "current",
  "defaultViewMode": "preview",
  "useMarkdownLinks": false,
  "showUnsupportedFiles": true,
  "promptDelete": false
}
```

## 页面格式规范

### 摘要格式 (summaries/)

```markdown
---
title: 标题
source: 来源文件/URL
date: 2026-05-07
tags: [tag1, tag2]
---

# 标题

## 摘要
（AI 补充中）

## 关键要点
- 要点1
- 要点2
- 要点3

## 相关概念
[[wiki/concepts/概念1]], [[wiki/concepts/概念2]]
```

### 概念格式 (concepts/)

```markdown
---
title: 概念名称
type: concept
created: 2026-05-07
---

# 概念名称

## 定义
概念的清晰定义

## 来源
- [[wiki/summaries/摘要1]]

## 关联
- [[wiki/concepts/相关概念1]]
```

## 搜索优先级

对于知识库查询（~100来源，~数百页面）：
1. 首先读取 `index.md` 定位
2. 无需向量检索
3. 简单文件搜索足够

---
*本文件由 LLM 和人类共同维护*