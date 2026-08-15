# FEAT-001 · 测试计划

## 层 1 · 归纳质量评估集（已有，每周跑）

`backend/eval/run_eval.py`：20 条跨领域人工标注样本，按（别名感知的）期望类型召回率计通过率。

- 基线：report-20260816-005919（45% 原始 / 70% 修正口径，召回 80.2%）
- 门槛：prompt v2 起，通过率不得低于上一版（回归红线）；每份报告落 `eval/reports/`
- 已知缺口（v2 靶点）：人员角色（mentor/technician/adjuster）、组织单元（branch）召回

## 层 2 · 单元级（现有为一次性脚本，W2 起固化 pytest）

- `parse_json` 七例：裸 JSON / ```json 栅栏 / 无语言栅栏 / 前后夹杂文字 / 字符串值含 `}` / 转义引号 / 纯文本须抛错 —— 已人工验证通过，待固化为 `backend/tests/test_llm_parse.py`
- `chunk_text`：空文本、短于块长、恰好整块、边界切割符优先级
- `_slug` / `_title_key` 归一化与去重合并语义

## 层 3 · API 契约（DoD 检查脚本化）

对跑通中的栈（db+api）按 `samples/health-commerce/` 演示文档验证：

1. `POST /api/documents` 上传 → status=parsed
2. `POST /{id}/process` → 轮询至 processed；extraction_runs 两行皆 ok 且 model 带 `@prompt-v`
3. `GET /api/ontology/object-types` ≥3 个可读草案（W1 DoD）
4. `GET /api/objects/graph` 节点/边数量门槛（W2 DoD：≥50/≥80）
5. `POST /api/review/object_type/{id}/approve` → provenance 变 llm_approved 且 audit_logs 有记录

## 层 4 · 错误路径

- 不支持的文件类型 → 文档落库带 error，process 返回 400
- LLM 连续 3 次非法 JSON → ExtractionRun failed，文档 failed，错误串落库
- LLM 不可达 → 客户端 120s 超时兜底，同上落 failed

## 不自动化的

- 前端图可视化人工走查（W2）
- MCP 端到端问答演示（W3，以演示脚本+录屏为准）
