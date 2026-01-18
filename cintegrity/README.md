# cintegrity

MCP gateway for restricted Python workflow execution with provenance tracking.

## Quick Start

```bash
# Install
uv sync

# Run MCP server (stdio)
uv run cintegrity-mcp --config mcp_server.json --transport stdio

# Run MCP server (SSE for agents)
uv run cintegrity-mcp --config mcp_server.json --transport streamable-http --port 8000
```

## Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cintegrity": {
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/codemode-py",
        "cintegrity-mcp", "--config", "mcp_server.json", "--transport", "stdio"
      ]
    }
  }
}
```

## MCP Config

Create `mcp_server.json` to connect external MCP servers:

```json
{
  "mcpServers": {
    "http_server": {
      "transport": "http",
      "url": "https://example.com/mcp/",
      "headers": { "Authorization": "Bearer TOKEN" }
    },
    "local_server": {
      "transport": "stdio",
      "command": "node",
      "args": ["server.js"]
    },
    "sse_server": {
      "transport": "sse",
      "url": "https://example.com/mcp"
    }
  }
}
```

**Transports:** `stdio` (requires `command`, `args`), `http`/`sse` (requires `url`)

## Exposed Tools

| Tool | Description |
|------|-------------|
| `search_tools(query)` | Search tools by name/description, returns schemas + import paths |
| `execute_workflow(planner_code)` | Execute restricted Python workflow |
| `execute_tool(tool_name, args)` | Execute single tool |
