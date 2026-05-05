---
title: LLM-Wiki 知识管理方法
tags: [concept, knowledge-management, ai]
created: 2025-05-05
updated: 2025-05-05
status: stable
---

# LLM-Wiki 知识管理方法

## 定义

由 Andrej Karpathy 提出的极简知识管理方法，核心理念是构建 **AI 原生** 的知识库。

## 为什么重要

传统知识库（Confluence、Notion 等）存在以下问题：
- 格式复杂，AI 难以解析
- 依赖特定平台，迁移困难
- 结构僵化，难以自然生长

llm-wiki 解决这些问题：
- 纯 Markdown，AI 直接理解
- Git 版本控制，历史可追溯
- 双向链接，知识自然关联

## 核心原则

### 1. 纯文本优先

所有内容都是 Markdown 文件，无复杂数据库。

```
knowledge-base/
├── index.md
├── concepts/
├── projects/
└── decisions/
```

### 2. 双向链接

使用 `[[链接]]` 语法建立知识网络：

```markdown
相关概念：[[RAG]]、[[Vector-Database]]
应用案例：[[项目A]]
```

### 3. 渐进式增长

从小做起，按需扩展：
- 不预设复杂分类
- 让结构自然演化
- 定期整理和重构

### 4. AI 原生

内容结构化，便于 LLM 理解：
- Front Matter 元数据
- 清晰的标题层级
- 明确的链接关系

## 实践案例

本知识库即采用 llm-wiki 方法构建：

- [[index]] - 知识地图入口
- [[concepts/]] - 原子化概念
- [[decisions/]] - 决策记录

## 相关概念

- [[双向链接]]
- [[知识图谱]]

## 外部资源

- [Karpathy's llm-wiki](https://github.com/karpathy/llm.c/discussions/758)
- [Obsidian 官方文档](https://help.obsidian.md/)

---

## 更新日志

- 2025-05-05: 初始创建
