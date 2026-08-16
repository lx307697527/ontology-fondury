# MCP 层

FastMCP（stdio）server：把知识图谱暴露为 LLM 工具，供外部 LLM 客户端（Claude Desktop / opencode / Cursor）挂载完成问答。这是滩头场景①（AI 应用知识层）的消费钩子。

## Key files

- `server.py` — FastMCP 实例 + 四个工具：list_object_types / list_link_types / search_objects(q, type_name?, limit?) / get_object_detail(object_id)。工具用 app.db.SessionLocal 手动开 session（不走 FastAPI Depends），查询逻辑与 modules/api 下的 objects.py、search.py 对齐。

## 约定

- 工具返回纯 dict/list（JSON 可序列化），不放 ORM 对象 —— MCP 经 stdio 序列化给客户端。
- 入口在 app 根（非本目录）：app/mcp_main.py，运行 `python -m app.mcp_main`（mcp.run() 默认 stdio 传输）。
- 改工具签名/语义 → 同步更新 docstring（LLM 据此判断何时调用）与 docs/mcp-client-config.md。
- 复用 modules/api 的查询模式（ILIKE + type 过滤、邻居遍历 direction），不重复发明；新增图谱查询能力时，API 与 MCP 工具同步暴露。
