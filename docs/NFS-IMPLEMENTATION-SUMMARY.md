# NFS Root Implementation Summary

## Overview

This document summarizes the changes made to the Arrakis REST server to support NFS root filesystems for VM boot. These changes enable seamless integration with AgentFS, allowing VMs to boot from an NFS-mounted root filesystem that tracks all filesystem operations.

## Changes Made

### 1. API Schema Updates (`api/server-api.yaml`)

**Added NFS configuration fields to `StartVMRequest`:**

```yaml
StartVMRequest:
  type: object
  properties:
    # ... existing fields ...
    useNfsRoot:
      type: boolean
      description: Whether to use NFS root filesystem instead of local disk
    nfsServer:
      type: string
      description: NFS server address (required when useNfsRoot is true)
    nfsPort:
      type: integer
      description: NFS server port (required when useNfsRoot is true)
    nfsPath:
      type: string
      description: NFS export path (default is /)
```

**Impact:** Clients can now specify NFS root configuration per VM request.

### 2. Configuration Structure (`pkg/config/config.go`)

**Added NFS fields to `ServerConfig`:**

```go
type ServerConfig struct {
    // ... existing fields ...
    NFSEnabled         bool   `mapstructure:"nfs_enabled"`
    NFSServer          string `mapstructure:"nfs_server"`
    NFSPort            int32  `mapstructure:"nfs_port"`
    NFSPath            string `mapstructure:"nfs_path"`
}
```

**Impact:** Server can be configured with default NFS settings that apply to all VMs.

### 3. Default Configuration (`config.yaml`)

**Added NFS configuration section:**

```yaml
hostservices:
  restserver:
    # ... existing settings ...
    # NFS root configuration (optional)
    nfs_enabled: false
    nfs_server: "127.0.0.1"
    nfs_port: 11111
    nfs_path: "/"
```

**Impact:** Administrators can enable NFS root globally via configuration file.

### 4. Kernel Command Line Generation (`pkg/server/server.go`)

**Modified `getKernelCmdLine` function:**

```go
func getKernelCmdLine(
    gatewayIP string, 
    guestIP string, 
    vmName string, 
    useNfsRoot bool, 
    nfsServer string, 
    nfsPort int32, 
    nfsPath string,
) string {
    if useNfsRoot {
        if nfsPath == "" {
            nfsPath = "/"
        }
        return fmt.Sprintf(
            "console=ttyS0 root=/dev/nfs nfsroot=%s:%s,nfsvers=3,tcp,nolock,port=%d ip=dhcp rw gateway_ip=\"%s\" guest_ip=\"%s\" vm_name=\"%s\"",
            nfsServer, nfsPath, nfsPort, gatewayIP, guestIP, vmName,
        )
    }
    // Standard disk-based boot cmdline
    return fmt.Sprintf(
        "console=ttyS0 gateway_ip=\"%s\" guest_ip=\"%s\" vm_name=\"%s\"",
        gatewayIP, guestIP, vmName,
    )
}
```

**Changes:**
- Added NFS parameters to function signature
- Conditional kernel command line generation based on `useNfsRoot`
- NFS root includes: `root=/dev/nfs`, `nfsroot=...`, `ip=dhcp`, `rw`

**Impact:** VMs boot with appropriate kernel parameters for NFS root.

### 5. VM Creation Logic (`pkg/server/server.go`)

**Modified `createVM` function signature:**

```go
func (s *Server) createVM(
    ctx context.Context,
    vmName string,
    kernelPath string,
    initramfsPath string,
    rootfsPath string,
    forRestore bool,
    useNfsRoot bool,      // NEW
    nfsServer string,     // NEW
    nfsPort int32,        // NEW
    nfsPath string,       // NEW
) (*vm, error) {
    // ...
}
```

**Modified disk configuration logic:**

```go
// Build disk configuration - skip rootfs if using NFS root
var disks []chvapi.DiskConfig
if !useNfsRoot {
    // Standard: rootfs (readonly) + stateful disk
    disks = []chvapi.DiskConfig{
        {Path: rootfsPath, Readonly: Bool(true), NumQueues: &numBlockDeviceQueues},
        {Path: statefulDiskPath, NumQueues: &numBlockDeviceQueues},
    }
} else {
    // NFS root: only stateful disk
    disks = []chvapi.DiskConfig{
        {Path: statefulDiskPath, NumQueues: &numBlockDeviceQueues},
    }
}
```

**Updated VM config creation:**

```go
vmConfig := chvapi.VmConfig{
    Payload: chvapi.PayloadConfig{
        Kernel:    String(kernelPath),
        Cmdline:   String(getKernelCmdLine(
            s.config.BridgeIP, 
            guestIP.String(), 
            vmName, 
            useNfsRoot,    // NEW
            nfsServer,     // NEW
            nfsPort,       // NEW
            nfsPath,       // NEW
        )),
        Initramfs: String(initramfsPath),
    },
    Disks: disks,  // Conditional disk list
    // ... rest of config ...
}
```

**Impact:** VMs are created with correct disk and kernel configuration based on NFS settings.

### 6. VM Startup Logic (`pkg/server/server.go`)

**Modified `StartVM` function:**

```go
func (s *Server) StartVM(ctx context.Context, req *serverapi.StartVMRequest) (*serverapi.StartVMResponse, error) {
    // ... existing vmName and snapshot handling ...

    // Extract NFS parameters from request, use config defaults if not provided
    useNfsRoot := req.GetUseNfsRoot()
    if !useNfsRoot {
        useNfsRoot = s.config.NFSEnabled
    }

    nfsServer := req.GetNfsServer()
    if nfsServer == "" {
        nfsServer = s.config.NFSServer
    }

    nfsPort := req.GetNfsPort()
    if nfsPort == 0 {
        nfsPort = s.config.NFSPort
    }

    nfsPath := req.GetNfsPath()
    if nfsPath == "" {
        nfsPath = s.config.NFSPath
    }

    // Validate NFS configuration if NFS root is enabled
    if useNfsRoot {
        if nfsServer == "" {
            return nil, fmt.Errorf("NFS server address is required when useNfsRoot is true")
        }
        if nfsPort == 0 {
            return nil, fmt.Errorf("NFS server port is required when useNfsRoot is true")
        }
        logger.Infof("Using NFS root: server=%s, port=%d, path=%s", nfsServer, nfsPort, nfsPath)
    }

    // ... create/boot VM with NFS parameters ...
    vm, err = s.createVM(ctx, vmName, kernelPath, initramfsPath, rootfsPath, false, 
                         useNfsRoot, nfsServer, nfsPort, nfsPath)
    // ...
}
```

**Changes:**
- Extract NFS parameters from request
- Fall back to config defaults if not provided
- Request parameters override config defaults
- Validate NFS configuration
- Pass NFS parameters to `createVM`

**Impact:** 
- Per-request NFS configuration
- Config-wide defaults
- Proper validation

### 7. Snapshot Restore Logic (`pkg/server/server.go`)

**Updated `restoreVM` function call:**

```go
// Snapshots don't use NFS parameters (preserved from original VM)
vm, err := s.createVM(ctx, vmName, "", "", "", true, false, "", 0, "")
```

**Impact:** Snapshot restoration continues to work, preserving original VM configuration.

### 8. Generated API Client Code

**Generated from updated OpenAPI spec:**

Files generated in `out/gen/serverapi/`:
- `model_start_vm_request.go` - Contains NFS fields with proper getters/setters
- Updated API client with NFS support

**New methods in `StartVMRequest`:**
- `GetUseNfsRoot() bool`
- `GetNfsServer() string`
- `GetNfsPort() int32`
- `GetNfsPath() string`
- `SetUseNfsRoot(v bool)`
- `SetNfsServer(v string)`
- `SetNfsPort(v int32)`
- `SetNfsPath(v string)`

## Configuration Precedence

The system uses the following precedence for NFS settings:

1. **Request parameters** (highest priority)
2. **Config file defaults**
3. **Hardcoded defaults** (lowest priority)

### Example Scenarios

**Scenario 1: Global NFS enabled, no request override**
- Config: `nfs_enabled: true, nfs_server: "127.0.0.1", nfs_port: 11111`
- Request: `{"vmName": "test"}`
- Result: VM uses NFS root from 127.0.0.1:11111

**Scenario 2: Global NFS disabled, request enables it**
- Config: `nfs_enabled: false`
- Request: `{"vmName": "test", "useNfsRoot": true, "nfsServer": "10.0.0.1", "nfsPort": 2049}`
- Result: VM uses NFS root from 10.0.0.1:2049

**Scenario 3: Global NFS enabled, request overrides server**
- Config: `nfs_enabled: true, nfs_server: "127.0.0.1", nfs_port: 11111`
- Request: `{"vmName": "test", "nfsServer": "192.168.1.100"}`
- Result: VM uses NFS root from 192.168.1.100:11111

## Validation Rules

1. If `useNfsRoot` is `true`:
   - `nfsServer` must be non-empty (either from request or config)
   - `nfsPort` must be non-zero (either from request or config)
   - `nfsPath` defaults to `/` if not specified
   - `rootfs` parameter is ignored

2. If `useNfsRoot` is `false`:
   - Standard disk-based boot
   - `rootfs` parameter is used

## Testing

### Build Verification

```bash
cd arrakis
make serverapi chvapi
go build -o out/arrakis-restserver ./cmd/restserver
go build -o out/arrakis-client ./cmd/client
```

All builds completed successfully.

### Manual Testing

**Test 1: NFS root via config**
```bash
# Edit config.yaml: nfs_enabled: true
./out/arrakis-restserver --config config.yaml

# In another terminal
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "test-vm"}'
```

**Test 2: NFS root via request**
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "nfs-vm",
    "useNfsRoot": true,
    "nfsServer": "127.0.0.1",
    "nfsPort": 11111
  }'
```

## Backward Compatibility

✅ **Fully backward compatible**

- Existing clients continue to work without changes
- Default behavior unchanged (NFS disabled by default)
- New fields are optional
- Disk-based boot still fully supported

## Documentation

Created comprehensive documentation:

1. **NFS-ROOT-USAGE.md** - Complete user guide with examples
2. **NFS-IMPLEMENTATION-SUMMARY.md** - This technical summary
3. Updated **config.yaml** with NFS configuration comments

## Integration with AgentFS

This implementation enables the following workflow:

1. Start AgentFS NFS server: `agentfs nfs start --port 11111`
2. Configure Arrakis with NFS settings
3. Start VM: VM boots with root filesystem from AgentFS
4. All filesystem operations tracked in AgentFS SQLite database
5. Full audit trail, diffs, and version control for VM filesystem

## Files Modified

1. `api/server-api.yaml` - API schema
2. `pkg/config/config.go` - Configuration structure
3. `config.yaml` - Default configuration
4. `pkg/server/server.go` - Core VM logic (3 functions modified)
5. `out/gen/serverapi/*.go` - Generated API client (regenerated)

## Files Created

1. `docs/NFS-ROOT-USAGE.md` - User documentation
2. `docs/NFS-IMPLEMENTATION-SUMMARY.md` - Technical summary

## Next Steps (Optional Future Enhancements)

1. **NFSv4 Support** - Add configuration for NFS version
2. **Authentication** - Add NFS authentication options
3. **Performance Tuning** - Add NFS mount options configuration
4. **Health Checks** - Verify NFS server availability before VM start
5. **Metrics** - Track NFS vs disk performance metrics
6. **Multi-Export** - Support different NFS exports per VM

## References

- [AgentFS Integration Guide](../setup/AGENTFS-INTEGRATION.md)
- [NFS Root Usage Documentation](./NFS-ROOT-USAGE.md)
- [OpenAPI Specification](../api/server-api.yaml)
- [Server Configuration](../config.yaml)