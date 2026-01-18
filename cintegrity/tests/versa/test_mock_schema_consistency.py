"""
Tests to verify all mock JSON files match their corresponding Pydantic schemas.

This ensures structured output consistency between mock data and response models.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cintegrity.versa import schemas

MOCK_DIR = Path(__file__).parent.parent.parent / "src" / "cintegrity" / "versa" / "mocks"


# =============================================================================
# Appliance Mock/Schema Mappings
# =============================================================================

APPLIANCE_MOCK_SCHEMA_MAP = {
    "get_all_appliance_status.json": schemas.AllApplianceStatusResponse,
    "get_single_appliance_status.json": schemas.SingleApplianceStatusResponse,
    "get_device_template_listing.json": schemas.DeviceTemplateListingResponse,
    "get_appliance_locations.json": schemas.ApplianceLocationsResponse,
    "get_routing_instance_information.json": schemas.RoutingInstancesResponse,
    "get_all_appliances_by_type_and_tags.json": schemas.AppliancesByTypeResponse,
    "get_all_appliances_lite.json": schemas.AppliancesLiteResponse,
    "get_all_appliances_liteview.json": schemas.AppliancesLiteViewResponse,
    "search_appliance_by_name.json": schemas.SearchApplianceResponse,
    "export_appliance_configuration.json": schemas.ConfigurationExportResponse,
    "get_appliances_summary.json": schemas.AppliancesSummaryResponse,
    "get_appliance_details_by_uuid.json": schemas.ApplianceDetailsResponse,
    "get_appliance_hardware.json": schemas.ApplianceHardwareResponse,
    "get_bw_measurement.json": schemas.BandwidthMeasurementResponse,
    "get_appliance_capabilities.json": schemas.CapabilitiesResponse,
    "get_appliance_sync_status.json": schemas.SyncStatusResponse,
    "get_appliance_services.json": schemas.ApplianceServicesResponse,
    "get_appliance_status.json": schemas.ApplianceStatusResponse,
    "get_appliance_status_brief.json": schemas.StatusBriefResponse,
    "get_all_appliance_names.json": schemas.ApplianceNamesResponse,
    "get_all_appliances_basic_details.json": schemas.AppliancesBasicResponse,
    "get_appliance_violations.json": schemas.ViolationsResponse,
}


# =============================================================================
# Health Mock/Schema Mappings
# =============================================================================

HEALTH_MOCK_SCHEMA_MAP = {
    "get_appliance_live_status.json": schemas.LiveStatusResponse,
    "get_next_page_data.json": schemas.PagedDataResponse,
    "get_enable_monitoring.json": schemas.MonitoringConfigResponse,
    "get_device_status_pulling_enabled.json": schemas.MonitorPullEnabledResponse,
    "get_health_ike.json": schemas.IkeHealthResponse,
    "get_health_interface.json": schemas.InterfaceHealthResponse,
    "get_health_path.json": schemas.PathHealthResponse,
    "get_devices_in_lte.json": schemas.LteDevicesResponse,
    "get_nav_tree_node.json": schemas.NavTreeResponse,
    "get_head_end_status.json": schemas.HeadEndStatusResponse,
    "get_vd_status.json": schemas.VdStatusResponse,
    "get_vd_ha_details.json": schemas.VdHaDetailsResponse,
    "get_vd_package_info.json": schemas.VdPackageInfoResponse,
    "get_sys_details.json": schemas.SysDetailsResponse,
    "get_sys_uptime.json": schemas.SysUptimeResponse,
}


# =============================================================================
# Alarm Mock/Schema Mappings
# =============================================================================

ALARM_MOCK_SCHEMA_MAP = {
    "filter_paginate_alarm.json": schemas.AlarmsPageResponse,
    "get_alarm_handling.json": schemas.AlarmHandlingResponse,
    "get_alarm_summary_per_org.json": schemas.AlarmSummaryByOrgResponse,
    "get_alarm_summary.json": schemas.AlarmSummaryResponse,
    "get_alarm_types.json": schemas.AlarmTypesResponse,
    "get_all_filtered_alarms.json": schemas.FilteredAlarmsResponse,
    "get_analytics_alarm_summary.json": schemas.AnalyticsAlarmSummaryResponse,
    "get_analytics_alarms.json": schemas.AnalyticsAlarmsResponse,
    "get_appliance_alarm_model.json": schemas.ApplianceAlarmModelResponse,
    "get_appliance_alarm_types.json": schemas.ApplianceAlarmTypesResponse,
    "get_device_alarm_summary.json": schemas.DeviceAlarmSummaryResponse,
    "get_director_alarm_summary.json": schemas.DirectorAlarmSummaryResponse,
    "get_director_alarms.json": schemas.DirectorAlarmsResponse,
    "get_director_fail_over_alarms.json": schemas.FailOverAlarmsResponse,
    "get_director_ha_alarms.json": schemas.HaAlarmsResponse,
    "get_imp_alarm_summary.json": schemas.ImpAlarmSummaryResponse,
    "get_imp_alarms.json": schemas.ImpAlarmsResponse,
    "get_status_change.json": schemas.StatusChangeResponse,
}


# =============================================================================
# Workflow Mock/Schema Mappings
# =============================================================================

WORKFLOW_MOCK_SCHEMA_MAP = {
    "get_template_workflow.json": schemas.TemplateWorkflowResponse,
    "device_workflow_fetch_all.json": schemas.DeviceWorkflowsResponse,
    "get_specific_device_workflow.json": schemas.SpecificDeviceWorkflowResponse,
    "get_template_bind_data_header_and_count.json": schemas.BindDataHeaderResponse,
    "template_fetch_all.json": schemas.TemplatesResponse,
    "get_specific_template_workflow.json": schemas.SpecificTemplateWorkflowResponse,
    "show_templates_associated_to_device.json": schemas.DeviceTemplatesResponse,
}


# =============================================================================
# Device Group Mock/Schema Mappings
# =============================================================================

DEVICE_GROUP_MOCK_SCHEMA_MAP = {
    "device_group_fetch_all.json": schemas.DeviceGroupsResponse,
    "get_specific_device_group.json": schemas.SpecificDeviceGroupResponse,
    "get_all_model_numbers.json": schemas.ModelNumbersResponse,
}


# =============================================================================
# Audit Mock/Schema Mappings
# =============================================================================

AUDIT_MOCK_SCHEMA_MAP = {
    "get_audit_logs.json": schemas.AuditLogsResponse,
}


# =============================================================================
# Assets Mock/Schema Mappings
# =============================================================================

ASSETS_MOCK_SCHEMA_MAP = {
    "get_all_assets.json": schemas.AssetsResponse,
}


# =============================================================================
# Test Functions
# =============================================================================


def validate_mock_file(mock_dir: Path, filename: str, schema_class: type) -> None:
    """Validate a single mock file against its schema."""
    filepath = mock_dir / filename
    assert filepath.exists(), f"Mock file not found: {filepath}"

    data = json.loads(filepath.read_text())
    try:
        schema_class.model_validate(data)
    except ValidationError as e:
        pytest.fail(f"Mock {filename} failed validation against {schema_class.__name__}:\n{e}")


class TestApplianceMocks:
    """Test all appliance mock files match their schemas."""

    @pytest.mark.parametrize("filename,schema_class", APPLIANCE_MOCK_SCHEMA_MAP.items())
    def test_appliance_mock_matches_schema(self, filename: str, schema_class: type) -> None:
        validate_mock_file(MOCK_DIR / "appliance", filename, schema_class)


class TestHealthMocks:
    """Test all health mock files match their schemas."""

    @pytest.mark.parametrize("filename,schema_class", HEALTH_MOCK_SCHEMA_MAP.items())
    def test_health_mock_matches_schema(self, filename: str, schema_class: type) -> None:
        validate_mock_file(MOCK_DIR / "health", filename, schema_class)


class TestAlarmMocks:
    """Test all alarm mock files match their schemas."""

    @pytest.mark.parametrize("filename,schema_class", ALARM_MOCK_SCHEMA_MAP.items())
    def test_alarm_mock_matches_schema(self, filename: str, schema_class: type) -> None:
        validate_mock_file(MOCK_DIR / "alarm", filename, schema_class)


class TestWorkflowMocks:
    """Test all workflow mock files match their schemas."""

    @pytest.mark.parametrize("filename,schema_class", WORKFLOW_MOCK_SCHEMA_MAP.items())
    def test_workflow_mock_matches_schema(self, filename: str, schema_class: type) -> None:
        validate_mock_file(MOCK_DIR / "workflow", filename, schema_class)


class TestDeviceGroupMocks:
    """Test all device group mock files match their schemas."""

    @pytest.mark.parametrize("filename,schema_class", DEVICE_GROUP_MOCK_SCHEMA_MAP.items())
    def test_device_group_mock_matches_schema(self, filename: str, schema_class: type) -> None:
        validate_mock_file(MOCK_DIR / "device_group", filename, schema_class)


class TestAuditMocks:
    """Test all audit mock files match their schemas."""

    @pytest.mark.parametrize("filename,schema_class", AUDIT_MOCK_SCHEMA_MAP.items())
    def test_audit_mock_matches_schema(self, filename: str, schema_class: type) -> None:
        validate_mock_file(MOCK_DIR / "audit", filename, schema_class)


class TestAssetsMocks:
    """Test all assets mock files match their schemas."""

    @pytest.mark.parametrize("filename,schema_class", ASSETS_MOCK_SCHEMA_MAP.items())
    def test_assets_mock_matches_schema(self, filename: str, schema_class: type) -> None:
        validate_mock_file(MOCK_DIR / "assets", filename, schema_class)


class TestAllMocksHaveSchemas:
    """Verify every mock file has a corresponding schema mapping."""

    def test_all_appliance_mocks_mapped(self) -> None:
        mock_dir = MOCK_DIR / "appliance"
        mock_files = {f.name for f in mock_dir.glob("*.json")}
        mapped_files = set(APPLIANCE_MOCK_SCHEMA_MAP.keys())
        unmapped = mock_files - mapped_files
        assert not unmapped, f"Unmapped appliance mocks: {unmapped}"

    def test_all_health_mocks_mapped(self) -> None:
        mock_dir = MOCK_DIR / "health"
        mock_files = {f.name for f in mock_dir.glob("*.json")}
        mapped_files = set(HEALTH_MOCK_SCHEMA_MAP.keys())
        unmapped = mock_files - mapped_files
        assert not unmapped, f"Unmapped health mocks: {unmapped}"

    def test_all_alarm_mocks_mapped(self) -> None:
        mock_dir = MOCK_DIR / "alarm"
        mock_files = {f.name for f in mock_dir.glob("*.json")}
        mapped_files = set(ALARM_MOCK_SCHEMA_MAP.keys())
        unmapped = mock_files - mapped_files
        assert not unmapped, f"Unmapped alarm mocks: {unmapped}"

    def test_all_workflow_mocks_mapped(self) -> None:
        mock_dir = MOCK_DIR / "workflow"
        mock_files = {f.name for f in mock_dir.glob("*.json")}
        mapped_files = set(WORKFLOW_MOCK_SCHEMA_MAP.keys())
        unmapped = mock_files - mapped_files
        assert not unmapped, f"Unmapped workflow mocks: {unmapped}"

    def test_all_device_group_mocks_mapped(self) -> None:
        mock_dir = MOCK_DIR / "device_group"
        mock_files = {f.name for f in mock_dir.glob("*.json")}
        mapped_files = set(DEVICE_GROUP_MOCK_SCHEMA_MAP.keys())
        unmapped = mock_files - mapped_files
        assert not unmapped, f"Unmapped device_group mocks: {unmapped}"

    def test_all_audit_mocks_mapped(self) -> None:
        mock_dir = MOCK_DIR / "audit"
        mock_files = {f.name for f in mock_dir.glob("*.json")}
        mapped_files = set(AUDIT_MOCK_SCHEMA_MAP.keys())
        unmapped = mock_files - mapped_files
        assert not unmapped, f"Unmapped audit mocks: {unmapped}"

    def test_all_assets_mocks_mapped(self) -> None:
        mock_dir = MOCK_DIR / "assets"
        mock_files = {f.name for f in mock_dir.glob("*.json")}
        mapped_files = set(ASSETS_MOCK_SCHEMA_MAP.keys())
        unmapped = mock_files - mapped_files
        assert not unmapped, f"Unmapped assets mocks: {unmapped}"
