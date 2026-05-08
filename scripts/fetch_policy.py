#!/usr/bin/env python3
"""
政策/热点自动获取脚本

功能：
1. 从配置的 RSS 源获取最新政策/热点
2. 自动抓取并保存到 raw/clippings/
3. 支持自定义 API 获取热点

使用：
    python3 scripts/fetch_policy.py           # 获取一次
    python3 scripts/fetch_policy.py --daily   # 每日自动获取
"""
import argparse
import os
import re
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

VAULT = Path(os.getcwd())
RAW = VAULT / "raw"
CLIPPINGS = RAW / "clippings"
RSS_CACHE = VAULT / ".claude" / "rss_cache.json"

# 默认 RSS 源（政策/科技/AI 相关）
DEFAULT_SOURCES = [
    # 中国政府网
    "http://www.gov.cn/xinwen/zhengce/index.htm",
    # 人民日报
    "https://tech.gmw.cn/node_112854.htm",
    # 36氪
    "https://www.36kr.com/information/AI/",
    # 钛媒体
    "https://www.tmtpost.com/taixuetest",
    # 澎湃新闻-科技
    "https://m.thepaper.cn/newsDetail_forward_13162085",
]

# API 配置（可选，用于获取热点）
USE_API = os.getenv("API_KEY") and os.getenv("API_BASE")
MODEL = os.getenv("MODEL", "Minimax-M2.5")


def load_cache() -> dict:
    """加载缓存"""
    if RSS_CACHE.exists():
        try:
            return json.loads(RSS_CACHE.read_text())
        except:
            pass
    return {"fetched": [], "last_fetch": None}


def save_cache(cache: dict):
    """保存缓存"""
    RSS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    RSS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def fetch_rss(url: str, max_items: int = 5) -> list:
    """获取 RSS/网页更新"""
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 尝试提取文章链接
        links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            text = a.get_text(strip=True)

            # 过滤有效链接
            if href and text and len(text) > 5:
                # 绝对 URL
                if href.startswith('http'):
                    links.append({"title": text[:100], "url": href})
                # 相对 URL
                elif href.startswith('/'):
                    parsed = urlparse(url)
                    full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                    links.append({"title": text[:100], "url": full_url})

            if len(links) >= max_items:
                break

        items = links

    except Exception as e:
        print(f"  ⚠️ 获取失败: {url} - {e}")

    return items


def fetch_with_api(prompt: str = None) -> list:
    """使用 API 获取热点"""
    if not USE_API:
        return []

    try:
        from api_client import chat

        if not prompt:
            prompt = """请列出今天（2024年）中国最重要的5条AI/科技/政策新闻，
                       每条包含：标题、URL。
                       回复格式：
                       1. 标题 - URL"""

        result = chat(prompt, max_tokens=1000)
        if not result:
            return []

        # 解析结果
        items = []
        for line in result.split('\n'):
            # 匹配 "1. 标题 - URL" 格式
            match = re.match(r'\d+\.\s*(.+?)\s*-\s*(https?://\S+)', line)
            if match:
                items.append({
                    "title": match.group(1).strip(),
                    "url": match.group(2).strip()
                })

        return items

    except Exception as e:
        print(f"  ⚠️ API 获取失败: {e}")
        return []


def fetch_article_content(url: str) -> dict:
    """获取文章内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 移除无关标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # 提取标题
        title = ""
        if soup.title:
            title = soup.title.string
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)

        # 提取正文
        content = ""
        article = soup.find('article')
        if article:
            content = article.get_text(separator='\n', strip=True)
        else:
            # 尝试获取 main 或 div.content
            main = soup.find('main') or soup.find('div', class_=re.compile('content|article'))
            if main:
                content = main.get_text(separator='\n', strip=True)

        # 截取前 3000 字符
        content = content[:3000]

        return {"title": title[:100], "content": content, "url": url}

    except Exception as e:
        return {"title": "", "content": "", "url": url, "error": str(e)}


def save_to_clippings(item: dict) -> Path:
    """保存到 clippings 目录"""
    title = item.get("title", "Untitled")
    content = item.get("content", "")
    url = item.get("url", "")

    # 生成文件名
    safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '-')[:50]
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"{date_str}-{safe_title}.md"

    # 生成 Markdown
    md_content = f"""---
title: {title}
source: {url}
date: {datetime.now().strftime('%Y-%m-%d')}
tags: [政策, 热点, 自动获取]
type: policy
---

# {title}

> 来源：[{url}]({url})

## 内容

{content[:2000]}

---

*由自动脚本获取于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    file_path = CLIPPINGS / filename
    file_path.write_text(md_content, encoding='utf-8')
    print(f"  ✅ 已保存: {filename}")

    return file_path


def fetch_policy(sources: list = None, use_api: bool = True) -> list:
    """获取政策热点"""
    print("\n" + "=" * 50)
    print("  📰 获取政策热点")
    print("=" * 50 + "\n")

    if sources is None:
        sources = DEFAULT_SOURCES

    cache = load_cache()
    new_items = []

    # 方式 1: 使用 API 获取热点（如果有配置）
    if use_api and USE_API:
        print("🔍 使用 API 获取热点...")
        api_items = fetch_with_api()
        if api_items:
            for item in api_items[:5]:
                url = item.get("url", "")
                if url and url not in cache["fetched"]:
                    print(f"  📄 获取: {item.get('title', '')[:50]}...")
                    content = fetch_article_content(url)
                    if content.get("content"):
                        save_to_clippings(content)
                        cache["fetched"].append(url)
                        new_items.append(content)
        print()

    # 方式 2: 从 RSS 源获取
    print("📡 从 RSS 源获取...")
    for source in sources[:3]:  # 限制数量
        print(f"  处理: {source[:50]}...")
        items = fetch_rss(source, max_items=3)

        for item in items:
            url = item.get("url", "")
            if url and url not in cache["fetched"]:
                # 获取内容
                content = fetch_article_content(url)
                if content.get("content"):
                    save_to_clippings(content)
                    cache["fetched"].append(url)
                    new_items.append(content)

        time.sleep(1)  # 避免请求过快

    cache["last_fetch"] = datetime.now().isoformat()
    save_cache(cache)

    print("\n" + "=" * 50)
    print(f"  ✅ 完成：获取 {len(new_items)} 条新内容")
    print("=" * 50 + "\n")

    return new_items


def run_daily(interval_hours: int = 24):
    """每日运行模式"""
    print(f"📅 每日自动获取模式，每 {interval_hours} 小时运行一次")
    print("按 Ctrl+C 退出\n")

    import time
    interval_seconds = interval_hours * 3600

    try:
        while True:
            fetch_policy()
            print(f"⏰ 下次获取: {interval_hours} 小时后\n")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n👋 已停止")


def main():
    parser = argparse.ArgumentParser(description="政策热点自动获取")
    parser.add_argument("--sources", nargs="*", help="指定 RSS 源")
    parser.add_argument("--no-api", action="store_true", help="不使用 API 获取")
    parser.add_argument("--daily", action="store_true", help="每日自动获取模式")
    parser.add_argument("--interval", type=int, default=24, help="每日模式间隔（小时）")

    args = parser.parse_args()

    if args.daily:
        run_daily(args.interval)
    else:
        fetch_policy(sources=args.sources, use_api=not args.no_api)


if __name__ == "__main__":
    main()