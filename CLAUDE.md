# CLAUDE.md - East-lake Wiki 维护规则

> 本文件定义了 East-lake 知识库的维护规范，供 LLM Agent 使用

## 项目概述

**East-lake** - 基于 Karpathy llm-wiki 方法的 AI 驱动知识管理系统

## 目录结构

```
.
├── raw/                    # 原始资料（不可变）
│   ├── articles/          # 网页文章
│   ├── papers/            # 论文
│   ├── podcasts/          # 播客转录
│   └── ...
│
├── wiki/                   # LLM 编译产物（由 LLM 维护）
│   ├── indexes/           # 索引文件
│   │   ├── index.md       # 内容目录（所有页面）
│   │   └── log.md         # 操作日志
│   ├── concepts/          # 概念条目
│   ├── summaries/         # 摘要
│   └── research/          # 研究文档
│
├── outputs/               # 运行时输出
│   ├── qa/               # 问答沉淀
│   └── health/           # 健康报告
│
├── concepts/              # 原子概念（原 llm-wiki）
├── research/              # 研究文档
├── decisions/             # 决策记录
├── meetings/              # 会议记录
└── templates/             # 文档模板
```

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
5. 在 `log.md` 记录

### Query（查询）

回答问题时：
1. 先读 `index.md` 定位相关页面
2. 读取相关页面内容
3. 合成答案，标注来源
4. **重要**：将高质量答案存回 wiki

### Lint（维护）

定期检查 wiki 健康度：
- 孤立页面（无 inbound 链接）
- 过时内容
- 缺失链接
- 矛盾信息

## 页面格式规范

### 摘要格式 (summaries/)

```markdown
---
title: 标题
source: 来源文件
date: 2026-05-06
tags: [tag1, tag2]
---

# 标题

## 摘要
（200字以内）

## 关键要点
- 要点1
- 要点2
- 要点3

## 相关概念
[[概念1]], [[概念2]]
```

### 概念格式 (concepts/)

```markdown
---
title: 概念名称
type: concept
created: 2026-05-06
related: [[相关概念]]
---

# 概念名称

## 定义
概念的清晰定义

## 来源
- [[摘要1]]
- [[摘要2]]

## 关联
- [[相关概念1]]
- [[相关概念2]]
```

## 日志格式 (log.md)

```markdown
## [2026-05-06] ingest | 文章标题
- 动作：摄入新文章
- 来源：raw/articles/xxx.md
- 提取概念：概念A, 概念B
- 更新页面：5个

## [2026-05-06] query | 问题摘要
- 动作：回答问题
- 涉及页面：概念A, 概念B
- 答案存至：outputs/qa/xxx.md
```

## 命名规范

- 文件名：使用英文短横线 `concept-name.md`
- 概念名：中文或英文，保持简洁
- 标签：使用英文小写

## 搜索优先级

对于知识库查询（~100来源，~数百页面）：
1. 首先读取 `index.md` 定位
2. 无需向量检索
3. 简单文件搜索足够

---
*本文件由 LLM 和人类共同维护*