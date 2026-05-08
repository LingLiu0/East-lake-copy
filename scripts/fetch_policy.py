#!/usr/bin/env python3
"""
政策热点自动获取脚本

通过大模型智能获取当天权威政策/热点，不用手动指定源

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
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

VAULT = Path(os.getcwd())
RAW = VAULT / "raw"
CLIPPINGS = RAW / "clippings"
RSS_CACHE = VAULT / ".claude" / "policy_cache.json"

# API 配置
USE_API = os.getenv("API_KEY") and os.getenv("API_BASE")
MODEL = os.getenv("MODEL", "Minimax-M2.5")
API_BASE = os.getenv("API_BASE", "https://zhenze-huhehaote.cmecloud.cn")
API_KEY = os.getenv("API_KEY", "")


def load_cache() -> dict:
    """加载缓存"""
    if RSS_CACHE.exists():
        try:
            return json.loads(RSS_CACHE.read_text())
        except:
            pass
    return {"fetched": [], "last_fetch": None, "dates": {}}


def save_cache(cache: dict):
    """保存缓存"""
    RSS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    RSS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def call_api(prompt: str, max_tokens: int = 2000) -> str:
    """调用大模型 API"""
    global USE_API, API_KEY, API_BASE, MODEL

    # 检查配置
    if not USE_API:
        API_KEY = os.getenv("API_KEY", "")
        API_BASE = os.getenv("API_BASE", "https://zhenze-huhehaote.cmecloud.cn")
        MODEL = os.getenv("MODEL", "Minimax-M2.5")
        if API_KEY:
            USE_API = True

    if not USE_API or not API_KEY:
        print("  ⚠️ 未配置 API_KEY/API_BASE")
        return ""

    # 使用 requests 调用自定义 API
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "你是一个专业的政策分析师，擅长获取最新政策信息。请直接回答，不要有思考过程。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens
        }

        resp = requests.post(
            f"{API_BASE}/api/coding/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if resp.status_code == 200:
            result = resp.json()
            content = ""

            if "choices" in result and len(result["choices"]) > 0:
                msg = result["choices"][0].get("message", {})
                content = msg.get("content", "")

                # 清理 reasoning 内容（如果有）
                if "reasoning_content" in msg:
                    # 只取 content 部分
                    pass

            if content:
                return content.strip()
            else:
                print(f"  ⚠️ API 返回内容为空")

        else:
            print(f"  ⚠️ API 返回状态: {resp.status_code}")

    except Exception as e:
        print(f"  ⚠️ API 调用失败: {e}")

    return ""


def get_policy_from_api() -> List[Dict]:
    """通过大模型获取当天热点政策"""
    today = datetime.now().strftime("%Y年%m月%d日")

    prompt = f"""今天是{today}。请列出今天中国最重要的10条政策/科技/AI/商业新闻。

格式要求（每行一条）：
标题 | 完整URL

权威来源包括：国务院、发改委、工信部、网信办、新华社、人民日报、央视新闻、36氪、虎嗅、澎湃新闻、网易科技、新浪科技、腾讯科技等。

直接输出10条，不要其他内容，每行格式必须是：标题 | URL"""

    print("  🤖 通过大模型获取热点政策...")

    result = call_api(prompt, max_tokens=1500)

    if not result:
        print("  ⚠️ API 返回为空，尝试备用方案")
        return get_fallback_list()

    # 解析结果
    items = []

    for line in result.split('\n'):
        line = line.strip()
        if not line:
            continue

        # 去除序号
        line = re.sub(r'^\d+[\.\、]\s*', '', line)

        # 匹配格式: 标题 | URL
        parts = line.split('|')
        if len(parts) >= 2:
            title = parts[0].strip()
            url = parts[1].strip()

            # 验证 URL
            if not url.startswith('http'):
                continue
            if 'example' in url.lower() or 'xxx' in url.lower():
                continue

            items.append({"title": title, "url": url})
            continue

        # 如果没有 | 符号，可能是格式问题，尝试修复
        if 'http' in line:
            url_match = re.search(r'(https?://[^\s]+)', line)
            if url_match:
                url = url_match.group(1)
                title = line.replace(url, '').strip()
                if title and len(title) > 5:
                    items.append({"title": title, "url": url})

    # 如果解析失败，使用备用
    if not items:
        print("  ⚠️ 解析失败，使用备用方案")
        return get_fallback_list()

    print(f"  ✅ 获取到 {len(items)} 条热点")
    return items


def get_fallback_list() -> List[Dict]:
    """备用：获取固定政策源列表"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 当 API 不可用时的备用策略 - 使用已知可用的URL
    fallback_sources = [
        {"title": "36氪 - AI频道", "url": "https://www.36kr.com/information/AI/"},
        {"title": "虎嗅网", "url": "https://www.huxiu.com/"},
        {"title": "钛媒体", "url": "https://www.tmtpost.com/"},
        {"title": "网易科技", "url": "https://tech.163.com/"},
        {"title": "新浪科技", "url": "https://tech.sina.com.cn/"},
        {"title": "腾讯科技", "url": "https://tech.qq.com/"},
    ]

    print("  ⚠️ 使用备用源列表（API 不可用）")
    return fallback_sources


def fetch_article_content(url: str) -> dict:
    """获取文章内容"""
    # 跳过无效 URL
    if not url or url == "无URL" or "example" in url.lower():
        return {"title": "", "content": "", "url": url, "error": "无效URL"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()

        # 检测编码
        resp.encoding = resp.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 移除无关标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        # 提取标题
        title = ""
        if soup.title:
            title = soup.title.string or ""

        # 尝试多种方式获取标题
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)

        # 获取 article 或 main
        content = ""
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            if paragraphs:
                content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
            else:
                content = article.get_text(separator='\n', strip=True)

        if not content:
            main = soup.find('main') or soup.find('div', class_=re.compile(r'content|article|main', re.I))
            if main:
                content = main.get_text(separator='\n', strip=True)

        # 清理内容
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content[:4000]  # 限制长度

        # 提取日期
        date_match = re.search(r'(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})', resp.text)
        date_str = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}" if date_match else datetime.now().strftime('%Y-%m-%d')

        return {
            "title": title[:150].strip() if title else "无标题",
            "content": content,
            "url": url,
            "date": date_str
        }

    except Exception as e:
        return {"title": "", "content": "", "url": url, "error": str(e)}


def save_to_clippings(item: dict) -> Path:
    """保存到 clippings 目录"""
    title = item.get("title", "Untitled") or "无标题"
    content = item.get("content", "")
    url = item.get("url", "")
    date = item.get("date", datetime.now().strftime('%Y-%m-%d'))

    # 生成文件名
    safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '-')[:40]
    filename = f"{date}-政策-{safe_title}.md"

    # 生成 Markdown
    md_content = f"""---
title: {title}
source: {url}
date: {date}
tags: [政策, 热点, 自动获取]
type: policy
---

# {title}

> 来源：[{url}]({url})

## 内容

{content[:3000]}

---

*由自动脚本获取于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    file_path = CLIPPINGS / filename
    file_path.write_text(md_content, encoding='utf-8')

    return file_path


def fetch_policy() -> int:
    """获取政策热点"""
    print("\n" + "=" * 50)
    print("  📰 获取今日政策热点")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50 + "\n")

    cache = load_cache()
    today = datetime.now().strftime('%Y-%m-%d')

    # 检查今天是否已获取
    if cache.get("dates", {}).get(today, False):
        print(f"  ⏭️  今天已获取，跳过")
        return 0

    # 获取热点列表
    if USE_API:
        items = get_policy_from_api()
    else:
        items = get_fallback_list()

    if not items:
        print("  ❌ 未能获取到任何热点")
        return 0

    new_count = 0
    errors = []

    for i, item in enumerate(items[:8], 1):  # 限制数量
        url = item.get("url", "")
        title = item.get("title", "")

        if not url or not url.startswith('http'):
            print(f"  ⏭️  跳过: {title[:30]}... (无效URL)")
            continue

        # 检查是否已获取
        if url in cache.get("fetched", []):
            print(f"  ⏭️  已获取: {title[:30]}...")
            continue

        print(f"  [{i}/{len(items)}] 获取: {title[:40]}...")

        # 获取内容
        content = fetch_article_content(url)

        if content.get("error"):
            errors.append(f"{title[:20]}: {content['error']}")
            print(f"      ❌ {content['error']}")
            continue

        if content.get("content"):
            save_to_clippings(content)
            cache["fetched"].append(url)
            new_count += 1
            print(f"      ✅ 已保存")
        else:
            errors.append(f"{title[:20]}: 无内容")
            print(f"      ⚠️ 无内容")

        time.sleep(1.5)  # 避免请求过快

    # 更新缓存
    if "dates" not in cache:
        cache["dates"] = {}
    cache["dates"][today] = True
    cache["last_fetch"] = datetime.now().isoformat()
    save_cache(cache)

    print("\n" + "=" * 50)
    print(f"  ✅ 完成：新增 {new_count} 条内容")

    if errors:
        print(f"  ⚠️  错误: {len(errors)} 条")
        for e in errors[:3]:
            print(f"      - {e[:50]}")

    print("=" * 50 + "\n")

    return new_count


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
    parser.add_argument("--no-api", action="store_true", help="不使用 API")
    parser.add_argument("--daily", action="store_true", help="每日自动获取模式")
    parser.add_argument("--interval", type=int, default=24, help="每日模式间隔（小时）")

    args = parser.parse_args()

    if args.daily:
        run_daily(args.interval)
    else:
        fetch_policy()


if __name__ == "__main__":
    main()