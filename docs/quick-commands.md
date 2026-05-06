# Obsidian AI 快速命令参考

本文档汇总所有可用的 AI 命令，方便快速查阅。

---

## 🚀 一键命令（推荐）

在知识库目录下运行：

```bash
# 进入知识库
cd /path/to/East-lake

# 提问（一次性）
python scripts/obsidian_workflow.py ask "什么是 RAG?"

# 交互式对话
python scripts/obsidian_workflow.py chat

# 导入文件
python scripts/obsidian_workflow.py import ~/Document/report.pdf

# 批量导入
python scripts/obsidian_workflow.py batch ~/Downloads/

# 知识库演化
python scripts/obsidian_workflow.py evolve

# 查看统计
python scripts/obsidian_workflow.py dashboard

# 分析缺口
python scripts/obsidian_workflow.py gaps
```

---

## ⚡ Obsidian 内部命令

### 通过 Shell Commands（推荐）

安装 Shell Commands 插件后，添加以下命令：

| 命令 | 快捷键 | 脚本 |
|------|--------|------|
| 🤖 Ask AI | Ctrl+Shift+A | `python {{vault.path}}/scripts/obsidian_workflow.py ask "{{clipboard}}"` |
| 💬 AI Chat | - | `python {{vault.path}}/scripts/obsidian_workflow.py chat` |
| 📥 Import File | Ctrl+Shift+I | `python {{vault.path}}/scripts/obsidian_workflow.py import` |
| 🧬 Evolve KB | - | `python {{vault.path}}/scripts/obsidian_workflow.py evolve` |
| 📊 Knowledge Stats | - | `python {{vault.path}}/scripts/obsidian_workflow.py dashboard` |

### 通过 QuickAdd

1. 安装 QuickAdd 插件
2. 添加用户脚本
3. 选择 `ai-integration.js`
4. 设置触发方式

### 通过 Templater

创建笔记时自动运行：

```javascript
<% await tp.user.dailyNote() %>
```

---

## 📋 详细功能

### 1. AI 对话

```bash
# 简单提问
python scripts/obsidian_workflow.py ask "今天有什么新文档?"

# 交互模式（可持续对话）
python scripts/obsidian_workflow.py chat
# 输入 quit 退出
# 输入 save 保存对话
# 输入 clear 清除历史
```

**功能：**
- 本地语义搜索（无需 API）
- AI 增强回答（需要 ANTHROPIC_API_KEY）
- 自动引用相关文档
- 保存对话历史

### 2. 文件导入

```bash
# 导入单个文件
python scripts/obsidian_workflow.py import ~/Document/report.pdf

# 导入并指定分类
python scripts/obsidian_workflow.py import ~/Document/report.pdf --category research

# 导入并添加标签
python scripts/obsidian_workflow.py import ~/Document/report.pdf --tags ai,report

# 批量导入
python scripts/obsidian_workflow.py batch ~/Downloads/*.pdf
```

**支持格式：**
- PDF (.pdf) - 需要 PyPDF2
- Word (.docx) - 需要 python-docx
- Markdown (.md)
- 纯文本 (.txt)

### 3. 知识库演化

```bash
# 执行一次演化
python scripts/obsidian_workflow.py evolve

# 分析缺口
python scripts/obsidian_workflow.py gaps

# 获取建议
python scripts/obsidian_workflow.py suggestions
```

**自动执行：**
- 更新概念索引
- 添加反向链接
- 检测孤立文档
- 生成演化建议

### 4. 搜索

```bash
# 搜索关键词
python scripts/obsidian_workflow.py search "RAG"

# 查看统计
python scripts/obsidian_workflow.py dashboard
```

---

## ⚙️ 配置

### 环境变量

```bash
# AI 需要
export ANTHROPIC_API_KEY="your-key"

# GitHub 同步需要
export GITHUB_TOKEN="your-token"
```

### AI 对话配置

编辑 `.obsidian/ai-config.json`：

```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1000,
  "temperature": 0.7,
  "include_backlinks": true,
  "search_top_k": 5
}
```

---

## 🔧 故障排除

### 问题：Python 找不到

```bash
# macOS/Linux
which python3

# Windows
where python
```

### 问题：模块未安装

```bash
pip install anthropic PyPDF2 python-docx watchdog
```

### 问题：权限被拒绝

```bash
chmod +x scripts/*.py
```

---

## 📁 脚本文件

| 脚本 | 功能 |
|------|------|
| `obsidian_workflow.py` | 统一入口 |
| `obsidian_chat.py` | AI 对话 |
| `obsidian_qa.py` | 问答与分析 |
| `import_to_obsidian.py` | 文件导入 |
| `auto_evolve.py` | 自动演化 |
| `embeddings.py` | 向量索引 |