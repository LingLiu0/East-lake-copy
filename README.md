# East-lake 知识库

> 基于 GitHub 的 AI 驱动知识管理系统，会"越用越聪明"

---

## 一句话介绍

像管理代码一样管理知识：资料放进去 → 自动编译成知识网络 → 团队共享、持续进化

---

## 核心理念

| 传统笔记 | East-lake |
|---------|-----------|
| 笔记散乱、找不到关联 | 自动建立概念之间的链接 |
| 时间久了积灰 | 越用越聪明，自动补全 |
| 无法深度问答 | AI 基于知识网络回答 |
| 团队协作困难 | 基于 GitHub，天然支持协作 |
| 政策信息分散 | 自动采集汇总，生成参考简报 |

---

## 能做什么

- 📥 **资料收集**：Web Clipper 一键收藏，支持 PDF/Word/PPT/Markdown
- 🧠 **知识提炼**：自动提取概念、建立双向链接
- 💬 **智能问答**：基于知识库回答专业问题
- 📊 **周报生成**：每周五自动报告知识库状态
- 🔄 **自动进化**：补全概念定义、强化知识关联
- 👥 **团队协作**：基于 GitHub，多人协同
- 📑 **政策简报**：自动获取重点政策，生成分析参考
- 📝 **AI生成**：参考模板生成政策报告、产业分析等

---

## 核心功能

### 1. 政策简报自动获取

自动采集重点政策信息，按日期生成简报：

```bash
# 获取当天政策
python3 scripts/fetch_policy.py

# 获取指定日期政策
python3 scripts/fetch_policy.py --date 2026-05-07

# 每日自动获取
python3 scripts/fetch_policy.py --daily
```

**政策来源**：
- 中央：国务院、发改委、工信部、科技部、网信办等
- 湖北：荆楚网、长江云等
- 科技：36氪等新质生产力源

**筛选原则**：
- 湖北移动视角：关注数字经济、AI、通信、产业发展
- 重大政策：中央重大会议、规划文件
- 排除：民生新闻、个人荣誉、其他省份无关信息

### 2. 知识库编译

将原始资料自动编译为结构化知识：

```bash
python3 scripts/obsidian.py ai compile
```

- 自动生成摘要
- 提取关键概念
- 建立双向链接
- 更新知识图谱

### 3. 智能问答

基于知识库回答专业问题：

```bash
python3 scripts/obsidian.py ask "湖北省数字经济发展有哪些政策支持？"
```

### 4. AI 生成物模板

`templates/` 文件夹存放人工撰写的输出模板，AI 生成同类产物时学习参考：

- policy_report.md - 政策简报模板
- industry_report.md - 产业观察报告模板
- policy_special.md - 政策专报模板

---

## 技术架构

```
┌─────────────┐     git push      ┌─────────────┐     GitHub Actions      ┌─────────────┐
│  团队成员    │ ───────────────→  │   GitHub    │ ───────────────────→  │  知识库     │
│  (本地)     │                   │   仓库      │                        │  (自动更新)  │
└─────────────┘                   └─────────────┘                         └─────────────┘
                                         ↓
                              ┌─────────────────────┐
                              │  daily-policy       │ → 政策简报获取
                              │  auto-compile       │ → 编译资料
                              │  auto-evolve        │ → 补全概念
                              │  knowledge-graph    │ → 更新图谱
                              │  weekly-report      │ → 生成周报
                              └─────────────────────┘
```

---

## 目录结构

```
East-lake/
├── raw/                     # 原始资料（不可变）
│   ├── clippings/           # Web Clipper 收藏
│   └── articles/            # 文章/文档
│
├── templates/               # AI生成物模板（人工维护）
│
├── wiki/                    # LLM 编译产物
│   ├── indexes/             # 索引、图谱、日志
│   ├── concepts/            # 概念条目
│   └── summaries/           # 摘要
│
├── outputs/                 # 运行时输出
│   ├── qa/                  # 问答沉淀
│   ├── reports/             # 周报
│   └── health/              # 健康报告
│
├── scripts/                 # 核心脚本
│   ├── obsidian.py          # 统一入口
│   ├── fetch_policy.py      # 政策简报获取
│   ├── auto_evolve.py       # 自动进化
│   ├── weekly_report.py     # 周报生成
│   └── api_client.py        # API 客户端
│
├── .github/workflows/       # 自动化
│   ├── daily-policy.yml     # 每日政策获取
│   ├── auto-compile.yml     # 自动编译
│   ├── auto-evolve.yml      # 自动进化
│   ├── knowledge-graph.yml  # 知识图谱
│   └── weekly-report.yml    # 周报
│
└── docs/                    # 文档
    ├── quick-start.md       # 快速入门
    ├── collaboration.md     # 团队协作
    ├── team-workflow.md     # 工作流
    └── system-mechanism.md  # 系统机制详解
```

---

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/huangtao900103/East-lake.git
cd East-lake

# 2. 配置 API（用于 AI 功能）
export API_KEY="your-api-key"
export API_BASE="https://your-api-endpoint.com"
export MODEL="your-model"

# 3. 添加资料
cp 我的文章.pdf raw/articles/

# 4. 编译知识库
python3 scripts/obsidian.py ai compile

# 5. 提问
python3 scripts/obsidian.py ask "这篇文章的核心观点是什么？"

# 6. 获取政策简报
python3 scripts/fetch_policy.py
```

---

## 命令参考

| 命令 | 功能 |
|------|------|
| `python3 scripts/obsidian.py status` | 查看状态 |
| `python3 scripts/obsidian.py ai compile` | 编译知识库 |
| `python3 scripts/obsidian.py ai graph` | 生成知识图谱 |
| `python3 scripts/obsidian.py ai lint` | 健康检查 |
| `python3 scripts/obsidian.py ask "问题"` | 智能问答 |
| `python3 scripts/fetch_policy.py` | 获取政策简报 |

---

## 团队协作

### 方式 A：协作者（推荐）

1. 管理员在 GitHub 添加协作者
2. 协作者 clone 后直接 push 到 master
3. GitHub Actions 自动编译 + 优化

### 方式 B：Fork + PR

1. Fork 仓库
2. 添加资料后发起 PR
3. 管理员审核合并

### 自动流程

```
添加资料 → git push → 自动编译 → 自动进化 → 自动生成周报
```

---

## 支持的大模型

- ✅ 自定义 API（兼容 OpenAI 格式）
- ✅ Anthropic Claude
- ✅ 移动云 Zhenze
- ✅ 阿里云 DashScope
- ✅ 其他兼容 OpenAI API 的模型

---

## 适用场景

- 🔬 **政策研究**：自动跟踪政策动态，生成分析简报
- 📊 **产业分析**：追踪数字经济、AI、通信等行业趋势
- 📚 **学习者**：构建个人知识体系
- 👥 **团队**：共享知识库，协作积累
- 📝 **写作者**：建立写作素材库

---

## 相关链接

- 📖 [快速入门](docs/quick-start.md)
- 👥 [团队协作](docs/collaboration.md)
- 📋 [命令参考](docs/quick-commands.md)
- 🔄 [工作流](docs/team-workflow.md)
- ⚙️ [系统机制](docs/system-mechanism.md)

---

**GitHub**: https://github.com/huangtao900103/East-lake