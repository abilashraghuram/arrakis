# Backward Compatibility Removed

## Date
January 2024

## Summary

**All backward compatibility with standard Arrakis has been removed.** AgentFS is now REQUIRED for all VM operations. There is no fallback to standard disk-based Arrakis.

## What Was Removed

### 1. Optional AgentFS Checks

**Before:**
```bash
if [ ! -f "$AGENTFS_BIN" ]; then
  print_warning "AgentFS CLI not found..."
  print_warning "Continuing without AgentFS integration..."
else
  print_message "AgentFS found"
fi
```

**After:**
```bash
if [ ! -f "$AGENTFS_BIN" ]; then
  print_error "AgentFS CLI not found..."
  print_error "AgentFS is REQUIRED for this setup."
  exit 1
fi

print_message "AgentFS found"
```

### 2. Standard Arrakis Usage Instructions

**Removed from all documentation:**
- Instructions for running `arrakis-restserver` without AgentFS
- Instructions for using `arrakis-client` with disk images
- References to "standard" vs "AgentFS-enabled" modes
- Optional language like "AgentFS Integration (Optional)"

### 3. Dual Workflow Documentation

**Before:** Documentation showed two paths:
- Option A: Standard Arrakis (no AgentFS)
- Option B: AgentFS-enabled Arrakis

**After:** Documentation shows single path:
- AgentFS-enabled Arrakis (required)

### 4. Comparison Tables

**Removed:** Tables comparing "Standard Arrakis" vs "AgentFS-Enabled"

**Replaced with:** Single feature table showing AgentFS capabilities only

### 5. Fallback Mechanisms

**Removed:**
- Setup script continuing without AgentFS
- Instructions for standard Arrakis REST API usage
- References to py-arrakis without AgentFS
- Alternative workflows without NFS root

## Why This Change

### 1. Clarity
No confusion about what is required vs optional. Users know from the start that AgentFS is mandatory.

### 2. Simplicity
One workflow to document, maintain, and support. No branching logic or conditional instructions.

### 3. Purpose
This setup exists specifically to provide AgentFS capabilities. Without AgentFS, users should use standard Arrakis from the original repository.

### 4. Maintenance
No need to maintain code paths, documentation, or support for non-AgentFS modes.

## Impact on Users

### New Users
- **Must install AgentFS** - No way around it
- **Clear requirements** - Know upfront what's needed
- **Single workflow** - Follow one set of instructions
- **No confusion** - No choices about standard vs AgentFS mode

### Migration from Standard Arrakis
If you were using standard Arrakis and want to migrate to this setup:

1. **Install AgentFS:**
   ```bash
   curl -sSL "https://raw.githubusercontent.com/.../install-deps.sh" | bash
   source ~/.bashrc
   ```

2. **Run setup:**
   ```bash
   curl -sSL "https://raw.githubusercontent.com/.../setup.sh" | bash
   ```

3. **Use AgentFS workflow:**
   ```bash
   cd ~/arrakis-prebuilt
   bash ../setup/arrakis-agentfs-launcher.sh my-agent
   bash ../setup/create-nfs-vm.sh 127.0.0.1 11111 my-vm
   ```

### If You Don't Want AgentFS

**Use the original Arrakis repository instead:**
- Repository: https://github.com/abilashraghuram/arrakis
- Standard setup without AgentFS requirements
- Disk-based VM filesystems
- No audit trail or version control

This fork is specifically for AgentFS integration.

## What Still Works

Everything AgentFS-related works exactly as before:

- ✅ NFS-based VM filesystem
- ✅ SQLite storage backend
- ✅ Complete audit trails
- ✅ Diff and rollback capabilities
- ✅ Version control for VM filesystems
- ✅ All AgentFS CLI commands

The only change is removal of non-AgentFS modes.

## Files Modified

### Scripts
- `setup.sh` - Now exits if AgentFS not found
- `install-deps.sh` - AgentFS installation is critical path

### Documentation
- `gcp-instructions.md` - Removed standard Arrakis instructions
- `README.md` - Removed optional language
- `AGENTFS-INTEGRATION.md` - Removed standard Arrakis comparisons
- `CHANGES.md` - Updated to reflect required status

## Benefits of This Approach

### For Users
- 🎯 **No ambiguity** - One way to do things
- 📖 **Clearer docs** - No conditional "if you want AgentFS" language
- 🚀 **Faster setup** - No decision paralysis
- 🔒 **Guaranteed features** - Always get audit trails

### For Maintainers
- 🧹 **Less code** - No conditional logic
- 📝 **Less documentation** - Single workflow to document
- 🐛 **Fewer bugs** - Fewer code paths to test
- 🔧 **Easier support** - One configuration to troubleshoot

## FAQ

**Q: Can I still use standard Arrakis?**  
A: Yes, but not from this repository. Use the original Arrakis repo: https://github.com/abilashraghuram/arrakis

**Q: Why make AgentFS mandatory?**  
A: This fork exists specifically to provide AgentFS capabilities. Without AgentFS, there's no reason to use this fork over the original.

**Q: What if I don't need audit trails?**  
A: Use the original Arrakis repository. This fork is purpose-built for auditability.

**Q: Is there any performance impact?**  
A: Yes, ~5-10% overhead from NFS. If this matters, use standard Arrakis with disk images.

**Q: Can backward compatibility be restored?**  
A: Technically yes, but it won't be. This is a deliberate design decision. Use the original repo if you need standard Arrakis.

**Q: What about existing VMs?**  
A: This setup only affects new VM creation. Existing standard Arrakis VMs are unaffected and continue to work with the original tools.

## Migration Timeline

- **Before this change:** Optional AgentFS, backward compatible
- **After this change:** Mandatory AgentFS, no backward compatibility
- **Future:** Full Arrakis REST API integration with AgentFS as default backend

## Support

- For AgentFS-enabled Arrakis: Use this repository
- For standard Arrakis: Use https://github.com/abilashraghuram/arrakis
- For AgentFS itself: https://github.com/tursodatabase/agentfs

## Conclusion

This is a **breaking change** that removes all backward compatibility with standard Arrakis. The setup now has a single purpose: provide Arrakis microVMs with mandatory AgentFS filesystem tracking.

**If you need standard Arrakis without AgentFS, use the original repository.**

This fork is purpose-built for complete auditability, version control, and filesystem tracking via AgentFS.