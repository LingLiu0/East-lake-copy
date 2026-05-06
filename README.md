# East-lake - Karpathy 式 AI 知识库

> 基于 Andrej Karpathy llm-wiki 方法：像编译代码一样编译知识

---

## 核心理念

传统 RAG：每次查询重新检索，无积累
llm-wiki：**知识被编译一次，持续累积，交叉引用已存在**

```
raw/ (原始资料)  →  wiki/ (LLM编译产物)  →  outputs/ (运行时输出)
  就像 src/          就像 build/             就像 logs/
```

---

## 🚀 快速开始

```bash
cd East-lake

# 1. 查看状态
python3 scripts/obsidian.py status

# 2. 放入原始资料到 raw/articles/
#    - 支持 .md, .txt, .pdf

# 3. 编译知识库
python3 scripts/obsidian.py ai compile

# 4. 提问
python3 scripts/obsidian.py ask "你的问题"
```

---

## 📖 三大核心操作

### 1️⃣ Ingest（摄入）

放入原始资料 → 自动编译

```bash
# 添加文件到 raw/articles/
cp my-article.md raw/articles/

# 编译
python3 scripts/obsidian.py ai compile
```

### 2️⃣ Query（查询）

```bash
# 简单提问
python3 scripts/obsidian.py ask "什么是推理工程化？"

# 交互对话
python3 scripts/obsidian.py chat
```

### 3️⃣ Lint（维护）

```bash
# 健康检查
python3 scripts/obsidian.py ai lint
```

---

## 📁 目录结构

```
East-lake/
├── raw/                     # 原始资料（不可变）
│   ├── articles/           # 网页文章
│   ├── papers/             # 论文
│   └── podcasts/           # 播客转录
│
├── wiki/                    # LLM 编译产物
│   ├── indexes/
│   │   ├── index.md        # 内容目录（所有页面）
│   │   └── log.md          # 操作日志
│   ├── concepts/           # 概念条目
│   ├── summaries/          # 摘要
│   └── research/           # 研究文档
│
├── outputs/                 # 运行时输出
│   ├── qa/                 # 问答沉淀
│   └── health/             # 健康报告
│
├── concepts/                # 原子概念
├── research/               # 研究文档
├── decisions/              # 决策记录
├── meetings/               # 会议记录
├── templates/              # 文档模板
├── CLAUDE.md               # LLM 维护规则 ⭐
└── scripts/                # 核心脚本
    └── obsidian.py         # 统一入口
```

---

## ⚡ 常用命令

| 功能 | 命令 |
|------|------|
| 查看状态 | `python3 scripts/obsidian.py status` |
| 编译知识库 | `python3 scripts/obsidian.py ai compile` |
| 健康检查 | `python3 scripts/obsidian.py ai lint` |
| 更新索引 | `python3 scripts/obsidian.py ai index` |
| 提问 | `python3 scripts/obsidian.py ask <问题>` |
| 交互对话 | `python3 scripts/obsidian.py chat` |

---

## 🔧 高级功能

### 直接使用命令

```bash
# 编译（新）
python3 scripts/obsidian.py compile

# 健康检查
python3 scripts/obsidian.py lint

# 更新索引
python3 scripts/obsidian.py index
```

### 启动 API 服务

```bash
cd api
pip install -r requirements.txt
python main.py
```

---

## 📋 工作流程

```
     ┌──────────┐
     │ 原始资料 │
     └────┬─────┘
          │
          ▼
     ┌──────────┐     ┌─────────────────┐
     │ raw/     │────▶│ ai compile      │
     └──────────┘     └────────┬────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ wiki/        │
                        │ - summaries/ │
                        │ - concepts/  │
                        │ - index.md   │
                        │ - log.md     │
                        └──────────────┘
```

---

## 📖 文档

- [CLAUDE.md](CLAUDE.md) - LLM 维护规则（必读）
- [系统运行机制](docs/system-mechanism.md)
- [快速命令参考](docs/quick-commands.md)

---

## ❓ 常见问题

**Q: 为什么不直接用 RAG？**
A: RAG 每次查询重新发现知识。llm-wiki 将知识编译一次，持续累积。

**Q: 和传统笔记有什么区别？**
A: LLM 自动维护摘要、概念、交叉链接。人只需提供资料和提问。

**Q: 需要配置 API 吗？**
A: 本地搜索不需要。AI 深度回答需要：`export ANTHROPIC_API_KEY="your-key"`

---

*基于 Karpathy llm-wiki 方法构建*
*参考：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f*