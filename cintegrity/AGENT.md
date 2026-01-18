# AGENT.md

This document provides context, patterns, and guidelines for AI coding assistants working in this repository.

## Product Overview

cintegrity is an MCP gateway for workflow execution with data flow provenance tracking. It provides a lightweight, flexible framework for executing multi-step workflows with full per-argument provenance tracking and audit trails.

**Core Features:**
- MCP Gateway: FastMCP-based gateway server for tool orchestration
- Data Flow Tracking: Per-argument provenance through workflow execution (TRANSPARENT, INSTRUMENTED, NONE strategies)
- Workflow Execution: Multi-step Python workflows with automatic provenance capture
- Tool Management: Search tools, execute single tools, or execute complex workflows
- Async Core: Core functions async, adapters wrap with `asyncio.run()` for framework compatibility
- Adapter Support: LangChain and ADK adapters for easy integration
- Audit JSON Output: Complete execution traces with data flow graphs
- External MCP Integration: Connect to external MCP servers and proxy their tools

## Directory Structure

```
codemode-py/
│
├── src/cintegrity/                      # Main package source code
│   ├── gateway/                         # MCP gateway server
│   │   ├── server.py                    # FastMCP gateway (create_gateway)
│   │   ├── connector.py                 # Connect to external MCP servers
│   │   ├── manager.py                   # ToolManager facade
│   │   ├── config.py                    # MCP config parsing
│   │   ├── cli.py                       # CLI entrypoint
│   │   ├── errors.py                    # ToolExecutionError, WorkflowError
│   │   ├── prompts.py                   # WORKFLOW_DESCRIPTION for MCP tools
│   │   ├── tools/                       # Gateway tools exposed via MCP
│   │   │   ├── search_tools.py          # Search tools by query
│   │   │   ├── execute_tool.py          # Single tool execution
│   │   │   └── execute_workflow.py      # Multi-step workflow execution
│   │   └── search/                      # Tool search indexing
│   │       ├── base.py                  # SearchStrategy protocol
│   │       └── bm25.py                  # BM25 search implementation
│   │
│   ├── pybox/                           # Data flow tracking engine
│   │   ├── engine.py                    # WorkflowEngine orchestration
│   │   ├── bridge.py                    # ToolBridge protocol
│   │   ├── proxy.py                     # ToolProxy with provenance tracking
│   │   ├── factory.py                   # ProxyFactory creates tool proxies
│   │   ├── resolver.py                  # ValueResolver unwraps tracked values
│   │   ├── provenance.py                # Origin, ToolCallRecord, ExecutionResult
│   │   ├── importer.py                  # Dynamic import handling
│   │   ├── dataflow/                    # Tracking strategies
│   │   │   ├── base.py                  # TrackedValue, ValueWrapper protocols
│   │   │   ├── transparent.py           # TransparentValue (dunder methods)
│   │   │   ├── instrumented.py          # InstrumentedValue (AST transform)
│   │   │   ├── raw.py                   # RawValue (no tracking)
│   │   │   └── extractor.py             # OriginExtractor protocol
│   │   ├── runtime/                     # Code execution environments
│   │   │   ├── base.py                  # Runtime protocol
│   │   │   └── local.py                 # LocalRuntime (exec-based)
│   │   └── security/                    # Future: taint labels, policies
│   │
│   ├── adapters/                        # Agent framework adapters
│   │   ├── prompt.py                    # SYSTEM_PROMPT for framework integration
│   │   ├── shared.py                    # Shared tool factory
│   │   ├── langchain.py                 # LangChain adapter
│   │   └── mcp_gateway.py               # build_mcp_gateway helper
│   │
│   └── logging/                         # Structured logging
│       └── logger.py                    # Logging configuration
│
├── tests/                               # Unit tests (mirrors src/)
│   ├── conftest.py                      # Pytest fixtures
│   ├── gateway/                         # Gateway tests
│   │   ├── test_server.py
│   │   ├── test_manager.py
│   │   ├── test_config.py
│   │   └── tools/
│   │       ├── test_search_tools.py
│   │       ├── test_execute_tool.py
│   │       └── test_execute_workflow.py
│   └── pybox/                           # Pybox tests
│       ├── test_engine.py
│       ├── test_proxy.py
│       ├── test_resolver.py
│       ├── test_provenance.py
│       └── dataflow/
│           ├── test_transparent.py
│           ├── test_instrumented.py
│           └── test_raw.py
│
├── docs/                                # Developer documentation
│   ├── README.md                        # Docs folder overview
│   ├── STYLE_GUIDE.md                   # Code style conventions
│   └── PR.md                            # PR description guidelines
│
├── skill-plugin/                        # Claude Code skill integration
│   └── SKILL.md                         # Skill documentation
│
├── pyproject.toml                       # Project config (build, deps, tools)
├── CLAUDE.md                            # Main project instructions (symlink to AGENT.md)
├── AGENT.md                             # This file - guidance for AI coding assistants
├── mcp_server.json                      # MCP server configuration
└── Dockerfile                           # Container build definition
```

### Directory Purposes

- **`src/cintegrity/`**: All production code
- **`tests/`**: Unit tests mirroring src/ structure
- **`docs/`**: Developer documentation for contributors
- **`skill-plugin/`**: Claude Code skill integration

**IMPORTANT**: After making changes that affect the directory structure (adding new directories, moving files, or adding significant new files), you MUST update this directory structure section to reflect the current state of the repository.

## Development Workflow

### 1. Environment Setup

```bash
uv sync                                        # Install dependencies
pre-commit install -t pre-commit -t commit-msg # Install hooks (optional)
```

### 2. Making Changes

1. Create feature branch
2. Implement changes following the patterns below
3. Run quality checks before committing
4. Commit with conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
5. Push and open PR

### 3. Pull Request Guidelines

When creating pull requests, you MUST follow the guidelines in PR.md. Key principles:

Focus on WHY: Explain motivation and user impact, not implementation details
Document public API changes: Show before/after code examples
Be concise: Use prose over bullet lists; avoid exhaustive checklists
Target senior engineers: Assume familiarity with the SDK
Exclude implementation details: Leave these to code comments and diffs
See PR.md for the complete guidance and template.

### 4. Quality Gates

Run quality checks before committing:
- Formatting (ruff format)
- Linting (ruff check)
- Type checking (pyright)
- Tests (pytest)

Pre-commit hooks are optional but recommended for automatic enforcement.

## Coding Patterns and Best Practices

### Logging Style

Use structured logging with field-value pairs followed by human-readable messages:

```python
logger.debug("field1=<%s>, field2=<%s> | human readable message", field1, field2)
```

**Guidelines:**
- Add context as `FIELD=<VALUE>` pairs at the beginning
- Separate pairs with commas
- Enclose values in `<>` for readability (especially for empty values)
- Use `%s` string interpolation (not f-strings) for performance
- Use lowercase messages, no punctuation
- Separate multiple statements with pipe `|`

**Good:**
```python
logger.debug("user_id=<%s>, action=<%s> | user performed action", user_id, action)
logger.info("request_id=<%s>, duration_ms=<%d> | request completed", request_id, duration)
logger.warning("attempt=<%d>, max_attempts=<%d> | retry limit approaching", attempt, max_attempts)
```

**Bad:**
```python
logger.debug(f"User {user_id} performed action {action}")  # Don't use f-strings
logger.info("Request completed in %d ms.", duration)       # Don't add punctuation
```

### Type Annotations

All code must include type annotations:
- Function parameters and return types required
- No implicit optional types
- Use `typing` or `typing_extensions` for complex types
- Pyright type checking enforced
- Consider using [Pyrefly](https://pyrefly.org/) for runtime type validation when needed

```python
def execute_workflow(code: str, tracking: str | None = None) -> ExecutionResult:
    ...
```

### Docstrings

Use Google-style docstrings for all public functions, classes, and modules:

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of function.

    Longer description if needed. This docstring is used by LLMs
    to understand the function's purpose when used as a tool.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input is provided
    """
    pass
```

### Import Organization

Imports must be at the top of the file.

Imports are automatically organized by ruff/isort:
1. Standard library imports
2. Third-party imports
3. Local application imports

Use absolute imports for cross-package references, relative imports within packages.

```python
# Standard library
import logging
from typing import Any

# Third-party
from fastmcp import FastMCP

# Local
from cintegrity.gateway import ToolManager
from .tools import execute_workflow
```

### File Organization

- Each major feature in its own directory
- Base classes and interfaces defined first
- Implementation-specific code in separate files
- Private modules prefixed with `_`
- Test files prefixed with `test_`

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with `_`

### Error Handling

- Use custom exceptions from `cintegrity.gateway.errors`
- Provide clear error messages with context
- Don't swallow exceptions silently

## Testing Patterns

### Unit Tests (`tests/`)

- Mirror the `src/cintegrity/` structure exactly
- Focus on isolated component testing
- Use mocking for external dependencies
- Use fixtures from `tests/conftest.py`

```python
# tests/gateway/test_server.py mirrors src/cintegrity/gateway/server.py
```

### Test File Naming

- Unit tests: `test_{module}.py` in `tests/{path}/`

### Running Tests

```bash
PYTHONPATH=src uv run pytest                    # Run all tests
PYTHONPATH=src uv run pytest tests/gateway/     # Run specific directory
PYTHONPATH=src uv run pytest tests/pybox/ -v    # Run with verbose output
PYTHONPATH=src uv run pytest --cov              # Run with coverage
```

### Writing Tests

- Use pytest fixtures for setup/teardown
- Use `anyio` for async tests, not `asyncio`
- Keep tests focused and independent
- If pytest marks fail, use: `PYTEST_DISABLE_PLUGIN_AUTOLOAD="" PYTHONPATH=src uv run pytest`

## Things to Do

- Use explicit return types for all functions
- Write Google-style docstrings for public APIs
- Use structured logging format
- Add type annotations everywhere
- Use relative imports within packages
- Mirror src/ structure in tests/
- Run `uv run ruff format` and `uv run ruff check` before committing
- Run `uv run pyright` for type checking
- Follow conventional commits (`feat:`, `fix:`, `docs:`, etc.)

## Things NOT to Do

- Don't use f-strings in logging calls
- Don't use `Any` type without good reason
- Don't skip type annotations
- Don't put unit tests outside `tests/` structure
- Don't add punctuation to log messages
- Don't use implicit optional types
- Don't use pip - always use uv for package management

## Development Commands

```bash
# Environment
uv sync                                    # Install dependencies

# Formatting & Linting
uv run ruff format .                       # Format code
uv run ruff check .                        # Run linter
uv run pyright                             # Type checking

# Testing
PYTHONPATH=src uv run pytest               # Run tests
PYTHONPATH=src uv run pytest tests/pybox/ -v  # Run specific tests with verbose output

# MCP Server
uv run cintegrity-mcp --config mcp_server.json --transport stdio  # Run MCP server (stdio)
uv run cintegrity-mcp --config mcp_server.json --transport sse --port 8000  # Run MCP server (SSE)

# Pre-commit (optional)
pre-commit run --all-files                 # Run all hooks manually
```

## Agent-Specific Notes

### Writing Code

- Make the SMALLEST reasonable changes to achieve the desired outcome
- Prefer simple, clean, maintainable solutions over clever ones
- Reduce code duplication, even if refactoring takes extra effort
- Match the style and formatting of surrounding code
- Fix broken things immediately when you find them

### Code Comments

- Comments should explain WHAT the code does or WHY it exists
- NEVER add comments about what used to be there or how something changed
- NEVER refer to temporal context ("recently refactored", "moved")
- Keep comments concise and evergreen

### Code Review Considerations

- Address all review comments
- Test changes thoroughly
- Update documentation if behavior changes
- Maintain test coverage
- Follow conventional commit format for fix commits

## Additional Resources

- [CLAUDE.md](./CLAUDE.md) - Main project instructions (symlink to this file)
- [docs/](./docs/) - Developer documentation
  - [README.md](./docs/README.md) - Docs folder overview
  - [STYLE_GUIDE.md](./docs/STYLE_GUIDE.md) - Code style conventions
  - [PR.md](./docs/PR.md) - PR description guidelines