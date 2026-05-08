# 团队协作指南

> 协作者加入 East-lake 知识库的完整流程

---

## 一、获取仓库访问权限

### 方式 A：直接添加为协作者

仓库所有者（admin）在 GitHub 仓库设置中添加协作者：
- 进入仓库 → Settings → Collaborators → Add collaborator
- 输入协作者的 GitHub 用户名或邮箱

### 方式 B：Fork 后贡献

1. **Fork 仓库**：点击仓库页面的 "Fork" 按钮
2. **克隆你的 Fork**：
   ```bash
   git clone https://github.com/你的用户名/East-lake.git
   cd East-lake
   ```
3. **添加上游仓库**：
   ```bash
   git remote add upstream https://github.com/huangtao900103/East-lake.git
   ```

---

## 二、本地开发环境配置

### 1. 克隆仓库

```bash
git clone https://github.com/huangtao900103/East-lake.git
cd East-lake
```

### 2. 安装依赖

```bash
pip install requests beautifulsoup4 anthropic PyPDF2 python-docx
```

### 3. 配置 GitHub Secrets（可选）

如果需要触发自动化编译，需要在 GitHub 仓库中配置：

1. 进入仓库 → Settings → Secrets and variables → Actions
2. 添加新 secret：
   - **Name**: `ANTHROPIC_API_KEY`
   - **Value**: 你的 Anthropic API Key

> 注意：只有仓库管理员才能配置 Secrets

---

## 三、Obsidian 工作流（推荐）

### 1. 安装 Obsidian 插件

| 插件 | 安装方式 | 用途 |
|------|----------|------|
| Obsidian Git | 社区插件市场 | 自动同步 |
| Web Clipper | 社区插件市场 | 网页剪藏 |
| BRAT | 社区插件市场 | 安装测试版插件 |
| Claudian | 通过 BRAT 安装 | AI 问答 |

### 2. Claudian 安装步骤

1. 安装 BRAT 插件
2. 命令面板 → "BRAT: Add a beta plugin"
3. 输入：`https://github.com/YishenTu/claudian`
4. 配置环境变量：`ANTHROPIC_API_KEY`

### 3. 日常使用

```markdown
# 工作流程

1. 用 Obsidian 打开 East-lake 目录
2. 使用 Web Clipper 收集网页到 raw/clippings/
3. 手动放入资料到 raw/articles/
4. Obsidian Git 自动推送（或手动 git push）
5. GitHub Actions 自动编译知识库
6. 团队成员 git pull 同步
```

---

## 四、命令行工作流

### 协作者标准操作

```bash
# 1. 同步最新代码
git pull

# 2. 添加新资料
cp /path/to/article.md raw/articles/

# 3. 本地测试编译（可选）
python3 scripts/obsidian.py ai compile

# 4. 提交并推送
git add raw/
git commit -m "feat: 添加新文章"
git push
```

### 自动流程触发

推送到远程后，GitHub Actions 会自动：

```
✅ 1. 检测 raw/ 目录变化
✅ 2. 调用 AI 编译知识库
✅ 3. 更新 wiki/index.md
✅ 4. 更新知识图谱
✅ 5. 自动提交并推送
```

---

## 五、同步团队更新

```bash
# 获取最新代码
git pull

# 或手动解决冲突
git fetch origin
git merge origin/master
```

---

## 六、常见问题

### Q: 没有 ANTHROPIC_API_KEY 怎么办？

A: 
- 本地搜索不需要 API Key
- 只使用 `python3 scripts/obsidian.py ask` 回答需要 API Key
- 可以跳过编译，直接同步团队的 wiki 目录

### Q: 推送后自动化没触发？

A: 
- 检查是否推送到 master 分支
- 检查 GitHub Actions 是否启用
- 检查仓库的 Secrets 是否配置

### Q: 和团队成员冲突了怎么办？

A: 
```bash
# 保留你的修改，先拉取远程
git stash
git pull
# 再恢复你的修改
git stash pop
# 手动解决冲突后提交
```

---

*最后更新：2026-05-08*