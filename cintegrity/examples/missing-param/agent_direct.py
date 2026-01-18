"""Math Workflow Agent demonstrating mid-workflow parameter handling."""

import asyncio
import logging
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from cintegrity.logger import LoggingConfig, configure_logging


async def main():
    log_file = Path(__file__).parent / "log.txt"
    configure_logging(LoggingConfig(level=logging.DEBUG, file=str(log_file)))

    if not os.getenv("OPENAI_API_KEY"):
        print("Missing `OPENAI_API_KEY`; set it to run this example.")
        print("Example: `export OPENAI_API_KEY=...`")
        return 1

    # Connect to the gateway (which has MCP tools)
    client = MultiServerMCPClient(
        {
            "cintegrity": {
                "url": "http://localhost:9999/mcp",
                "transport": "http",
            }
        }
    )
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools from gateway:")
    for tool in tools:
        print(f"  - {tool.name}")
    print()

    agent = create_agent(model="gpt-5.2", tools=tools)
    # agent = create_agent(model="claude-sonnet-4-5-20250929", tools=tools, system_prompt=SYSTEM_PROMPT)

    user_message = "what is (a func1 (b func2 a)) func3 c, where a=10, b=2"

    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_message}]},
        stream_mode="values",
    ):
        msg = chunk["messages"][-1]
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"Tool calls: {[tc['name'] for tc in msg.tool_calls]}")
        elif hasattr(msg, "content") and msg.content:
            print(f"Agent response: {msg.content[:100]}")

    print(f"\nLogs written to: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())
