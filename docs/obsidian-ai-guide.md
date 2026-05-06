# Obsidian AI 问答与自动演化指南

本文档说明如何在 Obsidian 中实现 Karpathy llm-wiki 的 AI 自动问答和知识库自动演化。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Obsidian 本地 AI 演化系统                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Obsidian   │───▶│ obsidian_qa │───▶│ auto_evolve │                     │
│  │  本地编辑   │    │   (问答)     │    │   (演化)     │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│         │                  │                   │                            │
│         │            ┌─────┴─────┐       ┌────┴────┐                       │
│         │            │           │       │         │                       │
│         │            ▼           ▼       ▼         ▼                       │
│         │      ┌─────────┐  ┌────────┐ ┌───────┐ ┌──────┐                 │
│         │      │ 本地搜索 │  │AI 回答 │ │更新索引│ │添加链接│                │
│         │      └─────────┘  └────────┘ └───────┘ └──────┘                 │
│         │                                                           │
│         │         ┌─────────────────────────────────┐                  │
│         └────────▶│      Claude API (可选)          │                  │
│                   │   提供深度语义理解和生成能力    │                  │
│                   └─────────────────────────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 问答功能

```bash
# 设置 API Key（可选，但推荐）
export ANTHROPIC_API_KEY="your-api-key"

# 进入知识库目录
cd /path/to/East-lake

# 简单查询
python scripts/obsidian_qa.py "什么是 RAG 技术?"

# 交互式问答
python scripts/obsidian_qa.py --interactive

# 查看知识库摘要
python scripts/obsidian_qa.py --summary

# 分析知识缺口
python scripts/obsidian_qa.py --gaps
```

### 2. 自动演化

```bash
# 立即执行一次演化
python scripts/auto_evolve.py --once

# 后台守护进程模式（每5分钟检查）
python scripts/auto_evolve.py --daemon

# 实时监听文件变化
python scripts/auto_evolve.py --watch
```

### 3. 在 Obsidian 中使用

#### 方式 A：Shell Commands 插件

1. 安装 Obsidian 的 Shell Commands 插件
2. 添加命令：
   ```bash
   python /path/to/East-lake/scripts/obsidian_qa.py "{{selection}}"
   ```

#### 方式 B：QuickAdd 插件

1. 安装 QuickAdd 插件
2. 创建 Macro：
   - 添加 User Script 执行 Python
   - 捕获输出并插入当前光标位置

#### 方式 C：文本文件 + 热键

1. 创建 `qa-requests.md` 文件
2. 写入问题
3. 运行脚本处理该文件
4. 将结果写回 Obsidian

---

## 核心功能

### 1. 本地问答（无需 API）

```bash
$ python scripts/obsidian_qa.py "RAG"

🔍 查询: RAG
📊 找到 3 个相关文档:

[1] RAG-实现方案
    路径: concepts/rag-implementation.md
    得分: 15
    预览: RAG (Retrieval-Augmented Generation) 是一种...
```

功能：
- 关键词匹配搜索
- 标签加权
- 链接关系加权（被引用多的文档排名更高）
- 上下文预览

### 2. AI 增强问答（需要 API Key）

```bash
$ export ANTHROPIC_API_KEY="sk-..."
$ python scripts/obsidian_qa.py "如何实现 RAG?"

🤖 AI 回答:

根据知识库，RAG (检索增强生成) 的实现方案如下：

## 核心组件
1. 文档加载器
2. 文本分块
3. 向量嵌入
4. 向量存储
5. 检索和生成

## 相关文档
- [[RAG-实现方案]]
- [[向量数据库]]
- [[Embedding]]

...
```

### 3. 知识库健康分析

```bash
$ python scripts/obsidian_qa.py --gaps

=== 知识缺口分析 ===

📌 孤立文档（未被链接）: 3
   - 新概念A (concepts/new-concept-a.md)
   - 决策记录X (decisions/decision-x.md)

🏷️ 无标签文档: 5

📂 未分类文档: 2
```

### 4. 自动演化

运行 `auto_evolve.py` 会自动：

| 演化类型 | 说明 |
|----------|------|
| **更新索引** | 自动更新 `concepts/index.md` 列出所有概念 |
| **添加反向链接** | 在文档末尾添加"相关链接"部分 |
| **创建建议** | 生成 `evolution-suggestions.md` 建议创建的新概念 |

---

## 与 GitHub Actions 集成

GitHub 端自动演化（每周运行）：

| Workflow | 触发 | 功能 |
|----------|------|------|
| `ai-analyze.yml` | 文档变更 | AI 分析文档内容 |
| `knowledge-index.yml` | 文档变更 | 更新知识图谱 |
| `knowledge-evolution.yml` | 每周六 | 整体健康分析+演化建议 |

---

## 配置说明

### 环境变量

```bash
# Anthropic API（可选，用于 AI 功能）
export ANTHROPIC_API_KEY="your-key"

# GitHub Token（用于 GitHub Actions）
export GITHUB_TOKEN="your-token"
```

### 演化状态

状态保存在 `.obsidian/evolve_state.json`：

```json
{
  "last_hash": "a1b2c3...",
  "last_evolution": "2025-05-06T10:30:00",
  "evolution_count": 42
}
```

---

## 典型工作流

### 日常使用

```bash
# 每天早上：检查知识库状态
python scripts/obsidian_qa.py --gaps

# 工作时：随时问答
python scripts/obsidian_qa.py --interactive
# 或
python scripts/obsidian_qa.py "今天有什么新文档？"

# 定期：触发自动演化
python scripts/auto_evolve.py --once
```

### 自动化（推荐）

```bash
# 添加到 crontab（每天下班前演化）
crontab -e
# 添加：0 18 * * * cd /path/to/East-lake && python scripts/auto_evolve.py --once
```

---

## 常见问题

### Q: 没有 API Key 能否使用？
A: 可以。基础搜索和本地问答功能无需 API Key。AI 增强功能需要设置 `ANTHROPIC_API_KEY`。

### Q: 演化会修改我的文档吗？
A: 会。`auto_evolve.py` 会：
- 更新 `concepts/index.md`
- 在文档末尾添加"相关链接"部分（如果还没有）
- 创建 `evolution-suggestions.md`（建议文件，不会覆盖已有内容）

### Q: 如何禁用自动修改？
A: 使用 `--gaps` 或 `--evolve` 参数只做分析，不执行修改：
```bash
python scripts/obsidian_qa.py --evolve "分析"
```

### Q: 支持其他 LLM 吗？
A: 目前支持 Anthropic Claude。可通过修改 `ask_with_ai()` 函数切换到 OpenAI 或其他 provider。

---

## 相关脚本

| 脚本 | 功能 |
|------|------|
| `obsidian_qa.py` | 问答、健康分析、演化建议 |
| `auto_evolve.py` | 自动执行知识库演化 |
| `embeddings.py` | 向量索引和语义搜索（API 服务用） |