# API 层

FastAPI 路由层：每个领域一个模块，挂载见 `app/main.py`。无业务逻辑，只做参数校验、会话管理与调用 modules/services。

## Key files

- `documents.py` — 文档上传/列表/删除与 process 触发管线（后台任务）
- `ontology.py` — object types / link types 的 CRUD（人工创建即 provenance=human）
- `objects.py` — 对象查询、图谱快照（GET /api/objects/graph）、对象详情+邻居遍历；ObjectOut/NeighborOut 带 object_type_name（list/detail/neighbor 统一经 `_with_type_name` join ObjectType 填充）
- `review.py` — 审核队列与 approve/reject（approve 使徽章 llm 升为 llm_approved）
- `search.py` — ILIKE 全文搜索（objects 与 chunks）

## 约定

- 路由自身不带 prefix，由 main.py 挂载时统一给 /api/<name>（历史 bug：双层前缀）
- 返回 ORM 对象时用 `app/schemas.py` 的 Out 模型；review.py 的队列是例外（直接序列化）
