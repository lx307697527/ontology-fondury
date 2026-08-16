"""FastMCP stdio 入口：`.venv/bin/python -m app.mcp_main`。

供外部 LLM 客户端（Claude Desktop / opencode / Cursor）以 stdio 挂载。客户端配置见
docs/mcp-client-config.md。工具定义见 app.modules.mcp.server。
"""

from app.modules.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()  # 默认 stdio 传输
