# RAG 评估集使用说明

本目录是 RAG 智能问答引擎的回归评估集。

## 格式（JSONL，每行一条用例）

```json
{
  "query": "用户问题",
  "expected_intent": "policy_query | concept_explain | relation_analysis | synthesis | fallback",
  "expected_keywords": ["期望命中的关键词1", "关键词2"]
}
```

字段说明：
- `query`：用户问题
- `expected_intent`：期望的意图分类（可选）
- `expected_keywords`：top-5 检索结果中应包含的关键词（用于计算检索命中率）

## 示例

```json
{"query": "湖北省数字经济政策有哪些？", "expected_intent": "policy_query", "expected_keywords": ["湖北", "数字经济", "政策"]}
{"query": "什么是新质生产力？", "expected_intent": "concept_explain", "expected_keywords": ["新质", "生产力"]}
{"query": "5G 和 5G-A 有什么区别？", "expected_intent": "relation_analysis", "expected_keywords": ["5G", "5G-A"]}
```

## 运行评估

```bash
# 1. CLI
python3 scripts/qa_engine.py --rebuild-index

# 2. HTTP API
curl -X POST http://localhost:8000/qa/evaluate \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是新质生产力？", "save": false}'
```

## 评估指标

- **intent_accuracy**：意图分类正确率
- **retrieval_hit_at_5**：top-5 检索中任一 chunk 包含 expected_keywords 的命中率

目标：intent_accuracy ≥ 0.80，retrieval_hit_at_5 ≥ 0.70。

## 维护规则

- 新增用例：在 PR 中说明背景
- 调权：expected_keywords 调整需团队确认
- 失效用例：知识库删除后 30 天内必须移除
