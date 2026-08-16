"""W3 MCP 演示：用 fastmcp.Client 以 stdio 连本地 MCP server，串调四工具，
打印 LLM 可消费的结构化结果。不依赖外部 LLM，可复现。

真实问答演示（挂 opencode / Claude Desktop / Cursor）见 docs/mcp-client-config.md，
录屏/截图落 docs/demo/w3-mcp/（testplan 明确不自动化）。
"""

import asyncio
import json
import os
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
VENV_PY = os.path.join(BACKEND, ".venv", "bin", "python")


def _parse(res):
    """工具返回 dict/list 时优先取 structured data，否则从 content 文本解析。"""
    data = getattr(res, "data", None)
    if data is not None:
        return data
    if res.content:
        try:
            return json.loads(res.content[0].text)
        except Exception:
            return res.content[0].text
    return None


def _show(label, obj, limit=1000):
    print(f"\n== {label} ==")
    txt = json.dumps(obj, ensure_ascii=False, indent=2)
    print(txt[:limit] + (" …(truncated)" if len(txt) > limit else ""))


async def main():
    if not os.path.exists(VENV_PY):
        sys.exit(f"找不到 venv python：{VENV_PY}（先 cd backend && .venv/bin/pip install -e .）")
    transport = StdioTransport(command=VENV_PY, args=["-m", "app.mcp_main"], cwd=BACKEND)
    async with Client(transport) as client:
        tools = await client.list_tools()
        _show("tools", [t.name for t in tools])

        ots = _parse(await client.call_tool("list_object_types", {}))
        _show("list_object_types (前 3)", (ots or [])[:3])

        objs = _parse(await client.call_tool("search_objects", {"q": "褪黑素", "limit": 10}))
        _show("search_objects('褪黑素')", objs)

        if objs:
            oid = objs[0]["id"]
            det = _parse(await client.call_tool("get_object_detail", {"object_id": oid}))
            _show(f"get_object_detail({oid})", det)

        lts = _parse(await client.call_tool("list_link_types", {}))
        _show("list_link_types (前 5)", (lts or [])[:5])


if __name__ == "__main__":
    asyncio.run(main())
