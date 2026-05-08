#!/usr/bin/env python3
"""
政策热点精准获取脚本 V4

每天只获取重点政策，汇总成一个文件

重点领域：
- 数字经济、制造业、人工智能、数字政府、数字要素、卫星互联网（新质领域）
- 湖北省重点政策、支点建设
- 中央重大会议、规划（如中央经济工作会议、"十五五"规划等）

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
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

VAULT = Path(os.getcwd())
RAW = VAULT / "raw"
CLIPPINGS = RAW / "clippings"
CACHE_FILE = VAULT / ".claude" / "policy_cache.json"

# API 配置（可选，用于智能筛选）
API_KEY = os.getenv("API_KEY", "")
API_BASE = os.getenv("API_BASE", "https://zhenze-huhehaote.cmecloud.cn")
MODEL = os.getenv("MODEL", "Minimax-M2.5")

USE_API = bool(API_KEY and API_BASE)

# 重点政策源（政策类）
POLICY_SOURCES = [
    {"name": "中国政府网", "url": "https://www.gov.cn/zhengce/index.htm", "type": "政策"},
    {"name": "国务院公报", "url": "http://www.gov.cn/zhengce/gongbao/index.htm", "type": "政策"},
    {"name": "发改委", "url": "https://www.ndrc.gov.cn/xwzx/gnxw/", "type": "政策"},
    {"name": "工信部", "url": "https://www.miit.gov.cn/gxsj/tjfx/dzxx/", "type": "政策"},
    {"name": "网信办", "url": "http://www.cac.gov.cn/", "type": "政策"},
    {"name": "科技部", "url": "https://www.most.gov.cn/kjbg/index.htm", "type": "政策"},
    {"name": "商务部", "url": "http://www.mofcom.gov.cn/xwfb/rcxwfb/", "type": "政策"},
    {"name": "财政部", "url": "http://www.mof.gov.cn/zhengwugongkai/", "type": "政策"},
]

# 湖北政策源
HUBEI_SOURCES = [
    {"name": "湖北省政府", "url": "http://www.hubei.gov.cn/xw/zt/zt2020/", "type": "湖北"},
    {"name": "荆楚网", "url": "https://www.cnhubei.com/", "type": "湖北"},
    {"name": "长江云", "url": "https://www.hbtv.com.cn/", "type": "湖北"},
]

# 科技/新质生产力源（仅用于补充，不作为主要来源）
TECH_SOURCES = [
    {"name": "36氪", "url": "https://www.36kr.com/information/AI/", "type": "科技"},
]

# 重大会议/规划关键词（必须包含其一）
MAJOR_KEYWORDS = [
    "中央经济工作会议", "中央农村工作会议", "中央一号文件", "十五五", "十四五",
    "国务院常务会议", "国务院全体会议", "中央深改委", "中央财经委",
    "中央政治局", "中央委员会", "全国两会", "全国人大", "全国政协",
    "总书记", "国务院", "国务院印发", "国务院办公厅", "中共中央", "中共中央办公厅",
]

# 新质领域关键词（需同时包含新质领域关键词）
NEW_QUALITY_KEYWORDS = [
    "数字经济", "人工智能", "大模型", "智能制造", "制造业", "新质生产力",
    "数字政府", "数据要素", "数据资产", "卫星互联网", "商业航天",
    "低空经济", "量子计算", "脑机接口", "具身智能", "AI+", "人形机器人",
    "集成电路", "半导体", "芯片", "新能源汽车", "锂电池", "光伏", "储能",
    "工业互联网", "智能网联", "车路云", "自动驾驶", "算力", "大模型",
]

# 湖北重点关键词
HUBEI_KEYWORDS = [
    "湖北", "武汉", "支点", "先行区", "都市圈", "光谷",
    "湖北省", "省委书记", "省长", "王蒙徽", "王忠林",
    "中部崛起", "武汉新城", "东湖新区", "鄂州", "黄石", "宜昌", "襄阳",
]

# 排除的非重点新闻
EXCLUDE_KEYWORDS = [
    '招聘', '求职', '公示', '考试', '成绩', '分数线', '录取',
    '天气', '天气预报', '暴雨', '高温', '寒潮', '台风',
    '景区', '门票', '放假', '调休', '五一', '国庆', '春节', '清明', '端午',
    '晚会', '演唱会', '比赛', '赛事', '冠军', '世界杯', '奥运',
    '交通事故', '车祸', '火灾', '爆炸', '诈骗',
    '养生', "健康", "饮食", "减肥",
    '观光', '列车', '地铁', '行李箱', '龙虾', '博览会', '热搜',
    '投诉', '维权', '曝光',
    '运营亮点', '传播亮点', '三文鱼', '货轮', '海事',
    '客户端小程序', '举报中心', '委员会',
    '高考', '考点', '分数线', '填报', '招生',
    '公交', '司机', '帮扶', '老人',
    '微公交', '居民',
    '学会', '协会', '获评', '先进',
    '足球联赛', '直播', '夜现场', '视听狂欢',
    '创业', '同济医院', '医院',
    '工匠', '原创音乐剧', '村舞', '按摩', '跨境电商',
    '文旅', '知识产权', '专利', '判赔',
    '体育', '大赛', '舞蹈',
    '老里分', '出圈',
    '社保卡', '儿童', '头像',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def load_cache() -> dict:
    """加载缓存"""
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text())
            # 确保 fetched_urls 是集合
            if isinstance(data.get("fetched_urls"), list):
                data["fetched_urls"] = set(data["fetched_urls"])
            return data
        except Exception:
            pass
    return {"fetched_urls": set(), "last_dates": []}


def save_cache(cache: dict):
    """保存缓存"""
    # 将集合转换为列表以便 JSON 序列化
    data = {
        "fetched_urls": list(cache.get("fetched_urls", [])),
        "last_dates": cache.get("last_dates", [])
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    # 恢复为集合
    cache["fetched_urls"] = set(data["fetched_urls"])


def is_major_policy(title: str) -> bool:
    """判断是否重大政策"""
    for kw in MAJOR_KEYWORDS:
        if kw in title:
            return True
    return False


def is_new_quality_policy(title: str) -> bool:
    """判断是否新质领域政策"""
    for kw in NEW_QUALITY_KEYWORDS:
        if kw in title:
            return True
    return False


def is_hubei_policy(title: str) -> bool:
    """判断是否湖北政策"""
    for kw in HUBEI_KEYWORDS:
        if kw in title:
            return True
    return False


def should_include(title: str) -> Tuple[bool, str]:
    """
    判断文章是否应该包含在简报中
    返回: (是否包含, 分类)
    """
    title_clean = title.strip()

    # 排除非重点
    for exc in EXCLUDE_KEYWORDS:
        if exc in title_clean:
            return False, ""

    # 重大政策优先
    if is_major_policy(title_clean):
        return True, "重大政策"

    # 新质领域
    if is_new_quality_policy(title_clean):
        return True, "新质领域"

    # 湖北省委书记/省长关于重点领域的提法（特殊处理）
    leader_keywords = ["王忠林", "王蒙徽"]
    for leader in leader_keywords:
        if leader in title_clean:
            # 如果是省委书记/省长提及重点领域，保留
            for nq in NEW_QUALITY_KEYWORDS:
                if nq in title_clean:
                    return True, "湖北动态"
            # 如果只是省委书记/省长的普通活动，需要更严格的筛选
            # 保留关于支点建设、经济发展、重大项目的内容
            important_hubei = ["支点", "先行区", "都市圈", "经济", "发展", "建设", "项目", "产业", "投资"]
            for imp in important_hubei:
                if imp in title_clean:
                    return True, "湖北动态"
            # 其他省委书记/省长的一般性活动不保留
            return False, ""

    # 湖北重点
    if is_hubei_policy(title_clean):
        return True, "湖北动态"

    return False, ""


def extract_articles(url: str, source_name: str, max_items: int = 15) -> List[Dict]:
    """提取文章"""
    articles = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 移除干扰元素
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        seen = set()
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            title = a.get_text(strip=True)

            if not title or len(title) < 8:
                continue

            # 处理 URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                parsed = urlparse(url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"

            if not href or not href.startswith('http'):
                continue
            if href in seen:
                continue
            if any(x in href.lower() for x in ['login', 'register', 'javascript', 'logout']):
                continue

            seen.add(href)

            # 筛选
            include, category = should_include(title)
            if include:
                articles.append({
                    "title": title[:150],
                    "url": href,
                    "source": source_name,
                    "category": category
                })

            if len(articles) >= max_items:
                break

    except Exception as e:
        print(f"  ⚠️ {source_name}: {e}")

    return articles


def fetch_content(url: str, source: str) -> dict:
    """获取文章内容"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(resp.text, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        # 标题
        title = ""
        if soup.title:
            title = soup.title.string or ""
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)

        # 正文 - 尝试多种选择器
        content = ""
        article = soup.find('article')
        if article:
            ps = article.find_all('p')
            if ps:
                content = '\n\n'.join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 20)

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
        content = content[:4000]  # 限制长度

        return {
            "title": title[:150].strip() if title else "无标题",
            "content": content,
            "url": url,
            "source": source
        }

    except Exception as e:
        return {"title": "", "content": "", "url": url, "source": source, "error": str(e)}


def generate_summary_markdown(articles: List[dict], date: str = None) -> str:
    """生成简报 Markdown"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 按分类整理
    major = [a for a in articles if a.get('category') == '重大政策']
    new_quality = [a for a in articles if a.get('category') == '新质领域']
    hubei = [a for a in articles if a.get('category') == '湖北动态']

    lines = [
        f"# 政策简报 {date}",
        "",
        "> 重点关注：中央重大会议、规划，新质生产力领域，湖北省重点政策",
        "",
        "---",
        "",
    ]

    # 重大政策
    if major:
        lines.append("## 重大政策")
        lines.append("")
        for a in major[:8]:
            lines.append(f"- **{a['title']}**")
            lines.append(f"  - 来源: {a['source']}")
            lines.append(f"  - [原文]({a['url']})")
            lines.append("")

    # 新质领域
    if new_quality:
        lines.append("## 新质生产力")
        lines.append("")
        for a in new_quality[:8]:
            lines.append(f"- **{a['title']}**")
            lines.append(f"  - 来源: {a['source']}")
            lines.append(f"  - [原文]({a['url']})")
            lines.append("")

    # 湖北动态
    if hubei:
        lines.append("## 湖北动态")
        lines.append("")
        for a in hubei[:8]:
            lines.append(f"- **{a['title']}**")
            lines.append(f"  - 来源: {a['source']}")
            lines.append(f"  - [原文]({a['url']})")
            lines.append("")

    # 底部
    lines.append("---")
    lines.append("")
    lines.append(f"*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return '\n'.join(lines)


def summarize_with_api(articles: List[dict], date: str = None) -> str:
    """使用 API 汇总重点政策"""
    if not USE_API or not articles:
        return ""

    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 构建摘要
    article_list = []
    for i, a in enumerate(articles[:15], 1):
        category = a.get('category', '其他')
        article_list.append(f"{i}. [{a['title']}]({a['url']}) [{category}] - 来源: {a.get('source', '未知')}")

    prompt = f"""请根据以下{date}获取的新闻，提炼重点政策简报。

要求：
1. 只保留重点政策（中央重大决策、部委重要政策、湖北省委省政府重点政策）
2. 过滤掉一般性新闻、流水账、民生类新闻
3. 格式示例：

# 政策简报 {date}

## 重大政策
[筛选后的重大政策，如中央会议、国务院文件等]

## 新质生产力
[数字经济、人工智能、卫星互联网、商业航天等领域的政策]

## 湖北动态
[湖北省相关重点政策，特别是省委书记、省长的讲话和部署]

---

今天获取的新闻：
{chr(10).join(article_list)}

请直接生成简报内容，只输出markdown格式，不要其他说明："""

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "你是政策分析师，擅长提炼政策要点。回复必须是真实的政策内容，不能编造。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,  # 降低温度，减少幻觉
            "max_tokens": 3000
        }

        resp = requests.post(
            f"{API_BASE}/api/coding/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )

        if resp.status_code == 200:
            result = resp.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"].get("content", "")
                if content:
                    # 修复日期
                    content = re.sub(r'# 政策简报 \d{4}-\d{2}-\d{2}', f'# 政策简报 {date}', content)
                    return content.strip()

    except Exception as e:
        print(f"  ⚠️ API 汇总失败: {e}")

    return ""


def fetch_policy(date: str = None) -> int:
    """获取政策热点"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 验证日期格式
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        print(f"  ⚠️ 日期格式错误，请使用 YYYY-MM-DD 格式")
        return 0

    print("\n" + "=" * 50)
    print("  📰 获取重点政策")
    print(f"  时间: {date} {datetime.now().strftime('%H:%M')}")
    print("=" * 50 + "\n")

    cache = load_cache()

    # 检查指定日期是否已获取
    if date in cache.get("last_dates", []):
        print(f"  ⏭️  {date} 已获取，跳过")
        return 0

    all_articles = []

    # 1. 获取政策源
    print("📜 获取政策源...")
    for source in POLICY_SOURCES:
        print(f"  📡 {source['name']}...")
        articles = extract_articles(source["url"], source["name"], max_items=10)

        for a in articles:
            if a["url"] not in cache["fetched_urls"]:
                print(f"    ✓ {a['title'][:45]}...")
                all_articles.append(a)
                cache["fetched_urls"].add(a["url"])

        time.sleep(0.8)

    # 2. 获取湖北源
    print("\n🦅 获取湖北政策...")
    for source in HUBEI_SOURCES:
        print(f"  📡 {source['name']}...")
        articles = extract_articles(source["url"], source["name"], max_items=10)

        for a in articles:
            if a["url"] not in cache["fetched_urls"]:
                print(f"    ✓ {a['title'][:45]}...")
                all_articles.append(a)
                cache["fetched_urls"].add(a["url"])

        time.sleep(0.8)

    # 3. 获取科技源（补充）
    print("\n🚀 补充获取新质领域...")
    for source in TECH_SOURCES:
        print(f"  📡 {source['name']}...")
        articles = extract_articles(source["url"], source["name"], max_items=5)

        for a in articles:
            if a["url"] not in cache["fetched_urls"]:
                print(f"    ✓ {a['title'][:45]}...")
                all_articles.append(a)
                cache["fetched_urls"].add(a["url"])

        time.sleep(0.8)

    if not all_articles:
        print("\n  ⚠️ 未获取到重点政策")
        return 0

    # 4. 去重并按分类整理
    seen = set()
    unique_articles = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique_articles.append(a)

    print(f"\n📊 共获取 {len(unique_articles)} 条政策")

    # 5. 获取详细内容（可选，减少 API 调用）
    articles_with_content = unique_articles[:12]

    # 6. 生成简报
    print("\n📝 生成政策简报...")

    # 优先使用 API 汇总
    summary = ""
    if USE_API and articles_with_content:
        summary = summarize_with_api(articles_with_content, today)

    if not summary:
        summary = generate_summary_markdown(unique_articles, today)

    # 7. 保存
    summary_file = CLIPPINGS / f"{today}-政策简报.md"
    summary_file.write_text(summary, encoding='utf-8')
    print(f"  ✅ 已保存: {summary_file.name}")

    # 更新缓存
    cache["last_dates"] = [today]  # 只保留今天
    save_cache(cache)

    print("\n" + "=" * 50)
    print(f"  ✅ 完成：获取 {len(unique_articles)} 条重点政策")
    print("=" * 50 + "\n")

    return len(unique_articles)


def run_daily(interval_hours: int = 24):
    print(f"📅 每日自动获取模式，每 {interval_hours} 小时运行一次")
    print("按 Ctrl+C 退出\n")

    interval_seconds = interval_hours * 3600

    try:
        while True:
            fetch_policy()
            print(f"⏰ 下次获取: {interval_hours} 小时后\n")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n👋 已停止")


def main():
    parser = argparse.ArgumentParser(description="重点政策获取 V4")
    parser.add_argument("--daily", action="store_true", help="每日自动获取模式")
    parser.add_argument("--interval", type=int, default=24, help="每日模式间隔（小时）")
    parser.add_argument("--date", type=str, help="指定日期 (YYYY-MM-DD)，默认为今天")

    args = parser.parse_args()

    if args.daily:
        run_daily(args.interval)
    else:
        fetch_policy(args.date)


if __name__ == "__main__":
    main()