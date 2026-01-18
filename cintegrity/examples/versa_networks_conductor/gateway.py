"""cintegrity Gateway for Versa Networks Conductor.

Run this to start the gateway that aggregates the Versa MCP server.

Prerequisites:
    - Versa MCP server running at http://127.0.0.1:8001/sse

Usage:
    python gateway.py
"""

from cintegrity.gateway.server import create_gateway

# Connect to the Versa Networks Conductor MCP server
MCP_CONFIG = {
    "mcpServers": {
        "versa_networks_conductor": {
            "transport": "sse",
            "url": "http://127.0.0.1:8001/sse",
        },
    }
}


def main():
    print("Starting cintegrity Gateway for Versa Networks...")
    print("Gateway will be available at: http://localhost:8000/sse")
    print()
    print("Make sure the Versa MCP server is running at http://127.0.0.1:8001/sse")
    print()

    gateway = create_gateway(mcp_config=MCP_CONFIG)
    gateway.run(transport="sse")


if __name__ == "__main__":
    main()
