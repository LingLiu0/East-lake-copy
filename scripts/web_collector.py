#!/usr/bin/env python3
"""
Obsidian 网页剪藏器 - 从网上收集信息到知识库

使用场景：
- 团队成员发现有用的文章
- 把链接丢进收集箱
- 系统自动抓取、提取、生成笔记

使用方式：
    python web_collector.py add "https://example.com/article"
    python web_collector.py inbox     # 查看收集箱
    python web_collector.py process   # 处理收集箱
    python web_collector.py watch     # 监听模式
"""
import argparse
import json
import os
import re
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from urllib.parse import urlparse, urljoin
except ImportError:
    from urlparse import urlparse, urljoin


class WebCollector:
    """网页剪藏器"""

    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or os.getcwd())
        self.inbox = self.vault_path / "_inbox" / "web"  # 网页收集箱
        self.inbox.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config()
        self.state = self._load_state()

    def _load_config(self) -> dict:
        """加载配置"""
        config_path = self.vault_path / ".obsidian" / "web-collector-config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())

        return {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "timeout": 30,
            "extract_images": False,
            "category_rules": {
                "tech": {"keywords": ["tech", "技术", "代码", "programming", "dev"], "folder": "research/tech"},
                "ai": {"keywords": ["ai", "人工智能", "machine learning", "llm", "gpt"], "folder": "research/ai"},
                "product": {"keywords": ["product", "产品", "ux", "ui", "design"], "folder": "research/product"},
                "business": {"keywords": ["business", "商业", "运营", "增长"], "folder": "research/business"},
                "news": {"keywords": ["news", "新闻", "资讯"], "folder": "research/news"},
            }
        }

    def _load_state(self) -> dict:
        """加载状态"""
        state_path = self.vault_path / ".obsidian" / "web-collector-state.json"
        if state_path.exists():
            return json.loads(state_path.read_text())
        return {"collected": {}, "pending": []}

    def _save_state(self):
        """保存状态"""
        state_path = self.vault_path / ".obsidian" / "web-collector-state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(self.state, indent=2, ensure_ascii=False))

    def _compute_hash(self, url: str) -> str:
        """计算 URL 哈希"""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def add_url(self, url: str, title: str = None, tags: list = None) -> dict:
        """添加 URL 到收集箱"""
        # 验证 URL
        if not url.startswith(('http://', 'https://')):
            return {"success": False, "error": "无效的 URL"}

        url_hash = self._compute_hash(url)

        # 检查是否已收集
        if url_hash in self.state["collected"]:
            return {"success": False, "error": "URL 已收集", "existing": self.state["collected"][url_hash]}

        # 获取标题（如果未提供）
        if not title:
            title = self._fetch_title(url)
            if not title:
                title = url.split('/')[-1][:50] or "未命名"

        # 创建收集任务
        task = {
            "url": url,
            "title": title,
            "tags": tags or [],
            "added_at": datetime.now().isoformat(),
            "status": "pending",
        }

        # 保存到收集箱
        task_file = self.inbox / f"{url_hash}.json"
        task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False))

        # 更新状态
        self.state["pending"].append(url_hash)
        self._save_state()

        return {
            "success": True,
            "message": f"已添加到收集箱: {title}",
            "hash": url_hash,
        }

    def _fetch_title(self, url: str) -> Optional[str]:
        """快速获取标题"""
        if not HAS_BS4:
            return None

        try:
            headers = {"User-Agent": self.config.get("user_agent")}
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 尝试多种方式获取标题
            title = None

            # 1. og:title
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content')

            # 2. title 标签
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.string

            # 3. h1
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()[:100]

            return title[:100] if title else None

        except Exception:
            return None

    def collect_url(self, url: str) -> dict:
        """收集并处理单个 URL"""
        if not HAS_BS4:
            return {"success": False, "error": "需要安装依赖: pip install requests beautifulsoup4"}

        url_hash = self._compute_hash(url)

        # 检查是否已处理
        if url_hash in self.state["collected"]:
            return {"success": False, "error": "URL 已收集", "path": self.state["collected"][url_hash]["path"]}

        print(f"\n🌐 收集: {url}")

        try:
            # 获取网页内容
            headers = {"User-Agent": self.config.get("user_agent")}
            response = requests.get(url, headers=headers, timeout=self.config.get("timeout", 30), allow_redirects=True)
            response.encoding = response.apparent_encoding or 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取信息
            metadata = self._extract_metadata(soup, url)
            content = self._extract_content(soup, url)
            category = self._detect_category(url, metadata, content)

            # 确定目标路径
            target_dir = self.vault_path / category
            target_dir.mkdir(parents=True, exist_ok=True)

            safe_title = re.sub(r'[^\w\s-]', '', metadata["title"])
            safe_title = re.sub(r'\s+', '-', safe_title).lower()[:50]

            target_file = target_dir / f"{metadata['date']}-{safe_title}.md"

            # 处理文件名冲突
            counter = 1
            original_path = target_file
            while target_file.exists():
                target_file = target_dir / f"{metadata['date']}-{safe_title}-{counter}.md"
                counter += 1

            # 生成笔记
            note_content = self._generate_note(url, metadata, content, category)

            # 写入文件
            target_file.write_text(note_content, encoding='utf-8')
            print(f"   ✅ 已创建: {target_file.relative_to(self.vault_path)}")

            # 记录状态
            self.state["collected"][url_hash] = {
                "url": url,
                "title": metadata["title"],
                "path": str(target_file.relative_to(self.vault_path)),
                "category": category,
                "collected_at": datetime.now().isoformat(),
            }

            # 从待处理列表移除
            if url_hash in self.state["pending"]:
                self.state["pending"].remove(url_hash)

            self._save_state()

            return {
                "success": True,
                "title": metadata["title"],
                "path": str(target_file.relative_to(self.vault_path)),
                "category": category,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """提取元数据"""
        metadata = {
            "title": "",
            "description": "",
            "author": "",
            "site_name": "",
            "published_date": "",
        }

        # 标题
        og_title = soup.find('meta', property='og:title')
        if og_title:
            metadata["title"] = og_title.get('content', '')

        if not metadata["title"]:
            title_tag = soup.find('title')
            if title_tag:
                metadata["title"] = title_tag.string.strip()[:100]

        # 描述
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            metadata["description"] = og_desc.get('content', '')

        if not metadata["description"]:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                metadata["description"] = meta_desc.get('content', '')

        # 作者
        author = soup.find('meta', attrs={'name': 'author'})
        if author:
            metadata["author"] = author.get('content', '')

        # 站点名称
        og_site = soup.find('meta', property='og:site_name')
        if og_site:
            metadata["site_name"] = og_site.get('content', '')

        # 解析 URL 获取站点
        parsed = urlparse(url)
        if not metadata["site_name"]:
            metadata["site_name"] = parsed.netloc.replace('www.', '')

        metadata["url"] = url
        metadata["date"] = datetime.now().strftime('%Y-%m-%d')

        return metadata

    def _extract_content(self, soup: BeautifulSoup, url: str) -> str:
        """提取主要内容"""
        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # 尝试找主要内容区域
        main_content = None

        # 常见的内容选择器
        selectors = [
            'article',
            'main',
            '.content',
            '.post-content',
            '.article-content',
            '.entry-content',
            '#content',
            '.markdown-body',
            '.prose',
        ]

        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.body

        if not main_content:
            return ""

        # 提取文本，保留段落
        paragraphs = []
        for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
            text = p.get_text().strip()
            if text and len(text) > 20:  # 过滤短文本
                paragraphs.append(text)

        # 取前20段
        content = '\n\n'.join(paragraphs[:20])

        # 截断到适当长度
        if len(content) > 3000:
            content = content[:3000] + "\n\n... (内容已截断)"

        return content

    def _detect_category(self, url: str, metadata: dict, content: str) -> str:
        """检测分类"""
        url_lower = url.lower()
        content_lower = (metadata.get("title", "") + " " + metadata.get("description", "") + " " + content).lower()

        for category, rule in self.config.get("category_rules", {}).items():
            for keyword in rule["keywords"]:
                if keyword in url_lower or keyword in content_lower:
                    return rule["folder"]

        return "research/misc"

    def _generate_note(self, url: str, metadata: dict, content: str, category: str) -> str:
        """生成笔记内容"""
        lines = []

        # Front Matter
        lines.append("---")
        lines.append(f"title: {metadata['title']}")
        lines.append(f"tags: [web-collector, {Path(category).name}, {datetime.now().strftime('%Y-%m')}]")
        lines.append(f"created: {metadata['date']}")
        lines.append(f"updated: {datetime.now().strftime('%Y-%m-%d')}")
        if metadata.get("author"):
            lines.append(f"author: {metadata['author']}")
        lines.append(f"source: {url}")
        lines.append(f"site: {metadata.get('site_name', '')}")
        lines.append(f"category: {category}")
        lines.append("status: collected")
        lines.append("---")
        lines.append("")

        # 标题
        lines.append(f"# {metadata['title']}")
        lines.append("")

        # 信息卡片
        lines.append("> [!info] 网页剪藏")
        lines.append("> ")
        lines.append(f"> - **来源**: [{metadata.get('site_name', '网站')}]({url})")
        lines.append(f"> - **作者**: {metadata.get('author', '未知')}")
        lines.append(f"> - **日期**: {metadata['date']}")
        if metadata.get("description"):
            lines.append(f"> - **摘要**: {metadata['description'][:100]}")
        lines.append("")

        # 原文链接
        lines.append("## 🔗 原文链接")
        lines.append("")
        lines.append(f"🔗 [{metadata['title']}]({url})")
        lines.append("")

        # 内容摘要
        if content:
            lines.append("## 📝 内容摘要")
            lines.append("")
            lines.append(content)
            lines.append("")

        # 后续操作
        lines.append("---")
        lines.append("")
        lines.append("## 💡 后续操作")
        lines.append("")
        lines.append("- [ ] 阅读完整内容")
        lines.append("- [ ] 提取关键要点")
        lines.append("- [ ] 添加相关概念链接")
        lines.append("- [ ] 写上自己的思考")
        lines.append("")

        return "\n".join(lines)

    def get_inbox(self) -> list:
        """获取收集箱内容"""
        files = []

        for json_file in self.inbox.glob("*.json"):
            try:
                task = json.loads(json_file.read_text())
                files.append({
                    "hash": json_file.stem,
                    "url": task.get("url"),
                    "title": task.get("title"),
                    "added_at": task.get("added_at"),
                    "status": task.get("status"),
                })
            except:
                pass

        return sorted(files, key=lambda x: x["added_at"], reverse=True)

    def process_inbox(self) -> dict:
        """处理收集箱"""
        inbox = self.get_inbox()

        if not inbox:
            return {"success": True, "processed": 0, "message": "收集箱为空"}

        results = []
        for item in inbox:
            result = self.collect_url(item["url"])
            results.append(result)

        success_count = sum(1 for r in results if r["success"])

        return {
            "success": True,
            "processed": success_count,
            "total": len(inbox),
            "results": results,
        }

    def show_inbox(self):
        """显示收集箱"""
        inbox = self.get_inbox()

        if not inbox:
            print("\n📭 网页收集箱为空")
            print("   添加: python web_collector.py add <URL>")
            return

        print(f"\n📭 网页收集箱 ({len(inbox)} 条)")
        print("=" * 60)

        for item in inbox:
            print(f"\n🌐 {item['title'][:50]}")
            print(f"   URL: {item['url'][:60]}...")
            print(f"   添加时间: {item['added_at'][:19]}")

        print("\n" + "=" * 60)
        print("\n💡 运行 'python scripts/web_collector.py process' 处理")


def main():
    parser = argparse.ArgumentParser(
        description="Obsidian 网页剪藏器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 添加网页
  python scripts/web_collector.py add "https://example.com/article"

  # 添加并指定标签
  python scripts/web_collector.py add "https://example.com" --tags tech,ai

  # 查看收集箱
  python scripts/web_collector.py inbox

  # 处理收集箱
  python scripts/web_collector.py process
        """
    )

    parser.add_argument("command", nargs="?", help="命令")
    parser.add_argument("url", nargs="?", help="URL")
    parser.add_argument("--path", "-p", default=".", help="Obsidian 路径")
    parser.add_argument("--tags", "-t", help="标签（逗号分隔）")
    parser.add_argument("--title", help="指定标题")

    args = parser.parse_args()

    vault_path = str(Path(args.path).resolve())
    collector = WebCollector(vault_path)

    if args.command == "add":
        if not args.url:
            print("错误: 请提供 URL")
            sys.exit(1)

        tags = args.tags.split(',') if args.tags else None
        result = collector.add_url(args.url, args.title, tags)

        if result["success"]:
            print(f"\n✅ {result['message']}")
            print(f"   运行 'python scripts/web_collector.py process' 开始收集")
        else:
            print(f"\n❌ {result['error']}")

    elif args.command == "inbox":
        collector.show_inbox()

    elif args.command == "process":
        print("\n🔄 开始收集...")
        result = collector.process_inbox()
        print(f"\n✅ 完成: 收集 {result['processed']}/{result['total']} 条")

        for r in result.get("results", []):
            if r["success"]:
                print(f"   ✅ {r['title'][:50]}")
            else:
                print(f"   ❌ {r.get('error')}")

    else:
        # 默认显示收集箱
        collector.show_inbox()


if __name__ == "__main__":
    main()