# 模板库说明

本目录是「在岗技术革新」项目（子任务三：知识库智能进化与问答服务）的 Prompt 工程模板库。

## 目录结构

```
templates/
├── README.md                       # 本文件
├── qa/                             # 问答场景 Prompt 模板
│   ├── policy_query.md             # 政策查询（用户问"X 领域有什么政策"）
│   ├── concept_explain.md          # 概念解释（用户问"什么是 X"）
│   ├── relation_analysis.md        # 关联分析（用户问"X 和 Y 有什么关系"）
│   ├── synthesis.md                # 综合问答（用户问开放式问题）
│   ├── fallback.md                 # 未知兜底（检索不到任何相关内容时）
│   ├── intent_classify.md          # 查询意图分类（路由到上面 4 个场景）
│   └── quality_eval.md             # 答案质量评估
└── evolution/                      # 知识库自动进化 Prompt 模板
    ├── concept_complete.md         # 补全概念定义
    ├── concept_link.md             # 推荐概念关联
    ├── contradiction_check.md      # 矛盾检测
    └── qa_to_concept.md            # 问答转概念
```

## 模板格式约定

每个模板是一个独立 Markdown 文件，含 3 段：

1. **Front matter**：模板元信息（名称、用途、调用时机、输入输出 schema）
2. **System Prompt**：直接喂给 LLM 的 system 消息，含角色设定、约束、输出格式
3. **Few-shot 示例**：1-2 组标准问答样例（仅部分模板有）

## 调用方式

`scripts/qa_engine.py` 通过 `templates.load_template(name, kind)` 接口加载模板：

```python
from qa_engine import load_template
system_prompt, examples = load_template("qa", "policy_query")
```

## 维护规则

- 模板命名：小写 + 下划线，与文件名一致
- 模板更新：在 PR 中说明背景、给出 before/after 对比
- 新增模板：先在 `qa/` 写一版，跑 5 条真实查询验证，再合并

---
*最后更新：2026-09-09 — 子任务三首版*
