"""Math operation tools for demonstrating mid-workflow parameter requests."""

from typing import TypedDict

# --- Tool Argument Types ---


class Func1Args(TypedDict):
    a: int
    b: int


class Func2Args(TypedDict):
    a: int
    b: int


class Func3Args(TypedDict):
    a: int
    b: int


class Func4Args(TypedDict):
    a: int
    b: int


# --- Tool Output Types ---


class MathResult(TypedDict):
    result: int


# --- Math Tools ---


def func1(args: Func1Args) -> MathResult:
    """Add two integers (a + b)."""
    result = args["a"] + args["b"]
    print(f"  [func1] {args['a']} + {args['b']} = {result}")
    return {"result": result}


def func2(args: Func2Args) -> MathResult:
    """Multiply two integers (a * b)."""
    result = args["a"] * args["b"]
    print(f"  [func2] {args['a']} * {args['b']} = {result}")
    return {"result": result}


def func3(args: Func3Args) -> MathResult:
    """Subtract b from a (a - b)."""
    result = args["a"] - args["b"]
    print(f"  [func3] {args['a']} - {args['b']} = {result}")
    return {"result": result}


def func4(args: Func4Args) -> MathResult:
    """Divide a by b (a / b)."""
    result = args["a"] // args["b"]  # Integer division
    print(f"  [func4] {args['a']} / {args['b']} = {result}")
    return {"result": result}


# Export all tools
TOOLS = [func1, func2, func3, func4]
