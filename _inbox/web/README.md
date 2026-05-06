# 🌐 网页收集箱

> **团队网页剪藏入口** - 把有用的链接丢到这里

---

## 🎯 使用方法

### 方式一：命令行添加

```bash
# 添加单个网页
python scripts/web_collector.py add "https://article.example.com"

# 添加并指定标签
python scripts/web_collector.py add "https://article.example.com" --tags tech,ai
```

### 方式二：查看和处理

```bash
# 查看收集箱
python scripts/web_collector.py inbox

# 处理收集箱（自动抓取内容）
python scripts/web_collector.py process
```

---

## 🔄 自动处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                   网页剪藏流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ 添加 URL                                                │
│     • 命令行: add <url>                                     │
│     • 或直接把 URL 写入 _inbox/web/urls.txt                 │
│                                                             │
│       ↓                                                    │
│                                                             │
│  2️⃣ 自动抓取                                                │
│     • 标题、描述、作者                                      │
│     • 页面主要内容                                          │
│     • 站点信息                                              │
│                                                             │
│       ↓                                                    │
│                                                             │
│  3️⃣ 智能分类                                                │
│     • research/tech      (技术)                            │
│     • research/ai        (AI)                              │
│     • research/product   (产品)                            │
│     • research/business  (商业)                            │
│     • research/misc      (其他)                            │
│                                                             │
│       ↓                                                    │
│                                                             │
│  4️⃣ 生成笔记                                                │
│     • Front Matter 元数据                                  │
│     • 内容摘要                                              │
│     • 原文链接                                              │
│     • 后续操作提示                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 支持的网站类型

| 类型 | 示例关键词 | 分类 |
|------|-----------|------|
| 技术文章 | tech, programming, dev | research/tech |
| AI/机器学习 | ai, llm, gpt, ml | research/ai |
| 产品设计 | product, ux, ui, design | research/product |
| 商业运营 | business, 运营, 增长 | research/business |
| 新闻资讯 | news, 新闻 | research/news |

---

## 📝 生成笔记示例

```markdown
---
title: 理解 Transformer 架构
tags: [web-collector, ai, 2025-05]
created: 2025-05-06
source: https://blog.example.com/transformer
site: Example Blog
category: research/ai
status: collected
---

# 理解 Transformer 架构

> [!info] 网页剪藏
> - 来源: Example Blog
> - 日期: 2025-05-06
> - 摘要: 本文介绍...

## 🔗 原文链接

🔗 [理解 Transformer 架构](https://blog.example.com/transformer)

## 📝 内容摘要

Transformer 架构最初由 Google 在 2017 年提出...

... (自动提取的正文内容) ...

---

## 💡 后续操作

- [ ] 阅读完整内容
- [ ] 提取关键要点
- [ ] 添加相关概念链接
- [ ] 写上自己的思考
```

---

## ⚡ 快捷命令

```bash
# 添加网页
python scripts/web_collector.py add "URL"

# 查看收集箱
python scripts/web_collector.py inbox

# 处理收集箱
python scripts/web_collector.py process
```

---

## 📦 依赖安装

```bash
pip install requests beautifulsoup4
```