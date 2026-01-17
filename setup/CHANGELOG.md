# Setup Directory Changelog

## 2025-01-02 - NFS-Only Mode Migration

### Breaking Changes

**Arrakis now runs exclusively in NFS-only mode.** All VMs boot with their root filesystem mounted over NFS from AgentFS. Disk-based root filesystem support has been completely removed.

### Files Deleted

The following outdated documentation has been removed:

- `AGENTFS-INTEGRATION.md` - Replaced by NFS-ROOT-QUICKSTART.md and GCP-SETUP.md
- `CHANGES.md` - Outdated change log
- `NO-BACKWARD-COMPATIBILITY.md` - Redundant with new documentation
- `README.md` - Replaced with updated version
- `gcp-instructions.md` - Replaced by GCP-SETUP.md

### Files Updated

#### `arrakis-agentfs-launcher.sh`

**Before:** Complex script that required rootfs mounting, manual initialization, and provided instructions for manual VM configuration.

**After:** Simplified launcher that:
- Automatically starts AgentFS NFS server on port 11111
- Automatically starts Arrakis REST server on port 7000
- Monitors both services and restarts on failure
- Works with arrakis-prebuilt or arrakis-runtime directories
- No manual VM configuration needed (NFS is automatic)
- Shows helpful usage instructions and examples

**Key improvements:**
- Removed rootfs mounting complexity
- Removed manual configuration steps
- Added automatic service monitoring
- Added health checks
- Simplified user experience

### Files Created

#### `GCP-SETUP.md`

Comprehensive setup guide for deploying Arrakis in NFS-only mode on Google Cloud Platform.

**Contents:**
- GCP VM creation with nested virtualization
- System dependency installation
- Go, Node.js, Rust installation
- AgentFS compilation from source
- Arrakis building from repository
- Network bridge configuration
- NFS-only mode startup
- Testing procedures
- Troubleshooting guide
- Systemd service setup for persistence

**Target audience:** Users deploying from scratch on GCP

#### `README.md`

Directory overview and quick reference guide.

**Contents:**
- File descriptions
- NFS-only mode explanation
- Architecture diagram
- Quick setup steps
- Common troubleshooting
- Documentation links

### Scripts Retained

The following scripts remain unchanged and are still supported:

- `install-deps.sh` - Installs system dependencies and AgentFS
- `setup.sh` - Downloads Arrakis prebuilt components
- `build-nfs-kernel.sh` - Builds custom kernel (optional)
- `create-nfs-vm.sh` - Manual VM creation helper (legacy)
- `install-images.py` - Component download helper

### Migration Impact

#### For New Users

✅ **Easier setup** - Clear, step-by-step instructions in GCP-SETUP.md
✅ **Automated launcher** - Single command starts everything
✅ **Better documentation** - Comprehensive troubleshooting

#### For Existing Users

⚠️ **Breaking changes** - Old documentation references removed
⚠️ **Manual setup different** - Follow new GCP-SETUP.md guide
⚠️ **Launcher updated** - New simplified version

### Key Architectural Changes

#### NFS-Only Mode

**What changed:**
- All VMs now boot with NFS root (no disk-based option)
- AgentFS NFS server is required (port 11111)
- REST API simplified (no `rootfs` or `useNfsRoot` parameters)

**Benefits:**
- Automatic filesystem tracking
- Complete audit trail in SQLite
- Simpler VM creation
- No confusion about boot modes

#### Simplified Workflow

**Old workflow:**
1. Download rootfs image
2. Mount and extract rootfs
3. Initialize AgentFS with base
4. Start NFS server
5. Manually configure VMs with NFS root parameters
6. Start REST server

**New workflow:**
1. Build/copy Arrakis binaries
2. Run `bash arrakis-agentfs-launcher.sh my-agent-id`
3. Create VMs via REST API (NFS automatic)

### Documentation Structure

```
arrakis/
├── setup/
│   ├── CHANGELOG.md              # This file
│   ├── README.md                 # Directory overview
│   ├── GCP-SETUP.md             # Complete GCP setup guide
│   ├── arrakis-agentfs-launcher.sh  # All-in-one launcher
│   └── [other scripts]
├── NFS-ROOT-QUICKSTART.md       # Quick start guide
├── NFS-ONLY-MODE.md             # Breaking changes doc
├── IMPLEMENTATION-SUMMARY.md    # Technical details
└── docs/
    ├── NFS-ROOT-USAGE.md        # Comprehensive usage
    └── NFS-IMPLEMENTATION-SUMMARY.md  # Implementation details
```

### Testing

All changes have been tested with:
- Fresh GCP VM setup following GCP-SETUP.md
- Launcher script starting both services
- VM creation via REST API
- AgentFS filesystem tracking
- Service monitoring and restart

### Version Information

- **Arrakis Version:** NFS-Only Mode (2025-01-02)
- **AgentFS Requirement:** Latest from main branch
- **Go Version:** 1.21.6+
- **Node.js Version:** 18+
- **Java Version:** 17+ (for OpenAPI generator)

### Backward Compatibility

⚠️ **No backward compatibility** with disk-based root mode.

All existing VMs must be recreated using the new NFS-only mode. Snapshots from disk-based VMs are not compatible.

### Future Plans

- Add more cloud provider setup guides (AWS, Azure)
- Improve launcher script with more options
- Add health monitoring dashboard
- Create Docker/container deployment option
- Add VM templates for common use cases

### Support

For issues or questions:
- Review GCP-SETUP.md troubleshooting section
- Check ../NFS-ROOT-QUICKSTART.md for usage examples
- File issues on GitHub repository
- Review logs in `.agentfs-nfs.log` and `.arrakis-rest.log`

---

**All VMs boot with NFS root. No exceptions. Simple. Trackable. 🚀**