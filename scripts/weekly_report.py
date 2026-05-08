#!/usr/bin/env python3
"""
知识库周报生成器

生成包含以下内容的报告：
1. 本周新增资料统计
2. 知识进化状态
3. 新概念分析
4. 知识网络健康度
"""
import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

VAULT = Path(os.getcwd())
WIKI = VAULT / "wiki"
RAW = VAULT / "raw"
OUTPUTS = VAULT / "outputs"
LOG_FILE = WIKI / "indexes" / "log.md"


def read_file(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="ignore")


def get_git_stats():
    """获取 Git 统计信息"""
    import subprocess

    stats = {
        "total_commits": 0,
        "contributors": defaultdict(int),
        "recent_files": [],
        "weekly_commits": 0
    }

    try:
        # 获取提交数量
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=VAULT,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            stats["total_commits"] = int(result.stdout.strip())

        # 获取本周提交数
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "log", f"--since={week_ago}", "--pretty=format:%an"],
            cwd=VAULT,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            authors = result.stdout.strip().split("\n")
            stats["weekly_commits"] = len([a for a in authors if a])
            for author in authors:
                if author:
                    stats["contributors"][author] += 1

        # 获取本周新增文件
        result = subprocess.run(
            ["git", "log", f"--since={week_ago}", "--name-only", "--pretty=format:"],
            cwd=VAULT,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            # 统计 raw/ 目录下的新文件
            raw_files = [f for f in files if f.startswith("raw/")]
            stats["recent_files"] = raw_files[:20]

    except Exception as e:
        print(f"⚠️ Git 统计失败: {e}")

    return stats


def get_wiki_stats():
    """获取知识库统计"""
    stats = {
        "total_concepts": 0,
        "total_summaries": 0,
        "total_links": 0,
        "new_concepts_this_week": [],
        "incomplete_concepts": [],
        "isolated_concepts": [],
        "top_keywords": defaultdict(int)
    }

    # 概念统计
    concepts_dir = WIKI / "concepts"
    if concepts_dir.exists():
        concept_files = list(concepts_dir.glob("*.md"))
        stats["total_concepts"] = len(concept_files)

        for cf in concept_files:
            content = read_file(cf)

            # 检查是否完善
            if "AI 补充中" in content or "待提取" in content:
                stats["incomplete_concepts"].append(cf.stem)

            # 检查是否孤立（无关联）
            links = re.findall(r'\[\[wiki/concepts/[^\]]+\]\]', content)
            if len(links) < 2:
                stats["isolated_concepts"].append(cf.stem)

            # 提取关键词
            keywords = re.findall(r'#{1,6}\s+([^#\n]+)', content)
            for kw in keywords[:3]:
                kw = kw.strip()[:10]
                if kw and len(kw) > 1:
                    stats["top_keywords"][kw] += 1

    # 摘要统计
    summaries_dir = WIKI / "summaries"
    if summaries_dir.exists():
        stats["total_summaries"] = len(list(summaries_dir.glob("*.md")))

    # 链接统计
    for md_file in WIKI.rglob("*.md"):
        if "indexes" in str(md_file):
            continue
        content = read_file(md_file)
        stats["total_links"] += len(re.findall(r'\[\[', content))

    return stats


def get_evolution_status():
    """获取知识进化状态"""
    status = {
        "qa_count": 0,
        "health_reports": [],
        "last_compile": None,
        "last_evolve": None
    }

    # 问答数量
    qa_dir = OUTPUTS / "qa"
    if qa_dir.exists():
        status["qa_count"] = len(list(qa_dir.glob("*.md")))

    # 健康报告
    health_dir = OUTPUTS / "health"
    if health_dir.exists():
        reports = sorted(health_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        status["health_reports"] = [r.name for r in reports[:5]]

    # 从日志获取最后操作
    log_content = read_file(LOG_FILE)
    compile_match = re.search(r'\[(\d{4}-\d{2}-\d{2})\].*compile', log_content)
    evolve_match = re.search(r'\[(\d{4}-\d{2}-\d{2})\].*evolve', log_content)

    if compile_match:
        status["last_compile"] = compile_match.group(1)
    if evolve_match:
        status["last_evolve"] = evolve_match.group(1)

    return status


def analyze_new_knowledge(git_stats, wiki_stats):
    """分析新知识"""
    analysis = {
        "new_sources": [],
        "new_concepts": [],
        "knowledge_gaps": [],
        "summary": ""
    }

    # 本周新增的源文件
    raw_files = [f for f in git_stats["recent_files"] if f.startswith("raw/")]
    if raw_files:
        analysis["new_sources"] = list(set(raw_files))[:10]

    # 本周新增的概念（通过检查文件创建时间）
    concepts_dir = WIKI / "concepts"
    if concepts_dir.exists():
        week_ago = datetime.now() - timedelta(days=7)
        for cf in concepts_dir.glob("*.md"):
            if cf.stat().st_mtime > week_ago.timestamp():
                analysis["new_concepts"].append(cf.stem)

    # 知识盲区
    if wiki_stats["incomplete_concepts"]:
        analysis["knowledge_gaps"].append(f"{len(wiki_stats['incomplete_concepts'])} 个概念待完善")
    if wiki_stats["isolated_concepts"]:
        analysis["knowledge_gaps"].append(f"{len(wiki_stats['isolated_concepts'])} 个概念缺乏关联")

    return analysis


def generate_weekly_report():
    """生成周报"""
    report_date = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "=" * 60)
    print(f"  📊 AI 知识库周报 - {report_date}")
    print("=" * 60)

    # 1. Git 统计
    print("\n📥 一、资料导入统计")
    print("-" * 40)
    git_stats = get_git_stats()
    print(f"  本周提交: {git_stats['weekly_commits']} 次")
    print(f"  本周新增文件: {len(set(git_stats['recent_files']))} 个")

    if git_stats["contributors"]:
        print("  贡献者:")
        for author, count in sorted(git_stats["contributors"].items(), key=lambda x: -x[1])[:5]:
            print(f"    - {author}: {count} 次提交")

    if git_stats["recent_files"]:
        unique_files = list(set(git_stats["recent_files"]))[:5]
        print("  新增资料文件:")
        for f in unique_files:
            print(f"    - {f}")

    # 2. 知识库状态
    print("\n🧠 二、知识库状态")
    print("-" * 40)
    wiki_stats = get_wiki_stats()
    print(f"  概念总数: {wiki_stats['total_concepts']} 个")
    print(f"  摘要总数: {wiki_stats['total_summaries']} 篇")
    print(f"  交叉链接: {wiki_stats['total_links']} 个")

    # 3. 进化状态
    print("\n🔄 三、进化状态")
    print("-" * 40)
    evolution = get_evolution_status()
    print(f"  问答沉淀: {evolution['qa_count']} 条")
    print(f"  最后编译: {evolution['last_compile'] or '未知'}")
    print(f"  最后进化: {evolution['last_evolve'] or '未知'}")

    # 4. 新知识分析
    print("\n💡 四、新知识分析")
    print("-" * 40)
    analysis = analyze_new_knowledge(git_stats, wiki_stats)

    if analysis["new_concepts"]:
        print(f"  本周新概念 ({len(analysis['new_concepts'])} 个):")
        for c in analysis["new_concepts"][:5]:
            print(f"    - {c}")

    if analysis["knowledge_gaps"]:
        print("  知识盲区:")
        for gap in analysis["knowledge_gaps"]:
            print(f"    ⚠️ {gap}")

    # 5. 健康度评估
    print("\n📈 五、知识网络健康度")
    print("-" * 40)

    # 计算健康分数
    health_score = 100
    health_score -= len(wiki_stats["incomplete_concepts"]) * 5
    health_score -= len(wiki_stats["isolated_concepts"]) * 3
    health_score = max(0, health_score)

    # 平均链接数
    avg_links = wiki_stats["total_links"] / max(1, wiki_stats["total_concepts"])

    print(f"  健康分数: {health_score}/100")
    print(f"  平均概念关联: {avg_links:.1f} 个")
    print(f"  待完善概念: {len(wiki_stats['incomplete_concepts'])} 个")
    print(f"  孤立概念: {len(wiki_stats['isolated_concepts'])} 个")

    if health_score >= 80:
        print("  状态: 🟢 优秀")
    elif health_score >= 60:
        print("  状态: 🟡 良好")
    else:
        print("  状态: 🔴 需改进")

    # 生成建议
    print("\n💡 六、优化建议")
    print("-" * 40)

    suggestions = []
    if wiki_stats["incomplete_concepts"]:
        suggestions.append(f"1. 完善 {len(wiki_stats['incomplete_concepts'])} 个待完善概念的定义")
    if wiki_stats["isolated_concepts"]:
        suggestions.append(f"2. 为 {len(wiki_stats['isolated_concepts'])} 个孤立概念建立关联")
    if not evolution["last_evolve"] or evolution["last_evolve"] != report_date[:10]:
        suggestions.append("3. 运行 auto_evolve 补全概念定义")
    if not analysis["new_sources"]:
        suggestions.append("4. 建议添加新的学习资料")

    if suggestions:
        for s in suggestions:
            print(f"  {s}")
    else:
        print("  ✅ 知识库状态良好，继续保持！")

    # 生成 Markdown 报告
    report_content = f"""# AI 知识库周报

> 生成时间: {report_date}

## 一、资料导入统计

- 本周提交: {git_stats['weekly_commits']} 次
- 本周新增文件: {len(set(git_stats['recent_files']))} 个

### 贡献者

"""
    for author, count in sorted(git_stats["contributors"].items(), key=lambda x: -x[1])[:5]:
        report_content += f"- {author}: {count} 次提交\n"

    if analysis["new_sources"]:
        report_content += f"""
### 新增资料

"""
        for f in analysis["new_sources"]:
            report_content += f"- {f}\n"

    report_content += f"""
## 二、知识库状态

| 指标 | 数值 |
|------|------|
| 概念总数 | {wiki_stats['total_concepts']} 个 |
| 摘要总数 | {wiki_stats['total_summaries']} 篇 |
| 交叉链接 | {wiki_stats['total_links']} 个 |
| 问答沉淀 | {evolution['qa_count']} 条 |

## 三、进化状态

- 最后编译: {evolution['last_compile'] or '未知'}
- 最后进化: {evolution['last_evolve'] or '未知'}

## 四、新概念

"""
    if analysis["new_concepts"]:
        for c in analysis["new_concepts"]:
            report_content += f"- {c}\n"
    else:
        report_content += "本周无新概念\n"

    report_content += f"""
## 五、知识网络健康度

- 健康分数: {health_score}/100
- 平均概念关联: {avg_links:.1f} 个
- 待完善概念: {len(wiki_stats['incomplete_concepts'])} 个
- 孤立概念: {len(wiki_stats['isolated_concepts'])} 个

状态: {"🟢 优秀" if health_score >= 80 else "🟡 良好" if health_score >= 60 else "🔴 需改进"}

## 六、优化建议

"""
    if suggestions:
        for s in suggestions:
            report_content += f"- {s}\n"
    else:
        report_content += "✅ 知识库状态良好，继续保持！\n"

    report_content += f"""
---

*由自动脚本生成*
"""

    # 保存报告
    report_dir = OUTPUTS / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"weekly-{report_date}.md"
    report_file.write_text(report_content, encoding="utf-8")

    print(f"\n📄 报告已保存: {report_file.relative_to(VAULT)}")

    return report_file


if __name__ == "__main__":
    generate_weekly_report()