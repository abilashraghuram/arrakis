# NFS Root Quick Start Guide

## What is NFS Root?

Arrakis REST server boots **ALL VMs with NFS root filesystems**. There is no disk-based boot option - every VM mounts its root filesystem over NFS.

This design enables seamless integration with **AgentFS**, where every filesystem operation in your VM is automatically tracked, versioned, and auditable.

## Why NFS Root Only?

- 🔍 **Complete Transparency**: Every file operation is tracked in SQLite
- 📦 **Version Control**: Branch, merge, and diff VM filesystems like Git  
- 🔄 **Zero VM Modifications**: Standard NFS - no special drivers needed
- 🎯 **Built for AgentFS**: Designed specifically for filesystem tracking
- 🚀 **Simplified Architecture**: One boot path, no complexity

## Quick Setup (5 minutes)

### Prerequisites

- Arrakis built and ready: `make restserver`
- Kernel with NFS support (included in Arrakis prebuilt)
- NFS server running (AgentFS recommended)

### Step 1: Start Your NFS Server

**Option A: AgentFS (Recommended)**
```bash
cd /path/to/agentfs
agentfs nfs start --port 11111
```

**Option B: Any NFSv3 Server**
```bash
# Configure and start your NFSv3 server
# Ensure it exports on a known port
```

### Step 2: Configure Arrakis

Edit `config.yaml` with your NFS server details:

```yaml
hostservices:
  restserver:
    host: "0.0.0.0"
    port: "7000"
    # ... other settings ...
    
    # NFS root configuration (REQUIRED)
    nfs_server: "127.0.0.1"
    nfs_port: 11111
    nfs_path: "/"
```

**Configuration Fields:**
- `nfs_server`: NFS server IP address (REQUIRED)
- `nfs_port`: NFS server port (REQUIRED)  
- `nfs_path`: NFS export path (default: `/`)

### Step 3: Start Arrakis REST Server

```bash
./out/arrakis-restserver --config config.yaml
```

### Step 4: Create a VM

**Using config defaults:**
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "my-vm"}'
```

**Override NFS server per-VM:**
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-vm",
    "nfsServer": "10.0.0.5",
    "nfsPort": 2049
  }'
```

That's it! Your VM is running with NFS root. 🎉

## How It Works

### VM Configuration
```
VM Disks:
  - /dev/vda: stateful.img (local, for /var, /tmp, etc.)
  
Root Filesystem:
  - /: Mounted via NFS from configured server
  
Kernel Command Line:
  console=ttyS0 root=/dev/nfs 
  nfsroot=127.0.0.1:/,nfsvers=3,tcp,nolock,port=11111 
  ip=dhcp rw ...
```

### Architecture

```
┌─────────────────────────────────────┐
│   Cloud Hypervisor MicroVM          │
│                                     │
│   Root: /dev/nfs (always)           │
│   Stateful: /dev/vda (local)        │
└─────────────┬───────────────────────┘
              │ NFSv3 Protocol
              ▼
┌─────────────────────────────────────┐
│   NFS Server (AgentFS/Standard)     │
│                                     │
│   Exports root filesystem           │
│   Tracks all operations (AgentFS)   │
└─────────────────────────────────────┘
```

## Verification

Check if your VM is using NFS root:

```bash
# Get VM details
curl -s http://localhost:7000/v1/vms/my-vm | jq .

# Inside the VM (if accessible)
mount | grep nfs
# Output: 127.0.0.1:/ on / type nfs (rw,...)
```

## Common Use Cases

### 1. Development with AgentFS Tracking
```bash
# Start AgentFS NFS server
agentfs nfs start --port 11111

# Create VM - all filesystem ops tracked!
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "dev-vm"}'

# View filesystem changes in real-time
agentfs diff
agentfs log
```

### 2. Multiple VMs, Same NFS Server
```bash
# All VMs share the same tracked filesystem
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "vm1"}'

curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"vmName": "vm2"}'
```

### 3. Different NFS Servers Per VM
```bash
# VM 1: AgentFS
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "tracked-vm",
    "nfsServer": "127.0.0.1",
    "nfsPort": 11111
  }'

# VM 2: Production NFS
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "prod-vm",
    "nfsServer": "10.0.0.5",
    "nfsPort": 2049
  }'
```

## Configuration Options

### Server-Wide Defaults (config.yaml)
```yaml
nfs_server: "127.0.0.1"    # Default NFS server IP
nfs_port: 11111            # Default NFS server port
nfs_path: "/"              # Default NFS export path
```

### Per-VM Override (API Request)
```json
{
  "vmName": "my-vm",
  "nfsServer": "10.0.0.1",   // Override config server
  "nfsPort": 2049,           // Override config port
  "nfsPath": "/exports/vm"   // Override config path
}
```

**Priority**: Request parameters > Config defaults

**Validation**: `nfsServer` and `nfsPort` are REQUIRED (either from config or request)

## Troubleshooting

### VM Won't Boot

**Error: "VFS: Unable to mount root fs via NFS"**

1. **Check NFS server is running:**
   ```bash
   netstat -ln | grep 11111
   ```

2. **Verify NFS server is accessible:**
   ```bash
   telnet 127.0.0.1 11111
   ```

3. **Check kernel has NFS support:**
   ```bash
   # Arrakis prebuilt kernel includes:
   # CONFIG_NFS_FS=y
   # CONFIG_ROOT_NFS=y
   # CONFIG_IP_PNP=y
   ```

### Connection Refused

```bash
# Check firewall rules
sudo iptables -L | grep 11111

# Check REST server logs
tail -f vm-state/*.log

# Verify AgentFS NFS server
agentfs nfs status
```

### Permission Issues

```bash
# AgentFS NFS runs as current user
# Ensure UID/GID match between host and guest

# Check file ownership in VM
ls -la /
```

### Missing NFS Configuration

**Error: "NFS server address is required"**

Solution: Either set in `config.yaml` OR provide in API request:
```bash
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-vm",
    "nfsServer": "127.0.0.1",
    "nfsPort": 11111
  }'
```

## Testing

Run the included test suite:

```bash
./test_nfs_integration.sh
```

This will:
- ✓ Start REST server
- ✓ Test NFS root VM creation
- ✓ Test configuration validation
- ✓ Clean up

## Performance Notes

- **Latency**: NFS adds ~1-5ms per filesystem operation
- **Throughput**: Network-limited (typically 100-1000 MB/s)
- **Caching**: NFSv3 client caching reduces network overhead
- **Best For**: Development, testing, filesystem tracking
- **Optimization**: Use localhost NFS server for minimal latency

## Security Considerations

⚠️ **Important**:
- Only expose NFS server on trusted networks
- Use firewall rules to restrict NFS port access
- Consider VPN/encrypted tunnels for remote access
- AgentFS NFS runs with user permissions (not root)
- Limit NFS exports to specific IP ranges

## What Makes This Different?

**Traditional VM Boot:**
- Disk image contains entire root filesystem
- No visibility into filesystem operations
- Manual tracking required
- Snapshot-only versioning

**Arrakis NFS Root Boot:**
- Root filesystem served over NFS
- Every operation visible to NFS server
- AgentFS provides automatic tracking
- Git-like version control
- Complete audit trail

## Next Steps

- 📖 **Full Documentation**: [docs/NFS-ROOT-USAGE.md](docs/NFS-ROOT-USAGE.md)
- 🔧 **Implementation Details**: [docs/NFS-IMPLEMENTATION-SUMMARY.md](docs/NFS-IMPLEMENTATION-SUMMARY.md)
- 🏗️ **AgentFS Integration**: [setup/AGENTFS-INTEGRATION.md](setup/AGENTFS-INTEGRATION.md)

## API Reference

### StartVMRequest
```json
{
  "vmName": "string",              // Required
  "kernel": "string",              // Optional, uses config default
  "initramfs": "string",           // Optional, uses config default
  "entryPoint": "string",          // Optional
  "snapshotId": "string",          // Optional, for restore
  "nfsServer": "string",           // Required (config or request)
  "nfsPort": "integer",            // Required (config or request)
  "nfsPath": "string"              // Optional, default: "/"
}
```

### Example Response
```json
{
  "vmName": "my-vm",
  "status": "running",
  "ip": "10.20.1.2",
  "tapDeviceName": "tap0",
  "portForwards": [
    {
      "hostPort": "5901",
      "guestPort": "5901",
      "description": "gui"
    }
  ]
}
```

## Support

- 📝 File issues on GitHub
- 💬 Check documentation in `docs/`
- 🔍 Search setup scripts in `setup/`

---

**All VMs boot with NFS root. No exceptions. Simple. Trackable. Powerful. 🚀**