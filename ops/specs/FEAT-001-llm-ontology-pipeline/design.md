# FEAT-001 · 设计

## 数据模型（Palantir 三原语简化版）

```
documents ──< chunks ──< (LLM) ──┬── object_types ──< objects (JSONB 动态属性)
                                 └── link_types   ──< links (source→target)
extraction_runs（每次 LLM 调用审计）   audit_logs（人工操作）
```

- `object_types.properties` JSONB 存 `[{name, display_name, dtype, description}]`，动态 schema
- 一切 LLM 产物带 `provenance`（llm/human/llm_approved）+ `confidence`；approve 升级徽章
- 去重：objects 按 `(object_type_id, title_key)` 合并（属性并集、置信度取 max、来源 chunk 追加）；links 按 `(link_type_id, source, target)` 唯一

## 管线（`pipeline.run_pipeline`，后台任务）

1. 分块：`parsing.chunk_text`，size 1200 / overlap 150，每文档上限 60 块
2. 归纳：前 8 块抽样 → `llm.induce_schema` → `_merge_proposed_schema` 按 name 去重落库（草案态）
3. 抽取：逐块 `llm.extract_instances`，本体 digest 作为硬约束（禁止发明类型）
4. 审计：两个 ExtractionRun（induction/extraction），`model` 字段记 `<model>@prompt-<N>`

## LLM 层（`services/llm.py`）

- OpenAI 兼容协议，base_url/model/key 全配置化（DeepSeek/GLM/Qwen 均可）
- 结构化 JSON 输出：`parse_json` 三级容错（裸 JSON / markdown 栅栏 / 字符串感知的花括号配平）+ 解析失败带错误重试（3 次）
- 客户端显式 timeout 120s（防 SDK 默认 600s × 重试叠加拖死管线）
- 提示词版本化：改动提示词必须递增 `PROMPT_VERSION`，随 ExtractionRun 落库可追溯

## 关键取舍

- **不用 RDF/OWL 做内核**：绑定活数据与运营语义（Palantir 路线），JSONB 动态属性优于三方本体标准
- **抽取受本体约束**：归纳与抽取分离，抽取阶段只见 digest——LLM 不在抽取时发明 schema，治理后置到审核队列
- **单租户 + API Key**：一个月内不做权限体系（PLAN.md 锁定决策）

## 影响 / blast-radius

方法：`rg -n "def (induce_schema|extract_instances|run_pipeline|_process|_merge_proposed_schema)|class LLM" backend/app`，对核心入口逐一定位（2026-08-16 核验）：

| 入口 | 位置 |
|---|---|
| LLM 客户端与提示词 | `backend/app/modules/services/llm.py:39` |
| 归纳调用 | `backend/app/modules/services/llm.py:71` |
| 抽取调用 | `backend/app/modules/services/llm.py:75` |
| 管线编排 | `backend/app/modules/services/pipeline.py:18` |
| 逐阶段流程 | `backend/app/modules/services/pipeline.py:36` |
| schema 合并落库 | `backend/app/modules/services/pipeline.py:87` |
| 触发点（API） | `backend/app/modules/api/documents.py:50` |

改动 `llm.py` 提示词 → 影响所有后续 ExtractionRun 的产物语义（需递增版本号）；改动 `models.py`（127 行）/`schemas.py`（138 行）→ 迁移影响全部五个 API 模块与前端。
