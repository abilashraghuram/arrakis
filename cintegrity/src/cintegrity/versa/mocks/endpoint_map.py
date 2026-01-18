"""
Endpoint to Mock File Mapping

Maps API URL patterns to their corresponding mock JSON files.
Supports path parameters like {id}, {deviceName}, etc.
"""

ENDPOINT_TO_MOCK = {
    # ============================================
    # APPLIANCE APIs (23 endpoints)
    # ============================================
    "/nextgen/appliance/status": "appliance/get_all_appliance_status.json",
    "/nextgen/appliance/status/{id}": "appliance/get_single_appliance_status.json",
    "/nextgen/appliance/template_listing/{deviceName}": "appliance/get_device_template_listing.json",
    "/vnms/dashboard/appliance/location": "appliance/get_appliance_locations.json",
    "/vnms/appliance/{applianceName}/routing-instances": "appliance/get_routing_instance_information.json",
    "/vnms/appliance/appliance": "appliance/get_all_appliances_by_type_and_tags.json",
    "/vnms/appliance/appliance/lite": "appliance/get_all_appliances_lite.json",
    "/vnms/appliance/appliance/liteView": "appliance/get_all_appliances_liteview.json",
    "/vnms/appliance/applianceByName": "appliance/search_appliance_by_name.json",
    "/vnms/appliance/export": "appliance/export_appliance_configuration.json",
    "/vnms/appliance/summary": "appliance/get_appliances_summary.json",
    "/vnms/dashboard/appliance/{Uuid}": "appliance/get_appliance_details_by_uuid.json",
    "/vnms/dashboard/appliance/{Uuid}/hardware": "appliance/get_appliance_hardware.json",
    "/vnms/dashboard/appliance/{applianceName}/bandwidthservers": "appliance/get_bw_measurement.json",
    "/vnms/dashboard/appliance/{applianceName}/capabilities": "appliance/get_appliance_capabilities.json",
    "/vnms/dashboard/appliance/{applianceUUID}/syncStatus": "appliance/get_appliance_sync_status.json",
    "/vnms/dashboard/applianceServices/{applianceName}": "appliance/get_appliance_services.json",
    "/vnms/dashboard/applianceStatus/{applianceUUID}": "appliance/get_appliance_status.json",
    "/vnms/dashboard/applianceStatus/{applianceUUID}/brief": "appliance/get_appliance_status_brief.json",
    "/vnms/cloud/systems/getAllApplianceNames": "appliance/get_all_appliance_names.json",
    "/vnms/cloud/systems/getAllAppliancesBasicDetails": "appliance/get_all_appliances_basic_details.json",
    "/vnms/dashboard/applianceviolations/{applianceName}": "appliance/get_appliance_violations.json",
    # ============================================
    # HEALTH / DASHBOARD APIs (14 endpoints)
    # ============================================
    "/vnms/dashboard/appliance/{applianceName}/live": "health/get_appliance_live_status.json",
    "/vnms/dashboard/appliance/next_page_data": "health/get_next_page_data.json",
    "/vnms/dashboard/enableMonitoring": "health/get_enable_monitoring.json",
    "/vnms/dashboard/getMonitorPullEnabled/{deviceName}": "health/get_device_status_pulling_enabled.json",
    "/vnms/dashboard/health/ike": "health/get_health_ike.json",
    "/vnms/dashboard/health/interface": "health/get_health_interface.json",
    "/vnms/dashboard/health/path": "health/get_health_path.json",
    "/vnms/dashboard/lte/list": "health/get_devices_in_lte.json",
    "/vnms/dashboard/navTree": "health/get_nav_tree_node.json",
    "/vnms/dashboard/status/headEnds": "health/get_head_end_status.json",
    "/vnms/dashboard/vdStatus": "health/get_vd_status.json",
    "/vnms/dashboard/vdStatus/haDetails": "health/get_vd_ha_details.json",
    "/vnms/dashboard/vdStatus/packageInfo": "health/get_vd_package_info.json",
    "/vnms/dashboard/vdStatus/sysDetails": "health/get_sys_details.json",
    "/vnms/dashboard/vdStatus/sysUptime": "health/get_sys_uptime.json",
    # ============================================
    # WORKFLOW / TEMPLATE APIs (8 endpoints)
    # ============================================
    "/vnms/alltypes/workflow/templates/template/{templateworkflowName}": "workflow/get_template_workflow.json",
    "/vnms/sdwan/workflow/devices": "workflow/device_workflow_fetch_all.json",
    "/vnms/sdwan/workflow/devices/device/{deviceName}": "workflow/get_specific_device_workflow.json",
    "/vnms/sdwan/workflow/binddata/devices/header/template/{templateName}": (
        "workflow/get_template_bind_data_header_and_count.json"
    ),
    "/vnms/sdwan/workflow/templates": "workflow/template_fetch_all.json",
    "/vnms/sdwan/workflow/templates/template/{templateworkflowName}": "workflow/get_specific_template_workflow.json",
    "/nextgen/device/{deviceName}": "workflow/show_templates_associated_to_device.json",
    # ============================================
    # DEVICE GROUP APIs (3 endpoints)
    # ============================================
    "/nextgen/deviceGroup": "device_group/device_group_fetch_all.json",
    "/nextgen/deviceGroup/{deviceGroupName}": "device_group/get_specific_device_group.json",
    "/nextgen/deviceGroup/modelNumbers": "device_group/get_all_model_numbers.json",
    # ============================================
    # ALARM / FAULT APIs (18 endpoints)
    # ============================================
    "/vnms/fault/alarms/page": "alarm/filter_paginate_alarm.json",
    "/vnms/fault/alarm/handling": "alarm/get_alarm_handling.json",
    "/vnms/fault/alarms/summary/{org}": "alarm/get_alarm_summary_per_org.json",
    "/vnms/fault/alarms/summary": "alarm/get_alarm_summary.json",
    "/vnms/fault/types": "alarm/get_alarm_types.json",
    "/vnms/fault/alarms": "alarm/get_all_filtered_alarms.json",
    "/vnms/fault/analytics/alarms/summary": "alarm/get_analytics_alarm_summary.json",
    "/vnms/fault/analytics/alarms": "alarm/get_analytics_alarms.json",
    "/vnms/fault/appliance/alarm_model": "alarm/get_appliance_alarm_model.json",
    "/vnms/fault/appliance/types": "alarm/get_appliance_alarm_types.json",
    "/vnms/fault/alarms/summary/device/{deviceName}": "alarm/get_device_alarm_summary.json",
    "/vnms/fault/director/alarms/summary": "alarm/get_director_alarm_summary.json",
    "/vnms/fault/director/alarms": "alarm/get_director_alarms.json",
    "/vnms/fault/director/fail-over-alarms": "alarm/get_director_fail_over_alarms.json",
    "/vnms/fault/director/ha-alarms": "alarm/get_director_ha_alarms.json",
    "/vnms/fault/director/pop-up-summary": "alarm/get_imp_alarm_summary.json",
    "/vnms/fault/director/pop-up": "alarm/get_imp_alarms.json",
    "/vnms/fault/alarm/status": "alarm/get_status_change.json",
    # ============================================
    # AUDIT APIs (1 endpoint)
    # ============================================
    "/vnms/audit/logs": "audit/get_audit_logs.json",
    # ============================================
    # ASSETS APIs (1 endpoint)
    # ============================================
    "/vnms/assets/asset": "assets/get_all_assets.json",
}


def normalize_endpoint(url: str, base_url: str) -> str:
    """
    Normalize a full URL to an endpoint pattern.
    Strips the base URL and converts path parameters to placeholders.
    """
    import re

    # Remove base URL
    endpoint = url.replace(base_url, "")

    # Try exact match first
    if endpoint in ENDPOINT_TO_MOCK:
        return endpoint

    # Try to match with path parameters
    # Sort by specificity (more slashes = more specific)
    patterns = sorted(ENDPOINT_TO_MOCK.keys(), key=lambda x: -x.count("/"))

    for pattern in patterns:
        # Convert pattern to regex
        regex_pattern = pattern
        # Replace {param} with a capture group
        regex_pattern = re.sub(r"\{[^}]+\}", r"[^/]+", regex_pattern)
        regex_pattern = f"^{regex_pattern}$"

        if re.match(regex_pattern, endpoint):
            return pattern

    return endpoint


def get_mock_file(endpoint: str) -> str:
    """Get the mock file path for an endpoint pattern."""
    return ENDPOINT_TO_MOCK.get(endpoint)
