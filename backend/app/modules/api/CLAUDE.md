# API 层

FastAPI 路由层：每个领域一个模块，挂载见 `app/main.py`。无业务逻辑，只做参数校验、会话管理与调用 modules/services。

## Key files

- `documents.py` — 文档上传/列表/删除与 process 触发管线（后台任务）。不支持的文件类型：落库 `status=failed` + `error`，`process` 据 `not raw_text` 返回 400（FEAT-001 层 4 错误路径）
- `ontology.py` — object types / link types 的 CRUD（人工创建即 provenance=human）
- `objects.py` — 对象查询、图谱快照（GET /api/objects/graph）、对象详情+邻居遍历；ObjectOut/NeighborOut 带 object_type_name（list/detail/neighbor 统一经 `_with_type_name` join ObjectType 填充）
- `review.py` — 审核队列与 approve/reject（四类实体：object_type/link_type/object/link）。/queue 列四类 draft 行，links 经 join LinkType + source/target Object（aliased 同表两次）取 title 填 LinkOut。approve 使徽章 llm 升为 llm_approved（仅当原 provenance==llm）、status→approved；reject → status=archived；两者写 audit_logs（detail.comment）。Link.status 由 db.run_legacy_migrations 幂等补列（无 Alembic）。
- `search.py` — ILIKE 全文搜索（objects 与 chunks）

## 约定

- 路由自身不带 prefix，由 main.py 挂载时统一给 /api/<name>（历史 bug：双层前缀）
- 返回 ORM 对象时用 `app/schemas.py` 的 Out 模型；review.py 的队列是例外（直接序列化）
