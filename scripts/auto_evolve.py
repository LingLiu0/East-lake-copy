#!/usr/bin/env python3
"""
auto_evolve.py - 知识库自动进化引擎（子任务三增强版）

在原版本基础上新增：
- 矛盾检测：新摘要与现有概念做语义比对，识别冲突
- 置信度评估：基于来源权威性 + 引用次数给概念打分
- 关联推荐：用 LLM 找遗漏的强关联
- 知识补全推理：基于问答自动生成新概念

运行：
    python3 scripts/auto_evolve.py --once          # 单次
    python3 scripts/auto_evolve.py --continuous   # 持续模式
    python3 scripts/auto_evolve.py --mode contradictions  # 仅跑矛盾检测
    python3 scripts/auto_evolve.py --mode confidence     # 仅跑置信度评估
    python3 scripts/auto_evolve.py --mode all           # 全部跑
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

VAULT = Path(os.getcwd())
WIKI = VAULT / "wiki"
OUTPUTS = VAULT / "outputs"
CONCEPTS_DIR = WIKI / "concepts"
SUMMARIES_DIR = WIKI / "summaries"
QA_DIR = OUTPUTS / "qa"
LOG_FILE = WIKI / "indexes" / "log.md"
TEMPLATES = VAULT / "templates"

sys.path.insert(0, str(VAULT / "scripts"))


# ============================================================
# 工具
# ============================================================

def get_client():
    """获取 LLM 客户端"""
    if os.getenv("API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        try:
            from api_client import chat
            return chat
        except ImportError:
            pass
    return None


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  [{timestamp}] {message}")


def read_file(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="ignore")


def write_file(file_path: Path, content: str):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def update_log(action: str, detail: str):
    entry = f"\n## [{datetime.now().strftime('%Y-%m-%d')}] {action}\n\n- {detail}\n"
    if LOG_FILE.exists():
        write_file(LOG_FILE, read_file(LOG_FILE) + entry)
    else:
        write_file(LOG_FILE, f"# Wiki Log\n{entry}")


# ============================================================
# 工具：模板加载
# ============================================================

def load_template(kind: str, name: str) -> Tuple[str, Dict]:
    """加载模板（与 qa_engine 同步）"""
    template_path = TEMPLATES / kind / f"{name}.md"
    if not template_path.exists():
        return ("", {})
    content = template_path.read_text(encoding="utf-8")
    fm: Dict = {}
    body = content
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()
        body = m.group(2)
    h1 = re.search(r'^#\s+System Prompt\s*\n(.*?)(?=^---\s*$|\Z)',
                   body, re.MULTILINE | re.DOTALL)
    return (h1.group(1).strip() if h1 else body.strip(), fm)


# ============================================================
# 功能 1（保留）：补全概念定义
# ============================================================

def complete_concept_definition(concept_file: Path, client) -> bool:
    content = read_file(concept_file)
    concept_name = concept_file.stem

    related_summaries = []
    for sf in SUMMARIES_DIR.glob("*.md"):
        sf_content = read_file(sf)
        if concept_name in sf_content or any(c in sf_content for c in concept_name.split() if len(c) >= 2):
            related_summaries.append(read_file(sf)[:1500])

    if not related_summaries:
        log(f"⚠️ {concept_name}: 没有找到相关摘要")
        return False

    context = "\n\n---\n\n".join(related_summaries[:2])
    system_prompt, _ = load_template("evolution", "concept_complete")
    user_msg = f"""概念名：{concept_name}

参考资料：
{context}"""

    if client is None:
        return False

    try:
        ai_content = client(system_prompt + "\n\n" + user_msg, max_tokens=500)
        if not ai_content:
            return False

        if "## 定义" in ai_content and "## 关键要点" in ai_content:
            definition_text = ai_content.split("## 关键要点")[0].replace("## 定义", "").strip()
        else:
            definition_text = ai_content.strip()[:200]

        new_content = content.replace("（AI 补充中）", definition_text)

        if "## 关键要点" in ai_content:
            key_points = ai_content.split("## 关键要点")[1].split("##")[0].strip()
            new_content = re.sub(
                r'## 关键要点\s*\n.*?(?=\n##|$)',
                f'## 关键要点\n{key_points}\n',
                new_content,
                flags=re.DOTALL,
            )

        write_file(concept_file, new_content)
        log(f"✅ {concept_name}: 已补全定义")
        return True
    except Exception as e:
        log(f"❌ {concept_name}: {e}")
        return False


def evolve_concepts() -> int:
    client = get_client()
    if not client:
        log("⚠️ 未配置 API Key，跳过概念补全")
        return 0

    if not CONCEPTS_DIR.exists():
        return 0

    incomplete = [cf for cf in CONCEPTS_DIR.glob("*.md")
                  if "AI 补充中" in read_file(cf) or "待提取" in read_file(cf)]

    if not incomplete:
        log("✅ 所有概念已完善")
        return 0

    log(f"🔄 开始补全 {len(incomplete)} 个概念...")
    completed = 0
    for cf in incomplete[:5]:
        if complete_concept_definition(cf, client):
            completed += 1
    return completed


# ============================================================
# 功能 2（保留）：将问答转化为概念
# ============================================================

def qa_to_concept(qa_file: Path, client) -> Optional[Path]:
    content = read_file(qa_file)
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if not title_match:
        return None

    ai_answer_match = re.search(r'## AI 回答\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
    if not ai_answer_match:
        return None

    ai_answer = ai_answer_match.group(1).strip()[:800]
    concept_name = title_match.group(1).strip()[:30]
    concept_file = CONCEPTS_DIR / f"{concept_name}.md"

    if concept_file.exists():
        return None

    definition = ai_answer[:200]
    key_points = "- 从问答中自动提取"

    if client:
        try:
            system_prompt, _ = load_template("evolution", "qa_to_concept")
            user_msg = f"""问题：{concept_name}
AI 回答：{ai_answer}"""
            ai_result = client(system_prompt + "\n\n" + user_msg, max_tokens=400)
            if ai_result:
                m = re.search(r'\{.*\}', ai_result, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    if not data.get("should_create"):
                        return None
                    concept_name = data.get("concept_name", concept_name)[:30]
                    definition = data.get("definition", definition)[:200]
                    key_points = "\n".join(f"- {p}" for p in data.get("key_points", [])) or key_points
        except Exception as e:
            log(f"  ⚠️ qa_to_concept LLM 失败: {e}")

    existing = [c.stem for c in CONCEPTS_DIR.glob("*.md")]
    related = [c for c in existing if c in content or c in concept_name][:3]

    content_str = f"""---
title: {concept_name}
type: concept
created: {datetime.now().strftime('%Y-%m-%d')}
source: [[{qa_file.relative_to(VAULT)}]]
related: [{', '.join(f'[[wiki/concepts/{r}]]' for r in related)}]
confidence: 0.5
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
    write_file(concept_file, content_str)
    log(f"✅ 从问答创建概念: {concept_name}")
    return concept_file


def evolve_qa() -> int:
    if not QA_DIR.exists():
        return 0
    client = get_client()
    qa_files = list(QA_DIR.glob("*.md"))
    if not qa_files:
        return 0

    converted = set()
    for cf in CONCEPTS_DIR.glob("*.md"):
        m = re.search(r'source:\s*\[\[([^]]+)\]\]', read_file(cf))
        if m:
            converted.add(m.group(1))

    new = 0
    for qf in qa_files:
        rel = str(qf.relative_to(VAULT))
        if rel not in converted and "outputs/qa/" in rel:
            if qa_to_concept(qf, client):
                new += 1
    return new


# ============================================================
# 功能 3（保留）：强化概念关联
# ============================================================

def strengthen_connections() -> int:
    if not CONCEPTS_DIR.exists():
        return 0

    concepts = list(CONCEPTS_DIR.glob("*.md"))
    if not concepts:
        return 0

    concept_keywords: Dict[Path, set] = {}
    for cf in concepts:
        name = cf.stem
        keywords = set(re.findall(r'[\w]+', name.lower()))
        for i in range(len(name) - 1):
            keywords.add(name[i:i+2])
        concept_keywords[cf] = keywords

    updated = 0
    for cf in concepts:
        content = read_file(cf)
        current_related = set(re.findall(r'\[\[wiki/concepts/([^\]]+)\]\]', content))
        new_related = set()
        cf_kw = concept_keywords.get(cf, set())
        for other_cf, other_kw in concept_keywords.items():
            if cf == other_cf:
                continue
            if cf_kw & other_kw:
                new_related.add(other_cf.stem)
        new_related = new_related - current_related
        if new_related:
            existing = list(current_related) + list(new_related)
            related_str = ', '.join(f'[[wiki/concepts/{r}]]' for r in existing[:10])
            new_content = re.sub(
                r'## 关联\s*\n.*?(?=\n##|$)',
                f'## 关联\n{related_str}\n',
                content,
                flags=re.DOTALL,
            )
            if new_content != content:
                write_file(cf, new_content)
                updated += 1
    return updated


# ============================================================
# 功能 4（保留）：发现知识盲区
# ============================================================

def find_knowledge_gaps() -> List[str]:
    gaps = []
    if not CONCEPTS_DIR.exists():
        return gaps

    for cf in CONCEPTS_DIR.glob("*.md"):
        content = read_file(cf)
        sources = re.search(r'## 来源\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if not sources or "无" in sources.group(1):
            gaps.append(f"概念无来源: {cf.stem}")
        links = re.findall(r'\[\[wiki/concepts/[^\]]+\]\]', content)
        if len(links) < 2:
            gaps.append(f"概念关联少: {cf.stem}")

    return gaps


# ============================================================
# 新增功能 5：矛盾检测
# ============================================================

def find_candidate_concepts(text: str, top_n: int = 3) -> List[Tuple[str, Path]]:
    """找与 text 相关的现有概念（基于关键词命中）"""
    if not CONCEPTS_DIR.exists():
        return []
    keywords = set(re.findall(r'[\w]+', text.lower()))
    keywords |= set(re.findall(r'[\u4e00-\u9fff]{2,}', text))

    candidates = []
    for cf in CONCEPTS_DIR.glob("*.md"):
        name = cf.stem
        if name in text:
            candidates.append((name, cf))
        else:
            name_kw = set(re.findall(r'[\w]+', name.lower())) | set(re.findall(r'[\u4e00-\u9fff]{2,}', name))
            if name_kw & keywords:
                candidates.append((name, cf))

    return candidates[:top_n]


def check_contradiction(new_text: str, concept_path: Path, client) -> Optional[Dict]:
    """检测新文本与现有概念是否矛盾"""
    if not client or len(new_text) < 100:
        return None

    concept_content = read_file(concept_path)
    system_prompt, _ = load_template("evolution", "contradiction_check")
    user_msg = f"""新摘要：
{new_text[:1500]}

现有概念 {concept_path.stem}：
{concept_content[:1500]}"""

    try:
        result = client(system_prompt + "\n\n" + user_msg, max_tokens=400)
        if not result:
            return None
        m = re.search(r'\{.*\}', result, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        log(f"  ⚠️ 矛盾检测 LLM 失败 ({concept_path.stem}): {e}")
    return None


def run_contradiction_check() -> int:
    """对最近 7 天的摘要跑矛盾检测"""
    if not SUMMARIES_DIR.exists() or not CONCEPTS_DIR.exists():
        return 0
    client = get_client()
    if not client:
        log("⚠️ 未配置 API Key，跳过矛盾检测")
        return 0

    log("🔍 运行矛盾检测...")
    cutoff = datetime.now().timestamp() - 7 * 86400
    recent_summaries = [sf for sf in SUMMARIES_DIR.glob("*.md")
                        if sf.stat().st_mtime > cutoff]

    if not recent_summaries:
        log("  无最近 7 天摘要")
        return 0

    log(f"  待检测: {len(recent_summaries)} 个摘要")
    conflicts_found = 0

    for sf in recent_summaries[:5]:
        content = read_file(sf)
        if len(content) < 200:
            continue
        candidates = find_candidate_concepts(content, top_n=3)
        for name, cf in candidates:
            result = check_contradiction(content, cf, client)
            if result and result.get("has_contradiction"):
                conflicts = result.get("conflicts", [])
                for c in conflicts:
                    log(f"  ⚠️ 矛盾: {sf.name} ↔ {c.get('concept_name')} [{c.get('severity')}] {c.get('conflict_description')}")
                    conflicts_found += 1
                if "## ⚠️ 冲突" not in content:
                    marker = f"\n\n## ⚠️ 冲突标记 ({datetime.now().strftime('%Y-%m-%d')})\n\n"
                    for c in conflicts:
                        marker += f"- {c.get('concept_name')}: {c.get('conflict_description')} [severity={c.get('severity')}]\n"
                    write_file(sf, content + marker)

    log(f"  发现 {conflicts_found} 个冲突")
    return conflicts_found


# ============================================================
# 新增功能 6：置信度评估
# ============================================================

def compute_concept_confidence(concept_path: Path) -> Tuple[float, Dict]:
    """
    计算概念置信度（不调 LLM，纯启发式）

    评分维度：
    - 来源丰富度（0-0.3）：关联的 summary 越多越好
    - 关联丰富度（0-0.3）：关联的概念越多越好
    - 内容完整度（0-0.2）：没有 "AI 补充中" 标记
    - 定义长度（0-0.2）：定义在 50-200 字最佳
    """
    content = read_file(concept_path)
    scores = {}

    sources = re.findall(r'\[\[(wiki/summaries/[^\]]+)\]\]', content)
    src_count = len(sources)
    scores["source_richness"] = min(src_count / 5, 1.0) * 0.30

    related = re.findall(r'\[\[wiki/concepts/([^\]]+)\]\]', content)
    rel_count = len(related)
    scores["relation_richness"] = min(rel_count / 5, 1.0) * 0.30

    is_complete = "AI 补充中" not in content and "待提取" not in content
    scores["completeness"] = 0.20 if is_complete else 0.0

    def_match = re.search(r'## 定义\s*\n(.+?)(?=\n##|$)', content, re.DOTALL)
    if def_match:
        def_len = len(def_match.group(1).strip())
        if 50 <= def_len <= 200:
            scores["definition_length"] = 0.20
        elif def_len < 50:
            scores["definition_length"] = 0.10
        else:
            scores["definition_length"] = 0.05
    else:
        scores["definition_length"] = 0.0

    total = sum(scores.values())
    return round(total, 3), scores


def update_concept_confidence_in_metadata() -> int:
    """把所有概念的置信度写入 front matter"""
    if not CONCEPTS_DIR.exists():
        return 0
    updated = 0
    for cf in CONCEPTS_DIR.glob("*.md"):
        confidence, _ = compute_concept_confidence(cf)
        content = read_file(cf)

        if re.search(r'^confidence:', content, re.MULTILINE):
            new_content = re.sub(
                r'^confidence:.*$',
                f'confidence: {confidence}',
                content,
                flags=re.MULTILINE,
            )
        else:
            new_content = re.sub(
                r'^(type:.*)$',
                rf'\1\nconfidence: {confidence}',
                content,
                count=1,
                flags=re.MULTILINE,
            )
        if new_content != content:
            write_file(cf, new_content)
            updated += 1
    return updated


# ============================================================
# 新增功能 7：用 LLM 推荐关联
# ============================================================

def recommend_links_for_orphan(concept_path: Path, candidate_concepts: List[Path], client) -> Optional[Dict]:
    """对孤立概念，用 LLM 推荐关联"""
    if not client:
        return None
    content = read_file(concept_path)
    candidate_names = [c.stem for c in candidate_concepts[:10]]

    system_prompt, _ = load_template("evolution", "concept_link")
    user_msg = f"""目标概念：{concept_path.stem}

目标概念现有内容：
{content[:1500]}

候选概念列表：
{', '.join(candidate_names)}"""

    try:
        result = client(system_prompt + "\n\n" + user_msg, max_tokens=400)
        if not result:
            return None
        m = re.search(r'\{.*\}', result, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        log(f"  ⚠️ 关联推荐失败: {e}")
    return None


def run_link_recommendation() -> int:
    """对关联少的概念跑 LLM 关联推荐"""
    if not CONCEPTS_DIR.exists():
        return 0
    client = get_client()
    if not client:
        log("⚠️ 未配置 API Key，跳过关联推荐")
        return 0

    log("🔗 运行关联推荐...")
    orphan_concepts = []
    for cf in CONCEPTS_DIR.glob("*.md"):
        content = read_file(cf)
        related = re.findall(r'\[\[wiki/concepts/[^\]]+\]\]', content)
        if len(related) < 2:
            orphan_concepts.append(cf)

    if not orphan_concepts:
        log("  所有概念已有充足关联")
        return 0

    log(f"  找到 {len(orphan_concepts)} 个孤立概念")
    all_candidates = [c for c in CONCEPTS_DIR.glob("*.md")]
    new_links = 0

    for cf in orphan_concepts[:3]:
        result = recommend_links_for_orphan(cf, all_candidates, client)
        if not result:
            continue
        related = result.get("related", [])
        if not related:
            continue
        content = read_file(cf)
        existing = set(re.findall(r'\[\[wiki/concepts/([^\]]+)\]\]', content))
        to_add = []
        for r in related:
            name = r.get("name", "")
            if name and name not in existing:
                to_add.append(name)
                existing.add(name)
        if to_add:
            new_related = list(existing)[:10]
            related_str = ', '.join(f'[[wiki/concepts/{r}]]' for r in new_related)
            new_content = re.sub(
                r'## 关联\s*\n.*?(?=\n##|$)',
                f'## 关联\n{related_str}\n',
                content,
                flags=re.DOTALL,
            )
            if new_content != content:
                write_file(cf, new_content)
                log(f"  ✅ {cf.stem}: 新增 {len(to_add)} 个关联")
                new_links += len(to_add)

    return new_links


# ============================================================
# 主流程
# ============================================================

def run_evolve(once: bool = True, mode: str = "all") -> Dict:
    print("\n" + "=" * 60)
    print("  🧬 知识库自动进化（增强版）")
    print("=" * 60 + "\n")

    summary = {
        "concepts_completed": 0,
        "concepts_created": 0,
        "connections_strengthened": 0,
        "contradictions_found": 0,
        "links_recommended": 0,
        "concepts_with_confidence": 0,
        "gaps_found": 0,
    }

    tasks = {
        "all": ["complete", "qa", "connect", "contradict", "link", "confidence", "gaps"],
        "complete": ["complete"],
        "qa": ["qa"],
        "connect": ["connect"],
        "contradictions": ["contradict"],
        "links": ["link"],
        "confidence": ["confidence"],
        "gaps": ["gaps"],
    }
    selected = tasks.get(mode, tasks["all"])

    if "complete" in selected:
        log("🔍 扫描待完善的概念...")
        summary["concepts_completed"] = evolve_concepts()

    if "qa" in selected:
        log("🔄 扫描问答记录...")
        summary["concepts_created"] = evolve_qa()

    if "connect" in selected:
        log("🔗 强化概念关联（关键词）...")
        summary["connections_strengthened"] = strengthen_connections()

    if "contradict" in selected:
        summary["contradictions_found"] = run_contradiction_check()

    if "link" in selected:
        summary["links_recommended"] = run_link_recommendation()

    if "confidence" in selected:
        log("📊 计算概念置信度...")
        summary["concepts_with_confidence"] = update_concept_confidence_in_metadata()

    if "gaps" in selected:
        log("🔎 发现知识盲区...")
        gaps = find_knowledge_gaps()
        summary["gaps_found"] = len(gaps)
        if gaps:
            print("\n  💡 知识盲区:")
            for gap in gaps[:5]:
                print(f"     - {gap}")

    log_detail = (
        f"补全 {summary['concepts_completed']} 个概念, "
        f"创建 {summary['concepts_created']} 个概念, "
        f"强化 {summary['connections_strengthened']} 个关联, "
        f"发现 {summary['contradictions_found']} 个矛盾, "
        f"推荐 {summary['links_recommended']} 个新关联"
    )
    update_log("evolve", log_detail)

    print("\n" + "=" * 60)
    print("  📊 进化结果")
    print("=" * 60)
    print(f"  ✅ 补全概念定义: {summary['concepts_completed']}")
    print(f"  ✅ 从问答创建概念: {summary['concepts_created']}")
    print(f"  ✅ 强化概念关联: {summary['connections_strengthened']}")
    print(f"  ⚠️  发现矛盾: {summary['contradictions_found']}")
    print(f"  🔗 LLM 推荐新关联: {summary['links_recommended']}")
    print(f"  📊 更新置信度: {summary['concepts_with_confidence']}")
    print(f"  💡 发现知识盲区: {summary['gaps_found']}")
    print()

    return summary


def main():
    parser = argparse.ArgumentParser(description="知识库自动进化（增强版）")
    parser.add_argument("--once", action="store_true", help="单次运行（默认）")
    parser.add_argument("--continuous", action="store_true", help="持续模式")
    parser.add_argument("--interval", type=int, default=3600, help="持续模式间隔（秒）")
    parser.add_argument(
        "--mode", default="all",
        choices=["all", "complete", "qa", "connect", "contradictions", "links", "confidence", "gaps"],
        help="运行模式"
    )
    args = parser.parse_args()

    if args.continuous:
        print(f"🔄 持续进化模式（{args.mode}），每 {args.interval}s 运行一次")
        try:
            import time
            while True:
                run_evolve(mode=args.mode)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋 进化已停止")
    else:
        run_evolve(mode=args.mode)


if __name__ == "__main__":
    main()
