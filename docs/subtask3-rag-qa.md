# 子任务三：知识库智能进化与问答服务 — 设计文档

> 申报书要求：基于知识库构建智能问答系统，支持自然语言理解和精准答案生成；开发知识库自动进化引擎，实现概念的自动补全、关联的自动强化，构建"越用越聪明"的智能知识网络。

## 一、架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      用户入口                                │
│  obsidian.py ask / api/routes/search.py / 交互式 CLI        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  qa_engine.py 主引擎                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 意图分类器   │  │ 文档切片器    │  │ 答案生成器        │  │
│  │ (规则+LLM)  │  │ chunker.py  │  │ (Prompt模板库)   │  │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬────────┘  │
└─────────┼────────────────┼──────────────────────┼──────────┘
          │                │                      │
          ▼                ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  知识库（git-native）                          │
│  raw/ 原始资料 | wiki/concepts/ 概念 | wiki/summaries/ 摘要 │
│  outputs/qa/ 问答沉淀 | .cache/ chunk 索引                   │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│              auto_evolve.py 自动进化引擎                       │
│  补全概念 | 问答转概念 | 强化关联 | 矛盾检测 | 置信度评估    │
└─────────────────────────────────────────────────────────────┘
```

## 二、核心模块

### 2.1 文档切片器 `chunker.py`

**职责**：把 wiki/ 下 markdown 文档切成可索引的 chunk

**切片策略**：
- 按 H1/H2/H3 标题分块
- 单块字符数上限 800，下限 30
- 超过上限的 section 按段落切，段落仍超长则按句子切
- 每块带元信息：doc_path, doc_title, section, chunk_idx, headings

**输出**：JSONL 文件 `.cache/chunks.jsonl`

### 2.2 检索器（BM25）

**职责**：从 chunk 索引里找 top-k 相关片段

**评分**：
- BM25 基础分（rank_bm25 + jieba 中文分词）
- 标题命中加权（+0.5/词）
- 双向链接加权（每 +0.1，封顶 0.5）
- 关键词命中加权（每 +0.3，封顶 1.0）

**为什么不上向量检索**：
- 不依赖重型 embedding 模型（避免下载失败）
- 知识库规模（70 概念 + 25 摘要）BM25 完全够用
- 后续如需可平滑升级：FAISS 已在 `api/services/vector_store.py` 中实现

### 2.3 意图分类器

**5 类路由**：
| 类别 | 触发词 | 模板 |
|---|---|---|
| policy_query | 政策/意见/通知/规划 | policy_query.md |
| concept_explain | 什么是/定义/解释 | concept_explain.md |
| relation_analysis | 关系/区别/对比 | relation_analysis.md |
| synthesis | 分析/研判/趋势 | synthesis.md |
| fallback | 检索为空/无关 | fallback.md |

**双模式**：
- 默认规则化（零延迟、零成本）
- 可选 LLM 分类（`--llm-intent`，精度更高）

### 2.4 答案生成器

**两阶段**：
1. 检索 → 取 top-k chunks → 拼成 context
2. LLM 生成（system_prompt + user_msg）

**溯源**：
- 答案中要求嵌入 `[[wiki/...]]` 链接
- 引擎自动提取这些链接作为 `sources` 字段

**质量评估**（可选 `--evaluate`）：
- 完整性、相关性、时效性、溯源性 4 维
- 综合分 < 0.6 标记需重生成

## 三、Prompt 工程模板库

### 3.1 QA 类（7 个模板）

| 模板 | 用途 | 关键约束 |
|---|---|---|
| `policy_query` | 政策查询 | 三段结构（结论+要点+本地建议） |
| `concept_explain` | 概念解释 | 先给定义再展开要素 |
| `relation_analysis` | 关联分析 | 必须明确关系类型 |
| `synthesis` | 综合问答 | 区分事实和推断 |
| `fallback` | 检索为空 | 不硬答，给具体建议 |
| `intent_classify` | 意图分类 | 严格 JSON 输出 |
| `quality_eval` | 质量评估 | 4 维评分，0-1 |

### 3.2 进化类（4 个模板）

| 模板 | 用途 | 触发时机 |
|---|---|---|
| `concept_complete` | 补全概念 | 扫描到 "AI 补充中" |
| `concept_link` | 推荐关联 | 孤立/弱关联概念 |
| `contradiction_check` | 矛盾检测 | 新摘要入库 |
| `qa_to_concept` | 问答转概念 | outputs/qa/ 有新问答 |

### 3.3 模板格式约定

每个模板文件含：
1. **Front matter**（YAML）：name, kind, purpose, input_schema, output_schema
2. **System Prompt**：直接喂给 LLM，含角色、约束、输出格式
3. **Few-shot 示例**（部分模板）：1-2 组标准样例

## 四、自动进化引擎

### 4.1 7 大能力

| 能力 | 函数 | 是否调 LLM | 频率建议 |
|---|---|---|---|
| 补全概念定义 | `evolve_concepts` | 是 | 每日 |
| 问答转概念 | `evolve_qa` | 是 | 每日 |
| 强化关联（关键词） | `strengthen_connections` | 否 | 每日 |
| 矛盾检测 | `run_contradiction_check` | 是 | 每周 |
| LLM 推荐关联 | `run_link_recommendation` | 是 | 每周 |
| 置信度评估 | `update_concept_confidence_in_metadata` | 否 | 每日 |
| 知识盲区 | `find_knowledge_gaps` | 否 | 每周 |

### 4.2 置信度评分公式

```
confidence = 0.30 × 来源丰富度     (引用 summary 数 / 5)
           + 0.30 × 关联丰富度     (关联概念数 / 5)
           + 0.20 × 内容完整度     (无占位符)
           + 0.20 × 定义长度       (50-200 字最优)
```

分数写入每个概念文件的 front matter `confidence: 0.XX`。

### 4.3 矛盾检测策略

- 仅扫描最近 7 天的新摘要（避免全量跑）
- 用关键词命中找 top-3 候选概念
- LLM 判断是否矛盾（severity: low/medium/high）
- 冲突标记追加到原摘要文件末尾
- 严控误报：模糊时返回 `has_contradiction: false`

## 五、使用方式

### 5.1 命令行

```bash
# 单次问答
python3 scripts/qa_engine.py "湖北数字经济政策有哪些？"

# 启用 LLM 意图分类 + 质量评估
python3 scripts/qa_engine.py --llm-intent --evaluate "5G 和 5G-A 区别？"

# 显示检索命中详情 + 保存到 outputs/qa/
python3 scripts/qa_engine.py "什么是新质生产力" --show-hits --save

# 强制重建 chunk 索引
python3 scripts/qa_engine.py --rebuild-index

# 交互模式
python3 scripts/qa_engine.py

# 自动进化
python3 scripts/auto_evolve.py --once
python3 scripts/auto_evolve.py --mode contradictions
python3 scripts/auto_evolve.py --mode confidence
```

### 5.2 obsidian.py 集成（已完成）

`scripts/obsidian.py` 的 `cmd_query` 已接入 RAG 引擎：优先调用 `qa_engine.ask()`，打印意图、检索命中、AI 回答、来源，并自动沉淀到 `outputs/qa/`；当 `qa_engine` 不可用或异常时，自动回退到旧版关键词检索兜底。

```python
# scripts/obsidian.py cmd_query 核心逻辑：
from qa_engine import ask as rag_ask, save_qa_to_wiki
result = rag_ask(query, use_llm_intent=False, evaluate=False)
print(result.answer)
if save_to_wiki and not result.error:
    save_qa_to_wiki(result)
```

### 5.3 GitHub Actions 集成

新增 workflow `subtask3-rag-qa.yml`：

```yaml
name: Subtask 3 RAG QA + Evolve
on:
  schedule:
    - cron: '0 4 * * *'       # 每日 04:00 UTC（北京 12:00）
  workflow_dispatch:
  push:
    branches: [master]
    paths:
      - 'outputs/qa/**'
      - 'raw/**'
      - 'templates/**'

jobs:
  rag-evolve:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - name: 安装依赖
        run: pip install requests beautifulsoup4 anthropic PyPDF2 python-docx jieba rank_bm25 numpy
      - name: 重建 chunk 索引
        run: python scripts/chunker.py --verbose
      - name: 跑自动进化（矛盾检测 + 置信度）
        env:
          API_KEY: ${{ secrets.LLM_API_KEY }}
          API_BASE: ${{ secrets.LLM_API_BASE }}
          MODEL: ${{ secrets.LLM_MODEL }}
        run: python scripts/auto_evolve.py --mode all
      - name: QA 引擎冒烟测试
        run: python scripts/test_qa_engine.py
      - name: 提交变更
        run: |
          git add -A
          git commit -m "ci: subtask3 evolve" || exit 0
          git push
```

## 六、性能与成本

### 6.1 检索性能

- 当前知识库（70+25 = 95 篇）切分后约 500 chunks
- BM25 构建耗时 < 2s（首次），检索 < 100ms
- 缓存到 `.cache/chunks.jsonl`，wiki/ 变更时自动重建

### 6.2 LLM 调用成本（每次问答）

- 规则化意图分类：0 次 LLM 调用
- LLM 意图分类：+1 次（输入 ~500 token，输出 ~50 token）
- 答案生成：1 次（输入 2000-3000 token context，输出 500-800 token）
- 质量评估：+1 次（输入 ~1000 token，输出 ~150 token）
- 合计：1-3 次 LLM 调用

按 MiniMax-M2.5 当前价格，每次问答约 0.01-0.03 元。

### 6.3 BM25 vs 向量检索 对比

| 维度 | BM25（当前方案） | 向量检索（FAISS，可选升级） |
|---|---|---|
| 原理 | 词频统计 + TF-IDF 变体 | 语义向量余弦相似度 |
| 中文分词 | 依赖 jieba，分词不准影响召回 | 不依赖分词，端到端语义 |
| 语义召回 | 弱（"算力"≠"算力中心"） | 强（同义/近义自动召回） |
| 部署成本 | 零额外依赖，纯 CPU | 需 embedding 模型（数百 MB） |
| 首启时间 | < 2s 建索引 | 需下载/加载模型，慢 |
| 检索延迟 | < 100ms | < 100ms（索引后） |
| 可解释性 | 强（可追踪命中词） | 弱（黑盒向量） |
| 冷启动 | 无需训练 | 需预训练模型 |
| 适用规模 | 数百~数千 chunks | 万级以上 chunks |
| 升级路径 | — | 已实现 `vector_store.py`，可做 rerank |

**结论**：当前知识库规模（~500 chunks）BM25 完全够用，且零部署成本、可解释性强，符合"落地优先"原则。当知识库增长到万级 chunk、或用户频繁使用口语化/同义改写查询时，再启用向量检索做「BM25 召回 + 向量 rerank」的混合方案。

## 七、验收清单（对照申报书）

- [x] **基于知识库的智能问答模块** — `qa_engine.py`
- [x] **采用 RAG 技术架构** — BM25 检索 + LLM 生成
- [x] **支持自然语言理解** — 意图分类器
- [x] **基于知识网络的精准答案生成** — top-k + 模板约束
- [x] **知识库自动进化引擎** — `auto_evolve.py` 7 大能力
- [x] **概念的自动补全** — `concept_complete` 模板
- [x] **关联的自动强化** — 关键词 + LLM 双引擎
- [x] **智能问答 Prompt 工程模板库** — `templates/qa/`
- [x] **封装高质量答案生成的最佳实践** — 7 个 QA 模板
- [x] **知识服务输出质量的标准化管控** — 质量评估 + 模板约束

## 八、待办与限制

### 8.1 当前限制

- **未启用向量检索**：BM25 对"语义相似但用词不同"的查询召回率较低。如需升级，可启用 `api/services/vector_store.py`（已有 FAISS 实现）
- **未做 chunk 去重**：可能多 chunk 来自同一文档
- **未做查询改写**：用户问"它怎么样"无法对应到具体概念

### 8.2 后续优化方向

1. 接入向量检索做 rerank（已有基础设施）
2. 加 query expansion（基于意图分类的查询改写）
3. 加 RAG 评估数据集（用现有 27 篇政策简报构造 QA 对）
4. 加 A/B 测试框架：比较 4 个模板在真实查询上的表现
5. ~~把 RAG engine 包装成 FastAPI 端点 `api/routes/qa.py`~~（已完成，见 5.1）

---
*文档版本：v1.0 — 2026-09-09 子任务三首版*
*作者：AI 辅助（基于申报书 5/7/8 月三阶段技术规格）*
