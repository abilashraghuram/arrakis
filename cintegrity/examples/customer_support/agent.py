"""Customer Support agent example."""

import json
import logging
import os

from langchain.agents import create_agent
from tools import TOOLS

from cintegrity.adapters.langchain import build_langchain_tools
from cintegrity.logger import LoggingConfig, configure_logging


def main():
    configure_logging(LoggingConfig(level=logging.INFO))
    if not os.getenv("OPENAI_API_KEY"):
        print("Missing `OPENAI_API_KEY`; set it to run this example.")
        return 1

    tools, system_prompt, _ = build_langchain_tools(function_calls=TOOLS)

    agent = create_agent(
        model="gpt-5.2",
        tools=tools,
        system_prompt=system_prompt,
    )

    user_message = """
    Review all open support tickets and escalate the high priority ones using the
    ticket subject as the reason. For each ticket, look up the customer details.
    Give me a summary of all tickets with their customer info and any escalations made.
    """

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
            content = latest_message.content
            if isinstance(content, str):
                s = content.strip()
                if s.startswith("{") or s.startswith("["):
                    try:
                        content = json.dumps(json.loads(s), indent=2)
                    except json.JSONDecodeError:
                        pass
        elif latest_message.tool_calls:
            print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
            print("\n")


if __name__ == "__main__":
    exit(main())
