"""Local runtime implementation.

Uses exec() for code execution - no sandboxing.
"""

import asyncio
from typing import Any

from ..importer import parse_imports, validate_imports


class LocalRuntime:
    """Local execution via exec() - no sandboxing.

    Implements Runtime protocol.
    Use for development and testing only.
    For production, use FirecrackerRuntime or SeatbeltRuntime.
    """

    # Builtin functions available without imports
    BUILTIN_FUNCTIONS: set[str] = {"elicit"}

    async def execute(
        self,
        code: str,
        namespace: dict[str, Any],
        timeout: float = 30.0,
        available_tools: set[str] | None = None,
    ) -> Any:
        """Execute workflow code.

        Args:
            code: Python code with imports and 'async def workflow():' function
            namespace: Dict of tool_name -> ToolProxy (all available tools)
            timeout: Execution timeout in seconds
            available_tools: Set of all available tool names for validation

        Returns:
            Return value from workflow execution

        Raises:
            ValueError: If code doesn't define 'async def workflow():'
        """
        # 1. Parse imports from code
        imports, code_without_imports = parse_imports(code)

        # 2. Validate imported tools exist
        if available_tools:
            validate_imports(imports, available_tools)

        # 3. Build restricted namespace with ONLY imported tools
        restricted_namespace: dict[str, Any] = {}
        for imp in imports:
            name = imp.alias or imp.tool_name
            if imp.tool_name in namespace:
                restricted_namespace[name] = namespace[imp.tool_name]

        # Inject builtin functions (available without imports)
        for builtin_name in self.BUILTIN_FUNCTIONS:
            if builtin_name in namespace:
                restricted_namespace[builtin_name] = namespace[builtin_name]

        # 4. Execute code (must define async def workflow())
        exec(code_without_imports, restricted_namespace)

        # 5. Validate and call workflow function
        if "workflow" not in restricted_namespace:
            raise ValueError("Workflow code must define 'async def workflow():'")
        workflow_fn = restricted_namespace["workflow"]
        return await asyncio.wait_for(workflow_fn(), timeout=timeout)
