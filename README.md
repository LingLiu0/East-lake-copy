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

# 2. 放入原始资料
#    - 方式一：Web Clipper 插件 → raw/clippings/（推荐）
#    - 方式二：手动复制文件 → raw/articles/

# 3. 编译知识库
python3 scripts/obsidian.py ai compile

# 4. 提问
python3 scripts/obsidian.py ask "你的问题"
```

---

## 🤖 使用 Claude for Obsidian 插件（推荐）

推荐使用 [Claude for Obsidian](https://github.com/nickmilo/claudian) 插件进行问答，体验更流畅。

### 安装步骤

1. **安装插件**
   - 打开 Obsidian → 设置 → 社区插件
   - 关闭安全模式（如果需要）
   - 搜索 "Claudian" 或 "Claude for Obsidian" 并安装
   
   或者手动安装：
   ```bash
   # 复制插件到 Obsidian 插件目录
   cp -r claudian ~/.obsidian/plugins/
   ```

2. **配置 API Key**
   - 插件设置中添加 `ANTHROPIC_API_KEY`
   - 或在终端设置环境变量：
     ```bash
     export ANTHROPIC_API_KEY="your-api-key"
     ```

3. **配置知识库路径**
   - 在插件设置中将 `vault_path` 指向 East-lake 目录
   - 或设置环境变量：
     ```bash
     export EAST_LAKE_PATH="/path/to/East-lake"
     ```

### 使用方式

- **快捷键提问**：`Ctrl+Shift+A`（可自定义）
- **命令面板**：`Ctrl+P` → 输入 "Ask AI" 或 "AI Chat"
- **侧边栏对话**：打开 Claude 面板进行对话

### 在对话中使用知识库

在提问时可以使用以下指令：

```
@wiki 什么是推理工程化？
@index 查找关于 RAG 的内容
@recent 最近添加了哪些概念？
```

或者直接在问题中引用：
- `[[wiki/concepts/概念名]]` - 引用特定概念
- `[[wiki/summaries/摘要名]]` - 引用特定摘要

详细入门指南：[docs/quick-start.md](docs/quick-start.md)

---

## 📖 三大核心操作

### 1️⃣ Ingest（摄入）

放入原始资料 → 自动编译

```bash
# Web Clipper 保存到 raw/clippings/
# 或手动复制到 raw/articles/

# 编译
python3 scripts/obsidian.py ai compile
```

### 2️⃣ Query（查询）

```bash
# 简单提问
python3 scripts/obsidian.py ask "什么是推理工程化？"
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
│   ├── clippings/           # Web Clipper 收藏（推荐）
│   └── articles/            # 文章/文档（支持多格式）
│
├── wiki/                    # LLM 编译产物
│   ├── indexes/
│   │   ├── index.md         # 内容目录
│   │   ├── log.md           # 操作日志
│   │   └── knowledge-graph.md # 知识图谱
│   ├── concepts/            # 概念条目
│   └── summaries/           # 摘要
│
├── outputs/                 # 运行时输出
│   ├── qa/                  # 问答沉淀
│   └── health/              # 健康报告
│
├── scripts/                 # 核心脚本
│   ├── obsidian.py          # 统一入口
│   ├── generate_graph.py    # 知识图谱
│   └── diagnose.py          # 诊断
│
├── .github/workflows/       # 自动化
│   ├── auto-compile.yml     # 自动编译
│   └── knowledge-graph.yml  # 知识图谱
│
├── docs/                    # 文档
│   ├── quick-start.md       # 快速入门
│   ├── quick-commands.md    # 命令参考
│   └── system-mechanism.md  # 运行机制
│
├── CLAUDE.md                # LLM 维护规则 ⭐
└── README.md                # 本文件
```

## 📄 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| Markdown | `.md` | 完整解析，支持 front matter |
| 文本 | `.txt` | 纯文本处理 |
| PDF | `.pdf` | 文本提取 |
| Word | `.docx` | 文档解析 |
| PPT | `.ppt`, `.pptx` | 演示文稿解析 |
| 网页 | `.html`, `.htm` | HTML 解析 |

---

## ⚡ 常用命令

| 功能 | 命令 |
|------|------|
| 查看状态 | `python3 scripts/obsidian.py status` |
| 编译知识库 | `python3 scripts/obsidian.py ai compile` |
| 生成知识图谱 | `python3 scripts/obsidian.py ai graph` |
| 健康检查 | `python3 scripts/obsidian.py ai lint` |
| 提问 | `python3 scripts/obsidian.py ask <问题>` |

---

## 📋 工作流程

```
浏览器发现好文章
      ↓
Web Clipper → raw/clippings/
      ↓
Git Push → GitHub Actions 自动编译
      ↓
wiki/ 生成：摘要 + 概念 + 知识图谱
      ↓
团队成员 Git Pull
      ↓
提问 / Obsidian 浏览
```

---

## 📖 文档

- [快速入门](docs/quick-start.md) - 5 分钟上手
- [命令参考](docs/quick-commands.md) - 常用命令
- [运行机制](docs/system-mechanism.md) - 系统架构详解
- [CLAUDE.md](CLAUDE.md) - LLM 维护规则

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