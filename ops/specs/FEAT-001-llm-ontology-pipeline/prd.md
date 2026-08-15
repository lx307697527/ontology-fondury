# FEAT-001 · LLM 本体归纳与实例抽取管线

> 状态：W1 已交付（2026-08-16），W2-W4 推进中 · 关联：`docs/PLAN.md` 周里程碑 · 本目录三件套为本 feature 的权威记录

## 问题

Palantir 式企业 ontology 人工建模贵且慢（百万级咨询项目）。企业手里只有文档：产品手册、规章制度、话术脚本。需要一条管线把「文档 → 本体（object/link types）→ 实例图谱」自动化，且产物可信可治理。

## 目标用户与场景

1. **AI 应用知识层**：RAG / Agent 需要结构化、可遍历的企业知识，而非裸 chunk 检索
2. **企业数据知识化**：存量文档一次性知识化，图浏览 + REST/MCP 消费

演示滩头场景：保健品与大健康带货合规（`templates/health-commerce.yaml` 为人工参照本体；`samples/health-commerce/` 为演示文档）。

## 需求（IN）

1. 文档接入：txt/md/pdf/docx 上传 → 解析 → 滑窗分块
2. LLM 本体归纳（schema induction）：抽样片段 → object types + link types 草案（`provenance=llm`, `status=draft`）
3. LLM 实例抽取：在**已定义本体约束内**逐块抽取 objects/links，带置信度与来源 chunk 追溯
4. 治理基线：来源徽章（llm / llm_approved / human）、审核队列、审计日志、ExtractionRun 记录每次 LLM 调用

## 非目标（CUT，见 PLAN.md）

- Action Types 受控写回（Phase 2 第一优先级）
- RDF/OWL、实体对齐算法、多租户、向量语义搜索、数据源连接器

## 验收（DoD）

| 周 | DoD | 状态 |
|---|---|---|
| W1 | 真实企业文档经 API 返回 ≥3 个可读 object type 草案 | ✅ 8 个（2026-08-16） |
| W2 | `/api/objects/graph` ≥50 对象 ≥80 关系，前端图可浏览 | 进行中 |
| W3 | 审核 approve 徽章升级+审计；MCP endpoint 完成一次问答 | 待启动 |
| W4 | docker-compose 一键起 + 完整演示脚本 | 待启动 |

## 质量基线

`backend/eval/`：20 条人工标注归纳样本。v1 基线（deepseek-v4-pro@prompt-v1）：通过率 45%、平均召回 80.2%；修正评分别名后 70%。剩余失败集中于人员角色与组织单元概念被「克制建模」压掉——prompt v2 靶点。每周跑分对比见 `backend/eval/reports/`。
