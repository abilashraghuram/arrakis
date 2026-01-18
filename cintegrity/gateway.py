"""FastMCP Cloud entrypoint for cintegrity gateway.

FastMCP Cloud supports FastMCP 2.0 servers.
This file creates the FastMCP server instance that FastMCP Cloud will run.

The gateway exposes only 3 tools: search_tools, execute_tool, execute_workflow.
Versa tools are added to the ToolManager as a local server, so they're
searchable via search_tools but not directly exposed as MCP tools.
"""

from cintegrity.gateway.server import create_gateway
from cintegrity.versa import tools as versa_tools

# Create the gateway with versa tools as a local server
# This adds versa tools to the ToolManager (searchable via search_tools)
# but only exposes the 3 gateway tools via MCP
# Input/output schemas are inferred automatically from function signatures
mcp = create_gateway(
    local_servers={"versa": versa_tools},
)
