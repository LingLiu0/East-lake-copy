# 知识库 Git 工作流

东湖智库采用 Git 分支管理模式，确保知识质量和团队协作效率。

---

## 一、角色定义

| 角色 | 分支权限 | 职责 |
|------|----------|------|
| **Maintainer（管理员）** | main 直接写入 | 审核合并、维护结构、最终把关 |
| **Contributor（贡献者）** | 分支 + PR | 创建分支、提交内容、响应审核 |

### 当前角色

- **Maintainer**: @huangtao900103（main 分支负责人）
- **Contributor**: 所有其他团队成员

---

## 二、分支策略

```
┌─────────────────────────────────────────────────────────────┐
│                    Git 分支模型                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                      main (受保护)                           │
│                        ↑                                    │
│                        │ merge                              │
│                        │                                    │
│         ┌──────────────┼──────────────┐                    │
│         │              │              │                     │
│    content/xxx    docs/xxx      fix/xxx                    │
│    (新增内容)     (文档更新)    (修正错误)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `content/` | 新增内容 | `content/rag-technology` |
| `docs/` | 文档更新 | `docs/update-readme` |
| `fix/` | 修正错误 | `fix/typo-concepts` |
| `refactor/` | 结构调整 | `refactor/reorganize-folders` |

---

## 三、工作流程

### 标准流程（推荐）

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. 同步最新代码                                             │
│     git checkout main && git pull                           │
│                       ↓                                     │
│  2. 创建功能分支                                             │
│     git checkout -b content/your-topic                      │
│                       ↓                                     │
│  3. 编辑内容                                                 │
│     在 Obsidian 中编辑文档                                   │
│                       ↓                                     │
│  4. 提交变更                                                 │
│     git add . && git commit -m "content: 添加xxx"           │
│                       ↓                                     │
│  5. 推送分支                                                 │
│     git push -u origin content/your-topic                   │
│                       ↓                                     │
│  6. 创建 Pull Request                                        │
│     gh pr create --title "content: 添加xxx"                 │
│                       ↓                                     │
│  7. 等待审核                                                 │
│     Maintainer 审核、评论、要求修改                          │
│                       ↓                                     │
│  8. 合并到 main                                              │
│     审核通过后合并                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 快速流程（日常小修改）

对于**个人笔记、会议记录**等日常内容，可直接提交：

```bash
# 确保在 main 分支
git checkout main
git pull

# 直接编辑后提交
git add .
git commit -m "notes: 添加会议记录"
git push
```

> 注意：此方式仅适用于**非核心内容**，重要文档必须走 PR 流程。

---

## 四、PR 提交规范

### 标题格式

```
<类型>: <简短描述>

类型：
- content: 新增内容
- docs: 文档更新
- fix: 修正错误
- refactor: 结构调整
```

### PR 模板

创建 PR 时请填写以下内容：

```markdown
## 变更类型
- [ ] 新增内容 (content)
- [ ] 文档更新 (docs)
- [ ] 修正错误 (fix)
- [ ] 结构调整 (refactor)

## 变更说明
<!-- 简要描述本次变更的内容和原因 -->

## 相关 Issue
<!-- 如有相关 Issue，请关联：Closes #编号 -->

## 检查清单
- [ ] 已测试双向链接正确
- [ ] 已添加 Front Matter
- [ ] 已关联相关文档
- [ ] 文件命名符合规范

## 截图（如适用）
<!-- 添加截图帮助理解 -->
```

---

## 五、审核标准

### Maintainer 审核要点

| 检查项 | 要求 |
|--------|------|
| **内容质量** | 准确、完整、有价值 |
| **结构规范** | 符合目录结构，命名正确 |
| **链接有效** | 双向链接指向存在的文档 |
| **格式正确** | Front Matter 完整，Markdown 格式正确 |
| **无冲突** | 与 main 分支无冲突 |

### 审核流程

```bash
# 1. 检出 PR 分支
gh pr checkout <PR编号>

# 2. 在 Obsidian 中预览检查

# 3. 如需修改，添加评论
gh pr comment <PR编号> --body "请修改：xxx"

# 4. 审核通过，合并
gh pr merge <PR编号> --squash --delete-branch
```

---

## 六、冲突解决

### 预防冲突

```bash
# 提交 PR 前，先同步 main 最新代码
git checkout main
git pull
git checkout your-branch
git rebase main

# 解决冲突后
git add .
git rebase --continue
git push --force-with-lease
```

### 常见冲突场景

| 场景 | 解决方案 |
|------|----------|
| 同一文件不同位置 | Git 自动合并 |
| 同一文件同一位置 | 手动选择保留内容 |
| 文件被删除/移动 | 确认意图后手动处理 |

---

## 七、权限管理

### 分支保护（需 GitHub Pro）

```
main 分支保护规则：
- ☑ Require pull request before merging
- ☑ Require approvals: 1
- ☑ Dismiss stale reviews on new commits
```

### 权限配置

| 成员 | 权限 | 说明 |
|------|------|------|
| Maintainer | Admin | 完全控制 |
| Contributor | Write | 可推送分支，创建 PR |

---

## 八、常用命令速查

### 分支操作

```bash
# 查看所有分支
git branch -a

# 创建并切换分支
git checkout -b content/topic-name

# 切换分支
git checkout main

# 删除本地分支
git branch -d content/topic-name

# 删除远程分支
git push origin --delete content/topic-name
```

### PR 操作

```bash
# 创建 PR
gh pr create --title "content: 添加新文档" --body "变更说明"

# 查看 PR 列表
gh pr list --repo huangtao900103/East-lake

# 检出 PR
gh pr checkout <编号>

# 审核 PR
gh pr review <编号> --approve --body "LGTM"

# 合并 PR
gh pr merge <编号> --squash --delete-branch

# 关闭 PR
gh pr close <编号>
```

### 同步操作

```bash
# 同步 main
git checkout main && git pull

# 同步分支
git checkout your-branch && git pull

# Rebase 到最新 main
git checkout your-branch
git fetch origin
git rebase origin/main
```

---

## 九、示例场景

### 场景 1：新增技术文档

```bash
# 1. 同步并创建分支
git checkout main && git pull
git checkout -b content/vector-database

# 2. 创建文档
# 在 Obsidian 中创建 concepts/vector-database.md

# 3. 提交
git add concepts/vector-database.md
git commit -m "content: 添加向量数据库概念文档"

# 4. 推送并创建 PR
git push -u origin content/vector-database
gh pr create --title "content: 添加向量数据库概念文档" \
  --body "## 变更说明
新增向量数据库技术概念文档，包含定义、应用场景、常见产品对比。

## 检查清单
- [x] 已添加 Front Matter
- [x] 已关联 [[RAG]] 等相关概念"

# 5. 等待 Maintainer 审核

# 6. 审核通过后自动合并
```

### 场景 2：修正错误

```bash
# 1. 创建修复分支
git checkout main && git pull
git checkout -b fix/typo-llm-wiki

# 2. 修正错误
# 编辑 concepts/llm-wiki.md 修正错别字

# 3. 提交
git add concepts/llm-wiki.md
git commit -m "fix: 修正 llm-wiki 文档错别字"

# 4. 推送并创建 PR
git push -u origin fix/typo-llm-wiki
gh pr create --title "fix: 修正 llm-wiki 文档错别字" \
  --body "修正第 15 行错别字"
```

### 场景 3：记录会议（快速流程）

```bash
# 会议记录直接提交到 main
# （前提：Maintainer 允许日常笔记直接推送）

cd ~/East-lake
git pull

# 在 Obsidian 中创建会议记录
# meetings/2025-05-05-weekly.md

# Obsidian Git 自动提交
# 或手动提交
git add meetings/2025-05-05-weekly.md
git commit -m "notes: 添加周会记录"
git push
```

---

## 十、最佳实践

### 提交信息规范

```bash
# 好的提交信息
git commit -m "content: 添加向量数据库文档"
git commit -m "fix: 修正 RAG 概念描述错误"
git commit -m "docs: 更新协作指南"

# 不好的提交信息
git commit -m "update"
git commit -m "修改了一些东西"
git commit -m "fix bug"
```

### 分支管理

```bash
# 保持分支短小精悍
# 一个分支只做一件事

# 及时删除已合并分支
gh pr merge <编号> --delete-branch

# 定期清理本地分支
git branch -d $(git branch --merged main | grep -v main)
```

### 协作礼仪

1. **提交前**：确保内容正确，格式规范
2. **PR 描述**：清晰说明变更原因和内容
3. **响应审核**：及时处理 Maintainer 的反馈
4. **保持同步**：定期 rebase 到最新 main
5. **冲突处理**：主动沟通，协商解决

---

*最后更新：2025-05-05*
