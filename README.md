# ontology-fondury

> Palantir 收几百万让人手工建的 ontology，我们让 LLM 一天建出来。

LLM 原生的企业知识图谱平台：上传企业文档 → LLM 自动归纳本体（object types / link types）并抽取实例构建图谱 → 通过图浏览、REST API、MCP 工具供人与 AI 应用消费。所有 LLM 产物带来源徽章（`llm` / `llm_approved` / `human`），人工审核升级可信度——治理与可信是护城河。

## 架构

```
文档(txt/md/pdf/docx) → 解析分块 → LLM 本体归纳 ─┬→ object_types ─→ objects
                                                └→ link_types   ─→ links
                                                        ↓
                            图可视化 / REST API / MCP tools ← 审核队列(来源徽章)
```

本体模型采用 Palantir Foundry 三原语的简化版（Object Type / Link Type；Action Type 留 Phase 2），绑定活数据、带置信度与来源追溯，不使用 RDF/OWL 作为内核。

## 快速启动

```bash
cp backend/.env.example backend/.env   # 填 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
docker compose up --build              # db :5432, api :8000, web :3000
# API 文档: http://localhost:8000/docs
```

本地裸跑后端：

```bash
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload
```

## 目录

```
backend/   FastAPI + SQLAlchemy + PostgreSQL；services/ 内为 LLM 管线
frontend/  Next.js 15 + Cytoscape.js 图浏览
docs/      PLAN.md — 一个月执行计划（范围、分工、周里程碑）
```

## 试用流程

1. `POST /api/documents` 上传一份企业文档（如产品说明、规章制度）
2. `POST /api/documents/{id}/process` 触发 LLM 归纳 + 抽取
3. `GET /api/ontology/object-types` 看本体草案 → `POST /api/review/object_type/{id}/approve` 审核
4. `GET /api/graph` 拿图谱在前端可视化，或让 AI 应用走 REST/MCP 查询
