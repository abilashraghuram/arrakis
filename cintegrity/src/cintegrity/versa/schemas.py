"""
Pydantic models for Versa Director API responses.

These schemas provide structured, fully typed output for all MCP tools.
"""

from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Common/Shared Models
# =============================================================================


class Location(BaseModel):
    """Geographic location information."""

    site: str
    latitude: float
    longitude: float


class SeverityCounts(BaseModel):
    """Alarm counts by severity level."""

    CRITICAL: int = 0
    MAJOR: int = 0
    MINOR: int = 0
    WARNING: int = 0


# =============================================================================
# Appliance Models
# =============================================================================


class ApplianceStatusItem(BaseModel):
    """Individual appliance status in a list."""

    uuid: str
    name: str
    org: str
    ping_status: str = Field(alias="pingStatus")
    sync_status: str = Field(alias="syncStatus")
    services_status: str = Field(alias="servicesStatus")
    path_status: str = Field(alias="pathStatus")
    hardware_health: str = Field(alias="hardwareHealth")
    software_version: str = Field(alias="softwareVersion")
    last_updated: str = Field(alias="lastUpdated")

    model_config = {"populate_by_name": True}


class AllApplianceStatusResponse(BaseModel):
    """Response for get_all_appliance_status."""

    total_count: int = Field(alias="totalCount")
    appliances: list[ApplianceStatusItem]

    model_config = {"populate_by_name": True}


class SingleApplianceLocation(BaseModel):
    """Location within a single appliance status."""

    site: str
    latitude: float
    longitude: float


class SingleApplianceStatusResponse(BaseModel):
    """Response for get_single_appliance_status."""

    uuid: str
    name: str
    org: str
    type: str
    model: str
    serial_number: str = Field(alias="serialNumber")
    ping_status: str = Field(alias="pingStatus")
    sync_status: str = Field(alias="syncStatus")
    controller_status: str = Field(alias="controllerStatus")
    services_status: str = Field(alias="servicesStatus")
    path_status: str = Field(alias="pathStatus")
    hardware_health: str = Field(alias="hardwareHealth")
    cpu_usage: int = Field(alias="cpuUsage")
    memory_usage: int = Field(alias="memoryUsage")
    disk_usage: int = Field(alias="diskUsage")
    software_version: str = Field(alias="softwareVersion")
    uptime_seconds: int = Field(alias="uptimeSeconds")
    last_seen: str = Field(alias="lastSeen")
    location: SingleApplianceLocation

    model_config = {"populate_by_name": True}


class TemplateListingItem(BaseModel):
    """Template in a device template listing."""

    template_name: str = Field(alias="templateName")
    template_type: str = Field(alias="templateType")
    version: str
    status: str
    last_applied: str = Field(alias="lastApplied")

    model_config = {"populate_by_name": True}


class DeviceTemplateListingResponse(BaseModel):
    """Response for get_device_template_listing."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    org: str
    templates: list[TemplateListingItem]

    model_config = {"populate_by_name": True}


class ApplianceLocationItem(BaseModel):
    """Individual appliance location."""

    uuid: str
    name: str
    org: str
    site: str
    latitude: float
    longitude: float
    address: str
    status: str


class ApplianceLocationsResponse(BaseModel):
    """Response for get_appliance_locations."""

    total_count: int = Field(alias="totalCount")
    locations: list[ApplianceLocationItem]

    model_config = {"populate_by_name": True}


class RoutingInstance(BaseModel):
    """Individual routing instance."""

    name: str
    type: str
    rd: str
    interfaces: list[str]
    routes: int
    status: str


class RoutingInstancesResponse(BaseModel):
    """Response for get_routing_instance_information."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    instances: list[RoutingInstance]

    model_config = {"populate_by_name": True}


class ApplianceByTypeItem(BaseModel):
    """Appliance in type/tags list."""

    uuid: str
    name: str
    org: str
    type: str
    model: str
    tags: list[str]
    status: str


class AppliancesByTypeResponse(BaseModel):
    """Response for get_all_appliances_by_type_and_tags."""

    total_count: int = Field(alias="totalCount")
    appliances: list[ApplianceByTypeItem]

    model_config = {"populate_by_name": True}


class ApplianceLiteItem(BaseModel):
    """Lite appliance information."""

    uuid: str
    name: str
    org: str
    status: str


class AppliancesLiteResponse(BaseModel):
    """Response for get_all_appliances_lite."""

    total_count: int = Field(alias="totalCount")
    appliances: list[ApplianceLiteItem]

    model_config = {"populate_by_name": True}


class ApplianceLiteViewItem(BaseModel):
    """Lite view appliance information."""

    uuid: str
    name: str
    org: str
    type: str
    status: str
    ip: str


class AppliancesLiteViewResponse(BaseModel):
    """Response for get_all_appliances_liteview."""

    total_count: int = Field(alias="totalCount")
    appliances: list[ApplianceLiteViewItem]

    model_config = {"populate_by_name": True}


class SearchResultItem(BaseModel):
    """Search result appliance."""

    uuid: str
    name: str
    org: str
    type: str
    model: str
    status: str
    site: str


class SearchApplianceResponse(BaseModel):
    """Response for search_appliance_by_name."""

    total_count: int = Field(alias="totalCount")
    appliances: list[SearchResultItem]

    model_config = {"populate_by_name": True}


class ConfigurationSystem(BaseModel):
    """System configuration section."""

    hostname: str
    domain: str
    ntp_servers: list[str] = Field(alias="ntpServers")

    model_config = {"populate_by_name": True}


class InterfaceConfig(BaseModel):
    """Interface configuration."""

    description: str
    ip: str


class RoutingBgp(BaseModel):
    """BGP routing configuration."""

    as_number: int = Field(alias="as")
    neighbors: list[str]

    model_config = {"populate_by_name": True}


class RoutingConfig(BaseModel):
    """Routing configuration section."""

    bgp: RoutingBgp


class ConfigurationDetails(BaseModel):
    """Full configuration details."""

    system: ConfigurationSystem
    interfaces: dict[str, InterfaceConfig]
    routing: RoutingConfig


class ConfigurationExportResponse(BaseModel):
    """Response for export_appliance_configuration."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    export_time: str = Field(alias="exportTime")
    format: str
    configuration: ConfigurationDetails

    model_config = {"populate_by_name": True}


class StatusCounts(BaseModel):
    """Appliance status counts."""

    UP: int = 0
    DOWN: int = 0
    DEGRADED: int = 0
    UNREACHABLE: int = 0


class SyncStatusCounts(BaseModel):
    """Sync status counts."""

    IN_SYNC: int = 0
    OUT_OF_SYNC: int = 0
    PENDING: int = 0


class AppliancesSummaryResponse(BaseModel):
    """Response for get_appliances_summary."""

    total_appliances: int = Field(alias="totalAppliances")
    by_status: StatusCounts = Field(alias="byStatus")
    by_type: dict[str, int] = Field(alias="byType")
    by_sync_status: SyncStatusCounts = Field(alias="bySyncStatus")
    by_org: dict[str, int] = Field(alias="byOrg")

    model_config = {"populate_by_name": True}


class ApplianceDetailsResponse(BaseModel):
    """Response for get_appliance_details_by_uuid."""

    uuid: str
    name: str
    org: str
    type: str
    model: str
    serial_number: str = Field(alias="serialNumber")
    software_version: str = Field(alias="softwareVersion")
    hardware_version: str = Field(alias="hardwareVersion")
    site: str
    ip: str
    management_ip: str = Field(alias="managementIp")
    controller: str
    controller_uuid: str = Field(alias="controllerUuid")
    status: str
    sync_status: str = Field(alias="syncStatus")
    uptime_seconds: int = Field(alias="uptimeSeconds")
    last_boot: str = Field(alias="lastBoot")
    last_seen: str = Field(alias="lastSeen")
    templates: list[str]
    device_groups: list[str] = Field(alias="deviceGroups")
    tags: list[str]

    model_config = {"populate_by_name": True}


class CpuInfo(BaseModel):
    """CPU hardware information."""

    model: str
    cores: int
    frequency_mhz: int = Field(alias="frequencyMhz")
    usage_percent: int = Field(alias="usagePercent")

    model_config = {"populate_by_name": True}


class MemoryInfo(BaseModel):
    """Memory hardware information."""

    total_gb: int = Field(alias="totalGb")
    used_gb: float = Field(alias="usedGb")
    usage_percent: int = Field(alias="usagePercent")

    model_config = {"populate_by_name": True}


class DiskInfo(BaseModel):
    """Disk hardware information."""

    total_gb: int = Field(alias="totalGb")
    used_gb: int = Field(alias="usedGb")
    usage_percent: int = Field(alias="usagePercent")

    model_config = {"populate_by_name": True}


class HardwareInterface(BaseModel):
    """Hardware interface information."""

    name: str
    mac: str
    speed_mbps: int = Field(alias="speedMbps")
    type: str

    model_config = {"populate_by_name": True}


class PowerSupply(BaseModel):
    """Power supply information."""

    status: str
    input_voltage: int = Field(alias="inputVoltage")
    output_watts: int = Field(alias="outputWatts")

    model_config = {"populate_by_name": True}


class Temperature(BaseModel):
    """Temperature information."""

    cpu_celsius: int = Field(alias="cpuCelsius")
    system_celsius: int = Field(alias="systemCelsius")
    status: str

    model_config = {"populate_by_name": True}


class ApplianceHardwareResponse(BaseModel):
    """Response for get_appliance_hardware."""

    uuid: str
    name: str
    model: str
    serial_number: str = Field(alias="serialNumber")
    cpu: CpuInfo
    memory: MemoryInfo
    disk: DiskInfo
    interfaces: list[HardwareInterface]
    power_supply: PowerSupply = Field(alias="powerSupply")
    temperature: Temperature

    model_config = {"populate_by_name": True}


class BandwidthMeasurement(BaseModel):
    """Individual bandwidth measurement."""

    interface: str
    circuit: str
    configured_bandwidth_mbps: int = Field(alias="configuredBandwidthMbps")
    measured_download_mbps: float = Field(alias="measuredDownloadMbps")
    measured_upload_mbps: float = Field(alias="measuredUploadMbps")
    last_test: str = Field(alias="lastTest")
    status: str | None = None

    model_config = {"populate_by_name": True}


class BandwidthMeasurementResponse(BaseModel):
    """Response for get_bw_measurement."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    timestamp: str
    measurements: list[BandwidthMeasurement]

    model_config = {"populate_by_name": True}


class CapabilitiesDetail(BaseModel):
    """Appliance capability flags."""

    sdwan: bool
    ngfw: bool
    ipsec_vpn: bool = Field(alias="ipsecVpn")
    ssl_vpn: bool = Field(alias="sslVpn")
    url_filtering: bool = Field(alias="urlFiltering")
    ids_ips: bool = Field(alias="idsIps")
    anti_malware: bool = Field(alias="antiMalware")
    dlp: bool
    casb: bool
    ztna: bool
    lte_support: bool = Field(alias="lteSupport")
    five_g_support: bool = Field(alias="fiveGSupport")
    wifi: bool
    poe: bool
    ha: bool

    model_config = {"populate_by_name": True}


class LicenseInfo(BaseModel):
    """License information."""

    status: str
    expiry: str


class CapabilitiesResponse(BaseModel):
    """Response for get_appliance_capabilities."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    model: str
    capabilities: CapabilitiesDetail
    licenses: dict[str, LicenseInfo]
    max_tunnels: int = Field(alias="maxTunnels")
    max_policies: int = Field(alias="maxPolicies")
    max_routes: int = Field(alias="maxRoutes")

    model_config = {"populate_by_name": True}


class SyncDetails(BaseModel):
    """Sync status details."""

    configuration: str
    policies: str
    routes: str
    certificates: str


class LastDeploy(BaseModel):
    """Last deployment information."""

    timestamp: str
    user: str
    status: str


class SyncStatusResponse(BaseModel):
    """Response for get_appliance_sync_status."""

    uuid: str
    name: str
    org: str
    sync_status: str = Field(alias="syncStatus")
    last_sync: str = Field(alias="lastSync")
    sync_details: SyncDetails = Field(alias="syncDetails")
    pending_changes: int = Field(alias="pendingChanges")
    last_deploy: LastDeploy = Field(alias="lastDeploy")

    model_config = {"populate_by_name": True}


class ServiceInfo(BaseModel):
    """Individual service information."""

    name: str
    status: str
    uptime_seconds: int = Field(alias="uptimeSeconds")
    cpu_percent: int = Field(alias="cpuPercent")
    memory_mb: int = Field(alias="memoryMb")

    model_config = {"populate_by_name": True}


class ApplianceServicesResponse(BaseModel):
    """Response for get_appliance_services."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    services: list[ServiceInfo]

    model_config = {"populate_by_name": True}


class HealthStatus(BaseModel):
    """Health status breakdown."""

    overall: str
    cpu: str
    memory: str
    disk: str
    interfaces: str
    paths: str
    services: str


class MetricsInfo(BaseModel):
    """Appliance metrics."""

    cpu_percent: int = Field(alias="cpuPercent")
    memory_percent: int = Field(alias="memoryPercent")
    disk_percent: int = Field(alias="diskPercent")
    active_sessions: int = Field(alias="activeSessions")
    throughput_mbps: float = Field(alias="throughputMbps")

    model_config = {"populate_by_name": True}


class ApplianceStatusResponse(BaseModel):
    """Response for get_appliance_status."""

    uuid: str
    name: str
    org: str
    status: str
    ping_status: str = Field(alias="pingStatus")
    controller_status: str = Field(alias="controllerStatus")
    controller: str
    software_version: str = Field(alias="softwareVersion")
    uptime_seconds: int = Field(alias="uptimeSeconds")
    last_seen: str = Field(alias="lastSeen")
    health: HealthStatus
    metrics: MetricsInfo

    model_config = {"populate_by_name": True}


class StatusBriefResponse(BaseModel):
    """Response for get_appliance_status_brief."""

    uuid: str
    name: str
    org: str
    status: str
    health: str
    sync_status: str = Field(alias="syncStatus")
    last_seen: str = Field(alias="lastSeen")

    model_config = {"populate_by_name": True}


class ApplianceNamesResponse(BaseModel):
    """Response for get_all_appliance_names."""

    total_count: int = Field(alias="totalCount")
    names: list[str]

    model_config = {"populate_by_name": True}


class BasicApplianceItem(BaseModel):
    """Basic appliance details."""

    uuid: str
    name: str
    org: str
    type: str
    status: str
    ip: str


class AppliancesBasicResponse(BaseModel):
    """Response for get_all_appliances_basic_details."""

    total_count: int = Field(alias="totalCount")
    appliances: list[BasicApplianceItem]

    model_config = {"populate_by_name": True}


class Violation(BaseModel):
    """Individual violation."""

    violation_id: str = Field(alias="violationId")
    type: str
    severity: str
    description: str
    path: str | None = None
    threshold: int | None = None
    actual_value: int | None = Field(default=None, alias="actualValue")
    unit: str | None = None
    detected_at: str = Field(alias="detectedAt")
    status: str

    model_config = {"populate_by_name": True}


class ViolationsResponse(BaseModel):
    """Response for get_appliance_violations."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    total_violations: int = Field(alias="totalViolations")
    violations: list[Violation]

    model_config = {"populate_by_name": True}


# =============================================================================
# Audit Models
# =============================================================================


class AuditLogEntry(BaseModel):
    """Individual audit log entry."""

    log_id: str = Field(alias="logId")
    timestamp: str
    user: str
    action: str
    target_type: str = Field(alias="targetType")
    target_id: str = Field(alias="targetId")
    target_name: str = Field(alias="targetName")
    details: str
    source_ip: str = Field(alias="sourceIp")
    result: str

    model_config = {"populate_by_name": True}


class AuditLogsResponse(BaseModel):
    """Response for get_audit_logs."""

    total_count: int = Field(alias="totalCount")
    logs: list[AuditLogEntry]

    model_config = {"populate_by_name": True}


# =============================================================================
# Workflow/Template Models
# =============================================================================


class WorkflowStage(BaseModel):
    """Workflow stage status."""

    stage: str
    completed: bool


class TemplateWorkflowResponse(BaseModel):
    """Response for get_template_workflow."""

    template_name: str = Field(alias="templateName")
    org: str
    type: str
    version: str
    description: str
    created: str
    created_by: str = Field(alias="createdBy")
    last_modified: str = Field(alias="lastModified")
    modified_by: str = Field(alias="modifiedBy")
    workflow_stages: list[WorkflowStage] = Field(alias="workflowStages")
    current_stage: str = Field(alias="currentStage")
    devices_bound: int = Field(alias="devicesBound")

    model_config = {"populate_by_name": True}


class DeviceWorkflowItem(BaseModel):
    """Device in workflow list."""

    uuid: str
    name: str
    org: str
    status: str
    templates: list[str]
    last_deploy: str = Field(alias="lastDeploy")
    deploy_status: str = Field(alias="deployStatus")

    model_config = {"populate_by_name": True}


class DeviceWorkflowsResponse(BaseModel):
    """Response for device_workflow_fetch_all."""

    total_count: int = Field(alias="totalCount")
    devices: list[DeviceWorkflowItem]

    model_config = {"populate_by_name": True}


class DeviceTemplateInfo(BaseModel):
    """Template info in specific device workflow."""

    template_name: str = Field(alias="templateName")
    type: str
    status: str
    version: str

    model_config = {"populate_by_name": True}


class DeployHistoryEntry(BaseModel):
    """Deploy history entry."""

    timestamp: str
    user: str
    status: str
    templates: list[str]


class SpecificDeviceWorkflowResponse(BaseModel):
    """Response for get_specific_device_workflow."""

    uuid: str
    name: str
    org: str
    status: str
    templates: list[DeviceTemplateInfo]
    bind_data: dict[str, str] = Field(alias="bindData")
    deploy_history: list[DeployHistoryEntry] = Field(alias="deployHistory")

    model_config = {"populate_by_name": True}


class BindDataHeader(BaseModel):
    """Bind data header field."""

    field: str
    type: str
    required: bool


class BindDataSample(BaseModel):
    """Sample bind data."""

    device: str
    hostname: str
    wan1_ip: str = Field(alias="wan1Ip")
    wan2_ip: str = Field(alias="wan2Ip")
    lan_subnet: str = Field(alias="lanSubnet")

    model_config = {"populate_by_name": True}


class BindDataHeaderResponse(BaseModel):
    """Response for get_template_bind_data_header_and_count."""

    template_name: str = Field(alias="templateName")
    org: str
    total_devices: int = Field(alias="totalDevices")
    headers: list[BindDataHeader]
    sample_data: list[BindDataSample] = Field(alias="sampleData")

    model_config = {"populate_by_name": True}


class TemplateItem(BaseModel):
    """Template in list."""

    template_name: str = Field(alias="templateName")
    org: str
    type: str
    description: str
    devices_bound: int = Field(alias="devicesBound")
    version: str
    last_modified: str = Field(alias="lastModified")
    modified_by: str = Field(alias="modifiedBy")

    model_config = {"populate_by_name": True}


class TemplatesResponse(BaseModel):
    """Response for template_fetch_all."""

    total_count: int = Field(alias="totalCount")
    templates: list[TemplateItem]

    model_config = {"populate_by_name": True}


class TemplateConfiguration(BaseModel):
    """Template configuration details."""

    interfaces: dict[str, int]
    routing: dict[str, bool]
    security: dict[str, bool]
    sdwan: dict[str, int]


class BindDataSchema(BaseModel):
    """Bind data schema."""

    fields: list[str]


class SpecificTemplateWorkflowResponse(BaseModel):
    """Response for get_specific_template_workflow."""

    template_name: str = Field(alias="templateName")
    org: str
    type: str
    version: str
    description: str
    configuration: TemplateConfiguration
    bind_data_schema: BindDataSchema = Field(alias="bindDataSchema")
    devices_bound: int = Field(alias="devicesBound")

    model_config = {"populate_by_name": True}


class DeviceTemplateAssociation(BaseModel):
    """Template associated to device."""

    template_name: str = Field(alias="templateName")
    type: str
    bind_status: str = Field(alias="bindStatus")
    version: str
    last_deployed: str = Field(alias="lastDeployed")

    model_config = {"populate_by_name": True}


class DeviceTemplatesResponse(BaseModel):
    """Response for show_templates_associated_to_device."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    org: str
    templates: list[DeviceTemplateAssociation]

    model_config = {"populate_by_name": True}


# =============================================================================
# Device Group Models
# =============================================================================


class DeviceInGroup(BaseModel):
    """Device in a device group."""

    uuid: str
    name: str
    type: str | None = None
    status: str | None = None
    site: str | None = None


class DeviceGroupItem(BaseModel):
    """Device group in list."""

    name: str
    org: str
    description: str
    device_count: int = Field(alias="deviceCount")
    devices: list[DeviceInGroup]
    created: str
    created_by: str = Field(alias="createdBy")

    model_config = {"populate_by_name": True}


class DeviceGroupsResponse(BaseModel):
    """Response for device_group_fetch_all."""

    total_count: int = Field(alias="totalCount")
    device_groups: list[DeviceGroupItem] = Field(alias="deviceGroups")

    model_config = {"populate_by_name": True}


class SpecificDeviceGroupResponse(BaseModel):
    """Response for get_specific_device_group."""

    name: str
    org: str
    description: str
    device_count: int = Field(alias="deviceCount")
    devices: list[DeviceInGroup]
    policies: list[Any]
    created: str
    created_by: str = Field(alias="createdBy")
    last_modified: str = Field(alias="lastModified")
    modified_by: str = Field(alias="modifiedBy")

    model_config = {"populate_by_name": True}


class ModelNumber(BaseModel):
    """Model number information."""

    model: str
    type: str
    description: str
    max_tunnels: int = Field(alias="maxTunnels")
    max_bandwidth_mbps: int = Field(alias="maxBandwidthMbps")
    device_count: int = Field(alias="deviceCount")

    model_config = {"populate_by_name": True}


class ModelNumbersResponse(BaseModel):
    """Response for get_all_model_numbers."""

    models: list[ModelNumber]


# =============================================================================
# Asset Models
# =============================================================================


class Asset(BaseModel):
    """Asset information."""

    uuid: str
    name: str
    org: str
    type: str
    model: str
    serial_number: str = Field(alias="serialNumber")
    status: str
    site: str
    purchase_date: str = Field(alias="purchaseDate")
    warranty_expiry: str = Field(alias="warrantyExpiry")
    license_status: str = Field(alias="licenseStatus")

    model_config = {"populate_by_name": True}


class AssetsResponse(BaseModel):
    """Response for get_all_assets."""

    total_count: int = Field(alias="totalCount")
    assets: list[Asset]

    model_config = {"populate_by_name": True}


# =============================================================================
# Health/Dashboard Models
# =============================================================================


class PagedDataItem(BaseModel):
    """Item in paged data."""

    uuid: str
    name: str
    status: str


class PagedDataResponse(BaseModel):
    """Response for get_next_page_data."""

    query_id: str = Field(alias="queryId")
    total_count: int = Field(alias="totalCount")
    offset: int
    limit: int
    has_more: bool = Field(alias="hasMore")
    data: list[PagedDataItem]

    model_config = {"populate_by_name": True}


class MonitoringConfigResponse(BaseModel):
    """Response for get_enable_monitoring."""

    enabled: bool
    poll_interval_seconds: int = Field(alias="pollIntervalSeconds")
    metrics_retention_days: int = Field(alias="metricsRetentionDays")
    alerting_enabled: bool = Field(alias="alertingEnabled")
    monitored_services: list[str] = Field(alias="monitoredServices")

    model_config = {"populate_by_name": True}


class MonitorPullEnabledResponse(BaseModel):
    """Response for get_device_status_pulling_enabled."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    pull_enabled: bool = Field(alias="pullEnabled")
    poll_interval_seconds: int = Field(alias="pollIntervalSeconds")
    last_poll: str = Field(alias="lastPoll")
    next_poll: str = Field(alias="nextPoll")
    metrics_enabled: list[str] = Field(alias="metricsEnabled")

    model_config = {"populate_by_name": True}


class IkeSession(BaseModel):
    """IKE session information."""

    tunnel_name: str = Field(alias="tunnelName")
    peer_ip: str = Field(alias="peerIp")
    peer_device: str = Field(alias="peerDevice")
    peer_uuid: str = Field(alias="peerUuid")
    local_interface: str = Field(alias="localInterface")
    status: str
    ike_version: int = Field(alias="ikeVersion")
    encryption: str
    auth: str
    uptime_seconds: int | None = Field(default=None, alias="uptimeSeconds")
    bytes_in: int | None = Field(default=None, alias="bytesIn")
    bytes_out: int | None = Field(default=None, alias="bytesOut")
    packets_in: int | None = Field(default=None, alias="packetsIn")
    packets_out: int | None = Field(default=None, alias="packetsOut")
    down_reason: str | None = Field(default=None, alias="downReason")

    model_config = {"populate_by_name": True}


class IkeHealthResponse(BaseModel):
    """Response for get_health_ike."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    timestamp: str
    ike_sessions: list[IkeSession] = Field(alias="ikeSessions")

    model_config = {"populate_by_name": True}


class InterfaceHealth(BaseModel):
    """Interface health information."""

    name: str
    description: str
    admin_status: str = Field(alias="adminStatus")
    oper_status: str = Field(alias="operStatus")
    health: str
    speed_mbps: int = Field(alias="speedMbps")
    duplex: str
    mtu: int
    utilization_percent: float | None = Field(default=None, alias="utilizationPercent")
    errors_in: int | None = Field(default=None, alias="errorsIn")
    errors_out: int | None = Field(default=None, alias="errorsOut")
    drops_in: int | None = Field(default=None, alias="dropsIn")
    drops_out: int | None = Field(default=None, alias="dropsOut")
    down_reason: str | None = Field(default=None, alias="downReason")
    down_since: str | None = Field(default=None, alias="downSince")

    model_config = {"populate_by_name": True}


class InterfaceHealthResponse(BaseModel):
    """Response for get_health_interface."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    timestamp: str
    interfaces: list[InterfaceHealth]

    model_config = {"populate_by_name": True}


class PathMetrics(BaseModel):
    """Path metrics."""

    latency_ms: int = Field(alias="latencyMs")
    jitter_ms: int = Field(alias="jitterMs")
    packet_loss_percent: float = Field(alias="packetLossPercent")
    bandwidth_mbps: int = Field(alias="bandwidthMbps")

    model_config = {"populate_by_name": True}


class PathHealth(BaseModel):
    """Individual path health."""

    name: str
    circuit_name: str = Field(alias="circuitName")
    local_interface: str = Field(alias="localInterface")
    remote_device: str = Field(alias="remoteDevice")
    remote_uuid: str = Field(alias="remoteUuid")
    status: str
    sla_class: str = Field(alias="slaClass")
    metrics: PathMetrics | None = None
    down_reason: str | None = Field(default=None, alias="downReason")
    down_since: str | None = Field(default=None, alias="downSince")

    model_config = {"populate_by_name": True}


class PathHealthResponse(BaseModel):
    """Response for get_health_path."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    timestamp: str
    paths: list[PathHealth]

    model_config = {"populate_by_name": True}


class LteDevice(BaseModel):
    """LTE device information."""

    uuid: str
    name: str
    org: str
    lte_interface: str = Field(alias="lteInterface")
    carrier: str
    signal_strength_dbm: int = Field(alias="signalStrengthDbm")
    connection_type: str = Field(alias="connectionType")
    data_used_mb: int = Field(alias="dataUsedMb")
    data_limit_mb: int = Field(alias="dataLimitMb")
    status: str

    model_config = {"populate_by_name": True}


class LteDevicesResponse(BaseModel):
    """Response for get_devices_in_lte."""

    total_count: int = Field(alias="totalCount")
    devices: list[LteDevice]

    model_config = {"populate_by_name": True}


class NavTreeNode(BaseModel):
    """Navigation tree node."""

    uuid: str | None = None
    name: str
    type: str
    children: list["NavTreeNode"] | None = None
    status: str | None = None
    site: str | None = None


class NavTreeResponse(BaseModel):
    """Response for get_nav_tree_node."""

    root: NavTreeNode


class HeadEnd(BaseModel):
    """Head end status."""

    uuid: str
    name: str
    org: str
    type: str
    status: str
    role: str
    connected_branches: int = Field(alias="connectedBranches")
    active_tunnels: int = Field(alias="activeTunnels")
    throughput_mbps: float = Field(alias="throughputMbps")
    cpu_percent: int = Field(alias="cpuPercent")
    memory_percent: int = Field(alias="memoryPercent")
    uptime_seconds: int = Field(alias="uptimeSeconds")

    model_config = {"populate_by_name": True}


class HeadEndStatusResponse(BaseModel):
    """Response for get_head_end_status."""

    total_count: int = Field(alias="totalCount")
    head_ends: list[HeadEnd] = Field(alias="headEnds")

    model_config = {"populate_by_name": True}


class VdSystemStatus(BaseModel):
    """VD system status."""

    cpu_percent: int = Field(alias="cpuPercent")
    memory_percent: int = Field(alias="memoryPercent")
    disk_percent: int = Field(alias="diskPercent")

    model_config = {"populate_by_name": True}


class VdServicesStatus(BaseModel):
    """VD services status."""

    api: str
    database: str
    analytics: str
    scheduler: str


class ManagedDevicesStatus(BaseModel):
    """Managed devices status."""

    total: int
    connected: int
    disconnected: int


class VdStatusResponse(BaseModel):
    """Response for get_vd_status."""

    name: str
    version: str
    status: str
    role: str
    uptime_seconds: int = Field(alias="uptimeSeconds")
    last_restart: str = Field(alias="lastRestart")
    system: VdSystemStatus
    services: VdServicesStatus
    managed_devices: ManagedDevicesStatus = Field(alias="managedDevices")

    model_config = {"populate_by_name": True}


class HaNode(BaseModel):
    """HA node information."""

    name: str
    role: str
    status: str
    ip: str
    last_heartbeat: str = Field(alias="lastHeartbeat")

    model_config = {"populate_by_name": True}


class VdHaDetailsResponse(BaseModel):
    """Response for get_vd_ha_details."""

    ha_enabled: bool = Field(alias="haEnabled")
    cluster_status: str = Field(alias="clusterStatus")
    nodes: list[HaNode]
    sync_status: str = Field(alias="syncStatus")
    last_failover: str | None = Field(alias="lastFailover")
    failover_count: int = Field(alias="failoverCount")

    model_config = {"populate_by_name": True}


class InstalledPackage(BaseModel):
    """Installed package information."""

    name: str
    version: str


class AvailableUpgrade(BaseModel):
    """Available upgrade information."""

    version: str
    release_date: str = Field(alias="releaseDate")
    type: str

    model_config = {"populate_by_name": True}


class VdPackageInfoResponse(BaseModel):
    """Response for get_vd_package_info."""

    current_version: str = Field(alias="currentVersion")
    build_number: str = Field(alias="buildNumber")
    release_date: str = Field(alias="releaseDate")
    installed_packages: list[InstalledPackage] = Field(alias="installedPackages")
    available_upgrades: list[AvailableUpgrade] = Field(alias="availableUpgrades")

    model_config = {"populate_by_name": True}


class SysHardware(BaseModel):
    """System hardware details."""

    cpu_model: str = Field(alias="cpuModel")
    cpu_cores: int = Field(alias="cpuCores")
    memory_gb: int = Field(alias="memoryGb")
    disk_gb: int = Field(alias="diskGb")

    model_config = {"populate_by_name": True}


class SysNetwork(BaseModel):
    """System network details."""

    management_ip: str = Field(alias="managementIp")
    management_interface: str = Field(alias="managementInterface")

    model_config = {"populate_by_name": True}


class SysDetailsResponse(BaseModel):
    """Response for get_sys_details."""

    hostname: str
    version: str
    os: str
    kernel: str
    hardware: SysHardware
    network: SysNetwork
    timezone: str
    ntp_servers: list[str] = Field(alias="ntpServers")
    ntp_status: str = Field(alias="ntpStatus")

    model_config = {"populate_by_name": True}


class SysUptimeResponse(BaseModel):
    """Response for get_sys_uptime."""

    uptime_seconds: int = Field(alias="uptimeSeconds")
    uptime_human: str = Field(alias="uptimeHuman")
    last_boot: str = Field(alias="lastBoot")
    current_time: str = Field(alias="currentTime")

    model_config = {"populate_by_name": True}


class LiveStatusSystem(BaseModel):
    """Live status system metrics."""

    cpu_percent: int = Field(alias="cpuPercent")
    memory_percent: int = Field(alias="memoryPercent")
    disk_percent: int = Field(alias="diskPercent")
    uptime_seconds: int = Field(alias="uptimeSeconds")
    load_average: list[float] = Field(alias="loadAverage")

    model_config = {"populate_by_name": True}


class LiveStatusInterface(BaseModel):
    """Live status interface."""

    name: str
    description: str
    admin_status: str = Field(alias="adminStatus")
    oper_status: str = Field(alias="operStatus")
    speed_mbps: int = Field(alias="speedMbps")
    tx_bytes: int = Field(alias="txBytes")
    rx_bytes: int = Field(alias="rxBytes")
    tx_packets: int = Field(alias="txPackets")
    rx_packets: int = Field(alias="rxPackets")
    tx_errors: int = Field(alias="txErrors")
    rx_errors: int = Field(alias="rxErrors")
    down_reason: str | None = Field(default=None, alias="downReason")

    model_config = {"populate_by_name": True}


class LiveStatusResponse(BaseModel):
    """Response for get_appliance_live_status."""

    device_name: str = Field(alias="deviceName")
    uuid: str
    timestamp: str
    system: LiveStatusSystem
    interfaces: list[LiveStatusInterface]

    model_config = {"populate_by_name": True}


# =============================================================================
# Alarm Models
# =============================================================================


class AlarmPageItem(BaseModel):
    """Alarm in paginated list."""

    alarm_id: str = Field(alias="alarmId")
    device_name: str = Field(alias="deviceName")
    device_uuid: str = Field(alias="deviceUuid")
    org: str
    severity: str
    type: str
    managed_object: str = Field(alias="managedObject")
    alarm_text: str = Field(alias="alarmText")
    raised_time: str = Field(alias="raisedTime")
    is_cleared: bool = Field(alias="isCleared")
    ack_state: str = Field(alias="ackState")

    model_config = {"populate_by_name": True}


class AlarmsPageResponse(BaseModel):
    """Response for filter_paginate_alarm."""

    total_count: int = Field(alias="totalCount")
    offset: int
    limit: int
    has_more: bool = Field(alias="hasMore")
    alarms: list[AlarmPageItem]

    model_config = {"populate_by_name": True}


class AlarmHistoryEntry(BaseModel):
    """Alarm history entry."""

    timestamp: str
    action: str
    user: str
    details: str


class AlarmHandlingResponse(BaseModel):
    """Response for get_alarm_handling."""

    alarm_id: str = Field(alias="alarmId")
    device_name: str = Field(alias="deviceName")
    device_uuid: str = Field(alias="deviceUuid")
    org: str
    severity: str
    type: str
    handling_state: str = Field(alias="handlingState")
    ack_state: str = Field(alias="ackState")
    assignee: str | None
    notes: list[Any]
    history: list[AlarmHistoryEntry]

    model_config = {"populate_by_name": True}


class AlarmSummaryByOrgResponse(BaseModel):
    """Response for get_alarm_summary_per_org."""

    org: str
    timestamp: str
    total_active: int = Field(alias="totalActive")
    by_severity: SeverityCounts = Field(alias="bySeverity")
    by_device: dict[str, int] = Field(alias="byDevice")

    model_config = {"populate_by_name": True}


class AlarmTypeCounts(BaseModel):
    """Alarm counts by type."""

    LINK_DOWN: int = 0
    HIGH_CPU: int = 0
    PATH_DEGRADED: int = 0
    CONFIG_DRIFT: int = 0
    CERTIFICATE_EXPIRY: int = 0


class AlarmSummaryResponse(BaseModel):
    """Response for get_alarm_summary."""

    timestamp: str
    total_active: int = Field(alias="totalActive")
    by_severity: SeverityCounts = Field(alias="bySeverity")
    by_type: dict[str, int] = Field(alias="byType")
    cleared_last_24h: int = Field(alias="clearedLast24h")
    mttr_minutes: int = Field(alias="mttrMinutes")

    model_config = {"populate_by_name": True}


class AlarmTypeInfo(BaseModel):
    """Alarm type information."""

    type: str
    category: str
    default_severity: str = Field(alias="defaultSeverity")
    description: str

    model_config = {"populate_by_name": True}


class AlarmTypesResponse(BaseModel):
    """Response for get_alarm_types."""

    types: list[AlarmTypeInfo]


class FilteredAlarm(BaseModel):
    """Filtered alarm details."""

    alarm_id: str = Field(alias="alarmId")
    device_name: str = Field(alias="deviceName")
    device_uuid: str = Field(alias="deviceUuid")
    org: str
    severity: str
    type: str
    managed_object: str = Field(alias="managedObject")
    alarm_text: str = Field(alias="alarmText")
    specific_problem: str = Field(alias="specificProblem")
    probable_cause: str = Field(alias="probableCause")
    raised_time: str = Field(alias="raisedTime")
    last_status_change: str = Field(alias="lastStatusChange")
    is_cleared: bool = Field(alias="isCleared")
    ack_state: str = Field(alias="ackState")
    handling_state: str = Field(alias="handlingState")

    model_config = {"populate_by_name": True}


class FilteredAlarmsResponse(BaseModel):
    """Response for get_all_filtered_alarms."""

    total_count: int = Field(alias="totalCount")
    alarms: list[FilteredAlarm]

    model_config = {"populate_by_name": True}


class TopAlarmType(BaseModel):
    """Top alarm type count."""

    type: str
    count: int


class TopAffectedDevice(BaseModel):
    """Top affected device count."""

    device: str
    count: int


class AnalyticsAlarmSummaryResponse(BaseModel):
    """Response for get_analytics_alarm_summary."""

    timestamp: str
    period: str
    total_raised: int = Field(alias="totalRaised")
    total_cleared: int = Field(alias="totalCleared")
    mttr_minutes: int = Field(alias="mttrMinutes")
    by_severity: SeverityCounts = Field(alias="bySeverity")
    top_alarm_types: list[TopAlarmType] = Field(alias="topAlarmTypes")
    top_affected_devices: list[TopAffectedDevice] = Field(alias="topAffectedDevices")

    model_config = {"populate_by_name": True}


class AnalyticsAlarm(BaseModel):
    """Analytics alarm."""

    alarm_id: str = Field(alias="alarmId")
    device_name: str = Field(alias="deviceName")
    severity: str
    type: str
    alarm_text: str = Field(alias="alarmText")
    raised_time: str = Field(alias="raisedTime")
    duration_minutes: int = Field(alias="durationMinutes")

    model_config = {"populate_by_name": True}


class AnalyticsAlarmsResponse(BaseModel):
    """Response for get_analytics_alarms."""

    total_count: int = Field(alias="totalCount")
    alarms: list[AnalyticsAlarm]

    model_config = {"populate_by_name": True}


class AlarmDefinition(BaseModel):
    """Alarm definition."""

    type: str
    severity: str
    category: str
    auto_clear: bool = Field(alias="autoClear")
    clear_condition: str | None = Field(default=None, alias="clearCondition")
    threshold_percent: int | None = Field(default=None, alias="thresholdPercent")
    duration_seconds: int | None = Field(default=None, alias="durationSeconds")

    model_config = {"populate_by_name": True}


class ApplianceAlarmModelResponse(BaseModel):
    """Response for get_appliance_alarm_model."""

    model_version: str = Field(alias="modelVersion")
    alarm_definitions: list[AlarmDefinition] = Field(alias="alarmDefinitions")

    model_config = {"populate_by_name": True}


class ApplianceAlarmTypesResponse(BaseModel):
    """Response for get_appliance_alarm_types."""

    types: list[str]


class ActiveAlarmBrief(BaseModel):
    """Brief active alarm."""

    alarm_id: str = Field(alias="alarmId")
    severity: str
    type: str
    alarm_text: str = Field(alias="alarmText")

    model_config = {"populate_by_name": True}


class DeviceAlarmSummaryResponse(BaseModel):
    """Response for get_device_alarm_summary."""

    device_name: str = Field(alias="deviceName")
    device_uuid: str = Field(alias="deviceUuid")
    org: str
    timestamp: str
    total_active: int = Field(alias="totalActive")
    by_severity: SeverityCounts = Field(alias="bySeverity")
    active_alarms: list[ActiveAlarmBrief] = Field(alias="activeAlarms")

    model_config = {"populate_by_name": True}


class DirectorAlarmSummaryResponse(BaseModel):
    """Response for get_director_alarm_summary."""

    timestamp: str
    total_active: int = Field(alias="totalActive")
    by_severity: SeverityCounts = Field(alias="bySeverity")
    director_status: str = Field(alias="directorStatus")

    model_config = {"populate_by_name": True}


class DirectorAlarmsResponse(BaseModel):
    """Response for get_director_alarms."""

    total_count: int = Field(alias="totalCount")
    alarms: list[FilteredAlarm]

    model_config = {"populate_by_name": True}


class FailOverAlarmsResponse(BaseModel):
    """Response for get_director_fail_over_alarms."""

    total_count: int = Field(alias="totalCount")
    alarms: list[Any]
    last_failover: str | None = Field(alias="lastFailover")

    model_config = {"populate_by_name": True}


class HaAlarmsResponse(BaseModel):
    """Response for get_director_ha_alarms."""

    total_count: int = Field(alias="totalCount")
    alarms: list[Any]
    ha_status: str = Field(alias="haStatus")
    sync_status: str = Field(alias="syncStatus")

    model_config = {"populate_by_name": True}


class ImpAlarmSummaryResponse(BaseModel):
    """Response for get_imp_alarm_summary."""

    timestamp: str
    total_important: int = Field(alias="totalImportant")
    by_severity: dict[str, int] = Field(alias="bySeverity")
    requires_attention: bool = Field(alias="requiresAttention")

    model_config = {"populate_by_name": True}


class ImpAlarm(BaseModel):
    """Important alarm."""

    alarm_id: str = Field(alias="alarmId")
    device_name: str = Field(alias="deviceName")
    device_uuid: str = Field(alias="deviceUuid")
    org: str
    severity: str
    type: str
    alarm_text: str = Field(alias="alarmText")
    raised_time: str = Field(alias="raisedTime")
    duration_minutes: int = Field(alias="durationMinutes")
    impact: str

    model_config = {"populate_by_name": True}


class ImpAlarmsResponse(BaseModel):
    """Response for get_imp_alarms."""

    total_count: int = Field(alias="totalCount")
    alarms: list[ImpAlarm]

    model_config = {"populate_by_name": True}


class StatusChangeHistory(BaseModel):
    """Status change history entry."""

    timestamp: str
    severity: str
    status: str
    description: str


class StatusChangeResponse(BaseModel):
    """Response for get_status_change."""

    alarm_id: str = Field(alias="alarmId")
    device_name: str = Field(alias="deviceName")
    device_uuid: str = Field(alias="deviceUuid")
    org: str
    type: str
    current_severity: str = Field(alias="currentSeverity")
    current_status: str = Field(alias="currentStatus")
    history: list[StatusChangeHistory]

    model_config = {"populate_by_name": True}


# =============================================================================
# Error Response
# =============================================================================


class ErrorResponse(BaseModel):
    """Error response for API failures."""

    error: str
    endpoint: str | None = None
    text: str | None = None
