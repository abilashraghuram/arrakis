"""System prompt for agent framework integration."""

from __future__ import annotations

SYSTEM_PROMPT = """
## Available Tools

- `search_tools(query)` - Find tools and their schemas
- `execute_tool(tool_name, args)` - Execute single tool
- `execute_workflow(planner_code)` - Execute Python workflow

## Workflow Structure

```python
from cintegrity.mcp_tools.<server> import <tool_name>

async def workflow():
    result = await <tool_name>(arg=value)
    return result
```

## Return Value Handling

Tools return values directly:

**Scalars** (int, str, bool): Assign directly to variables
```python
count = await add(a=10, b=5)        # Returns: 15
total = await multiply(a=count, b=2) # Returns: 30
```

**Objects** (dict): Access fields by name
```python
user = await get_user(id=123)  # Returns: {"name": "Alice", "age": 30}
name = user["name"]
```

**User Input**: Request values with `elicit()`
```python
c = await elicit(message="Enter value:", response_type=int)  # Returns: 42
```

## Complete Example

```python
from cintegrity.mcp_tools.database import get_user, update_score

async def workflow():
    # Get user data (returns dict)
    user = await get_user(user_id=123)
    current_score = user["score"]

    # Request bonus points
    bonus = await elicit(message="Enter bonus points:", response_type=int)

    # Calculate new score (scalar)
    new_score = await update_score(user_id=123, score=current_score + bonus)

    return {"user": user["name"], "new_score": new_score}
```
""".strip()
