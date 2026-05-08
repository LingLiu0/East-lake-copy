# 快速命令参考

> East-lake 知识库常用命令速查

---

## 核心命令

```bash
# 进入知识库目录
cd /path/to/East-lake

# 查看状态
python3 scripts/obsidian.py status

# 编译知识库（将 raw/ 资料编译成 wiki/）
python3 scripts/obsidian.py ai compile

# 提问
python3 scripts/obsidian.py ask "你的问题"

# 交互对话
python3 scripts/obsidian.py chat

# 生成知识图谱
python3 scripts/obsidian.py ai graph

# 健康检查
python3 scripts/obsidian.py ai lint

# 更新索引
python3 scripts/obsidian.py ai index
```

---

## 自动进化

```bash
# 运行一次自动进化
python3 scripts/auto_evolve.py

# 持续运行（每小时）
python3 scripts/auto_evolve.py --continuous

# 查看帮助
python3 scripts/auto_evolve.py --help
```

---

## 周报生成

```bash
# 生成周报
python3 scripts/weekly_report.py
```

---

## 文件监控

```bash
# 一次性检查
python3 scripts/watch.py

# 持续监听
python3 scripts/watch.py --continuous
```

---

## 环境变量

```bash
# 自定义大模型 API（必须）
export API_KEY="your-api-key"
export API_BASE="https://your-api-endpoint.com"
export MODEL="your-model-name"

# 或使用 Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"
```

---

## Git 操作

```bash
# 添加资料
git add raw/
git commit -m "feat: 添加新文章"
git push

# 同步更新
git pull
```

---

## 脚本文件

| 脚本 | 功能 |
|------|------|
| `obsidian.py` | 统一入口 |
| `auto_evolve.py` | 自动进化 |
| `generate_graph.py` | 知识图谱 |
| `weekly_report.py` | 周报生成 |
| `api_client.py` | API 客户端 |
| `watch.py` | 文件监控 |

---

*最后更新：2026-05-08*