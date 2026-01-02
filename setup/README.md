# Arrakis + AgentFS Setup

Setup scripts for deploying Arrakis microVM sandboxes with AgentFS integration (REQUIRED) on Google Cloud Platform (GCP) or local Linux machines.

## What This Is

**Arrakis** provides lightweight, secure microVM sandboxes using cloud-hypervisor. Perfect for running untrusted code, AI agents, or isolated development environments.

**AgentFS Integration** (REQUIRED) provides persistent, auditable filesystem tracking. Every file operation is logged to SQLite, giving you complete visibility into what happens inside your VMs.

## Quick Start

### Option 1: Standard Setup (GCP)

Follow the [GCP Instructions](./gcp-instructions.md) for a complete cloud deployment.

### Option 2: Local Setup

```bash
# Install dependencies (includes AgentFS)
curl -sSL "https://raw.githubusercontent.com/abshkbh/arrakis/main/setup/install-deps.sh" | bash
source ~/.bashrc

# Install Arrakis
curl -sSL "https://raw.githubusercontent.com/abshkbh/arrakis/main/setup/setup.sh" | bash

# Verify
cd ~/arrakis-prebuilt
ls -la
agentfs --version
```

## Usage

### AgentFS-Enabled Arrakis (Required)

```bash
# Terminal 1: Start AgentFS NFS server
cd ~/arrakis-prebuilt
bash ../setup/arrakis-agentfs-launcher.sh my-agent-id

# Terminal 2: Create VM with NFS root
bash ../setup/create-nfs-vm.sh 127.0.0.1 11111 my-vm

# Terminal 3: View filesystem changes
agentfs diff my-agent-id
agentfs log my-agent-id
```

## Files in This Directory

- **`gcp-instructions.md`** - Complete GCP deployment guide
- **`install-deps.sh`** - Installs system dependencies and AgentFS CLI
- **`setup.sh`** - Downloads and sets up Arrakis binaries
- **`install-images.py`** - Downloads required kernel and hypervisor images
- **`arrakis-agentfs-launcher.sh`** - Starts AgentFS NFS server for VM integration
- **`create-nfs-vm.sh`** - Helper to manually create VMs with AgentFS NFS root
- **`AGENTFS-INTEGRATION.md`** - Detailed AgentFS integration documentation

## AgentFS Features

AgentFS is required for this setup and provides:
- ✅ **Complete audit trail** of all filesystem operations
- ✅ **Diff and rollback** capabilities
- ✅ **Persistent storage** in SQLite (not ephemeral disk images)
- ✅ **Zero VM modifications** (transparent via NFS)
- ✅ **Version control** for VM filesystems

Perfect for:
- AI agent sandboxing and monitoring
- Security research and malware analysis
- Debugging complex VM issues
- Development environment versioning
- Compliance and audit requirements

## Architecture

```
┌─────────────────────────┐
│  Cloud Hypervisor VM    │
│  (Arrakis Sandbox)      │
│                         │
│  Your code runs here    │
└───────────┬─────────────┘
            │
       NFSv3 (required)
            │
            ▼
┌─────────────────────────┐
│  AgentFS NFS Server     │
│  (Transparent Tracking) │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  SQLite Database        │
│  (Complete History)     │
└─────────────────────────┘
```

## Requirements

- **Linux host** with KVM support
- **GCP VM** with nested virtualization (for cloud deployments)
- **Rust toolchain** (installed automatically) - REQUIRED for AgentFS
- **Go 1.23+** (installed automatically)
- **Docker** (installed automatically)
- **AgentFS CLI** (installed automatically) - REQUIRED

## Getting Help

- **AgentFS Integration**: See [AGENTFS-INTEGRATION.md](./AGENTFS-INTEGRATION.md)
- **GCP Deployment**: See [gcp-instructions.md](./gcp-instructions.md)
- **Original Arrakis**: See [Arrakis README](https://github.com/abilashraghuram/arrakis)

## Examples

### View What an AI Agent Did

```bash
# Agent ran in VM
# ...

# On host, see exactly what files it touched
agentfs diff ai-agent-session
# Output:
# + /workspace/generated_code.py
# + /workspace/data.json
# M /etc/hostname
```

### Track Malware Behavior

```bash
# Run malware in isolated VM
# ...

# Examine filesystem changes
agentfs log malware-analysis | grep -E "CREATE|WRITE"
# Shows all files created/modified
```

### Clone Development Environment

```bash
# Export current state
agentfs export dev-env-1 /tmp/snapshot

# Create new environment from snapshot
agentfs init --base /tmp/snapshot dev-env-2

# Now have two identical environments
```

## License

- Arrakis: Apache 2.0
- AgentFS: Apache 2.0
- These setup scripts: Apache 2.0