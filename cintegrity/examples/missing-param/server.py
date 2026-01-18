from fastmcp import FastMCP

mcp = FastMCP("Test MCP server")


@mcp.tool
def func1(a: int, b: int) -> int:
    """func1 2 integers"""
    return a + b


@mcp.tool
def func2(a: int, b: int) -> int:
    """func2 2 integers"""
    return a * b


@mcp.tool
def func3(a: int, b: int) -> int:
    """func3 b from a"""
    return a - b


@mcp.tool
def func4(a: int, b: int) -> int:
    """func4 b by a"""
    return a / b


if __name__ == "__main__":
    mcp.run(transport="http", port=9999)
