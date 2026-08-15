# ontology-fondry · 一个月执行计划

> 定稿日期：2026-08-15 · 团队：4 名开发工程师 · 周期：1 个月（至 2026-09-15）

## 一、锁定决策

| 决策项 | 结论 |
|---|---|
| 产品路线 | Palantir 式私有企业操作层（商业产品），非 OBO 式开放注册库 |
| 一句话定位 | Palantir 收几百万让人手工建的 ontology，我们让 LLM 一天建出来 |
| 滩头场景 | 双场景共享同一条管线：文档/数据 → LLM 建本体+图谱 → API/浏览消费。① AI 应用知识层（RAG/Agent 记忆）② 企业数据知识化 |
| 护城河 | 治理与可信（来源徽章 + 人机协同审核）+ 本体约束生成（LLM 在受控 schema 内抽取） |
| 本体模型 | Palantir 三原语简化版：Object Type / Link Type /（Action Type 留 Phase 2），绑定活数据，不用 RDF/OWL 做内核 |

## 二、范围（一个月版）

**做（IN）：**
1. 文档接入：txt / md / pdf / docx 上传 → 解析 → 分块
2. LLM 本体归纳（schema induction）：从文档提出 object types + link types（草稿态）
3. LLM 实例抽取：按已定义本体抽取对象与关系，构建图谱，带置信度与来源块
4. 浏览与检索：对象类型目录、图可视化（Cytoscape.js）、对象详情+邻居遍历、全文搜索
5. REST API：对象查询 / 关系遍历 / 搜索 —— 供 AI 应用作为知识层调用
6. 治理 lite：provenance 徽章（`llm` / `llm_approved` / `human`）、审核队列、审计日志

**砍（CUT，进 Phase 2+）：**
- Action Types 受控写回（Phase 2 第一优先级——没有它只是"贵仪表盘"）
- SPARQL / RDF 导入导出、实体对齐算法（仅做 title 归一化去重）、多租户与权限体系（单租户 + API Key）
- 流式索引、本体版本分支、向量语义搜索（表结构预留，月内不实现）、数据源连接器（只做文档上传）

## 三、技术栈

- 后端：Python 3.12 + FastAPI + SQLAlchemy 2 + PostgreSQL 16（JSONB 存动态属性 + ILIKE/pg_trgm 全文搜索）
- LLM：OpenAI 兼容协议（base_url 可配，兼容 DeepSeek / GLM / Qwen），结构化 JSON 输出
- 前端：Next.js 15 + TypeScript + Cytoscape.js
- 部署：docker-compose（db + api + web）

## 四、数据模型（核心架构决策）

```
documents ──< chunks ──< (LLM 抽取) ──┬── object_types ──< objects
                                      └── link_types  ──< links (source→target objects)
extraction_runs（每次 LLM 调用的审计）   audit_logs（所有人工操作）
```

- `object_types.properties` 用 JSONB 存属性定义（name/display_name/dtype/description），Palantir 式动态 schema
- 所有 LLM 产物带 `provenance`（llm/human/llm_approved）+ `confidence`，审核通过即升级徽章
- objects 按 `(object_type_id, title_key)` 去重合并，links 按 `(link_type_id, source, target)` 唯一约束

## 五、分工（4 人）

| 角色 | 职责 |
|---|---|
| A · 后端/存储 | 数据模型、API 层、搜索、部署脚本 |
| B · LLM 管线 | schema induction 提示词工程、实例抽取、去重合并策略、抽取质量评估集 |
| C · 前端 | 上传流、本体目录、图可视化、审核队列 UI |
| D · 集成/交付 | MCP endpoint（把图谱暴露为 LLM 工具，滩头场景①的钩子）、演示场景数据、文档、联调兜底 |

## 六、周里程碑（每周末演示，定义完成 = DoD）

- **W1**：跑通"上传 → 解析分块 → LLM 归纳出第一批 object types（草稿）"。DoD：对一份真实企业文档，API 返回 ≥3 个可读的 object type 草案。
- **W2**：图谱成形。DoD：`/api/graph` 返回 ≥50 对象 ≥80 关系，前端图可浏览；REST 查询/遍历可用。
- **W3**：治理与消费闭环。DoD：审核队列可 approve（徽章升级+审计）；MCP endpoint 可被外部 LLM 客户端调用完成一次问答。
- **W4**：端到端硬化。DoD：docker-compose 一键起；一个完整演示脚本（企业文档 → 图谱 → Agent 问答）；错误路径有兜底；周报可对外。

## 七、风险与对策

- **LLM 抽取质量不稳** → B 在 W1 就建 20 条人工标注的评估样本，每周跑通过率；提示词版本化（prompt v1/v2…）
- **1 个月做不完** → 每周五对照 DoD 砍尾部功能（先砍 MCP，再砍审核 UI 用 API 顶替），In 列表之外一律不接
- **范围蠕变** → 任何新需求进 Phase 2 表，本月不动
