# Arrakis REST Server - NFS-Only Mode

## ⚠️ Breaking Change: NFS Root Only

Arrakis REST server now **exclusively supports NFS root filesystems**. All VMs boot with their root filesystem mounted over NFS. Disk-based root filesystem support has been completely removed.

## What Changed

### Removed Features
- ❌ Disk-based root filesystem boot
- ❌ Local rootfs image support
- ❌ `rootfs` parameter in API
- ❌ `useNfsRoot` toggle flag
- ❌ `--rootfs` client flag
- ❌ Backward compatibility with disk boot

### What Remains
- ✅ NFS root boot (only option)
- ✅ Stateful disk support (for /var, /tmp, etc.)
- ✅ Snapshot/restore functionality
- ✅ All other VM management features

## Why NFS-Only?

1. **Purpose-Built for AgentFS**: Designed specifically for filesystem tracking
2. **Simplified Architecture**: One boot path, no conditional logic
3. **Complete Observability**: Every filesystem operation is visible
4. **Easier Maintenance**: Less code, fewer bugs
5. **Clear Intent**: No ambiguity about the system's purpose

## Quick Start

### 1. Prerequisites

```bash
# Build Arrakis
cd arrakis
make restserver

# Start NFS server (AgentFS recommended)
cd /path/to/agentfs
agentfs nfs start --port 11111
```

### 2. Configure NFS

Edit `config.yaml`:

```yaml
hostservices:
  restserver:
    # ... other settings ...
    nfs_server: "127.0.0.1"
    nfs_port: 11111
    nfs_path: "/"
```

### 3. Start Server

```bash
./out/arrakis-restserver --config config.yaml
```

### 4. Create VM

```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "my-vm"}'
```

That's it! Your VM is running with NFS root.

## API Changes

### Before (Old API - No Longer Works)
```json
{
  "vmName": "my-vm",
  "rootfs": "/path/to/rootfs.img",
  "useNfsRoot": false
}
```

### After (New API - Required)
```json
{
  "vmName": "my-vm",
  "nfsServer": "127.0.0.1",
  "nfsPort": 11111
}
```

### Request Parameters

**Required:**
- `vmName` - VM identifier
- `nfsServer` - NFS server address (from config or request)
- `nfsPort` - NFS server port (from config or request)

**Optional:**
- `kernel` - Kernel path (uses config default)
- `initramfs` - Initramfs path (uses config default)
- `nfsPath` - NFS export path (default: `/`)
- `entryPoint` - Startup command
- `snapshotId` - For restore operations

## How It Works

### VM Boot Process

```
1. API request received with vmName
2. NFS parameters validated (server + port required)
3. Kernel cmdline generated with NFS root
4. Only stateful disk attached (no rootfs disk)
5. VM boots with root=  /dev/nfs
6. Kernel mounts root over NFS
7. All filesystem ops go through NFS server
```

### Kernel Command Line

Every VM boots with:
```
console=ttyS0 
root=/dev/nfs 
nfsroot=127.0.0.1:/,nfsvers=3,tcp,nolock,port=11111 
ip=dhcp 
rw 
...
```

### Disk Configuration

```
VM Disks:
  - /dev/vda: stateful.img (local, for /var, /tmp)

Root Filesystem:
  - /: NFS mount from configured server
```

## Configuration

### config.yaml

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
    initramfs: "./out/initramfs.cpio.gz"
    port_forwards:
      - port: "5901"
        description: "gui"
    stateful_size_in_mb: "2048"
    guest_mem_percentage: "30"
    # NFS configuration - REQUIRED
    nfs_server: "127.0.0.1"
    nfs_port: 11111
    nfs_path: "/"
```

### Priority Order

When starting a VM, parameters are resolved in this order:
1. **API request** (highest priority)
2. **config.yaml defaults**
3. **Hardcoded defaults** (lowest priority)

## CLI Changes

### Before (Old CLI)
```bash
./arrakis-client start \
  --name my-vm \
  --rootfs ./rootfs.img
```

### After (New CLI)
```bash
./arrakis-client start --name my-vm
# NFS config comes from config.yaml
```

## Examples

### Basic VM with Config Defaults
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "dev-vm"}'
```

### Override NFS Server
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "prod-vm",
    "nfsServer": "10.0.0.5",
    "nfsPort": 2049,
    "nfsPath": "/exports/vm"
  }'
```

### With AgentFS Tracking
```bash
# Start AgentFS NFS server
agentfs nfs start --port 11111

# Create VM - all filesystem ops tracked!
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "tracked-vm"}'

# View changes in real-time
agentfs diff
agentfs log
```

## Migration Guide

### Step 1: Update Configuration

Remove `rootfs` from config.yaml, add NFS settings:

```diff
  hostservices:
    restserver:
      kernel: "./resources/bin/vmlinux.bin"
-     rootfs: "./out/arrakis-guestrootfs-ext4.img"
      initramfs: "./out/initramfs.cpio.gz"
+     nfs_server: "127.0.0.1"
+     nfs_port: 11111
+     nfs_path: "/"
```

### Step 2: Start NFS Server

```bash
# Option A: AgentFS (recommended)
agentfs nfs start --port 11111

# Option B: Standard NFS server
# Configure your NFSv3 server to export root filesystem
```

### Step 3: Update API Calls

Remove `rootfs` and `useNfsRoot` from requests:

```diff
  {
    "vmName": "my-vm",
-   "rootfs": "/path/to/rootfs.img",
-   "useNfsRoot": false
+   "nfsServer": "127.0.0.1",
+   "nfsPort": 11111
  }
```

### Step 4: Update Client Commands

Remove `--rootfs` flag:

```diff
- ./arrakis-client start --name my-vm --rootfs ./rootfs.img
+ ./arrakis-client start --name my-vm
```

## Requirements

### Kernel Requirements
The kernel must include:
```
CONFIG_NFS_FS=y
CONFIG_NFS_V3=y
CONFIG_ROOT_NFS=y
CONFIG_IP_PNP=y
CONFIG_IP_PNP_DHCP=y
```

Arrakis prebuilt kernels include these options.

### NFS Server Requirements
- NFSv3 support
- Accessible from VM network
- Firewall allows configured port
- Proper export permissions

## Troubleshooting

### Error: "NFS server address is required"

**Solution:** Set NFS server in config.yaml or API request:

```yaml
# config.yaml
nfs_server: "127.0.0.1"
nfs_port: 11111
```

### Error: "VFS: Unable to mount root fs via NFS"

**Causes:**
1. NFS server not running
2. Firewall blocking port
3. Network connectivity issues
4. Wrong server address/port

**Check:**
```bash
# Verify NFS server is running
netstat -ln | grep 11111

# Test connectivity
telnet 127.0.0.1 11111

# Check firewall
sudo iptables -L | grep 11111
```

### VM Boots But No Root Filesystem

**Cause:** Kernel missing NFS support

**Solution:** Use Arrakis prebuilt kernel or rebuild with NFS options

## Files Changed

### Core Implementation
- `pkg/server/server.go` - Removed disk boot logic
- `pkg/config/config.go` - Removed rootfs fields
- `api/server-api.yaml` - Removed rootfs/useNfsRoot
- `cmd/client/main.go` - Removed rootfs flag
- `config.yaml` - Updated for NFS-only

### Generated Code
- `out/gen/serverapi/*.go` - Regenerated from updated spec

### Documentation
- `NFS-ONLY-MODE.md` - This file
- `NFS-ROOT-QUICKSTART.md` - Quick start guide
- `IMPLEMENTATION-SUMMARY.md` - Technical details
- `docs/NFS-ROOT-USAGE.md` - Comprehensive guide

## Testing

```bash
# Build everything
cd arrakis
make restserver client

# Run integration tests
./test_nfs_integration.sh

# Manual testing
./out/arrakis-restserver --config config.yaml

# In another terminal
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "test-vm"}'
```

## Benefits

✅ **Simpler Code**: One boot path, less complexity
✅ **Clear Purpose**: Designed for filesystem tracking
✅ **Better Performance**: Optimized for single use case
✅ **Easier Debugging**: Fewer code paths to trace
✅ **AgentFS Integration**: Perfect for tracking

## Documentation

- 📖 **Quick Start**: [NFS-ROOT-QUICKSTART.md](NFS-ROOT-QUICKSTART.md)
- 🔧 **Implementation**: [IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md)
- 📚 **Full Guide**: [docs/NFS-ROOT-USAGE.md](docs/NFS-ROOT-USAGE.md)
- 🏗️ **AgentFS**: [setup/AGENTFS-INTEGRATION.md](setup/AGENTFS-INTEGRATION.md)

## Support

- File issues on GitHub
- Check documentation in `docs/`
- Review setup scripts in `setup/`

---

**Arrakis is now NFS-only. Every VM boots with NFS root. No exceptions.**

**Simple. Trackable. Purpose-built for AgentFS. 🚀**