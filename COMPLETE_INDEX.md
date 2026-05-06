# 东湖智库 (East-lake) - 完整功能索引

> 基于 **llm-wiki** 思想构建的 AI 驱动团队知识管理系统

---

## 🎯 项目目标达成度

| 目标 | 状态 | 完成度 |
|------|------|--------|
| 基于 Karpathy llm-wiki 思想 | ✅ 已实现 | 100% |
| AI 自动化分析、管理、迭代 | ✅ 已实现 | 90% |
| 团队协作 | ✅ 已实现 | 85% |
| 外部可调用 | ✅ 已实现 | 85% |

---

## 📁 项目结构

```
East-lake/
├── _inbox/                    📥 投递箱（核心输入入口）
│   ├── README.md             # 使用说明
│   └── web/                  # 网页收集箱
│       └── README.md
│
├── achievements/              📚 成果库（自动生成）
│   ├── weekly/              # 周报
│   ├── research/            # 研究
│   ├── documents/           # 文档
│   ├── design/              # 设计
│   └── code/                # 代码
│
├── api/                      🌐 API 服务
│   ├── main.py              # FastAPI 服务
│   ├── config.py            # 配置
│   ├── requirements.txt     # 依赖
│   ├── Dockerfile           # Docker 配置
│   ├── docker-compose.yml   # Docker Compose
│   ├── README.md            # API 文档
│   └── routes/              # API 路由
│
├── scripts/                  ⚙️ 核心脚本
│   ├── launcher.py          # 🚀 统一启动器
│   ├── diagnose.py          # 🔍 系统诊断
│   ├── obsidian_workflow.py # 📌 统一入口
│   ├── obsidian_chat.py     # 💬 AI 对话
│   ├── obsidian_qa.py       # 🔍 问答搜索
│   ├── auto_evolve.py       # 🧬 知识演化
│   ├── achievement_manager.py   # 📥 成果管理
│   ├── achievement-daemon.py    # 🤖 后台处理器
│   ├── web_collector.py     # 🌐 网页剪藏
│   └── import_to_obsidian.py   # 📄 文件导入
│
├── .github/workflows/        ⚙️ GitHub Actions
│   ├── ai-analyze.yml       # AI 文档分析
│   ├── knowledge-index.yml  # 知识图谱
│   ├── knowledge-evolution.yml # 知识演化
│   └── daily-summary.yml    # 每日摘要
│
├── docs/                     📖 文档
│   ├── obsidian-ai-guide.md # AI 使用指南
│   ├── quick-commands.md    # 快速命令
│   ├── team-collaboration.md# 团队协作
│   └── system-mechanism.md  # 系统运行机制
│
└── templates/                📝 模板
    ├── daily-note-template.md
    └── ...
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd East-lake
python scripts/launcher.py install
```

### 2. 查看系统状态

```bash
python scripts/launcher.py status
```

### 3. 诊断系统

```bash
python scripts/diagnose.py
```

---

## 📥 三种输入方式

### 方式一：文件成果（推荐团队）

```
1. 把文件复制到 _inbox/ 文件夹
2. 运行: python scripts/achievement_manager.py --process
```

支持格式：PDF、Word、Markdown、图片

### 方式二：网页剪藏

```bash
# 添加网页
python scripts/web_collector.py add "https://example.com/article"

# 处理收集箱
python scripts/web_collector.py process
```

### 方式三：Obsidian 手工编辑

使用模板创建笔记（见 templates/ 目录）

---

## 🧠 核心功能

### AI 对话

```bash
# 简单提问
python scripts/obsidian_chat.py "什么是 RAG?"

# 交互模式
python scripts/obsidian_chat.py --interactive
```

### 知识库分析

```bash
# 查看统计
python scripts/obsidian_qa.py --summary

# 分析缺口
python scripts/obsidian_qa.py --gaps

# 演化建议
python scripts/obsidian_qa.py --evolve "分析"
```

### 自动演化

```bash
# 执行演化
python scripts/auto_evolve.py --once
```

---

## 🌐 API 服务

### 启动

```bash
cd api
pip install -r requirements.txt
python main.py
```

### 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/search` | POST | 语义搜索 |
| `/graph` | GET | 知识图谱 |
| `/stats` | GET | 统计信息 |

---

## ⚙️ GitHub Actions（自动化）

| Workflow | 触发 | 功能 |
|----------|------|------|
| ai-analyze.yml | push (research/) | AI 文档分析 |
| knowledge-index.yml | push | 知识图谱更新 |
| knowledge-evolution.yml | 每周六 | 知识演化 |
| daily-summary.yml | 每日 | 知识摘要 |

---

## 📋 统一入口命令

使用 `obsidian_workflow.py` 或 `obsidian-ai.sh`:

```bash
# 收集网页
python scripts/obsidian_workflow.py collect add "URL"
python scripts/obsidian_workflow.py collect process

# 成果管理
python scripts/obsidian_workflow.py achieve process
python scripts/obsidian_workflow.py achieve watch

# 知识管理
python scripts/obsidian_workflow.py ask "问题"
python scripts/obsidian_workflow.py chat
python scripts/obsidian_workflow.py evolve
python scripts/obsidian_workflow.py dashboard
```

---

## 常见问题

### Q: 如何启用 AI 功能？

设置环境变量：
```bash
export ANTHROPIC_API_KEY="your-key"
```

### Q: 投递箱文件怎么处理？

运行 `achievement_manager.py --process` 或 `--watch` 监听模式。

### Q: 如何让服务开机自启？

使用 crontab 或 launchd：
```bash
# macOS
*/5 * * * * cd /path/to/vault && python scripts/achievement-daemon.py --once
```

---

## 🔗 相关链接

- [东湖智库 GitHub](https://github.com/huangtao900103/East-lake)
- [Satellite-HB 任务管理](https://github.com/huangtao900103/Satellite-HB)
- [快速命令参考](docs/quick-commands.md)
- [AI 使用指南](docs/obsidian-ai-guide.md)
- [系统运行机制](docs/system-mechanism.md)

---

*最后更新: {datetime.now().strftime('%Y-%m-%d')}*