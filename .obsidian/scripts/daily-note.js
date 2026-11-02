/**
 * Obsidian Daily Note Creator with AI
 *
 * 使用方法:
 * 1. 安装 Templater 插件
 * 2. 创建模板文件引用此脚本
 * 3. 或通过命令面板运行
 */

class DailyNoteCreator {
    constructor() {
        this.today = new Date();
        this.vaultPath = app.vault.adapter.getBasePath();
    }

    async create() {
        const dateStr = this.formatDate(this.today);
        const notePath = `daily/${dateStr}.md`;

        // 检查是否已存在
        if (await this.exists(notePath)) {
            new Notice(`📝 日记已存在: ${dateStr}`);
            await app.workspace.openNoteByPath(notePath);
            return;
        }

        // 获取模板
        const templatePath = "templates/daily-note-template.md";
        let content = await this.getTemplate(templatePath);

        // 替换占位符
        content = content
            .replace(/\{\{date\}\}/g, dateStr)
            .replace(/\{\{year\}\}/g, this.today.getFullYear().toString())
            .replace(/\{\{month\}\}/g, (this.today.getMonth() + 1).toString().padStart(2, '0'))
            .replace(/\{\{day\}\}/g, this.today.getDate().toString().padStart(2, '0'))
            .replace(/\{\{weekday\}\}/g, this.getWeekday());

        // 创建笔记
        await app.vault.create(notePath, content);
        new Notice(`✅ 已创建日记: ${dateStr}`);

        // 打开笔记
        await app.workspace.openNoteByPath(notePath);

        // 可选：运行 AI 分析
        await this.suggestContent(notePath);
    }

    async exists(path) {
        try {
            await app.vault.adapter.stat(path);
            return true;
        } catch {
            return false;
        }
    }

    async getTemplate(path) {
        try {
            const file = await app.vault.getAbstractFileByPath(path);
            return await app.vault.read(file);
        } catch {
            return `---
title: Daily {{date}}
tags: [daily, {{date}}]
created: {{date}}
---

# {{date}} - {{weekday}}

## 今日回顾

### 完成的任务
-

### 学习的知识
-

### 新的想法
-

---

## 今日输入

### 看到的内容
-

### 听到的内容
-

### 思考的问题
-

---

## 今日输出

### 记录的知识
-

### 待深入研究
-

---

## 关联概念
-

`;
        }
    }

    formatDate(date) {
        const y = date.getFullYear();
        const m = (date.getMonth() + 1).toString().padStart(2, '0');
        const d = date.getDate().toString().padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    getWeekday() {
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        return weekdays[this.today.getDay()];
    }

    async suggestContent(notePath) {
        // 简单的建议，不是完整的 AI
        const suggested = `
---

> 💡 **使用 AI 增强此日记**
> 运行: \`python scripts/obsidian_workflow.py ask "今天的日记有什么值得注意的？"\`
`;

        try {
            const file = await app.vault.getAbstractFileByPath(notePath);
            const content = await app.vault.read(file);
            await app.vault.modify(file, content + suggested);
        } catch (e) {
            console.error(e);
        }
    }
}

// 主函数 - 供 Templater 调用
async function createDailyNote() {
    const creator = new DailyNoteCreator();
    await creator.create();
}

// 运行
module.exports = createDailyNote;