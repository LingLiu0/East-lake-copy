# 东湖智库 (East-lake)

> 基于 llm-wiki 思想构建：极简、AI 友好、渐进式增长

## 快速导航

### 核心概念
> 原子化的概念解释，便于理解和链接

- [[concepts/]] - 所有概念索引

### 项目文档
> 各项目的详细文档和进展

- [[projects/]] - 项目列表

### 决策记录
> 重要的技术和管理决策（ADR 风格）

- [[decisions/]] - 决策索引

### 会议记录
> 周会、讨论会记录

- [[meetings/]] - 会议列表

### 外部资源
> 论文、工具、教程等外部资源索引

- [[references/]] - 资源列表

---

## 新成员必读

- [[docs/team-collaboration|团队协作指南]] - 如何协作、任务流转、常用命令
- [[docs/quick-start|快速入门]] - 5 分钟上手配置

---

## 使用指南

### 编辑规范

1. **原子化**：每个文件只讲一个概念/主题
2. **链接优先**：新概念先搜后建，使用 `[[双向链接]]`
3. **Front Matter**：必须有 title, tags, created
4. **文件命名**：英文短横线命名，如 `concept-name.md`

### 同步方式

```bash
# 日常：自动同步（Obsidian Git 插件）
# 重要变更：PR 审核

# 手动同步
git pull
git add .
git commit -m "update: your changes"
git push
```

### 模板

- [[templates/concept-template|概念模板]]
- [[templates/decision-template|决策模板]]
- [[templates/meeting-template|会议模板]]

---

## 统计

- 创建日期: 2025-05-05
- 维护团队: 10 人小组
- 同步方式: Obsidian Git + GitHub
