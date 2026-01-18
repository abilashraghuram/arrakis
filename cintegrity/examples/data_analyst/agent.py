"""Data Analyst Agent demonstrating secure workflow execution.

The agent discovers tools and executes workflows through cintegrity.
"""

import json
import os

from langchain.agents import create_agent
from tools import TOOLS

from cintegrity.adapters.langchain import build_langchain_tools


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Missing `OPENAI_API_KEY`; set it to run this example.")
        return 1

    # Build tools with cintegrity
    tools, system_prompt, _ = build_langchain_tools(
        function_calls=TOOLS,
    )

    agent = create_agent(
        model="gpt-5.2",
        tools=tools,
        system_prompt=system_prompt,
    )

    # Simple task - the system prompt guides the agent to discover tools
    # and use execute_workflow for multi-step operations
    user_message = """
    Analyze the sales_2024 dataset and give me total revenue by region.
    Save the report to "q4_analysis.txt".
    """

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": user_message}]},
        stream_mode="values",
    ):
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
