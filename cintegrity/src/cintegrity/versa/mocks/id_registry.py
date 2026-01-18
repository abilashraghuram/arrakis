"""
ID Registry for Mock Data Validation

Loads valid IDs from master mock files to enable realistic 404 responses.
IDs are loaded once at module import time for fast O(1) lookups.
"""

import json
from pathlib import Path
from typing import Any

MOCKS_DIR = Path(__file__).parent


def _load_json(relative_path: str) -> Any:
    """Load JSON file from mocks directory."""
    file_path = MOCKS_DIR / relative_path
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def _build_registry() -> dict[str, set[str]]:
    """Build registry of valid IDs from mock data files."""
    registry: dict[str, set[str]] = {
        "appliance_uuids": set(),
        "appliance_names": set(),
        "device_group_names": set(),
        "template_names": set(),
        "org_names": set(),
    }

    # Load appliance UUIDs and names
    appliances_data = _load_json("appliance/get_all_appliances_lite.json")
    for appliance in appliances_data.get("appliances", []):
        uuid = appliance.get("uuid")
        name = appliance.get("name")
        org = appliance.get("org")
        if uuid:
            registry["appliance_uuids"].add(uuid)
        if name:
            registry["appliance_names"].add(name)
        if org:
            registry["org_names"].add(org)

    # Load device group names
    device_groups_data = _load_json("device_group/device_group_fetch_all.json")
    for group in device_groups_data.get("deviceGroups", []):
        name = group.get("name")
        if name:
            registry["device_group_names"].add(name)

    # Load template names
    templates_data = _load_json("workflow/template_fetch_all.json")
    for template in templates_data.get("templates", []):
        template_name = template.get("templateName")
        if template_name:
            registry["template_names"].add(template_name)

    return registry


# Build registry once at module load time
ID_REGISTRY = _build_registry()


def is_valid_appliance_uuid(uuid: str) -> bool:
    """Check if appliance UUID exists in mock data."""
    return uuid in ID_REGISTRY["appliance_uuids"]


def is_valid_appliance_name(name: str) -> bool:
    """Check if appliance/device name exists in mock data."""
    return name in ID_REGISTRY["appliance_names"]


def is_valid_device_group_name(name: str) -> bool:
    """Check if device group name exists in mock data."""
    return name in ID_REGISTRY["device_group_names"]


def is_valid_template_name(name: str) -> bool:
    """Check if template name exists in mock data."""
    return name in ID_REGISTRY["template_names"]


def is_valid_org_name(name: str) -> bool:
    """Check if org name exists in mock data."""
    return name in ID_REGISTRY["org_names"]


def get_registry_stats() -> dict[str, int]:
    """Get counts of registered IDs for debugging."""
    return {key: len(values) for key, values in ID_REGISTRY.items()}
