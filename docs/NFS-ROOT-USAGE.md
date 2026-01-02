# NFS Root Filesystem Support

## Overview

Arrakis REST server now supports booting VMs with NFS root filesystems instead of local disk images. This enables seamless integration with AgentFS, providing transparent filesystem tracking and version control capabilities for VM filesystems.

## How It Works

When NFS root is enabled, the VM boots with its root filesystem mounted over NFS from a remote server (typically AgentFS). The kernel command line is automatically configured with the necessary NFS root parameters, and the local rootfs disk is excluded from the VM configuration.

### Architecture

```
┌─────────────────────────────────────┐
│   Cloud Hypervisor MicroVM          │
│                                     │
│   Root: /dev/nfs (mounted via NFS)  │
│   Stateful disk: /dev/vdb (local)   │
└─────────────┬───────────────────────┘
              │ NFSv3 over network
              ▼
┌─────────────────────────────────────┐
│   AgentFS NFS Server (Host)         │
│                                     │
│   Port: 11111 (configurable)        │
│   Tracks all filesystem operations  │
└─────────────────────────────────────┘
```

## Configuration

### Option 1: Server-Wide Default (config.yaml)

Configure all VMs to use NFS root by default:

```yaml
hostservices:
  restserver:
    host: "0.0.0.0"
    port: "7000"
    # ... other settings ...
    
    # NFS root configuration
    nfs_enabled: true
    nfs_server: "127.0.0.1"
    nfs_port: 11111
    nfs_path: "/"
```

**Configuration Fields:**

- `nfs_enabled`: Enable NFS root for all VMs (default: `false`)
- `nfs_server`: NFS server IP address (e.g., `127.0.0.1`)
- `nfs_port`: NFS server port (e.g., `11111`)
- `nfs_path`: NFS export path (default: `/`)

### Option 2: Per-Request Override

Override NFS settings for individual VM requests via the REST API:

```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-nfs-vm",
    "kernel": "/path/to/vmlinux.bin",
    "initramfs": "/path/to/initramfs.cpio.gz",
    "useNfsRoot": true,
    "nfsServer": "127.0.0.1",
    "nfsPort": 11111,
    "nfsPath": "/"
  }'
```

**Request Parameters:**

- `useNfsRoot`: Enable NFS root for this VM (overrides config default)
- `nfsServer`: NFS server address (overrides config)
- `nfsPort`: NFS server port (overrides config)
- `nfsPath`: NFS export path (optional, defaults to `/`)

**Note:** When `useNfsRoot` is true:
- The `rootfs` parameter is ignored
- Only the stateful disk is attached to the VM
- The `nfsServer` and `nfsPort` parameters are **required**

## Usage Examples

### Example 1: Start VM with Config Defaults

If NFS is enabled in `config.yaml`, simply start a VM:

```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "test-vm"
  }'
```

### Example 2: Explicit NFS Configuration

Start a VM with explicit NFS settings, overriding config:

```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "agentfs-vm",
    "useNfsRoot": true,
    "nfsServer": "10.0.0.1",
    "nfsPort": 2049,
    "nfsPath": "/exports/vm-root"
  }'
```

### Example 3: Disable NFS for Specific VM

If NFS is enabled globally but you want to use local disk for one VM:

```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "local-disk-vm",
    "useNfsRoot": false,
    "rootfs": "/path/to/rootfs.img"
  }'
```

### Example 4: Python Client

Using the generated Python API client:

```python
import serverapi
from serverapi.rest import ApiException

# Configure API client
configuration = serverapi.Configuration()
configuration.host = "http://localhost:7000"

# Create API instance
api_client = serverapi.ApiClient(configuration)
api_instance = serverapi.DefaultApi(api_client)

# Start VM with NFS root
request = serverapi.StartVMRequest(
    vm_name="python-vm",
    use_nfs_root=True,
    nfs_server="127.0.0.1",
    nfs_port=11111,
    nfs_path="/"
)

try:
    response = api_instance.v1_vms_post(request)
    print(f"VM started: {response.vm_name}")
    print(f"VM IP: {response.ip}")
except ApiException as e:
    print(f"Exception: {e}")
```

## Kernel Configuration Requirements

For NFS root to work, the kernel must be compiled with:

```
CONFIG_NFS_FS=y
CONFIG_NFS_V3=y
CONFIG_ROOT_NFS=y
CONFIG_IP_PNP=y
CONFIG_IP_PNP_DHCP=y
```

The Arrakis prebuilt kernel includes these options. If building a custom kernel, use the script:

```bash
bash setup/build-nfs-kernel.sh
```

## Generated Kernel Command Line

### Standard (Disk-Based) Boot

```
console=ttyS0 gateway_ip="10.20.1.1" guest_ip="10.20.1.2" vm_name="my-vm"
```

### NFS Root Boot

```
console=ttyS0 root=/dev/nfs nfsroot=127.0.0.1:/,nfsvers=3,tcp,nolock,port=11111 ip=dhcp rw gateway_ip="10.20.1.1" guest_ip="10.20.1.2" vm_name="my-vm"
```

**Key differences:**
- `root=/dev/nfs`: Instructs kernel to use NFS as root
- `nfsroot=<server>:<path>,nfsvers=3,tcp,nolock,port=<port>`: NFS mount options
- `ip=dhcp`: Network configuration for NFS access
- `rw`: Mount root as read-write

## Disk Configuration

### With NFS Root

Only the stateful disk is attached:

```json
{
  "disks": [
    {"path": "/path/to/stateful.img", "numQueues": 4}
  ]
}
```

### Without NFS Root (Standard)

Both rootfs and stateful disks are attached:

```json
{
  "disks": [
    {"path": "/path/to/rootfs.img", "readonly": true, "numQueues": 4},
    {"path": "/path/to/stateful.img", "numQueues": 4}
  ]
}
```

## Integration with AgentFS

To use Arrakis with AgentFS NFS server:

1. **Start AgentFS NFS Server:**
   ```bash
   cd /path/to/agentfs
   agentfs nfs start --port 11111
   ```

2. **Configure Arrakis:**
   ```yaml
   # config.yaml
   nfs_enabled: true
   nfs_server: "127.0.0.1"
   nfs_port: 11111
   nfs_path: "/"
   ```

3. **Start REST Server:**
   ```bash
   ./out/arrakis-restserver --config config.yaml
   ```

4. **Create VM:**
   ```bash
   curl -X POST http://localhost:7000/v1/vms \
     -H "Content-Type: application/json" \
     -d '{"vmName": "tracked-vm"}'
   ```

All filesystem operations in the VM will now be tracked by AgentFS!

## Troubleshooting

### VM Fails to Boot with NFS Root

**Check kernel support:**
```bash
# In VM, check dmesg
dmesg | grep -i nfs
```

**Common errors:**
- "VFS: Unable to mount root fs via NFS" → Check NFS server is running
- "RPC: Remote system error - Connection refused" → Check port and firewall
- "mount.nfs: Connection timed out" → Check network connectivity

### NFS Server Connection Refused

```bash
# Verify NFS server is running
netstat -ln | grep 11111

# Check server logs
tail -f /path/to/agentfs/.agentfs/nfs.log

# Test NFS mount manually
mount -t nfs -o nfsvers=3,tcp,nolock,port=11111 127.0.0.1:/ /mnt
```

### Permission Errors

Ensure the NFS server runs with appropriate UID/GID. AgentFS NFS server runs as the current user.

## API Reference

### StartVMRequest Schema

```json
{
  "vmName": "string",
  "kernel": "string (optional)",
  "initramfs": "string (optional)",
  "rootfs": "string (optional, ignored if useNfsRoot=true)",
  "entryPoint": "string (optional)",
  "snapshotId": "string (optional)",
  "useNfsRoot": "boolean (optional, default: false)",
  "nfsServer": "string (required if useNfsRoot=true)",
  "nfsPort": "integer (required if useNfsRoot=true)",
  "nfsPath": "string (optional, default: /)"
}
```

### Validation Rules

- If `useNfsRoot` is `true`:
  - `nfsServer` must be provided (non-empty string)
  - `nfsPort` must be provided (non-zero integer)
  - `rootfs` is ignored
- If `useNfsRoot` is `false` or not provided:
  - Standard disk-based boot is used
  - `rootfs` parameter is used (or config default)

## Migration Guide

### From Disk-Based to NFS Root

**Before (disk-based):**
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-vm",
    "rootfs": "/path/to/rootfs.img"
  }'
```

**After (NFS root):**
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-vm",
    "useNfsRoot": true,
    "nfsServer": "127.0.0.1",
    "nfsPort": 11111
  }'
```

## Performance Considerations

- **Network Overhead:** NFS adds network latency to filesystem operations
- **Use Cases:** Best for development, debugging, and filesystem tracking
- **Production:** For production workloads, consider local disk with periodic snapshots
- **Caching:** NFSv3 client caching helps reduce network round trips

## Security Notes

- NFS server should only be accessible from trusted networks
- Use firewall rules to restrict NFS port access
- Consider VPN or encrypted tunnels for remote NFS access
- AgentFS NFS server runs with user permissions (not root)

## See Also

- [AgentFS Integration Guide](../setup/AGENTFS-INTEGRATION.md)
- [Building NFS-Enabled Kernel](../setup/build-nfs-kernel.sh)
- [REST API Specification](../api/server-api.yaml)
- [Configuration Reference](../config.yaml)