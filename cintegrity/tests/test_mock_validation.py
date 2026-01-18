"""
Tests for Mock ID Validation

Verifies that MockAsyncClient returns 404 for unknown IDs and 200 for known IDs.
"""

import pytest

from cintegrity.versa.mocks.mock_client import MockAsyncClient


@pytest.mark.anyio
async def test_valid_appliance_uuid_returns_200():
    """Valid appliance UUID should return 200 with data."""
    url = "https://mock-director.local/vnms/dashboard/appliance/dc-east-001"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "uuid" in data
    assert data["uuid"] == "dc-east-001"


@pytest.mark.anyio
async def test_unknown_appliance_uuid_returns_404():
    """Unknown appliance UUID should return 404."""
    url = "https://mock-director.local/vnms/dashboard/appliance/unknown-uuid-999"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


@pytest.mark.anyio
async def test_valid_appliance_name_returns_200():
    """Valid appliance name should return 200 with data."""
    url = "https://mock-director.local/vnms/appliance/DC-East-Primary/routing-instances"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "instances" in data  # Mock data uses "instances" not "routingInstances"


@pytest.mark.anyio
async def test_unknown_appliance_name_returns_404():
    """Unknown appliance name should return 404."""
    url = "https://mock-director.local/vnms/appliance/UnknownAppliance/routing-instances"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


@pytest.mark.anyio
async def test_valid_device_group_returns_200():
    """Valid device group name should return 200 with data."""
    url = "https://mock-director.local/nextgen/deviceGroup/DC-Controllers"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "DC-Controllers"


@pytest.mark.anyio
async def test_unknown_device_group_returns_404():
    """Unknown device group name should return 404."""
    url = "https://mock-director.local/nextgen/deviceGroup/UnknownGroup"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


@pytest.mark.anyio
async def test_valid_template_returns_200():
    """Valid template name should return 200 with data."""
    url = "https://mock-director.local/vnms/sdwan/workflow/templates/template/Enterprise-Branch-Gold"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "templateName" in data
    assert data["templateName"] == "Enterprise-Branch-Gold"


@pytest.mark.anyio
async def test_unknown_template_returns_404():
    """Unknown template name should return 404."""
    url = "https://mock-director.local/vnms/sdwan/workflow/templates/template/UnknownTemplate"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


@pytest.mark.anyio
async def test_list_endpoints_without_params_still_work():
    """Endpoints without path parameters should still return 200."""
    url = "https://mock-director.local/vnms/appliance/appliance/lite"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "appliances" in data
    assert "totalCount" in data


@pytest.mark.anyio
async def test_multiple_valid_uuids():
    """Test multiple known UUIDs to ensure registry is comprehensive."""
    known_uuids = [
        "dc-east-001",
        "dc-west-001",
        "hub-northeast-001",
        "cloud-aws-east-001",
        "br-nyc-001",
    ]

    for uuid in known_uuids:
        url = f"https://mock-director.local/vnms/dashboard/appliance/{uuid}"
        async with MockAsyncClient() as client:
            response = await client.get(url)

        # Validation works: all valid UUIDs return 200
        # Note: Static mock returns same data for all UUIDs (expected behavior)
        assert response.status_code == 200, f"UUID {uuid} should return 200"
        data = response.json()
        assert "uuid" in data  # Has uuid field
        assert "name" in data  # Has name field


@pytest.mark.anyio
async def test_appliance_status_with_valid_uuid():
    """Test applianceUUID parameter validation."""
    url = "https://mock-director.local/vnms/dashboard/applianceStatus/dc-east-001"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "uuid" in data


@pytest.mark.anyio
async def test_appliance_status_with_unknown_uuid():
    """Test applianceUUID parameter validation with unknown ID."""
    url = "https://mock-director.local/vnms/dashboard/applianceStatus/unknown-999"

    async with MockAsyncClient() as client:
        response = await client.get(url)

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
