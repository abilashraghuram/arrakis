# AgentFS Integration with Arrakis

## Overview

This integration combines **Arrakis** (microVM sandboxes via cloud-hypervisor) with **AgentFS** (persistent, auditable filesystem storage) to create a powerful platform for running AI agents and untrusted code with complete filesystem tracking.

### What You Get

- **Persistent Filesystem**: VM filesystem backed by SQLite, survives across sessions
- **Complete Audit Trail**: Every file operation (create, read, write, delete) is logged
- **Diff and Rollback**: See exactly what changed, when, and by whom
- **Zero VM Awareness**: VMs use standard NFS - no special drivers or modifications needed
- **Version Control for VMs**: Branch, merge, and manage VM filesystems like Git

### Architecture

```
┌─────────────────────────────────────────────┐
│   Cloud Hypervisor MicroVM (Arrakis)       │
│                                             │
│   Your Agent/Code runs here                 │
│   Thinks it has normal filesystem           │
│                                             │
│   All operations go through NFS             │
└──────────────┬──────────────────────────────┘
               │
        NFSv3 Protocol
               │
               ▼
┌──────────────────────────────────────────────┐
│        AgentFS NFS Server (Host)             │
│                                              │
│  Transparently converts NFS ops to SQLite    │
│  - CREATE → INSERT INTO files                │
│  - WRITE  → UPDATE blobs                     │
│  - READ   → SELECT FROM blobs                │
│  - DELETE → Mark as deleted                  │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│           SQLite Database                    │
│                                              │
│  Complete filesystem with history:           │
│  - File contents (deduplicated blobs)        │
│  - Metadata (permissions, timestamps)        │
│  - Operation logs (who, what, when)          │
│  - Change tracking (diffs from base)         │
└──────────────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites

- Linux host with KVM support (GCP VMs with nested virtualization enabled)
- Rust toolchain (installed by install-deps.sh)
- Go 1.23+ (installed by install-deps.sh)
- Docker (installed by install-deps.sh)

### Installation

1. **Install dependencies (includes AgentFS):**

   ```bash
   cd $HOME
   curl -sSL "https://raw.githubusercontent.com/abshkbh/arrakis/main/setup/install-deps.sh" | bash
   source ~/.bashrc
   ```

   This installs:
   - Rust toolchain
   - AgentFS CLI (built from source)
   - Arrakis dependencies (Go, Docker, etc.)

2. **Install Arrakis:**

   ```bash
   curl -sSL "https://raw.githubusercontent.com/abshkbh/arrakis/main/setup/setup.sh" | bash
   ```

   This downloads:
   - Arrakis binaries (restserver, client)
   - Cloud-hypervisor VMM
   - Linux kernel and rootfs images

3. **Verify installation:**

   ```bash
   cd $HOME/arrakis-prebuilt
   ls -la
   
   # Check AgentFS
   agentfs --version
   ```

## Usage

### Method 1: AgentFS NFS Server (Recommended)

This method starts AgentFS NFS server and keeps it running for VM integration.

```bash
cd $HOME/arrakis-prebuilt
bash ../setup/arrakis-agentfs-launcher.sh my-agent-id
```

What this does:
1. Extracts Arrakis rootfs from ext4 image
2. Initializes AgentFS database with rootfs as base
3. Starts NFS server on localhost:11111
4. Creates configuration for NFS root boot

The NFS server will keep running. Leave this terminal open.

### Method 2: Manual VM with NFS Root

In another terminal, start a VM with NFS root:

```bash
cd $HOME/arrakis-prebuilt
bash ../setup/create-nfs-vm.sh 127.0.0.1 11111 my-test-vm
```

This creates a cloud-hypervisor VM that:
- Boots from AgentFS NFS root
- All filesystem operations tracked in SQLite
- Console access via serial (ttyS0)



## AgentFS Commands

Once your VMs are running with AgentFS, use these commands:

### View Filesystem Changes

```bash
agentfs diff my-agent-id
```

Example output:
```
+ /tmp/agent_output.json
M /etc/hostname
- /var/log/old.log
M /home/elara/script.py
```

### View Operation Logs

```bash
agentfs log my-agent-id
```

Shows chronological list of all filesystem operations.

### List Files

```bash
# List root directory
agentfs ls my-agent-id /

# List specific directory
agentfs ls my-agent-id /home/elara
```

### Read File Contents

```bash
agentfs cat my-agent-id /etc/hostname
agentfs cat my-agent-id /home/elara/script.py
```

### Export Filesystem

```bash
# Export entire filesystem to directory
agentfs export my-agent-id /path/to/output
```

### Initialize New Agent

```bash
# Create new agent from base directory
agentfs init --base /path/to/rootfs new-agent-id
```

## Use Cases

### 1. AI Agent Sandboxing

Run AI agents in isolated VMs with complete audit trails:

```python
# In VM: AI agent writes code
with open('/workspace/generated_code.py', 'w') as f:
    f.write(ai_generated_code)

# On host: Audit what was created
$ agentfs diff ai-agent-session-123
+ /workspace/generated_code.py
+ /workspace/data.json
```

### 2. Code Execution Auditing

Track exactly what code does:

```bash
# Run untrusted script in VM
# ...script creates files, modifies system...

# On host: See everything it touched
$ agentfs log execution-session-456
2024-01-15 10:23:45 CREATE /tmp/download.sh
2024-01-15 10:23:46 WRITE /tmp/download.sh
2024-01-15 10:23:47 CREATE /root/.ssh/authorized_keys
2024-01-15 10:23:48 WRITE /root/.ssh/authorized_keys
```

### 3. Development Environments

Create reproducible dev environments:

```bash
# Start from base
agentfs init --base ./clean-rootfs dev-env-1

# Work in VM, make changes
# ...

# Clone environment
agentfs export dev-env-1 /tmp/snapshot
agentfs init --base /tmp/snapshot dev-env-2

# Now have two identical environments
```

### 4. Security Research

Analyze malware safely:

```bash
# Run malware in isolated VM
# ...

# Examine what it did
agentfs diff malware-analysis-789
+ /etc/cron.d/backdoor
M /etc/passwd
+ /tmp/.hidden/payload
M /root/.bashrc
```

### 5. Debugging VM Issues

Trace filesystem operations leading to errors:

```bash
# Application crashes in VM
# ...

# Review filesystem timeline
agentfs log debug-session | tail -100
```

## Advanced Features

### Multiple Agents

Run multiple isolated sessions:

```bash
# Terminal 1
bash arrakis-agentfs-launcher.sh agent-1

# Terminal 2  
bash arrakis-agentfs-launcher.sh agent-2

# Terminal 3
bash arrakis-agentfs-launcher.sh agent-3
```

Each has separate:
- SQLite database
- NFS server (different ports)
- Filesystem state

### Persistent Sessions

Agent filesystems persist across:
- VM reboots
- Host reboots
- Network interruptions

Just restart the NFS server and remount.

### Branching Environments

```bash
# Export agent state
agentfs export agent-1 /tmp/agent-1-snapshot

# Create new agent from snapshot
agentfs init --base /tmp/agent-1-snapshot agent-1-branch

# Now have two independent branches
```

### Diff Between Agents

```bash
# Export both
agentfs export agent-1 /tmp/agent-1
agentfs export agent-2 /tmp/agent-2

# Use standard diff tools
diff -r /tmp/agent-1 /tmp/agent-2
```

## Integration with Arrakis REST API (Required)

AgentFS is the default and only supported filesystem backend. To use Arrakis REST API with AgentFS, VMs must be configured to use NFS root:

### Option 1: Modify Arrakis Source

Edit `pkg/restserver/restserver.go` to add NFS root support:

```go
// Add NFS configuration
type NFSConfig struct {
    Enabled bool
    Server  string
    Port    int
}

// Modify kernel cmdline
cmdline := fmt.Sprintf("root=/dev/nfs nfsroot=%s:/,nfsvers=3,tcp,nolock,port=%d", 
    nfsConfig.Server, nfsConfig.Port)
```

### Option 2: Wrapper Script

Create a wrapper that intercepts VM creation:

```bash
#!/bin/bash
# Modify VM config JSON before passing to cloud-hypervisor
jq '.cmdline = "root=/dev/nfs nfsroot=127.0.0.1:/,nfsvers=3,tcp,nolock,port=11111"' \
   vm-config.json > vm-config-nfs.json
```

### Option 3: Direct cloud-hypervisor API

Use cloud-hypervisor HTTP API directly:

```bash
curl -X PUT http://localhost:8080/api/v1/vm.create -d '{
  "payload": {
    "kernel": "/path/to/vmlinux.bin",
    "cmdline": "root=/dev/nfs nfsroot=127.0.0.1:/,nfsvers=3,tcp,nolock,port=11111 rw"
  },
  "cpus": {"boot_vcpus": 2},
  "memory": {"size": 536870912},
  "net": [{"tap": "tap0"}]
}'
```

## Troubleshooting

### AgentFS NFS Server Won't Start

```bash
# Check if port is in use
netstat -ln | grep 11111

# Kill existing server
pkill -f "agentfs nfs"

# Check logs
cat arrakis-prebuilt/.agentfs/nfs.log
```

### VM Can't Mount NFS Root

Check kernel has NFS support:
```bash
# In kernel config, ensure these are set:
CONFIG_NFS_FS=y
CONFIG_NFS_V3=y
CONFIG_ROOT_NFS=y
CONFIG_IP_PNP=y
CONFIG_IP_PNP_DHCP=y
```

### Permission Errors in VM

AgentFS NFS server runs as current user. Ensure UID/GID match:
```bash
# Check in VM
id

# On host, AgentFS uses same UID/GID
```

### Slow Filesystem Performance

NFS over localhost is fast, but for very I/O intensive workloads:
- Consider using the standard disk image method
- Or use AgentFS for specific directories only

### Database Corruption

AgentFS uses SQLite with WAL mode. If corrupted:
```bash
# Backup database
cp .agentfs/agent-id.db .agentfs/agent-id.db.backup

# Try to recover
sqlite3 .agentfs/agent-id.db "PRAGMA integrity_check;"

# If unrecoverable, start fresh
rm .agentfs/agent-id.db
agentfs init --base ./rootfs-base agent-id
```

## Performance Considerations

- **NFS Overhead**: ~5-10% compared to direct disk access
- **SQLite Write**: Optimized with WAL mode, batched writes
- **Network**: Localhost NFS is fast (no actual network involved)
- **Memory**: AgentFS server uses ~50MB + database size

For production workloads, this overhead is negligible compared to the value of complete auditability.

## Security Notes

- **Isolation**: VMs are fully isolated by cloud-hypervisor/KVM
- **NFS Access**: Only localhost by default (configure bind address carefully)
- **SQLite**: Database is as secure as filesystem permissions
- **Audit Trail**: Immutable logs (appends only, no deletes)

## AgentFS Features

AgentFS is the required filesystem backend for this setup, providing:

| Feature | Details |
|---------|---------|
| Filesystem Storage | SQLite database |
| Persistence | Yes, across all sessions |
| Change Tracking | Yes, full history |
| Audit Trail | Yes, all operations logged |
| Diffs | Yes, complete diff support |
| Version Control | Yes, Git-like branching |
| Rollback | Built-in rollback capability |
| Overhead | ~5-10% (minimal) |
| VM Awareness | None (transparent via NFS) |

## FAQ

**Q: Does the VM know it's using AgentFS?**  
A: No. VMs just see a normal NFS mount. AgentFS is completely transparent.

**Q: Can I use this in production?**  
A: Yes, but test thoroughly. AgentFS is alpha software. The overhead is minimal and the audit value is high.

**Q: Is AgentFS required or optional?**  
A: Required. This setup is designed specifically for AgentFS integration. There is no fallback to standard disk images.

**Q: Does this work with Firecracker?**  
A: Yes! See the firecracker example in the AgentFS repo. Same NFS approach works with any VMM.

**Q: Can I access files from multiple VMs?**  
A: Each AgentFS instance serves one filesystem. For multiple VMs, start multiple AgentFS NFS servers with different agent IDs and ports.

**Q: What happens if NFS server crashes?**  
A: VM loses filesystem access. Restart NFS server and VM will reconnect. SQLite ensures data consistency.

**Q: Can I use this with Docker/Kubernetes?**  
A: Not directly. This is designed for VMs with NFS root. For containers, run them inside AgentFS-backed VMs.

**Q: Why not use standard Arrakis with disk images?**  
A: This setup prioritizes auditability and version control over simplicity. AgentFS provides complete filesystem history that disk images cannot.

## Contributing

This integration is experimental. Contributions welcome:

- Improve Arrakis integration (automatic NFS root configuration)
- Performance optimizations
- Better error handling
- Documentation improvements

## Resources

- [AgentFS Documentation](https://docs.turso.tech/agentfs)
- [Arrakis Repository](https://github.com/abilashraghuram/arrakis)
- [Cloud Hypervisor](https://github.com/cloud-hypervisor/cloud-hypervisor)
- [NFSv3 Protocol](https://datatracker.ietf.org/doc/html/rfc1813)

## License

- AgentFS: Apache 2.0
- Arrakis: Apache 2.0
- This integration: Apache 2.0