# Services 层

LLM 管线与文本处理。所有外部模型调用只发生在 `llm.py`，所有编排只发生在 `pipeline.py`。

## Key files

- `llm.py` — OpenAI 兼容客户端、induction/extraction 提示词（`PROMPT_VERSION` 递增落库）、`parse_json` 容错解析与重试
- `parsing.py` — txt/md/pdf/docx 文本抽取与滑窗分块（chunk_size/overlap 见 config）
- `pipeline.py` — 管线编排：分块 → schema 归纳与合并 → 逐块实例抽取 → upsert 去重合并；ExtractionRun 审计

## 约定

- 提示词改动必须递增 `PROMPT_VERSION`（v1/v2…），随 ExtractionRun.model 落库
- objects 按 (object_type_id, title_key) 去重合并属性取并集，links 按三元组唯一
- 评估集与跑分脚本在 `../../../eval/`（backend/eval，不在本模块地图管辖内）
