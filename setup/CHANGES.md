# Changes for AgentFS Integration with Arrakis

This document describes all changes made to integrate AgentFS with Arrakis setup scripts.

## Date
January 2024

## Summary
Added AgentFS integration to Arrakis setup, enabling persistent, auditable filesystem tracking for microVM sandboxes. AgentFS is now REQUIRED - all VMs must use AgentFS NFS root for filesystem operations.

## Modified Files

### 1. `install-deps.sh`
**Changes:**
- Added Rust toolchain installation (required for AgentFS CLI)
- Added AgentFS repository cloning and CLI build process
- Created symlink to `/usr/local/bin/agentfs` for global access

**Impact:**
- AgentFS CLI now automatically installed during dependency setup
- Users can immediately use `agentfs` commands after installation

### 2. `setup.sh`
**Changes:**
- Added AgentFS binary path and directory variables
- Added AgentFS CLI detection with helpful warning if not found
- Created `.agentfs` directory for database storage
- Updated completion messages to mention AgentFS integration option

**Impact:**
- Setup now enforces AgentFS requirement
- Exits with error if AgentFS not installed
- No fallback to standard Arrakis - AgentFS is mandatory

### 3. `gcp-instructions.md`
**Changes:**
- Added separate step to run `install-deps.sh` before `setup.sh`
- Removed all standard Arrakis usage instructions
- Documented all AgentFS commands (diff, log, export, ls, cat)
- Added usage examples for AgentFS features
- Included notes on manual integration requirements
- Made clear that AgentFS is REQUIRED, not optional

**Impact:**
- Users have complete documentation for AgentFS-only deployments
- Clear instructions for AgentFS workflow only
- Examples demonstrate real-world AgentFS usage
- No confusion about optional vs required features

## New Files Created

### 4. `arrakis-agentfs-launcher.sh` (NEW)
**Purpose:** Main launcher script for AgentFS-enabled Arrakis

**Features:**
- Extracts Arrakis rootfs from ext4 image
- Initializes AgentFS database with rootfs as base
- Starts AgentFS NFS server on localhost:11111
- Maintains NFS server running for VM connections
- Provides cleanup on exit with helpful diff/log commands
- Creates NFS configuration file

**Usage:**
```bash
bash arrakis-agentfs-launcher.sh [agent-id]
```

### 5. `create-nfs-vm.sh` (NEW)
**Purpose:** Helper script to manually create cloud-hypervisor VMs with AgentFS NFS root

**Features:**
- Validates AgentFS NFS server is running
- Sets up TAP networking device
- Configures kernel command line for NFS root boot
- Launches cloud-hypervisor with proper NFS parameters
- Provides console access via serial port
- Clean cleanup on exit

**Usage:**
```bash
bash create-nfs-vm.sh [nfs-server] [nfs-port] [vm-name]
```

**Example:**
```bash
bash create-nfs-vm.sh 127.0.0.1 11111 my-test-vm
```

### 6. `AGENTFS-INTEGRATION.md` (NEW)
**Purpose:** Comprehensive documentation for AgentFS integration

**Contents:**
- Architecture diagram and overview
- Detailed setup instructions
- Usage methods (3 different approaches)
- Complete AgentFS command reference
- Real-world use cases with examples
- Advanced features (multiple agents, branching, diffing)
- Integration guide for Arrakis REST API
- Troubleshooting section
- Performance and security considerations
- FAQ section

**Size:** 512 lines of detailed documentation

### 7. `README.md` (NEW)
**Purpose:** Main README for the setup directory

**Contents:**
- Quick start guide
- Usage options for both standard and AgentFS-enabled workflows
- File directory reference
- Architecture diagram
- Requirements list
- Practical examples
- Links to detailed documentation

**Size:** 171 lines

## Technical Details

### AgentFS Integration Approach

The integration uses **NFS (Network File System) as the transparent layer** between VMs and AgentFS:

1. **VM Side:** Standard Linux NFS client (built into kernel)
   - No modifications needed
   - VM thinks it's using normal filesystem
   - All operations go through NFS protocol

2. **Host Side:** AgentFS NFS server
   - Implements NFSv3 protocol
   - Translates NFS operations to SQLite operations
   - Provides complete audit trail

3. **Storage:** SQLite database
   - Stores file contents (deduplicated blobs)
   - Tracks metadata (permissions, timestamps)
   - Logs all operations (CREATE, READ, WRITE, DELETE)
   - Enables diffs, rollback, and version control

### Key Design Decisions

1. **AgentFS Required:**
   - AgentFS is mandatory for all VM operations
   - No fallback to disk images
   - Setup fails if AgentFS not installed

2. **Transparency:**
   - VMs have zero awareness of AgentFS
   - No guest modifications required
   - Works with any Linux VM

3. **Manual Integration:**
   - Currently requires manual VM configuration for NFS root
   - Future: Full integration into Arrakis REST API
   - Trade-off: Complete auditability vs. setup complexity

4. **Localhost by Default:**
   - NFS server binds to 127.0.0.1
   - Security: No external network exposure
   - Performance: Fast local communication

## Benefits

### For Users

1. **Complete Auditability:**
   - Track every filesystem operation
   - See exactly what code/agents did
   - Compliance and debugging

2. **Version Control:**
   - Diff filesystem changes
   - Rollback to previous states
   - Branch and merge VM filesystems

3. **Persistence:**
   - State survives VM restarts
   - SQLite-backed storage
   - Easy backup and transfer

### For Developers

1. **Purpose-Built Integration:**
   - Focused on AgentFS-only architecture
   - Standard protocols (NFS, SQLite)
   - Well-documented approach
   - No legacy code paths to maintain

2. **Extensibility:**
   - Easy to add more AgentFS features
   - Can integrate with Arrakis REST API
   - Foundation for advanced workflows

## Testing

All scripts have been:
- ✅ Syntax validated with `bash -n`
- ✅ Made executable with proper permissions
- ✅ Documented with usage examples
- ✅ Designed with error handling and cleanup

## Setup Path

### All Users

AgentFS is required. Single workflow:

```bash
# Step 1: Install with dependencies (includes AgentFS)
curl -sSL "https://raw.githubusercontent.com/.../install-deps.sh" | bash
source ~/.bashrc

# Step 2: Install Arrakis with AgentFS
curl -sSL "https://raw.githubusercontent.com/.../setup.sh" | bash

# Step 3: Use AgentFS-enabled workflow
cd ~/arrakis-prebuilt
bash ../setup/arrakis-agentfs-launcher.sh my-agent

# Step 4: Create VMs with NFS root
bash ../setup/create-nfs-vm.sh 127.0.0.1 11111 my-vm
```

## Future Enhancements

### Potential Improvements

1. **Automatic NFS Root Configuration:**
   - Patch Arrakis to support NFS root option
   - Add `--use-agentfs` flag to client
   - Simplify user experience

2. **REST API Integration:**
   - Extend Arrakis REST API with AgentFS endpoints
   - `/api/v1/agentfs/diff/:id`
   - `/api/v1/agentfs/log/:id`

3. **Dashboard/UI:**
   - Web interface for viewing diffs
   - Timeline visualization of operations
   - Real-time filesystem monitoring

4. **Performance Optimization:**
   - Implement caching layer
   - Batch SQLite writes
   - Optimize NFS operations

5. **Multi-VM Shared Filesystem:**
   - Multiple VMs accessing same AgentFS instance
   - Coordination and locking
   - Use cases: Distributed testing, collaboration

## Related Projects

- **Firecracker Example:** Similar NFS integration in `/examples/firecracker`
- **Just-Bash Example:** Filesystem integration in `/examples/ai-sdk-just-bash`
- **AgentFS CLI:** Main CLI tool in `/cli`
- **AgentFS SDK:** TypeScript/Python SDKs in `/sdk`

## Documentation Links

- [GCP Instructions](./gcp-instructions.md) - Cloud deployment
- [AgentFS Integration](./AGENTFS-INTEGRATION.md) - Detailed integration guide
- [Setup README](./README.md) - Quick start guide
- [AgentFS Docs](https://docs.turso.tech/agentfs) - Official documentation
- [Arrakis Repo](https://github.com/abilashraghuram/arrakis) - Arrakis project

## Conclusion

This integration brings powerful filesystem auditing and version control to Arrakis microVM sandboxes. The approach is:

- ✅ **Non-invasive** - No changes to VMs themselves
- ✅ **Required for all** - AgentFS mandatory, no optional modes
- ✅ **Well-documented** - Complete guides and examples
- ✅ **Practical** - Real-world use cases demonstrated
- ✅ **Extensible** - Foundation for future enhancements

This setup prioritizes complete auditability and version control, making AgentFS the required filesystem backend for all Arrakis VMs.