"""cintegrity MCP Gateway CLI."""

import argparse
import json
from pathlib import Path

from ..logger import configure_logging
from .server import create_gateway


def main() -> None:
    parser = argparse.ArgumentParser(description="cintegrity MCP Gateway")
    parser.add_argument("--config", type=Path, help="Path to MCP config JSON")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse", "streamable-http"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # Configure logging with file handler
    configure_logging()

    mcp_config = None
    if args.config:
        mcp_config = json.loads(args.config.read_text())

    mcp = create_gateway(function_calls=[], mcp_config=mcp_config)

    # FastMCP 2.0 handles all transports via mcp.run()
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
