#!/usr/bin/env python3
"""
政策热点自动获取脚本 V2

直接从权威新闻源获取政策/热点，不依赖大模型的实时能力

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
from typing import List, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

VAULT = Path(os.getcwd())
RAW = VAULT / "raw"
CLIPPINGS = RAW / "clippings"
RSS_CACHE = VAULT / ".claude" / "policy_cache.json"

# 权威新闻源配置
NEWS_SOURCES = [
    # 政策
    {"name": "中国政府网", "url": "https://www.gov.cn/xinwen/index.htm", "type": "policy"},
    {"name": "新华网", "url": "https://www.xinhuanet.com/tech/", "type": "tech"},
    {"name": "人民网", "url": "http://tech.people.com.cn/", "type": "tech"},
    {"name": "人民日报", "url": "https://m.hubpd.com/", "type": "tech"},

    # 科技媒体
    {"name": "36氪", "url": "https://www.36kr.com/information/AI/", "type": "tech"},
    {"name": "虎嗅", "url": "https://www.huxiu.com/", "type": "tech"},
    {"name": "钛媒体", "url": "https://www.tmtpost.com/", "type": "tech"},
    {"name": "澎湃科技", "url": "https://m.thepaper.cn/channel_25950", "type": "tech"},

    # 商业
    {"name": "网易科技", "url": "https://tech.163.com/", "type": "tech"},
    {"name": "新浪科技", "url": "https://tech.sina.com.cn/", "type": "tech"},
    {"name": "腾讯科技", "url": "https://tech.qq.com/", "type": "tech"},
    {"name": "凤凰科技", "url": "https://tech.ifeng.com/", "type": "tech"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def load_cache() -> dict:
    if RSS_CACHE.exists():
        try:
            return json.loads(RSS_CACHE.read_text())
        except:
            pass
    return {"fetched": set(), "last_fetch": None}


def save_cache(cache: dict):
    cache["fetched"] = list(cache["fetched"])
    RSS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    RSS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    cache["fetched"] = set(cache.get("fetched", []))


def extract_articles_from_page(url: str, source_name: str, max_items: int = 5) -> List[Dict]:
    """从新闻页面提取文章"""
    articles = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 移除无关标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # 查找文章链接
        seen_urls = set()
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            title = a.get_text(strip=True)

            # 过滤条件
            if not title or len(title) < 8:
                continue
            if '...' in title or '更多' in title or title in ['登录', '注册', '首页']:
                continue

            # 处理 URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                parsed = urlparse(url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"

            if not href or not href.startswith('http'):
                continue
            if href in seen_urls:
                continue
            if any(x in href.lower() for x in ['login', 'register', 'javascript', 'void', 'feedback']):
                continue

            seen_urls.add(href)
            articles.append({
                "title": title[:100],
                "url": href,
                "source": source_name
            })

            if len(articles) >= max_items:
                break

    except Exception as e:
        print(f"  ⚠️ {source_name}: {e}")

    return articles


def fetch_article_content(url: str, source: str) -> dict:
    """获取文章详细内容"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 移除无关标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        # 获取标题
        title = ""
        if soup.title:
            title = soup.title.string or ""
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)

        # 获取正文
        content = ""
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            if paragraphs:
                content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
            else:
                content = article.get_text(separator='\n', strip=True)

        if not content:
            main = soup.find('main') or soup.find('div', class_=re.compile(r'content|article|main|text', re.I))
            if main:
                ps = main.find_all('p')
                if ps:
                    content = '\n\n'.join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 20)
                else:
                    content = main.get_text(separator='\n', strip=True)

        # 清理
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        content = content[:4000]

        return {
            "title": title[:150].strip() if title else "无标题",
            "content": content,
            "url": url,
            "source": source,
            "date": datetime.now().strftime('%Y-%m-%d')
        }

    except Exception as e:
        return {"title": "", "content": "", "url": url, "source": source, "error": str(e)}


def save_to_clippings(item: dict) -> Path:
    """保存到 clippings"""
    title = item.get("title", "Untitled") or "无标题"
    content = item.get("content", "")
    url = item.get("url", "")
    source = item.get("source", "")
    date = item.get("date", datetime.now().strftime('%Y-%m-%d'))

    safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '-')[:40]
    filename = f"{date}-{source}-{safe_title}.md"

    md_content = f"""---
title: {title}
source: {url}
date: {date}
tags: [政策, 热点, {source}]
type: policy
---

# {title}

> 来源：[{source}]({url})

## 内容

{content[:3000]}

---

*自动获取于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    file_path = CLIPPINGS / filename
    file_path.write_text(md_content, encoding='utf-8')
    return file_path


def fetch_policy() -> int:
    """获取政策热点"""
    print("\n" + "=" * 50)
    print("  📰 获取政策热点")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50 + "\n")

    cache = load_cache()
    new_count = 0

    # 从多个源获取
    for source in NEWS_SOURCES:
        name = source["name"]
        url = source["url"]

        print(f"📡 {name}...")

        # 提取文章列表
        articles = extract_articles_from_page(url, name, max_items=3)

        for i, article in enumerate(articles, 1):
            article_url = article["url"]

            # 检查是否已获取
            if article_url in cache["fetched"]:
                print(f"   ⏭️  已获取: {article['title'][:30]}...")
                continue

            # 获取内容
            print(f"   [{i}/{len(articles)}] {article['title'][:35]}...")
            content = fetch_article_content(article_url, name)

            if content.get("error"):
                print(f"      ❌ {content['error']}")
                continue

            if content.get("content") and len(content.get("content", "")) > 100:
                save_to_clippings(content)
                cache["fetched"].add(article_url)
                new_count += 1
                print(f"      ✅ 已保存")
            else:
                print(f"      ⚠️ 内容太少")

            time.sleep(1)

    cache["last_fetch"] = datetime.now().isoformat()
    save_cache(cache)

    print("\n" + "=" * 50)
    print(f"  ✅ 完成：新增 {new_count} 条内容")
    print("=" * 50 + "\n")

    return new_count


def run_daily(interval_hours: int = 24):
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
    parser = argparse.ArgumentParser(description="政策热点自动获取 V2")
    parser.add_argument("--daily", action="store_true", help="每日自动获取模式")
    parser.add_argument("--interval", type=int, default=24, help="每日模式间隔（小时）")

    args = parser.parse_args()

    if args.daily:
        run_daily(args.interval)
    else:
        fetch_policy()


if __name__ == "__main__":
    main()