"""Tests for ToolManager and schema transformation functions."""

from __future__ import annotations

from cintegrity.gateway.manager import _unwrap_output_schema

# =============================================================================
# Test _unwrap_output_schema
# =============================================================================


def test_unwrap_output_schema_scalar():
    """FastMCP scalar wrapper should be unwrapped."""
    wrapped = {
        "type": "object",
        "properties": {"result": {"type": "integer"}},
        "required": ["result"],
    }
    result = _unwrap_output_schema(wrapped)
    assert result == {"type": "integer"}


def test_unwrap_output_schema_scalar_string():
    """FastMCP string scalar wrapper should be unwrapped."""
    wrapped = {
        "type": "object",
        "properties": {"result": {"type": "string"}},
        "required": ["result"],
    }
    result = _unwrap_output_schema(wrapped)
    assert result == {"type": "string"}


def test_unwrap_output_schema_scalar_boolean():
    """FastMCP boolean scalar wrapper should be unwrapped."""
    wrapped = {
        "type": "object",
        "properties": {"result": {"type": "boolean"}},
    }
    result = _unwrap_output_schema(wrapped)
    assert result == {"type": "boolean"}


def test_unwrap_output_schema_structured():
    """Multi-field objects should remain as-is."""
    structured = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
    }
    result = _unwrap_output_schema(structured)
    assert result == structured


def test_unwrap_output_schema_nested_object():
    """Nested objects with multiple fields should remain as-is."""
    nested = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            },
            "status": {"type": "string"},
        },
    }
    result = _unwrap_output_schema(nested)
    assert result == nested


def test_unwrap_output_schema_none():
    """None schema should return None."""
    result = _unwrap_output_schema(None)
    assert result is None


def test_unwrap_output_schema_non_object():
    """Non-object schemas should remain as-is."""
    array_schema = {"type": "array", "items": {"type": "string"}}
    result = _unwrap_output_schema(array_schema)
    assert result == array_schema


def test_unwrap_output_schema_empty_object():
    """Empty object schema should remain as-is."""
    empty = {"type": "object", "properties": {}}
    result = _unwrap_output_schema(empty)
    assert result == empty


def test_unwrap_output_schema_no_properties():
    """Object without properties field should remain as-is."""
    no_props = {"type": "object"}
    result = _unwrap_output_schema(no_props)
    assert result == no_props
