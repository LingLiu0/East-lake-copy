#!/usr/bin/env python3
"""
政策热点精准获取脚本 V5

设计原则：
1. 直接抓取政策正文，而非列表页标题
2. 采集完整的政策信息：标题、来源、正文要点、发布日期
3. 重点关注：中央重大会议、规划，新质领域，湖北省

使用方法：
    python3 scripts/fetch_policy.py           # 获取今天
    python3 scripts/fetch_policy.py --daily   # 每日自动
    python3 scripts/fetch_policy.py --date 2026-05-07  # 指定日期
"""
import argparse
import os
import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

VAULT = Path(os.getcwd())
RAW = VAULT / "raw"
CLIPPINGS = RAW / "clippings"
TEMPLATES = VAULT / "templates"    # AI生成物模板
CACHE_FILE = VAULT / ".claude" / "policy_cache.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ============================================================
# 政策源配置 - 直接配置政策详情页URL，而非列表页
# ============================================================

# 中央政策源 - 权威政策发布页
CENTRAL_SOURCES = [
    {
        "name": "中国政府网-政策",
        "base_url": "https://www.gov.cn",
        "list_url": "https://www.gov.cn/zhengce/index.htm",
        "type": "中央",
    },
    {
        "name": "中国政府网-要闻",
        "base_url": "https://www.gov.cn",
        "list_url": "https://www.gov.cn/xinwen/yaowen/index.htm",
        "type": "中央",
    },
    {
        "name": "国家网信办",
        "base_url": "https://www.cac.gov.cn",
        "list_url": "https://www.cac.gov.cn/",
        "type": "中央",
    },
    {
        "name": "新华社-时政",
        "base_url": "https://www.xinhuanet.com",
        "list_url": "https://www.xinhuanet.com/politics/",
        "type": "中央",
    },
    {
        "name": "人民日报-要闻",
        "base_url": "https://paper.people.com.cn",
        "list_url": "https://paper.people.com.cn/nmb/node_20210825_2.htm",
        "type": "中央",
    },
]

# 湖北政策源
HUBEI_SOURCES = [
    {
        "name": "湖北省政府",
        "base_url": "http://www.hubei.gov.cn",
        "list_url": "http://www.hubei.gov.cn/xw/tt/",
        "type": "湖北",
    },
    {
        "name": "荆楚网-首页",
        "base_url": "https://www.cnhubei.com",
        "list_url": "https://www.cnhubei.com/",
        "type": "湖北",
    },
    {
        "name": "长江云-首页",
        "base_url": "https://www.hbtv.com.cn",
        "list_url": "https://www.hbtv.com.cn/",
        "type": "湖北",
    },
]

# 科技/新质生产力源 - 只保留政府/权威网站
TECH_SOURCES = [
    # {
    #     "name": "36氪-AI",
    #     "base_url": "https://www.36kr.com",
    #     "list_url": "https://www.36kr.com/information/AI/",
    #     "type": "科技",
    # },
]

# ============================================================
# 湖北移动视角 - 重点关注与发展相关的政策
# ============================================================

# 必须保留的关键词组合
# 湖北 + 发展相关
HUBEI_GROWTH_KEYWORDS = [
    "湖北", "武汉", "支点", "先行区", "都市圈", "光谷",
    "王蒙徽", "王忠林", "中部崛起", "武汉新城", "鄂州",
    "数字经济", "人工智能", "5G", "通信", "信息化", "数字化",
    "智能制造", "工业互联网", "车联网", "智慧城市",
    "新基建", "算力", "数据中心", "云计算",
    "科技创新", "成果转化", "产学研", "高新区的",
    "招商", "投资", "项目", "产业", "经济",
]

# 中央重大政策 - 只保留与新质/数字化相关的
CENTRAL_GROWTH_KEYWORDS = [
    "数字经济", "人工智能", "大模型", "智能制造", "制造业",
    "数字政府", "数据要素", "数据资产", "卫星互联网", "商业航天",
    "低空经济", "量子计算", "算力", "芯片", "集成电路",
    "新质生产力", "新型工业化", "智能体", "AI", "Agent",
    "国务院办公厅", "国务院印发", "中共中央办公厅",
    "发改委", "工信部", "科技部", "网信办", "国家网信办",
    "6G", "第六代", "移动通信", "5G", "通信技术",
    "清洁能源", "能源双向赋能", "算力设施",
]

# 排除词 - 非发展相关的新闻（更严格）
EXCLUDE_KEYWORDS = [
    # 招聘/求职
    '招聘', '求职', '招录', '应聘', '高薪',
    # 天气/自然灾害
    '天气', '暴雨', '高温', '寒潮', '台风', '地震',
    # 民生/娱乐
    '景区', '门票', '放假', '调休', '晚会', '演唱会',
    '比赛', '赛事', '世界杯', '奥运',
    # 教育考试
    '考试', '成绩', '分数线', '录取', '高考', '考点',
    # 事故/灾害
    '车祸', '火灾', '爆炸', '诈骗', '事故',
    # 个人/荣誉（非发展相关）
    '公示', '拟推荐', '获得者', '获奖', '表彰', '评选',
    '十佳新闻工作者', '最美', '模范',
    # 民生通知
    '投诉', '维权', '调整', '通知',
    # 交通出行
    '观光', '列车', '地铁', '公交', '航班',
    # 商业活动
    '博览会', '展销会', '龙虾节', '美食',
    # 省份名（非湖北）- 只保留中央政策
    '吉林', '浙江', '广东', '江苏', '山东', '四川', '河南', '安徽', '上海', '北京',
    # 热搜/流量类
    '热搜', '上热搜', '人海', '行李箱', '暖心', '感人',
    '总书记的关切', '落地的回响',
    # 机构（非政策）
    '举报中心', '办公室', '委员会', '协会', '学会',
    # 技能大赛/一般性会议
    '技能大赛', '世界技能', '展演', '演出',
    # 新闻类标题（不需要）
    '答记者问', '一图读懂', '专家解读', '解读',
    '发布会', '新闻联播', '快讯', '日报', '周报',
]


@dataclass
class PolicyItem:
    """政策条目"""
    title: str
    url: str
    source: str
    category: str
    date: str = ""
    content: str = ""


def load_cache() -> dict:
    """加载缓存"""
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text())
            if isinstance(data.get("fetched_urls"), list):
                data["fetched_urls"] = set(data["fetched_urls"])
            return data
        except Exception:
            pass
    return {"fetched_urls": set(), "last_dates": []}


def save_cache(cache: dict):
    """保存缓存"""
    data = {
        "fetched_urls": list(cache.get("fetched_urls", [])),
        "last_dates": cache.get("last_dates", [])
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    cache["fetched_urls"] = set(data["fetched_urls"])


def is_relevant_policy(title: str) -> Tuple[bool, str]:
    """判断是否相关政策 - 湖北移动视角"""
    title_clean = title.strip()

    # 0. 首先检查排除词（最优先）
    for exc in EXCLUDE_KEYWORDS:
        if exc in title_clean:
            return False, ""

    # 1. 中央重大政策（新质/数字化相关）- 优先判断
    for kw in CENTRAL_GROWTH_KEYWORDS:
        if kw in title_clean:
            # 排除其他省份
            for prov in ['吉林', '浙江', '广东', '江苏', '山东', '四川', '河南', '安徽']:
                if prov in title_clean:
                    return False, ""
            return True, "重大政策"

    # 2. 湖北 + 发展相关
    for kw in HUBEI_GROWTH_KEYWORDS:
        if kw in title_clean:
            return True, "湖北动态"

    # 不符合条件
    return False, ""


def normalize_url(href: str, base_url: str) -> str:
    """规范化URL"""
    if not href:
        return ""
    if href.startswith('//'):
        return 'https:' + href
    elif href.startswith('/'):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{href}"
    elif href.startswith('http'):
        return href
    return ""


def extract_policy_links(url: str, source_name: str, base_url: str, max_items: int = 15) -> List[PolicyItem]:
    """从列表页提取政策链接"""
    items = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 移除干扰
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        seen = set()

        # 查找所有链接
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            title = a.get_text(strip=True)

            # 过滤标题
            if not title or len(title) < 8:
                continue

            # 规范化URL
            full_url = normalize_url(href, base_url)
            if not full_url or not full_url.startswith('http'):
                continue
            if any(x in full_url.lower() for x in ['login', 'register', 'javascript', '#']):
                continue
            if full_url in seen:
                continue

            seen.add(full_url)

            # 筛选相关政策
            include, category = is_relevant_policy(title)
            if include:
                items.append(PolicyItem(
                    title=title[:150],
                    url=full_url,
                    source=source_name,
                    category=category
                ))

            if len(items) >= max_items:
                break

    except Exception as e:
        print(f"  ⚠️ {source_name}: {e}")

    return items


def extract_content(url: str, source: str) -> Optional[PolicyItem]:
    """提取政策正文内容"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 清理
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form']):
            tag.decompose()

        # 提取标题
        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)

        # 尝试其他标题选择器
        if not title:
            for selector in ['.article-title', '.news-title', '.content-title', '[class*="title"]']:
                el = soup.select_one(selector)
                if el:
                    title = el.get_text(strip=True)
                    break

        # 提取正文
        content = ""
        date = ""

        # 方法1: 查找 article
        article = soup.find('article')
        if article:
            ps = article.find_all('p')
            if ps:
                content = '\n'.join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 20)

        # 方法2: 查找主内容区 - 更多选择器
        if not content:
            selectors = [
                '.article-content', '.news-content', '.article-text', '.news-text',
                '.content', '.main-content', 'main', '#article', '#content',
                '.text', '.detail', '.article-body',
                'div[class*="content"]', 'div[class*="article"]', 'div[class*="text"]'
            ]
            for selector in selectors:
                area = soup.select_one(selector)
                if area:
                    ps = area.find_all('p')
                    if ps and len(ps) > 2:  # 确保有足够段落
                        content = '\n'.join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 15)
                        if len(content) > 100:
                            break

        # 方法3: 直接查找所有段落，取最长的
        if not content:
            all_ps = soup.find_all('p')
            if all_ps:
                valid_ps = [p.get_text(strip=True) for p in all_ps if len(p.get_text(strip=True)) > 30]
                if valid_ps:
                    content = '\n'.join(valid_ps[:20])  # 最多20段

        # 提取日期 - 优先从 meta 标签和特定元素提取
        date = ""

        # 方法1: 从 meta 标签提取（最可靠）
        date_meta = (
            soup.find('meta', attrs={'name': 'publishdate'}) or
            soup.find('meta', attrs={'name': 'pubdate'}) or
            soup.find('meta', attrs={'property': 'article:published_time'}) or
            soup.find('meta', attrs={'name': 'date'}) or
            soup.find('meta', attrs={'name': 'datetime'})
        )
        if date_meta and date_meta.get('content'):
            content_val = date_meta.get('content', '')
            # 处理各种格式
            match = re.search(r'(\d{4}-\d{2}-\d{2})', content_val)
            if match:
                date = match.group(1)
            else:
                # 可能是 "2026-05-07T10:00:00" 格式
                match = re.search(r'^(\d{4}-\d{2}-\d{2})', content_val)
                if match:
                    date = match.group(1)

        # 方法2: 查找常见日期元素（包括荆楚网等）
        if not date:
            for selector in [
                '.pub-date', '.publish-date', '.date', '.time',
                '.news-date', '.article-date', '.post-date',
                '[class*="date"]', '[class*="time"]', '[class*="pub"]',
                'span[class*="date"]', 'div[class*="date"]',
                'span[class*="time"]', 'div[class*="time"]',
                'trs_date',  # 荆楚网特有
            ]:
                try:
                    el = soup.select_one(selector)
                    if el:
                        text = el.get_text(strip=True)
                        # 清理异常字符
                        text = re.sub(r'[^\d\-年月日]', '', text)
                        match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})', text)
                        if match:
                            date = match.group(1).replace('年', '-').replace('月', '-').replace('/', '-')
                            # 清理多余的 -
                            date = re.sub(r'-+', '-', date)
                            break
                except:
                    pass

        # 方法3: 从URL中提取日期（如中国政府网 /202604/）
        if not date:
            url_date_match = re.search(r'/(\d{4})(\d{2})/content', url)
            if url_date_match:
                # 完整日期可能需要去详情页获取，这里先取年月
                date = f"{url_date_match.group(1)}-{url_date_match.group(2)}"

        # 方法2.5: 解析特殊格式 publishdate:2026/05/08（如国家网信办）
        if not date:
            try:
                body_text = soup.get_text()
                match = re.search(r'publishdate[：:]\s*(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})', body_text)
                if match:
                    date = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
            except:
                pass

        # 方法4: 从正文提取"新华社北京 X月X日电"格式（新闻发布日）
        text_for_date = title + content
        if not date:
            # 优先匹配 "X月X日" 格式（新闻电头）
            match = re.search(r'(\d{1,2})月(\d{1,2})日', text_for_date)
            if match:
                # 需要结合当前年份
                current_year = datetime.now().year
                date = f"{current_year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"

        # 方法5: 次选其他日期格式
        if not date:
            for pattern in [r'(\d{4}-\d{2}-\d{2})', r'(\d{4})[/年](\d{1,2})[/月](\d{1,2})']:
                match = re.search(pattern, text_for_date)
                if match:
                    date = match.group(0)
                    break

        # 验证日期合理性：如果日期比今天还晚，清空
        if date:
            try:
                parsed_date = datetime.strptime(date[:10], '%Y-%m-%d')
                if parsed_date > datetime.now():
                    date = ""  # 清除未来日期
            except:
                # 如果日期格式不完整（如只有年月），保留
                pass
                for pattern in [r'(\d{4}-\d{2}-\d{2})', r'(\d{4})[/年](\d{1,2})[/月](\d{1,2})']:
                    match = re.search(pattern, text_for_date)
                    if match:
                        date = match.group(0)
                        break

        if not title:
            return None

        # 截取内容
        if content:
            content = content[:3000]
        else:
            # 如果没有提取到正文，至少保留标题
            content = f"来源: {source}\nURL: {url}"

        # 分类
        _, category = is_relevant_policy(title)

        return PolicyItem(
            title=title[:150],
            url=url,
            source=source,
            category=category,
            date=date,
            content=content
        )

    except Exception as e:
        print(f"  ⚠️ 获取失败: {e}")
        return None


def generate_markdown(items: List[PolicyItem], date: str) -> str:
    """生成简报Markdown"""
    lines = [
        f"# 政策简报 {date}",
        "",
        "> 重点关注：中央重大会议规划、新质生产力领域、湖北省重点政策",
        "",
        "---",
        "",
    ]

    # 按分类整理
    major = [i for i in items if i.category == "重大政策"]
    tech = [i for i in items if i.category == "新质生产力"]
    hubei = [i for i in items if i.category == "湖北动态"]
    other = [i for i in items if i.category not in ["重大政策", "新质生产力", "湖北动态"]]

    # 重大政策
    if major:
        lines.append("## 一、重大政策")
        lines.append("")
        for i, item in enumerate(major[:8], 1):
            lines.append(f"### {i}. {item.title}")
            lines.append(f"- 来源: {item.source}")
            if item.date:
                lines.append(f"- 日期: {item.date}")
            if item.content:
                # 提取内容摘要
                summary = item.content[:300] + "..." if len(item.content) > 300 else item.content
                lines.append(f"- 摘要: {summary}")
            lines.append(f"- [原文]({item.url})")
            lines.append("")

    # 新质生产力
    if tech:
        lines.append("## 二、新质生产力")
        lines.append("")
        for i, item in enumerate(tech[:6], 1):
            lines.append(f"### {i}. {item.title}")
            lines.append(f"- 来源: {item.source}")
            if item.date:
                lines.append(f"- 日期: {item.date}")
            if item.content:
                summary = item.content[:300] + "..." if len(item.content) > 300 else item.content
                lines.append(f"- 摘要: {summary}")
            lines.append(f"- [原文]({item.url})")
            lines.append("")

    # 湖北动态
    if hubei:
        lines.append("## 三、湖北动态")
        lines.append("")
        for i, item in enumerate(hubei[:6], 1):
            lines.append(f"### {i}. {item.title}")
            lines.append(f"- 来源: {item.source}")
            if item.date:
                lines.append(f"- 日期: {item.date}")
            if item.content:
                summary = item.content[:300] + "..." if len(item.content) > 300 else item.content
                lines.append(f"- 摘要: {summary}")
            lines.append(f"- [原文]({item.url})")
            lines.append("")

    # 其他
    if other:
        lines.append("## 四、其他政策")
        lines.append("")
        for i, item in enumerate(other[:4], 1):
            lines.append(f"- **{item.title}** ({item.source})")
            if item.date:
                lines.append(f"  - 日期: {item.date}")
            lines.append(f"  - [原文]({item.url})")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return '\n'.join(lines)


def fetch_policy(target_date: str = None, yesterday: bool = False) -> int:
    """获取政策
    target_date: 要获取的政策发布日期，如 "2026-05-07"
    yesterday: 是否获取昨天的政策（用于定时任务）
    """
    # 如果是定时任务（yesterday=True）或者没有指定日期，默认获取昨天
    if target_date is None:
        if yesterday:
            # 获取昨天的政策
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            target_date = datetime.now().strftime('%Y-%m-%d')

    try:
        datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        print("  ⚠️ 日期格式错误，请使用 YYYY-MM-DD")
        return 0

    print("\n" + "=" * 50)
    print("  📰 政策简报获取")
    print(f"  目标日期: {target_date}")
    print("=" * 50 + "\n")

    cache = load_cache()

    # 检查指定日期是否已获取
    if target_date in cache.get("last_dates", []):
        print(f"  ⏭️  {target_date} 已获取")
        return 0

    all_items = []

    # 1. 中央政策源
    print("📜 获取中央政策...")
    for source in CENTRAL_SOURCES:
        print(f"  📡 {source['name']}...")
        items = extract_policy_links(
            source["list_url"],
            source["name"],
            source["base_url"],
            max_items=12
        )
        for item in items:
            if item.url not in cache["fetched_urls"]:
                all_items.append(item)
                cache["fetched_urls"].add(item.url)
                print(f"    ✓ {item.title[:40]}...")
        time.sleep(0.5)

    # 2. 湖北政策源
    print("\n🦅 获取湖北政策...")
    for source in HUBEI_SOURCES:
        print(f"  📡 {source['name']}...")
        items = extract_policy_links(
            source["list_url"],
            source["name"],
            source["base_url"],
            max_items=12
        )
        for item in items:
            if item.url not in cache["fetched_urls"]:
                all_items.append(item)
                cache["fetched_urls"].add(item.url)
                print(f"    ✓ {item.title[:40]}...")
        time.sleep(0.5)

    # 3. 科技/新质源
    print("\n🚀 获取新质领域...")
    for source in TECH_SOURCES:
        print(f"  📡 {source['name']}...")
        items = extract_policy_links(
            source["list_url"],
            source["name"],
            source["base_url"],
            max_items=8
        )
        for item in items:
            if item.url not in cache["fetched_urls"]:
                all_items.append(item)
                cache["fetched_urls"].add(item.url)
                print(f"    ✓ {item.title[:40]}...")
        time.sleep(0.5)

    if not all_items:
        print("\n  ⚠️ 未获取到相关政策")
        return 0

    # 去重
    seen = set()
    unique_items = []
    for item in all_items:
        if item.url not in seen:
            seen.add(item.url)
            unique_items.append(item)

    print(f"\n📊 共获取 {len(unique_items)} 条政策链接")
    print("📄 提取正文内容和日期...")

    # 获取正文内容并提取日期
    content_items = []
    target_date_only = target_date[:10]  # "2026-05-07"
    seen_titles = set()  # 用于去重

    for i, item in enumerate(unique_items[:20], 1):
        print(f"  [{i}/{min(20, len(unique_items))}] {item.title[:35]}...")
        full_item = extract_content(item.url, item.source)
        if full_item:
            # 提取日期中的年月日进行比较
            item_date = full_item.date[:10] if full_item.date else ""

            # 过滤：只保留目标日期的政策（没有日期的跳过）
            if item_date == target_date_only:
                # 提取核心标题：去掉修饰词，取《》内的政策名
                title_clean = full_item.title
                for suffix in ['答记者问', '一图读懂', '专家解读', '解读', '全文', '发布']:
                    title_clean = title_clean.replace(suffix, '')
                # 提取政策名称
                import re
                policy_name = re.search(r'《(.+?)》', title_clean)
                if policy_name:
                    core_key = policy_name.group(1)[:20]  # 政策名取前20字符
                else:
                    core_key = title_clean.strip()[:20]

                # 去重：基于政策核心名称
                url_key = full_item.url
                if url_key in seen_titles or core_key in seen_titles:
                    print(f"    ✗ 重复，跳过")
                    continue
                seen_titles.add(url_key)
                seen_titles.add(core_key)

                # 重新分类：基于实际内容，而非来源
                is_policy, category = is_relevant_policy(full_item.title)
                full_item.category = category

                content_items.append(full_item)
                print(f"    ✓ 日期匹配: {item_date}")
            elif not item_date:
                print(f"    ✗ 无日期，跳过")
            else:
                print(f"    ✗ 日期不匹配: {item_date} != {target_date_only}")
        time.sleep(0.5)

    if not content_items:
        print(f"\n  ⚠️ {target_date} 没有找到发布的政策")
        print(f"  💡 提示：网站可能还没有更新，或者日期格式提取失败")
        return 0

    # 生成简报
    print(f"\n📝 生成 {target_date} 简报...")
    markdown = generate_markdown(content_items, target_date)

    # 保存文件名使用目标日期
    output_file = CLIPPINGS / f"{target_date}-政策简报.md"
    output_file.write_text(markdown, encoding='utf-8')
    print(f"  ✅ 已保存: {output_file.name}")

    # 更新缓存
    cache["last_dates"] = [target_date]
    save_cache(cache)

    print("\n" + "=" * 50)
    print(f"  ✅ 完成：获取 {len(content_items)} 条 {target_date} 政策")
    print("=" * 50 + "\n")

    return len(content_items)


def run_daily(interval_hours: int = 24):
    """每日自动获取"""
    print(f"📅 每日自动模式，每 {interval_hours} 小时运行")
    print("按 Ctrl+C 退出\n")

    import time
    interval = interval_hours * 3600

    try:
        while True:
            fetch_policy()
            print(f"⏰ 下次运行: {interval_hours} 小时后\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 已停止")


def main():
    parser = argparse.ArgumentParser(description="政策简报获取 V5")
    parser.add_argument("--daily", action="store_true", help="每日自动模式")
    parser.add_argument("--interval", type=int, default=24, help="间隔（小时）")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--yesterday", action="store_true", help="获取昨天的政策（用于定时任务）")

    args = parser.parse_args()

    if args.daily:
        run_daily(args.interval)
    else:
        fetch_policy(args.date, yesterday=args.yesterday)


if __name__ == "__main__":
    main()