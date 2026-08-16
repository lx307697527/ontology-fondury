# MCP 客户端挂载配置

W3 的 MCP endpoint 以 **stdio** 暴露，外部 LLM 客户端挂载后即可把图谱当作工具集调用。工具：`list_object_types` / `list_link_types` / `search_objects(q, type_name?, limit?)` / `get_object_detail(object_id)`。

## 前置

- db 容器在跑：`docker compose up -d db`
- backend 依赖已装（含 fastmcp）：`cd backend && .venv/bin/pip install -e .`

## 通用：先验证 server 可起

```bash
cd backend && .venv/bin/python -m app.mcp_main
# 阻塞在 stdin 等待 JSON-RPC 即正常（stdio 协议）
```

或跑可复现演示脚本（不依赖外部 LLM）：

```bash
cd backend && .venv/bin/python ../scripts/mcp_demo.py
```

## Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "ontology-fondry": {
      "command": "/Users/liuxing/ontology-fondury/backend/.venv/bin/python",
      "args": ["-m", "app.mcp_main"],
      "cwd": "/Users/liuxing/ontology-fondury/backend"
    }
  }
}
```

重启 Claude Desktop，工具应出现在工具列表。问例：「褪黑素软糖用了哪些原料？有哪些达人推广？合规话术分级？」

## opencode

opencode 的 MCP 配置（`opencode.json` 或 `~/.config/opencode/opencode.json` 的 `mcp` 节）：

```json
{
  "mcp": {
    "ontology-fondry": {
      "type": "local",
      "command": ["/Users/liuxing/ontology-fondury/backend/.venv/bin/python", "-m", "app.mcp_main"],
      "cwd": "/Users/liuxing/ontology-fondury/backend"
    }
  }
}
```

> opencode 的 local MCP 即 stdio。command 为数组，首项是解释器，`-m app.mcp_main` 让包以模块方式启动（相对 import 正确）。

## Cursor

`.cursor/mcp.json`（项目根）：

```json
{
  "mcpServers": {
    "ontology-fondry": {
      "command": "/Users/liuxing/ontology-fondury/backend/.venv/bin/python",
      "args": ["-m", "app.mcp_main"],
      "cwd": "/Users/liuxing/ontology-fondury/backend"
    }
  }
}
```

## 演示问答（W3 DoD）

挂载后向客户端提问，验证工具链被正确调用：

1. 「褪黑素软糖用了哪些原料？」→ 客户端应调 `search_objects(q="褪黑素")` 找到产品对象，再 `get_object_detail` 遍历邻居（`contains_ingredient` 之类 link_type）。
2. 「有哪些达人推广？」→ `get_object_detail` 邻居（`promoted_by` 之类）。
3. 「合规话术分级？」→ `search_objects` 找话术/合规对象，`get_object_detail` 看分级属性或邻居。

截图/录屏落 `docs/demo/w3-mcp/`（人工产出，testplan 明确不自动化）。
