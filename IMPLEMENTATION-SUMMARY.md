# Arrakis NFS-Only Implementation Summary

## Overview

Arrakis REST server has been modified to **exclusively support NFS root filesystems**. All VMs boot with their root filesystem mounted over NFS. There is no backward compatibility with disk-based root filesystems.

## Design Philosophy

**Why NFS-only?**

1. **Purpose-built for AgentFS**: The entire system is designed for filesystem tracking
2. **Simplified Architecture**: One boot path, no conditional logic
3. **Complete Observability**: Every filesystem operation is visible
4. **No Compromise**: Optimized for the tracking use case

**What was removed:**
- Disk-based root filesystem support
- Rootfs disk image attachment
- Conditional NFS logic
- `useNfsRoot` toggle flag
- Backward compatibility code

## Implementation Changes

### 1. API Schema (`api/server-api.yaml`)

**Removed:**
- `rootfs` parameter (no longer needed)
- `useNfsRoot` boolean flag (always true)

**Kept:**
- `nfsServer` - NFS server address (REQUIRED)
- `nfsPort` - NFS server port (REQUIRED)
- `nfsPath` - NFS export path (optional, default: `/`)

**StartVMRequest Schema:**
```yaml
StartVMRequest:
  properties:
    vmName: string          # Required
    kernel: string          # Optional
    initramfs: string       # Optional
    entryPoint: string      # Optional
    snapshotId: string      # Optional (for restore)
    nfsServer: string       # Required (from config or request)
    nfsPort: integer        # Required (from config or request)
    nfsPath: string         # Optional (default: /)
```

### 2. Configuration (`pkg/config/config.go`)

**Removed:**
- `RootfsPath` field (no rootfs disk)
- `NFSEnabled` field (always enabled)

**Kept:**
- `NFSServer` - default NFS server
- `NFSPort` - default NFS port
- `NFSPath` - default NFS path

**ServerConfig Structure:**
```go
type ServerConfig struct {
    Host               string
    Port               string
    StateDir           string
    BridgeName         string
    BridgeIP           string
    BridgeSubnet       string
    ChvBinPath         string
    KernelPath         string
    // RootfsPath removed
    PortForwards       []PortForwardConfig
    InitramfsPath      string
    StatefulSizeInMB   int32
    GuestMemPercentage int32
    // NFSEnabled removed - always true
    NFSServer          string
    NFSPort            int32
    NFSPath            string
}
```

### 3. Kernel Command Line (`pkg/server/server.go`)

**Before (conditional):**
```go
func getKernelCmdLine(gatewayIP, guestIP, vmName string, 
                      useNfsRoot bool, nfsServer string, 
                      nfsPort int32, nfsPath string) string {
    if useNfsRoot {
        return fmt.Sprintf("console=ttyS0 root=/dev/nfs nfsroot=%s:%s,nfsvers=3,tcp,nolock,port=%d ...", ...)
    }
    return fmt.Sprintf("console=ttyS0 gateway_ip=\"%s\" ...", ...)
}
```

**After (NFS-only):**
```go
func getKernelCmdLine(gatewayIP, guestIP, vmName string,
                      nfsServer string, nfsPort int32, nfsPath string) string {
    if nfsPath == "" {
        nfsPath = "/"
    }
    return fmt.Sprintf(
        "console=ttyS0 root=/dev/nfs nfsroot=%s:%s,nfsvers=3,tcp,nolock,port=%d ip=dhcp rw gateway_ip=\"%s\" guest_ip=\"%s\" vm_name=\"%s\"",
        nfsServer, nfsPath, nfsPort, gatewayIP, guestIP, vmName,
    )
}
```

**Key changes:**
- Removed `useNfsRoot` parameter
- Removed conditional logic
- Always generates NFS root kernel parameters

### 4. VM Creation (`pkg/server/server.go`)

**Function Signature:**

Before:
```go
func (s *Server) createVM(ctx context.Context, vmName, kernelPath, 
                          initramfsPath, rootfsPath string, forRestore bool,
                          useNfsRoot bool, nfsServer string, 
                          nfsPort int32, nfsPath string) (*vm, error)
```

After:
```go
func (s *Server) createVM(ctx context.Context, vmName, kernelPath,
                          initramfsPath string, forRestore bool,
                          nfsServer string, nfsPort int32, 
                          nfsPath string) (*vm, error)
```

**Disk Configuration:**

Before (conditional):
```go
var disks []chvapi.DiskConfig
if !useNfsRoot {
    disks = []chvapi.DiskConfig{
        {Path: rootfsPath, Readonly: Bool(true), NumQueues: &numBlockDeviceQueues},
        {Path: statefulDiskPath, NumQueues: &numBlockDeviceQueues},
    }
} else {
    disks = []chvapi.DiskConfig{
        {Path: statefulDiskPath, NumQueues: &numBlockDeviceQueues},
    }
}
```

After (NFS-only):
```go
// Only stateful disk - root comes from NFS
disks := []chvapi.DiskConfig{
    {Path: statefulDiskPath, NumQueues: &numBlockDeviceQueues},
}
```

### 5. VM Startup (`pkg/server/server.go`)

**StartVM Logic:**

Before:
```go
// Extract NFS parameters, fall back to config defaults
useNfsRoot := req.GetUseNfsRoot()
if !useNfsRoot {
    useNfsRoot = s.config.NFSEnabled
}
// ... more conditional logic
if useNfsRoot {
    // validate
}
```

After:
```go
// NFS is always used - extract parameters
nfsServer := req.GetNfsServer()
if nfsServer == "" {
    nfsServer = s.config.NFSServer
}
// ... similar for port and path

// Always validate (NFS is required)
if nfsServer == "" {
    return nil, fmt.Errorf("NFS server address is required")
}
if nfsPort == 0 {
    return nil, fmt.Errorf("NFS server port is required")
}
```

### 6. Client Updates (`cmd/client/main.go`)

**Removed:**
- `--rootfs` / `-r` flag from `start` command
- `rootfs` parameter from `startVM()` function

**Updated:**
```go
// Before
func startVM(vmName, kernel, rootfs, entryPoint, snapshotId string) error

// After
func startVM(vmName, kernel, entryPoint, snapshotId string) error
```

## Configuration File

**Updated `config.yaml`:**
```yaml
hostservices:
  restserver:
    host: "0.0.0.0"
    port: "7000"
    state_dir: "./vm-state"
    bridge_name: "br0"
    bridge_ip: "10.20.1.1/24"
    bridge_subnet: "10.20.1.0/24"
    chv_bin: "./resources/bin/cloud-hypervisor"
    kernel: "./resources/bin/vmlinux.bin"
    # rootfs removed - not used anymore
    initramfs: "./out/initramfs.cpio.gz"
    port_forwards:
      - port: "5901"
        description: "gui"
      - port: "5736-5740"
        description: "code"
    stateful_size_in_mb: "2048"
    guest_mem_percentage: "30"
    # NFS configuration - REQUIRED
    nfs_enabled: true  # Always true, kept for compatibility
    nfs_server: "127.0.0.1"
    nfs_port: 11111
    nfs_path: "/"
```

## VM Boot Process

### Step-by-step Boot Flow

1. **Request received** with vmName and optional NFS parameters
2. **NFS validation**: Ensure server and port are configured
3. **Kernel cmdline generated**: Always includes `root=/dev/nfs`
4. **Disk config created**: Only stateful disk attached
5. **VM spawned**: cloud-hypervisor starts with NFS root
6. **Kernel boots**: Mounts root over NFS via network
7. **VM ready**: All filesystem ops go through NFS

### Kernel Command Line

**Generated command line:**
```
console=ttyS0 
root=/dev/nfs 
nfsroot=127.0.0.1:/,nfsvers=3,tcp,nolock,port=11111 
ip=dhcp 
rw 
gateway_ip="10.20.1.1" 
guest_ip="10.20.1.2" 
vm_name="my-vm"
```

**Key parameters:**
- `root=/dev/nfs` - Use NFS as root filesystem
- `nfsroot=<server>:<path>,<options>` - NFS mount details
- `ip=dhcp` - Network configuration for NFS access
- `rw` - Mount root read-write

### Disk Layout in VM

```
/dev/vda  -> Stateful disk (local, writable)
            Typically mounted at /var, /tmp, etc.
            
/         -> NFS mount (network, from server)
            Root filesystem served by NFS
```

## API Usage Examples

### Basic VM Creation
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-vm"
  }'
# Uses NFS server from config.yaml
```

### Override NFS Server
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-vm",
    "nfsServer": "10.0.0.5",
    "nfsPort": 2049,
    "nfsPath": "/exports/vm"
  }'
```

### Validation Errors
```bash
# Missing NFS config
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "my-vm"}'
# Error: "NFS server address is required"
```

## Files Modified

### Core Implementation
1. `pkg/server/server.go`
   - Modified `getKernelCmdLine()` - removed conditional logic
   - Modified `createVM()` - removed rootfs parameter and disk-based logic
   - Modified `StartVM()` - simplified NFS parameter handling
   - Modified `restoreVM()` - updated createVM call

2. `pkg/config/config.go`
   - Removed `RootfsPath` field
   - Removed `NFSEnabled` field
   - Updated `String()` method

3. `api/server-api.yaml`
   - Removed `rootfs` parameter
   - Removed `useNfsRoot` flag
   - Updated descriptions to reflect NFS-only mode

4. `cmd/client/main.go`
   - Removed `--rootfs` flag
   - Updated `startVM()` signature
   - Updated `restoreVM()` call

5. `config.yaml`
   - Removed `rootfs` configuration
   - Updated NFS comments to indicate required

### Generated Code
6. `out/gen/serverapi/*.go`
   - Regenerated from updated OpenAPI spec
   - Removed UseNfsRoot and Rootfs fields

### Documentation
7. `NFS-ROOT-QUICKSTART.md` - Quick start guide
8. `docs/NFS-ROOT-USAGE.md` - Comprehensive usage guide
9. `docs/NFS-IMPLEMENTATION-SUMMARY.md` - Technical details
10. `IMPLEMENTATION-SUMMARY.md` - This file

## Validation Rules

**Required Parameters:**
- `vmName` - always required
- `nfsServer` - must be set (config or request)
- `nfsPort` - must be set (config or request)

**Optional Parameters:**
- `kernel` - defaults to config value
- `initramfs` - defaults to config value
- `nfsPath` - defaults to `/`
- `entryPoint` - optional startup command
- `snapshotId` - for restore operations

**Priority Order:**
1. Request parameters (highest)
2. Config file defaults
3. Hardcoded defaults (lowest)

## Breaking Changes

**This is a breaking change for existing users:**

### What No Longer Works
❌ Disk-based root filesystems
❌ `rootfs` parameter in API requests
❌ `useNfsRoot` toggle flag
❌ Starting VMs without NFS configuration
❌ `--rootfs` flag in client CLI

### Migration Path
✅ Configure NFS server in `config.yaml`
✅ Start AgentFS or standard NFS server
✅ Update API calls to remove `rootfs` parameter
✅ Update client commands to remove `--rootfs` flag

### Example Migration

**Before:**
```bash
./arrakis-client start --name my-vm --rootfs ./rootfs.img
```

**After:**
```bash
# Configure NFS in config.yaml first
./arrakis-client start --name my-vm
```

## Benefits of NFS-Only Design

1. **Simplicity**: One code path, easier to maintain
2. **Clarity**: No confusion about boot modes
3. **Performance**: Optimized for the single use case
4. **Reliability**: Less conditional logic = fewer bugs
5. **Purpose**: Designed specifically for AgentFS integration

## Requirements

### Kernel Requirements
Kernel must be compiled with:
```
CONFIG_NFS_FS=y
CONFIG_NFS_V3=y
CONFIG_ROOT_NFS=y
CONFIG_IP_PNP=y
CONFIG_IP_PNP_DHCP=y
```

### Network Requirements
- NFS server must be accessible from VM network
- Port must be open on firewall
- NFSv3 protocol support

### Server Requirements
- NFS server running (AgentFS or standard)
- Server must export root filesystem
- Correct permissions for VM access

## Testing

All tests pass:
```bash
# Build verification
cd arrakis
go build -o out/arrakis-restserver ./cmd/restserver
go build -o out/arrakis-client ./cmd/client

# Integration tests
./test_nfs_integration.sh
```

## Future Enhancements

Potential improvements (all NFS-focused):
- NFSv4 support
- Custom NFS mount options
- NFS authentication mechanisms
- Health checks for NFS server availability
- Metrics for NFS performance
- Multi-path NFS for redundancy

## Summary

**What Changed:**
- Removed all disk-based root filesystem support
- Removed conditional NFS logic
- Simplified API to NFS-only mode
- Updated all documentation to reflect NFS-only design

**Result:**
- Simpler, more maintainable codebase
- Clear purpose: filesystem tracking with AgentFS
- No ambiguity in boot process
- Optimized for the tracking use case

**Status:** ✅ Complete, tested, and ready for use

---

**Arrakis is now NFS-only. Every VM boots with NFS root. Simple. Trackable. Powerful.**