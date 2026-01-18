"""
Versa Networks tool registry for cintegrity gateway.

This module provides versa tools that can be registered with ToolManager.add_local_server().
Input schemas are derived from function signatures.
Output schemas are derived from return type annotations (Pydantic models).

Tools return dicts at runtime but have Pydantic model return type annotations
for schema introspection. Schema validation is handled by tests.

Note: Return type annotations are Pydantic models for schema extraction,
but actual returns are dict from response.json(). This is intentional.
"""
# pyright: reportReturnType=false

from typing import Any, Optional

from .mocks.mock_client import MockAsyncClient
from .schemas import (
    AlarmHandlingResponse,
    AlarmsPageResponse,
    AlarmSummaryByOrgResponse,
    AlarmSummaryResponse,
    AlarmTypesResponse,
    AllApplianceStatusResponse,
    AnalyticsAlarmsResponse,
    AnalyticsAlarmSummaryResponse,
    ApplianceAlarmModelResponse,
    ApplianceAlarmTypesResponse,
    ApplianceDetailsResponse,
    ApplianceHardwareResponse,
    ApplianceLocationsResponse,
    ApplianceNamesResponse,
    AppliancesBasicResponse,
    AppliancesByTypeResponse,
    ApplianceServicesResponse,
    AppliancesLiteResponse,
    AppliancesLiteViewResponse,
    AppliancesSummaryResponse,
    ApplianceStatusResponse,
    AssetsResponse,
    AuditLogsResponse,
    BandwidthMeasurementResponse,
    BindDataHeaderResponse,
    CapabilitiesResponse,
    ConfigurationExportResponse,
    DeviceAlarmSummaryResponse,
    DeviceGroupsResponse,
    DeviceTemplateListingResponse,
    DeviceTemplatesResponse,
    DeviceWorkflowsResponse,
    DirectorAlarmsResponse,
    DirectorAlarmSummaryResponse,
    FailOverAlarmsResponse,
    FilteredAlarmsResponse,
    HaAlarmsResponse,
    HeadEndStatusResponse,
    IkeHealthResponse,
    ImpAlarmsResponse,
    ImpAlarmSummaryResponse,
    InterfaceHealthResponse,
    LiveStatusResponse,
    LteDevicesResponse,
    ModelNumbersResponse,
    MonitoringConfigResponse,
    MonitorPullEnabledResponse,
    NavTreeResponse,
    PagedDataResponse,
    PathHealthResponse,
    RoutingInstancesResponse,
    SearchApplianceResponse,
    SingleApplianceStatusResponse,
    SpecificDeviceGroupResponse,
    SpecificDeviceWorkflowResponse,
    SpecificTemplateWorkflowResponse,
    StatusBriefResponse,
    StatusChangeResponse,
    SyncStatusResponse,
    SysDetailsResponse,
    SysUptimeResponse,
    TemplatesResponse,
    TemplateWorkflowResponse,
    VdHaDetailsResponse,
    VdPackageInfoResponse,
    VdStatusResponse,
    ViolationsResponse,
)

MOCK_DIRECTOR_URL = "https://mock-director.local"
MOCK_HEADERS = {
    "Authorization": "Bearer mock-token",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


async def get_all_appliance_status(
    limit: Optional[str] = None, offset: Optional[str] = None
) -> AllApplianceStatusResponse:
    """Get All Appliance Status - returns status for all appliances with pagination."""
    url = f"{MOCK_DIRECTOR_URL}/nextgen/appliance/status"
    query_params = {}
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_single_appliance_status(id: str, byName: Optional[str] = None) -> SingleApplianceStatusResponse:
    """Get Single Appliance Status - returns detailed status for a specific appliance."""
    url = f"{MOCK_DIRECTOR_URL}/nextgen/appliance/status/{id}"
    query_params = {}
    if byName:
        query_params["byName"] = byName

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_device_template_listing(deviceName: str, tenant: Optional[str] = None) -> DeviceTemplateListingResponse:
    """Get Device Template Listing - returns templates associated with a device."""
    url = f"{MOCK_DIRECTOR_URL}/nextgen/appliance/template_listing/{deviceName}"
    query_params = {}
    if tenant:
        query_params["tenant"] = tenant

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_appliance_locations() -> ApplianceLocationsResponse:
    """Get Appliance Locations - returns all appliance locations with coordinates."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/location"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_routing_instance_information(
    applianceName: str,
) -> RoutingInstancesResponse:
    """Get Routing Instance Information - returns routing instances for an appliance."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/appliance/{applianceName}/routing-instances"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_all_appliances_by_type_and_tags(
    offset: Optional[str] = None,
    limit: Optional[str] = None,
    type: Optional[str] = None,
    tags: Optional[str] = None,
) -> AppliancesByTypeResponse:
    """Get All Appliances By Type and Tags - returns appliances filtered by type and tags."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/appliance/appliance"
    query_params = {}
    if offset:
        query_params["offset"] = offset
    if limit:
        query_params["limit"] = limit
    if type:
        query_params["type"] = type
    if tags:
        query_params["tags"] = tags

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_all_appliances_lite(
    filterString: Optional[str] = None,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    org: Optional[str] = None,
    tags: Optional[str] = None,
) -> AppliancesLiteResponse:
    """Get All Appliances Lite - returns lightweight appliance list."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/appliance/appliance/lite"
    query_params = {}
    if filterString:
        query_params["filterString"] = filterString
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if org:
        query_params["org"] = org
    if tags:
        query_params["tags"] = tags

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_all_appliances_liteview(
    exportToCSV: Optional[str] = None,
    filterString: Optional[str] = None,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    org: Optional[str] = None,
    tags: Optional[str] = None,
) -> AppliancesLiteViewResponse:
    """Get All Appliances LiteView - returns lightweight appliance view with IPs."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/appliance/appliance/liteView"
    query_params = {}
    if exportToCSV:
        query_params["exportToCSV"] = exportToCSV
    if filterString:
        query_params["filterString"] = filterString
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if org:
        query_params["org"] = org
    if tags:
        query_params["tags"] = tags

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def search_appliance_by_name(
    name: str,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
) -> SearchApplianceResponse:
    """Search Appliance By Name - returns appliance search results."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/appliance/applianceByName"
    query_params: dict[str, Any] = {"name": name}
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def export_appliance_configuration(
    applianceName: str, export_as_plain_text: Optional[str] = None
) -> ConfigurationExportResponse:
    """Export Appliance Configuration - exports appliance configuration."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/appliance/export"
    query_params: dict[str, Any] = {"applianceName": applianceName}
    if export_as_plain_text:
        query_params["export-as-plain-text"] = export_as_plain_text

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_appliances_summary(
    filterByName: Optional[str] = None,
) -> AppliancesSummaryResponse:
    """Get Appliances Summary - returns summary statistics for appliances."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/appliance/summary"
    query_params = {}
    if filterByName:
        query_params["filterByName"] = filterByName

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_appliance_details_by_uuid(Uuid: str) -> ApplianceDetailsResponse:
    """Get Appliance Details by UUID - returns detailed appliance information."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/{Uuid}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_appliance_hardware(Uuid: str) -> ApplianceHardwareResponse:
    """Get Appliance Hardware - returns appliance hardware details."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/{Uuid}/hardware"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_bw_measurement(
    applianceName: str,
    command: Optional[str] = None,
    uuid: Optional[str] = None,
) -> BandwidthMeasurementResponse:
    """Get BW Measurement - returns bandwidth measurements."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/{applianceName}/bandwidthservers"
    query_params = {}
    if command:
        query_params["command"] = command
    if uuid:
        query_params["uuid"] = uuid

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_appliance_capabilities(applianceName: str) -> CapabilitiesResponse:
    """Get Appliance Capabilities - returns appliance capabilities."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/{applianceName}/capabilities"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_appliance_sync_status(applianceUUID: str) -> SyncStatusResponse:
    """Get Appliance Sync Status - returns appliance sync status."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/{applianceUUID}/syncStatus"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_appliance_services(applianceName: str) -> ApplianceServicesResponse:
    """Get Appliance Services - returns appliance services."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/applianceServices/{applianceName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_appliance_status(applianceUUID: str) -> ApplianceStatusResponse:
    """Get Appliance Status - returns appliance status."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/applianceStatus/{applianceUUID}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_appliance_status_brief(applianceUUID: str) -> StatusBriefResponse:
    """Get Appliance Status Brief - returns brief appliance status."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/applianceStatus/{applianceUUID}/brief"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_all_appliance_names() -> ApplianceNamesResponse:
    """Get All Appliance Names - returns all appliance names."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/cloud/systems/getAllApplianceNames"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_all_appliances_basic_details(
    limit: Optional[str] = None,
    offset: Optional[str] = None,
) -> AppliancesBasicResponse:
    """Get All Appliances Basic Details - returns basic appliance details."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/cloud/systems/getAllAppliancesBasicDetails"
    query_params = {}
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_appliance_violations(applianceName: str) -> ViolationsResponse:
    """Get Appliance Violations - returns appliance violations."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/applianceviolations/{applianceName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_appliance_live_status(
    applianceName: str,
    command: Optional[str] = None,
    decode: Optional[str] = None,
    fetch: Optional[str] = None,
    filters: Optional[str] = None,
    uuid: Optional[str] = None,
) -> LiveStatusResponse:
    """Get Appliance Live Status - returns live appliance status."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/{applianceName}/live"
    query_params = {}
    if command:
        query_params["command"] = command
    if decode:
        query_params["decode"] = decode
    if fetch:
        query_params["fetch"] = fetch
    if filters:
        query_params["filters"] = filters
    if uuid:
        query_params["uuid"] = uuid

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_audit_logs(
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    searchKey: Optional[str] = None,
) -> AuditLogsResponse:
    """Get Audit Logs - returns audit log entries."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/audit/logs"
    query_params = {}
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if searchKey:
        query_params["searchKey"] = searchKey

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_template_workflow(
    templateworkflowName: str,
) -> TemplateWorkflowResponse:
    """Get Template Workflow - returns template workflow details."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/alltypes/workflow/templates/template/{templateworkflowName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def device_workflow_fetch_all(
    filters: Optional[str] = None,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    orgname: Optional[str] = None,
) -> DeviceWorkflowsResponse:
    """Device WorkFlow Fetch All - returns all device workflows."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/sdwan/workflow/devices"
    query_params = {}
    if filters:
        query_params["filters"] = filters
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if orgname:
        query_params["orgname"] = orgname

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_specific_device_workflow(
    deviceName: str,
) -> SpecificDeviceWorkflowResponse:
    """Get Specific Device WorkFlow - returns device workflow details."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/sdwan/workflow/devices/device/{deviceName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_template_bind_data_header_and_count(
    templateName: str, organization: Optional[str] = None
) -> BindDataHeaderResponse:
    """Get Template Bind Data Header and Count - returns template bind data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/sdwan/workflow/binddata/devices/header/template/{templateName}"
    query_params = {}
    if organization:
        query_params["organization"] = organization

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def template_fetch_all(
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    orgname: Optional[str] = None,
    searchKeyword: Optional[str] = None,
) -> TemplatesResponse:
    """Template Fetch All - returns all templates."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/sdwan/workflow/templates"
    query_params = {}
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if orgname:
        query_params["orgname"] = orgname
    if searchKeyword:
        query_params["searchKeyword"] = searchKeyword

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_specific_template_workflow(
    templateworkflowName: str,
) -> SpecificTemplateWorkflowResponse:
    """Get Specific Template WorkFlow - returns specific template workflow."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/sdwan/workflow/templates/template/{templateworkflowName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def device_group_fetch_all(
    filters: Optional[str] = None,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    organization: Optional[str] = None,
) -> DeviceGroupsResponse:
    """Device Group Fetch All - returns all device groups."""
    url = f"{MOCK_DIRECTOR_URL}/nextgen/deviceGroup"
    query_params = {}
    if filters:
        query_params["filters"] = filters
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if organization:
        query_params["organization"] = organization

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_specific_device_group(
    deviceGroupName: str,
) -> SpecificDeviceGroupResponse:
    """Get Specific Device Group - returns specific device group details."""
    url = f"{MOCK_DIRECTOR_URL}/nextgen/deviceGroup/{deviceGroupName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_all_model_numbers() -> ModelNumbersResponse:
    """Get All Model Numbers - returns all model numbers."""
    url = f"{MOCK_DIRECTOR_URL}/nextgen/deviceGroup/modelNumbers"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def show_templates_associated_to_device(
    deviceName: str,
) -> DeviceTemplatesResponse:
    """Show Templates Associated to Device - returns templates for a device."""
    url = f"{MOCK_DIRECTOR_URL}/nextgen/device/{deviceName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_all_assets(
    filters: Optional[str] = None,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    organization: Optional[str] = None,
) -> AssetsResponse:
    """Get All Assets - returns all assets."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/assets/asset"
    query_params = {}
    if filters:
        query_params["filters"] = filters
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if organization:
        query_params["organization"] = organization

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_next_page_data(
    queryId: str,
    filters: Optional[str] = None,
    offset: Optional[str] = None,
) -> PagedDataResponse:
    """Get Next Page Data - returns next page of data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/appliance/next_page_data"
    query_params: dict[str, Any] = {"queryId": queryId}
    if filters:
        query_params["filters"] = filters
    if offset:
        query_params["offset"] = offset

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_enable_monitoring() -> MonitoringConfigResponse:
    """Get Enable Monitoring - returns monitoring configuration."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/enableMonitoring"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_device_status_pulling_enabled(
    deviceName: str,
) -> MonitorPullEnabledResponse:
    """Get Device Status Pulling Enabled - returns device status pulling info."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/getMonitorPullEnabled/{deviceName}"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_health_ike(deviceName: Optional[str] = None) -> IkeHealthResponse:
    """Get Health IKE - returns IKE health data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/health/ike"
    query_params = {}
    if deviceName:
        query_params["deviceName"] = deviceName

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_health_interface(
    deviceName: Optional[str] = None,
) -> InterfaceHealthResponse:
    """Get Health Interface - returns interface health data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/health/interface"
    query_params = {}
    if deviceName:
        query_params["deviceName"] = deviceName

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_health_path(deviceName: Optional[str] = None) -> PathHealthResponse:
    """Get Health Path - returns path health data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/health/path"
    query_params = {}
    if deviceName:
        query_params["deviceName"] = deviceName

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_devices_in_lte() -> LteDevicesResponse:
    """Get Devices in LTE - returns LTE devices."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/lte/list"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_nav_tree_node(
    appUUID: Optional[str] = None,
    forceRefresh: Optional[str] = None,
    skipCpeNodes: Optional[str] = None,
) -> NavTreeResponse:
    """Get Nav Tree Node - returns navigation tree data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/navTree"
    query_params = {}
    if appUUID:
        query_params["appUUID"] = appUUID
    if forceRefresh:
        query_params["forceRefresh"] = forceRefresh
    if skipCpeNodes:
        query_params["skipCpeNodes"] = skipCpeNodes

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_head_end_status() -> HeadEndStatusResponse:
    """Get Head-End Status - returns head-end status."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/status/headEnds"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_vd_status() -> VdStatusResponse:
    """Get VD Status - returns VD status."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/vdStatus"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_vd_ha_details() -> VdHaDetailsResponse:
    """Get VD HA Details - returns VD HA details."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/vdStatus/haDetails"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_vd_package_info() -> VdPackageInfoResponse:
    """Get VD Package Info - returns VD package info."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/vdStatus/packageInfo"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_sys_details() -> SysDetailsResponse:
    """Get Sys Details - returns system details."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/vdStatus/sysDetails"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_sys_uptime() -> SysUptimeResponse:
    """Get Sys Uptime - returns system uptime."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/dashboard/vdStatus/sysUptime"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def filter_paginate_alarm(
    device_name: Optional[str] = None,
    filtertype: Optional[str] = None,
    force_refresh: Optional[str] = None,
    include_children: Optional[str] = None,
    is_cleared: Optional[str] = None,
    is_deep: Optional[str] = None,
    last_alarm_text: Optional[str] = None,
    last_change_after: Optional[str] = None,
    last_change_before: Optional[str] = None,
    last_perceived_severity: Optional[str] = None,
    last_status_change: Optional[str] = None,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    org: Optional[str] = None,
    show_system_alarm: Optional[str] = None,
    sort_column: Optional[str] = None,
    sort_order: Optional[str] = None,
    type: Optional[str] = None,
) -> AlarmsPageResponse:
    """Filter Paginate Alarm - returns paginated alarm data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/alarms/page"
    query_params: dict[str, Any] = {}
    if device_name:
        query_params["device_name"] = device_name
    if filtertype:
        query_params["filtertype"] = filtertype
    if force_refresh:
        query_params["force_refresh"] = force_refresh
    if include_children:
        query_params["include_children"] = include_children
    if is_cleared:
        query_params["is_cleared"] = is_cleared
    if is_deep:
        query_params["is_deep"] = is_deep
    if last_alarm_text:
        query_params["last_alarm_text"] = last_alarm_text
    if last_change_after:
        query_params["last_change_after"] = last_change_after
    if last_change_before:
        query_params["last_change_before"] = last_change_before
    if last_perceived_severity:
        query_params["last_perceived_severity"] = last_perceived_severity
    if last_status_change:
        query_params["last_status_change"] = last_status_change
    if limit:
        query_params["limit"] = limit
    if offset:
        query_params["offset"] = offset
    if org:
        query_params["org"] = org
    if show_system_alarm:
        query_params["show_system_alarm"] = show_system_alarm
    if sort_column:
        query_params["sort_column"] = sort_column
    if sort_order:
        query_params["sort_order"] = sort_order
    if type:
        query_params["type"] = type

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_alarm_handling(
    device_name: Optional[str] = None,
    managed_object: Optional[str] = None,
    org: Optional[str] = None,
    type: Optional[str] = None,
    specific_problem: Optional[str] = None,
) -> AlarmHandlingResponse:
    """Get Alarm Handling - returns alarm handling data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/alarm/handling"
    query_params = {}
    if device_name:
        query_params["device_name"] = device_name
    if managed_object:
        query_params["managed_object"] = managed_object
    if org:
        query_params["org"] = org
    if type:
        query_params["type"] = type
    if specific_problem:
        query_params["specific_problem"] = specific_problem

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_alarm_summary_per_org(
    org: str,
    include_children: Optional[str] = None,
    include_system: Optional[str] = None,
) -> AlarmSummaryByOrgResponse:
    """Get Alarm Summary Per Org - returns alarm summary for org."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/alarms/summary/{org}"
    query_params = {}
    if include_children:
        query_params["include_children"] = include_children
    if include_system:
        query_params["include_system"] = include_system

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_alarm_summary() -> AlarmSummaryResponse:
    """Get Alarm Summary - returns alarm summary."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/alarms/summary"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_alarm_types() -> AlarmTypesResponse:
    """Get Alarm Types - returns alarm types."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/types"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_all_filtered_alarms(
    device_name: Optional[str] = None,
    filtertype: Optional[str] = None,
    is_cleared: Optional[str] = None,
    is_deep: Optional[str] = None,
    last_alarm_text: Optional[str] = None,
    last_change_after: Optional[str] = None,
    last_change_before: Optional[str] = None,
    last_perceived_severity: Optional[str] = None,
    last_status_change: Optional[str] = None,
    org: Optional[str] = None,
    type: Optional[str] = None,
) -> FilteredAlarmsResponse:
    """Get All Filtered Alarms - returns filtered alarm data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/alarms"
    query_params = {}
    if device_name:
        query_params["device_name"] = device_name
    if filtertype:
        query_params["filtertype"] = filtertype
    if is_cleared:
        query_params["is_cleared"] = is_cleared
    if is_deep:
        query_params["is_deep"] = is_deep
    if last_alarm_text:
        query_params["last_alarm_text"] = last_alarm_text
    if last_change_after:
        query_params["last_change_after"] = last_change_after
    if last_change_before:
        query_params["last_change_before"] = last_change_before
    if last_perceived_severity:
        query_params["last_perceived_severity"] = last_perceived_severity
    if last_status_change:
        query_params["last_status_change"] = last_status_change
    if org:
        query_params["org"] = org
    if type:
        query_params["type"] = type

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_analytics_alarm_summary() -> AnalyticsAlarmSummaryResponse:
    """Get Analytics Alarm Summary - returns analytics alarm summary."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/analytics/alarms/summary"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_analytics_alarms(
    search_string: Optional[str] = None,
    severity: Optional[str] = None,
) -> AnalyticsAlarmsResponse:
    """Get Analytics Alarms - returns analytics alarms."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/analytics/alarms"
    query_params = {}
    if search_string:
        query_params["search_string"] = search_string
    if severity:
        query_params["severity"] = severity

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_appliance_alarm_model() -> ApplianceAlarmModelResponse:
    """Get Appliance Alarm Model - returns appliance alarm model."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/appliance/alarm_model"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_appliance_alarm_types() -> ApplianceAlarmTypesResponse:
    """Get Appliance Alarm Types - returns appliance alarm types."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/appliance/types"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_device_alarm_summary(
    deviceName: str,
    org: Optional[str] = None,
) -> DeviceAlarmSummaryResponse:
    """Get Device Alarm Summary - returns device alarm summary."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/alarms/summary/device/{deviceName}"
    query_params = {}
    if org:
        query_params["org"] = org

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_director_alarm_summary() -> DirectorAlarmSummaryResponse:
    """Get Director Alarm Summary - returns director alarm summary."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/director/alarms/summary"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_director_alarms(
    search_string: Optional[str] = None,
    severity: Optional[str] = None,
) -> DirectorAlarmsResponse:
    """Get Director Alarms - returns director alarms."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/director/alarms"
    query_params = {}
    if search_string:
        query_params["search_string"] = search_string
    if severity:
        query_params["severity"] = severity

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()


async def get_director_fail_over_alarms() -> FailOverAlarmsResponse:
    """Get Director Fail Over Alarms - returns director fail-over alarms."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/director/fail-over-alarms"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_director_ha_alarms() -> HaAlarmsResponse:
    """Get Director HA Alarms - returns director HA alarms."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/director/ha-alarms"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_imp_alarm_summary() -> ImpAlarmSummaryResponse:
    """Get IMP Alarm Summary - returns IMP alarm summary."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/director/pop-up-summary"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_imp_alarms() -> ImpAlarmsResponse:
    """Get IMP Alarms - returns IMP alarms."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/director/pop-up"
    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS)
    return response.json()


async def get_status_change(
    device_name: Optional[str] = None,
    managed_object: Optional[str] = None,
    org: Optional[str] = None,
    type: Optional[str] = None,
    specific_problem: Optional[str] = None,
) -> StatusChangeResponse:
    """Get Status Change - returns status change data."""
    url = f"{MOCK_DIRECTOR_URL}/vnms/fault/alarm/status"
    query_params = {}
    if device_name:
        query_params["device_name"] = device_name
    if managed_object:
        query_params["managed_object"] = managed_object
    if org:
        query_params["org"] = org
    if type:
        query_params["type"] = type
    if specific_problem:
        query_params["specific_problem"] = specific_problem

    async with MockAsyncClient(verify=False) as client:
        response = await client.get(url, headers=MOCK_HEADERS, params=query_params)
    return response.json()
