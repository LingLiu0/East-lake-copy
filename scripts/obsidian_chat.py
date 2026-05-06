#!/usr/bin/env python3
"""
Obsidian AI 对话核心引擎
通过命名管道与 Obsidian 通信，实现实时 AI 对话

使用方法:
    1. 在 Obsidian 中安装 Shell Commands 插件
    2. 配置命令调用此脚本
    3. 或者通过 QuickAdd 插件调用
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# 尝试导入 Anthropic
try:
    import anthropic
    HAS_ANTHROPIC = bool(os.getenv("ANTHROPIC_API_KEY"))
except ImportError:
    HAS_ANTHROPIC = False


class ObsidianAI:
    """Obsidian AI 对话引擎"""

    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or os.getcwd())
        self.config = self._load_config()
        self.conversation_history = []
        self.max_history = 10

    def _load_config(self) -> dict:
        """加载配置"""
        config_path = self.vault_path / ".obsidian" / "ai-config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())

        return {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "temperature": 0.7,
            "include_backlinks": True,
            "search_top_k": 5,
        }

    def search_knowledge(self, query: str, top_k: int = None) -> list[dict]:
        """搜索知识库"""
        top_k = top_k or self.config.get("search_top_k", 5)
        query_lower = query.lower()
        results = []

        for md_file in self.vault_path.rglob("*.md"):
            if self._should_skip(md_file):
                continue

            content = md_file.read_text(encoding='utf-8', errors='ignore')
            content_lower = content.lower()

            # 计算相关度
            score = 0

            # 标题匹配
            title = self._extract_title(content, md_file.stem)
            if query_lower in title.lower():
                score += 10

            # 标签匹配
            tags = self._extract_tags(content)
            for tag in tags:
                if query_lower in tag.lower():
                    score += 5

            # 内容匹配
            score += content_lower.count(query_lower)

            if score > 0:
                # 提取相关片段
                preview = self._extract_preview(content, query)

                results.append({
                    "path": str(md_file.relative_to(self.vault_path)),
                    "title": title,
                    "score": score,
                    "preview": preview,
                    "tags": tags,
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def _should_skip(self, path: Path) -> bool:
        """跳过某些路径"""
        skip_patterns = [".git", ".obsidian", "node_modules", "scripts"]
        return any(p in str(path) for p in skip_patterns)

    def _extract_title(self, content: str, default: str) -> str:
        """提取标题"""
        match = self._extract_front_matter(content, "title")
        return match.strip() if match else default.replace("-", " ").title()

    def _extract_tags(self, content: str) -> list[str]:
        """提取标签"""
        match = self._extract_front_matter(content, "tags")
        if match:
            return [t.strip().strip('"\'[]') for t in match.split(',')]
        return []

    def _extract_front_matter(self, content: str, key: str) -> str:
        """提取 front matter"""
        import re
        pattern = f"^{key}:\\s*(.+)$"
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _extract_preview(self, content: str, query: str, context: int = 150) -> str:
        """提取包含查询词的预览"""
        import re

        # 移除 front matter
        content = re.sub(r'^---[\s\S]*?---\n', '', content)

        # 查找匹配位置
        query_lower = query.lower()
        content_lower = content.lower()
        pos = content_lower.find(query_lower)

        if pos == -1:
            return content[:context * 2].strip() + "..."

        start = max(0, pos - context)
        end = min(len(content), pos + len(query) + context)

        preview = content[start:end].strip()
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."

        return preview

    def get_backlinks(self, doc_path: str) -> list[str]:
        """获取反向链接"""
        stem = Path(doc_path).stem
        backlinks = []

        import re
        for md_file in self.vault_path.rglob("*.md"):
            if self._should_skip(md_file):
                continue

            content = md_file.read_text(encoding='utf-8', errors='ignore')
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)

            if stem in links:
                backlinks.append(md_file.stem)

        return backlinks[:5]

    def build_context(self, query: str) -> str:
        """构建 AI 上下文"""
        results = self.search_knowledge(query)

        if not results:
            return "无相关知识库内容"

        context_parts = ["## 相关知识库内容\n"]

        for i, doc in enumerate(results, 1):
            context_parts.append(f"### {i}. {doc['title']}")
            context_parts.append(f"来源: {doc['path']}")
            context_parts.append(f"预览: {doc['preview']}")

            if doc.get("tags"):
                context_parts.append(f"标签: {', '.join(doc['tags'])}")

            # 获取反向链接
            if self.config.get("include_backlinks"):
                backlinks = self.get_backlinks(doc["path"])
                if backlinks:
                    context_parts.append(f"相关: {', '.join(backlinks)}")

            context_parts.append("")

        return "\n".join(context_parts)

    def chat(self, message: str, stream: bool = False) -> str:
        """AI 对话"""
        if not HAS_ANTHROPIC:
            # 无 API 时使用本地搜索
            return self._local_chat(message)

        # 添加到历史
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # 保持历史长度
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        # 构建系统提示
        system_prompt = f"""你是一个知识库助手，基于 Obsidian 知识库回答用户问题。

当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

知识库位置: {self.vault_path}

请遵循以下规则：
1. 优先使用提供的知识库内容回答
2. 如果知识库没有相关信息，明确告知用户
3. 使用中文回答
4. 引用相关文档时使用 [[文档名]] 格式
5. 回答要简洁明了"""

        # 获取相关知识
        knowledge_context = self.build_context(message)

        # 构建完整提示
        full_prompt = f"""{system_prompt}

{knowledge_context}

---

用户问题: {message}

请回答:"""

        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = client.messages.create(
                model=self.config.get("model", "claude-sonnet-4-20250514"),
                max_tokens=self.config.get("max_tokens", 1000),
                messages=[{"role": "user", "content": full_prompt}]
            )

            answer = response.content[0].text

            # 添加到历史
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            return answer

        except Exception as e:
            return f"抱歉，发生错误: {str(e)}"

    def _local_chat(self, message: str) -> str:
        """本地模式（无 API）"""
        results = self.search_knowledge(message)

        if not results:
            return "未在知识库中找到相关信息。\n\n可以尝试：\n1. 使用更通用的关键词\n2. 在知识库中添加相关文档\n3. 设置 ANTHROPIC_API_KEY 启用 AI 回答"

        response = f"在知识库中找到 {len(results)} 个相关文档：\n\n"

        for i, doc in enumerate(results, 1):
            response += f"**{i}. {doc['title']}**\n"
            response += f"   {doc['preview'][:100]}...\n"
            response += f"   [[{doc['path']}]]\n\n"

        response += "---\n💡 设置 ANTHROPIC_API_KEY 环境变量可启用 AI 深度回答"

        return response

    def save_conversation(self, title: str = None):
        """保存对话到笔记"""
        if not self.conversation_history:
            return "无对话记录"

        title = title or f"AI 对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        content = f"""---
title: {title}
tags: [ai-chat, conversation]
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {title}

"""

        for msg in self.conversation_history:
            role = "🤖 AI" if msg["role"] == "assistant" else "👤 用户"
            content += f"### {role}\n\n{msg['content']}\n\n---\n\n"

        # 保存到文件
        filename = f"ai-chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        output_path = self.vault_path / "conversations" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')

        return f"对话已保存到: {output_path.relative_to(self.vault_path)}"


def main():
    parser = argparse.ArgumentParser(description="Obsidian AI 对话引擎")
    parser.add_argument("message", nargs="?", help="要发送的消息")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--path", "-p", default=".", help="Obsidian 路径")
    parser.add_argument("--save", "-s", action="store_true", help="保存对话")
    parser.add_argument("--clear", "-c", action="store_true", help="清除历史")

    args = parser.parse_args()

    vault_path = str(Path(args.path).resolve())
    ai = ObsidianAI(vault_path)

    if args.clear:
        ai.conversation_history = []
        print("🗑️ 对话历史已清除")
        return

    if args.interactive:
        print("=" * 60)
        print("   Obsidian AI 对话助手")
        print("   输入 'quit' 退出, 'save' 保存, 'clear' 清除历史")
        print("=" * 60)

        while True:
            try:
                message = input("\n👤 你: ").strip()
            except EOFError:
                break

            if not message:
                continue

            if message.lower() in ["quit", "q", "exit"]:
                if args.save:
                    result = ai.save_conversation()
                    print(f"\n{result}")
                print("\n👋 再见!")
                break

            if message.lower() == "save":
                result = ai.save_conversation()
                print(f"\n🤖 {result}")
                continue

            if message.lower() == "clear":
                ai.conversation_history = []
                print("\n🗑️ 历史已清除")
                continue

            print("\n🤖 思考中...")

            response = ai.chat(message)

            # 格式化输出
            print("\n" + "=" * 60)
            print("🤖 AI:")
            print("=" * 60)
            print(response)
            print()

    elif args.message:
        response = ai.chat(args.message)
        print(response)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()