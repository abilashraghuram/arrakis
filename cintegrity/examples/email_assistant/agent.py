"""Email Assistant Agent using Cintegrity + LangChain."""

import logging
import os

from langchain.agents import create_agent
from tools import TOOLS

from cintegrity.adapters.langchain import build_langchain_tools
from cintegrity.logger import LoggingConfig, configure_logging


def main():
    configure_logging(LoggingConfig(level=logging.DEBUG))
    if not os.getenv("OPENAI_API_KEY"):
        print("Missing `OPENAI_API_KEY`; set it to run this example.")
        print("Example: `export OPENAI_API_KEY=...`")
        return 1

    # Build tools with cintegrity
    tools, system_prompt, _ = build_langchain_tools(function_calls=TOOLS)
    print("tools", tools)

    # Create agent
    agent = create_agent(
        model="gpt-5.2",
        tools=tools,
        system_prompt=system_prompt,
    )

    # Run with a multi-step task
    user_message = "Read my inbox and send a summary of all emails to boss@company.com"

    for chunk in agent.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ]
        },
        stream_mode="values",
    ):
        # Each chunk contains the full state at that point
        latest_message = chunk["messages"][-1]
        if latest_message.content:
            print(f"Agent: {latest_message.content}")
            print("\n")
        elif latest_message.tool_calls:
            print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
            print("\n")


if __name__ == "__main__":
    exit(main())
