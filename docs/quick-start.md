# East-lake 快速入门指南

> 5 分钟快速上手团队 AI 知识库

---

## 一、本地运行

### 1. 克隆仓库

```bash
git clone https://github.com/你的仓库/East-lake.git
cd East-lake
```

### 2. 安装依赖

```bash
python3 scripts/obsidian.py install
```

### 3. 查看状态

```bash
python3 scripts/obsidian.py status
```

---

## 二、添加知识（三种方式）

### 方式一：Web Clipper 插件（推荐）

1. **安装插件**
   - Chrome: [Web Clipper 商店](https://chromewebstore.google.com/detail/obsidian-web-clipper/hbfnancohjgjjmofefclnpjbcijhcbfg)
   - 或在 Obsidian 中搜索 "Web Clipper" 安装

2. **配置**
   - 点击插件图标 → 连接保险库 → 选择 `East-lake`
   - 设置默认保存位置：`raw/clippings/`

3. **使用**
   - 浏览器看到好文章 → 点击插件 → Clip
   - 自动保存到 `raw/clippings/`

### 方式二：手动放入文件

直接把文件拖到 `raw/clippings/` 或 `raw/articles/` 目录

### 方式三：API 服务（高级）

```bash
cd api && python main.py
```

---

## 三、编译知识库

```bash
python3 scripts/obsidian.py ai compile
```

自动生成：
- 摘要 → `wiki/summaries/`
- 概念 → `wiki/concepts/`
- 索引 → `wiki/indexes/`

---

## 四、提问

```bash
# 简单提问
python3 scripts/obsidian.py ask "你的问题"

# 交互对话
python3 scripts/obsidian.py chat
```

---

## 五、团队协作

### 提交到 GitHub

```bash
git add raw/
git commit -m "feat: 添加新文章"
git push
```

### 自动流程

```
Git Push → GitHub Actions 自动：
  1. 编译知识库 (ai compile)
  2. 生成知识图谱 (ai graph)
  3. 更新索引
```

### 成员同步

```bash
git pull
```

---

## 六、其他命令

| 命令 | 功能 |
|------|------|
| `python3 scripts/obsidian.py status` | 查看状态 |
| `python3 scripts/obsidian.py ai compile` | 编译知识库 |
| `python3 scripts/obsidian.py ai graph` | 生成知识图谱 |
| `python3 scripts/obsidian.py ai lint` | 健康检查 |
| `python3 scripts/obsidian.py ai index` | 更新索引 |

---

## 七、Obsidian 配合使用

1. 用 Obsidian 打开 East-lake 目录
2. 安装插件：
   - **Obsidian Git** - 自动同步（必装）
   - **Web Clipper** - 网页收集（必装）
3. 在 Obsidian 中浏览 `wiki/` 目录查看知识

---

## 完整工作流

```
浏览器发现好文章
      ↓
Web Clipper 保存 → raw/articles/
      ↓
Git Push → 自动编译 + 知识图谱
      ↓
团队成员 Git Pull
      ↓
在 Obsidian 中浏览知识 / 提问
```

---

## 常见问题

**Q: 为什么需要 compile？**
A: compile 会将原始资料编译成结构化的摘要和概念，建立知识网络。

**Q: 需要配置 API 吗？**
A: 本地搜索不需要。启用 AI 回答需要：
```bash
export ANTHROPIC_API_KEY="your-key"
```

**Q: 知识图谱在哪里？**
A: `wiki/indexes/knowledge-graph.md`，支持 Mermaid 渲染。

---

*最后更新：2026-05-07*