from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPServerConfig:
    """Configuration for a single external MCP server."""

    name: str
    transport: str
    url: str | None = None
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None

    def __post_init__(self) -> None:
        if self.transport == "stdio" and not self.command:
            raise ValueError(f"stdio transport requires 'command' for server {self.name}")
        if self.transport in ("http", "streamable-http", "sse") and not self.url:
            raise ValueError(f"{self.transport} transport requires 'url' for server {self.name}")


def parse_mcp_config(config: dict[str, Any]) -> list[MCPServerConfig]:
    """Parse an MCPConfig dict into a list of MCPServerConfig objects.

    Expects format:
    {
        "mcpServers": {
            "server_name": {
                "url": "...",
                "transport": "streamable-http",
                "headers": {"Authorization": "Bearer ..."}
            },
            "another": {
                "command": "npx",
                "args": ["-y", "@some/mcp-server"],
                "transport": "stdio"
            }
        }
    }
    """
    servers: list[MCPServerConfig] = []
    mcp_servers = config.get("mcpServers", {})

    for name, server_config in mcp_servers.items():
        transport = server_config.get("transport", "stdio")
        servers.append(
            MCPServerConfig(
                name=name,
                transport=transport,
                url=server_config.get("url"),
                command=server_config.get("command"),
                args=server_config.get("args", []),
                env=server_config.get("env", {}),
                headers=server_config.get("headers", {}),
                cwd=server_config.get("cwd"),
            )
        )

    return servers
