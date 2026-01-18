import asyncio
import os

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from cintegrity.adapters.prompt import SYSTEM_PROMPT


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY environment variable")
        return 1

    print("Connecting to cintegrity Gateway...")

    # Connect to the gateway (which has Versa MCP tools)
    async with MultiServerMCPClient(
        {
            "cintegrity": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }
    ) as client:
        tools = await client.get_tools()

        print(f"Loaded {len(tools)} tools from gateway:")
        for tool in tools:
            print(f"  - {tool.name}")
        print()

        # Create agent
        agent = create_agent(
            model="gpt-5.1",
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
        )

        # Run with a Versa-specific query
        user_message = "Branch-101 in New York is reporting connectivity issues."
        print(f"User: {user_message}")
        print("-" * 40)

        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode="values",
        ):
            latest_message = chunk["messages"][-1]
            if hasattr(latest_message, "content") and latest_message.content:
                print(f"Agent: {latest_message.content}")
            elif hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
                print(f"Calling: {[tc['name'] for tc in latest_message.tool_calls]}")


if __name__ == "__main__":
    asyncio.run(main())
