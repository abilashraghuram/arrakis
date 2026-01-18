"""
Mock HTTP Client

A drop-in replacement for httpx.AsyncClient that returns mock data.
Toggle with MOCK_MODE=true environment variable.
"""

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .endpoint_map import ENDPOINT_TO_MOCK, normalize_endpoint
from .id_registry import (
    is_valid_appliance_name,
    is_valid_appliance_uuid,
    is_valid_device_group_name,
    is_valid_org_name,
    is_valid_template_name,
)

MOCK_DIR = Path(__file__).parent


class MockResponse:
    """Mock HTTP response that mimics httpx.Response"""

    def __init__(self, data: dict[str, Any], status_code: int = 200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def json(self) -> dict[str, Any]:
        return self._data


class MockAsyncClient:
    """
    Mock async HTTP client that returns data from JSON files.

    Usage:
        async with MockAsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            data = response.json()
    """

    def __init__(self, verify: bool = True, **kwargs):
        self.verify = verify

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def _extract_endpoint(self, url: str) -> str:
        """Extract the endpoint path from a full URL."""
        parsed = urlparse(url)
        return parsed.path

    def _extract_path_params(self, endpoint: str, pattern: str) -> dict[str, str]:
        """Extract path parameter values from endpoint using pattern."""
        # Convert pattern placeholders to regex capture groups
        regex_pattern = pattern
        param_names = re.findall(r"\{([^}]+)\}", pattern)

        # Replace {param} with named capture groups
        for param_name in param_names:
            regex_pattern = regex_pattern.replace(f"{{{param_name}}}", f"(?P<{param_name}>[^/]+)")

        regex_pattern = f"^{regex_pattern}$"

        # Match and extract parameters
        match = re.match(regex_pattern, endpoint)
        if match:
            return match.groupdict()
        return {}

    def _validate_path_params(self, pattern: str, path_params: dict[str, str]) -> tuple[bool, str | None]:
        """
        Validate path parameter values against ID registry.
        Returns (is_valid, error_message).
        """
        for param_name, param_value in path_params.items():
            # Check different parameter types
            if param_name in ("Uuid", "applianceUUID", "id"):
                if not is_valid_appliance_uuid(param_value):
                    return False, f"Appliance with UUID '{param_value}' not found"

            elif param_name in ("applianceName", "deviceName"):
                if not is_valid_appliance_name(param_value):
                    return (
                        False,
                        f"Appliance/device with name '{param_value}' not found",
                    )

            elif param_name == "deviceGroupName":
                if not is_valid_device_group_name(param_value):
                    return False, f"Device group '{param_value}' not found"

            elif param_name in ("templateworkflowName", "templateName"):
                if not is_valid_template_name(param_value):
                    return False, f"Template '{param_value}' not found"

            elif param_name == "org":
                if not is_valid_org_name(param_value):
                    return False, f"Organization '{param_value}' not found"

        return True, None

    def _load_mock(self, endpoint: str) -> tuple[dict[str, Any], int]:
        """
        Load mock data from JSON file for the given endpoint.
        Returns (data, status_code).
        """
        # Normalize the endpoint to match a pattern
        pattern = normalize_endpoint(endpoint, "")
        mock_file = ENDPOINT_TO_MOCK.get(pattern)

        if not mock_file:
            return {
                "error": "No mock mapping for endpoint",
                "endpoint": endpoint,
                "available_patterns": list(ENDPOINT_TO_MOCK.keys())[:5],
            }, 500

        # Extract and validate path parameters
        path_params = self._extract_path_params(endpoint, pattern)
        if path_params:
            is_valid, error_message = self._validate_path_params(pattern, path_params)
            if not is_valid:
                return {
                    "error": error_message,
                    "endpoint": endpoint,
                    "status": "NOT_FOUND",
                }, 404

        # Load mock data file
        mock_path = MOCK_DIR / mock_file
        if mock_path.exists():
            with open(mock_path) as f:
                return json.load(f), 200
        else:
            return {
                "error": f"Mock file not found: {mock_file}",
                "endpoint": endpoint,
            }, 500

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> MockResponse:
        """Mock GET request - returns data from JSON file."""
        # Extract endpoint path from URL (strips scheme and host)
        endpoint = self._extract_endpoint(url)

        # Load mock data (with validation)
        data, status_code = self._load_mock(endpoint)

        return MockResponse(data, status_code=status_code)

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        data: Any | None = None,
    ) -> MockResponse:
        """Mock POST request - returns success response."""
        endpoint = self._extract_endpoint(url)

        # For POST requests, return a generic success
        return MockResponse(
            {
                "status": "success",
                "message": f"Mock POST to {endpoint}",
                "request_data": json or {},
            }
        )

    async def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> MockResponse:
        """Mock PUT request - returns success response."""
        endpoint = self._extract_endpoint(url)

        return MockResponse(
            {
                "status": "success",
                "message": f"Mock PUT to {endpoint}",
                "request_data": json or {},
            }
        )

    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> MockResponse:
        """Mock DELETE request - returns success response."""
        endpoint = self._extract_endpoint(url)

        return MockResponse({"status": "success", "message": f"Mock DELETE to {endpoint}"})
