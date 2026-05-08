#!/usr/bin/env python3
"""
自动进化脚本 - 让知识库越用越聪明

功能：
1. 补全概念定义（AI 补充中 → AI 补全）
2. 将问答中的高质量答案转化为概念
3. 发现知识盲区并标注
4. 建立更强的概念关联
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

VAULT = Path(os.getcwd())
WIKI = VAULT / "wiki"
OUTPUTS = VAULT / "outputs"
CONCEPTS_DIR = WIKI / "concepts"
SUMMARIES_DIR = WIKI / "summaries"
QA_DIR = OUTPUTS / "qa"
LOG_FILE = WIKI / "indexes" / "log.md"


def get_anthropic_client():
    """获取 Anthropic 客户端"""
    # 优先使用自定义 API
    if os.getenv("API_KEY"):
        return "custom"
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        return None


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  [{timestamp}] {message}")


def read_file(file_path: Path) -> str:
    """安全读取文件"""
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="ignore")


def write_file(file_path: Path, content: str):
    """安全写入文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def update_log(action: str, detail: str):
    """更新操作日志"""
    entry = f"\n## [{datetime.now().strftime('%Y-%m-%d')}] {action}\n\n- {detail}\n"
    if LOG_FILE.exists():
        existing = read_file(LOG_FILE)
        write_file(LOG_FILE, existing + entry)
    else:
        write_file(LOG_FILE, f"# Wiki Log\n{entry}")


# ============================================================
# 功能1: 补全概念定义
# ============================================================

def complete_concept_definition(concept_file: Path, client) -> bool:
    """使用 AI 补全概念定义"""
    content = read_file(concept_file)
    concept_name = concept_file.stem

    # 查找相关的摘要内容作为上下文
    related_summaries = []
    for sf in SUMMARIES_DIR.glob("*.md"):
        sf_content = read_file(sf)
        if concept_name in sf_content or any(c in sf_content for c in concept_name.split()):
            related_summaries.append(read_file(sf)[:1500])

    if not related_summaries:
        log(f"⚠️ {concept_name}: 没有找到相关摘要")
        return False

    context = "\n\n---\n\n".join(related_summaries[:2])

    prompt = f"""你是一个知识管理专家。请根据以下资料，为概念 "{concept_name}" 补全定义。

要求：
1. 给出清晰、准确的定义（50-100字）
2. 提取3-5个关键要点
3. 保持简洁专业

参考内容：
{context}

请用中文回复，格式如下：
## 定义
[定义内容]

## 关键要点
- 要点1
- 要点2
- 要点3
"""

    try:
        # 自定义 API
        if client == "custom":
            from api_client import chat as custom_chat
            ai_content = custom_chat(prompt, max_tokens=500)
        else:
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            ai_content = resp.content[0].text

        # 替换占位符
        new_content = re.sub(
            r'## 定义\s*\n.*?\(AI 补充中\)',
            f'## 定义\n{ai_content.split("## 关键要点")[0].replace("## 定义", "").strip()}',
            content,
            flags=re.DOTALL
        )

        # 替换关键要点
        if "## 关键要点" in ai_content:
            key_points = ai_content.split("## 关键要点")[1].strip()
            new_content = re.sub(
                r'## 关键要点\s*\n.*?(?=\n##|$)',
                f'## 关键要点\n{key_points}',
                new_content,
                flags=re.DOTALL
            )

        write_file(concept_file, new_content)
        log(f"✅ {concept_name}: 已补全定义")
        return True
    except Exception as e:
        log(f"❌ {concept_name}: {e}")
        return False


def evolve_concepts():
    """进化所有待完善的概念"""
    client = get_anthropic_client()

    if not client:
        log("⚠️ 未配置 ANTHROPIC_API_KEY，跳过概念补全")
        return 0

    if not CONCEPTS_DIR.exists():
        log("⚠️ concepts/ 目录不存在")
        return 0

    # 查找所有包含 "AI 补充中" 或 "待提取" 的概念
    incomplete = []
    for cf in CONCEPTS_DIR.glob("*.md"):
        content = read_file(cf)
        if "AI 补充中" in content or "待提取" in content:
            incomplete.append(cf)

    if not incomplete:
        log("✅ 所有概念已完善")
        return 0

    log(f"🔄 开始补全 {len(incomplete)} 个概念...")

    completed = 0
    for cf in incomplete[:5]:  # 每次最多处理5个
        if complete_concept_definition(cf, client):
            completed += 1

    return completed


# ============================================================
# 功能2: 将问答转化为概念
# ============================================================

def qa_to_concept(qa_file: Path, client) -> Optional[Path]:
    """将高质量问答转化为概念"""
    content = read_file(qa_file)

    # 提取问题作为概念名
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if not title_match:
        return None

    concept_name = title_match.group(1).strip()[:30]

    # 提取 AI 回答
    ai_answer_match = re.search(r'## AI 回答\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
    if not ai_answer_match:
        return None

    ai_answer = ai_answer_match.group(1).strip()[:500]

    # 查找相关概念
    existing_concepts = [c.stem for c in CONCEPTS_DIR.glob("*.md")]
    related = [c for c in existing_concepts if c in content or c in concept_name][:3]

    # 生成概念文件
    concept_file = CONCEPTS_DIR / f"{concept_name}.md"

    # 如果概念已存在，跳过
    if concept_file.exists():
        return None

    # 尝试 AI 补全定义
    definition = ai_answer
    key_points = "- 从问答中自动提取"

    if client:
        prompt = f"""请为概念 "{concept_name}" 提取定义和关键要点。

已有内容：
{ai_answer}

请简洁回复：
## 定义
[50字以内定义]

## 关键要点
- 要点1
- 要点2
"""
        try:
            # 自定义 API
            if client == "custom":
                from api_client import chat as custom_chat
                ai_result = custom_chat(prompt, max_tokens=300)
            else:
                resp = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_result = resp.content[0].text
            if "## 定义" in ai_result:
                definition = ai_result.split("## 定义")[1].split("##")[0].strip()[:200]
            if "## 关键要点" in ai_result:
                key_points = ai_result.split("## 关键要点")[1].strip()
        except:
            pass

    concept_content = f"""---
title: {concept_name}
type: concept
created: {datetime.now().strftime('%Y-%m-%d')}
source: [[{qa_file.relative_to(VAULT)}]]
related: [{', '.join(f'[[wiki/concepts/{r}]]' for r in related)}]
---

# {concept_name}

## 定义
{definition}

## 关键要点
{key_points}

## 来源
- [[{qa_file.relative_to(VAULT)}]]

## 关联
{', '.join(f'[[wiki/concepts/{r}]]' for r in related) if related else '无'}
"""

    write_file(concept_file, concept_content)
    log(f"✅ 从问答创建概念: {concept_name}")
    return concept_file


def evolve_qa():
    """将问答转化为概念"""
    if not QA_DIR.exists():
        log("⚠️ outputs/qa/ 目录不存在")
        return 0

    client = get_anthropic_client()

    qa_files = list(QA_DIR.glob("*.md"))
    if not qa_files:
        log("⚠️ 没有问答记录")
        return 0

    # 检查哪些问答已经转化为概念
    converted = set()
    for cf in CONCEPTS_DIR.glob("*.md"):
        content = read_file(cf)
        # 查找 source 字段
        source_match = re.search(r'source:\s*\[\[([^]]+)\]\]', content)
        if source_match:
            converted.add(source_match.group(1))

    new_concepts = 0
    for qf in qa_files:
        qf_relative = str(qf.relative_to(VAULT))
        if qf_relative not in converted and "outputs/qa/" in qf_relative:
            if qa_to_concept(qf, client):
                new_concepts += 1

    return new_concepts


# ============================================================
# 功能3: 强化概念关联
# ============================================================

def strengthen_connections():
    """强化概念之间的关联"""
    if not CONCEPTS_DIR.exists():
        return 0

    concepts = list(CONCEPTS_DIR.glob("*.md"))
    if not concepts:
        return 0

    # 收集所有概念名和它们的关键词
    concept_keywords = {}
    for cf in concepts:
        content = read_file(cf)
        # 提取概念名中的词
        name = cf.stem
        keywords = set(name.lower().split()) | set(re.findall(r'[A-Za-z]+', name.lower()))
        concept_keywords[cf] = keywords

    # 为每个概念找新的关联
    updated = 0
    for cf in concepts:
        content = read_file(cf)
        current_related = set(re.findall(r'\[\[wiki/concepts/([^\]]+)\]\]', content))

        # 找相关概念
        new_related = set()
        cf_keywords = concept_keywords.get(cf, set())
        for other_cf, other_keywords in concept_keywords.items():
            if cf == other_cf:
                continue
            # 有共同关键词
            if cf_keywords & other_keywords:
                new_related.add(other_cf.stem)

        # 添加新关联
        new_related = new_related - current_related
        if new_related:
            # 更新关联部分
            existing_related = list(current_related) + list(new_related)
            related_str = ', '.join(f'[[wiki/concepts/{r}]]' for r in existing_related[:10])

            # 替换关联部分
            new_content = re.sub(
                r'## 关联\s*\n.*?(?=\n##|$)',
                f'## 关联\n{related_str}',
                content,
                flags=re.DOTALL
            )

            if new_content != content:
                write_file(cf, new_content)
                updated += 1
                log(f"🔗 {cf.stem}: 新增 {len(new_related)} 个关联")

    return updated


# ============================================================
# 功能4: 发现知识盲区
# ============================================================

def find_knowledge_gaps():
    """发现知识盲区"""
    if not SUMMARIES_DIR.exists():
        return []

    gaps = []

    # 检查孤立的概念（没有来源）
    for cf in CONCEPTS_DIR.glob("*.md"):
        content = read_file(cf)
        if "## 来源" in content:
            sources = re.search(r'## 来源\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if not sources or "无" in sources.group(1):
                gaps.append(f"概念无来源: {cf.stem}")

    # 检查未关联的概念
    for cf in CONCEPTS_DIR.glob("*.md"):
        content = read_file(cf)
        links = re.findall(r'\[\[wiki/concepts/[^\]]+\]\]', content)
        if len(links) < 2:
            gaps.append(f"概念关联少: {cf.stem}")

    # 检查摘要中的孤立概念
    for sf in SUMMARIES_DIR.glob("*.md"):
        content = read_file(sf)
        if "## 相关概念" in content:
            related = re.search(r'## 相关概念\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if related and "无" in related.group(1):
                gaps.append(f"摘要无关联: {sf.stem}")

    return gaps


# ============================================================
# 主流程
# ============================================================

def run_evolve(once: bool = True):
    """运行自动进化"""
    print("\n" + "=" * 50)
    print("  🧬 知识库自动进化")
    print("=" * 50 + "\n")

    summary = {
        "concepts_completed": 0,
        "concepts_created": 0,
        "connections_strengthened": 0,
        "gaps_found": 0
    }

    # 1. 补全概念定义
    log("🔍 扫描待完善的概念...")
    summary["concepts_completed"] = evolve_concepts()

    # 2. 将问答转化为概念
    log("🔄 扫描问答记录...")
    summary["concepts_created"] = evolve_qa()

    # 3. 强化概念关联
    log("🔗 强化概念关联...")
    summary["connections_strengthened"] = strengthen_connections()

    # 4. 发现知识盲区
    log("🔎 发现知识盲区...")
    gaps = find_knowledge_gaps()
    summary["gaps_found"] = len(gaps)

    if gaps:
        print("\n  💡 知识盲区:")
        for gap in gaps[:5]:
            print(f"     - {gap}")

    # 记录日志
    update_log("evolve", f"补全{summary['concepts_completed']}个概念, 创建{summary['concepts_created']}个概念, 强化{summary['connections_strengthened']}个关联")

    # 输出总结
    print("\n" + "=" * 50)
    print("  📊 进化结果")
    print("=" * 50)
    print(f"  ✅ 补全概念定义: {summary['concepts_completed']}")
    print(f"  ✅ 从问答创建概念: {summary['concepts_created']}")
    print(f"  ✅ 强化概念关联: {summary['connections_strengthened']}")
    print(f"  💡 发现知识盲区: {summary['gaps_found']}")
    print()

    return summary


def main():
    parser = argparse.ArgumentParser(description="知识库自动进化")
    parser.add_argument("--once", action="store_true", help="运行一次（默认）")
    parser.add_argument("--continuous", action="store_true", help="持续运行")
    parser.add_argument("--interval", type=int, default=3600, help="进化间隔（秒）")

    args = parser.parse_args()

    if args.continuous:
        print(f"🔄 持续进化模式，每 {args.interval} 秒运行一次")
        print("按 Ctrl+C 退出\n")
        import time
        try:
            while True:
                run_evolve()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋 进化已停止")
    else:
        run_evolve()


if __name__ == "__main__":
    main()