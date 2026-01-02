#!/usr/bin/env bash
set -e

# Arrakis + AgentFS Integration Launcher
# This script starts Arrakis REST server with AgentFS NFS-backed filesystem

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARRAKIS_DIR="${SCRIPT_DIR}/arrakis-prebuilt"
AGENTFS_BIN="${HOME}/projects/agentfs/cli/target/release/agentfs"
AGENTFS_DIR="${ARRAKIS_DIR}/.agentfs"
ROOTFS_IMAGE="${ARRAKIS_DIR}/out/arrakis-guestrootfs-ext4.img"
ROOTFS_MOUNT="${ARRAKIS_DIR}/.rootfs-mount"
ROOTFS_BASE="${ARRAKIS_DIR}/.rootfs-base"
NFS_BIND_IP="127.0.0.1"
NFS_PORT="11111"
AGENT_ID="${1:-arrakis-sandbox}"

# Print colored messages
print_message() {
  echo -e "${GREEN}[Arrakis+AgentFS]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[Warning]${NC} $1"
}

print_error() {
  echo -e "${RED}[Error]${NC} $1"
}

print_info() {
  echo -e "${BLUE}[Info]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
  print_message "Checking prerequisites..."

  if [ ! -f "${AGENTFS_BIN}" ]; then
    print_error "AgentFS CLI not found at: ${AGENTFS_BIN}"
    print_error "Please run install-deps.sh first or build AgentFS manually"
    exit 1
  fi

  if [ ! -f "${ROOTFS_IMAGE}" ]; then
    print_error "Rootfs image not found at: ${ROOTFS_IMAGE}"
    print_error "Please run setup.sh first to download Arrakis components"
    exit 1
  fi

  if [ ! -f "${ARRAKIS_DIR}/arrakis-restserver" ]; then
    print_error "Arrakis REST server not found"
    print_error "Please run setup.sh first"
    exit 1
  fi

  print_message "All prerequisites satisfied"
}

# Initialize AgentFS database with rootfs as base
initialize_agentfs() {
  local db_path="${AGENTFS_DIR}/${AGENT_ID}.db"

  if [ -f "${db_path}" ]; then
    print_info "AgentFS database already exists for agent: ${AGENT_ID}"
    print_info "To reset, delete: ${db_path}"
    return 0
  fi

  print_message "Initializing AgentFS database for agent: ${AGENT_ID}"

  # Create mount point and base directory
  mkdir -p "${ROOTFS_MOUNT}"
  mkdir -p "${ROOTFS_BASE}"

  # Mount the ext4 rootfs image (read-only)
  print_message "Mounting rootfs image to extract base filesystem..."
  sudo mount -o loop,ro "${ROOTFS_IMAGE}" "${ROOTFS_MOUNT}"

  # Copy rootfs contents to base directory
  print_message "Copying rootfs contents (this may take a moment)..."
  sudo rsync -a "${ROOTFS_MOUNT}/" "${ROOTFS_BASE}/"

  # Change ownership to current user
  sudo chown -R $(whoami):$(whoami) "${ROOTFS_BASE}"

  # Unmount
  sudo umount "${ROOTFS_MOUNT}"

  # Initialize AgentFS with the base
  print_message "Initializing AgentFS database from base..."
  cd "${ARRAKIS_DIR}"
  ${AGENTFS_BIN} init --base "${ROOTFS_BASE}" "${AGENT_ID}"

  print_message "AgentFS initialized successfully"
}

# Start AgentFS NFS server
start_agentfs_nfs() {
  print_message "Starting AgentFS NFS server..."
  print_info "  Binding to: ${NFS_BIND_IP}:${NFS_PORT}"
  print_info "  Agent ID: ${AGENT_ID}"

  cd "${ARRAKIS_DIR}"
  ${AGENTFS_BIN} nfs --bind "${NFS_BIND_IP}" --port "${NFS_PORT}" "${AGENT_ID}" > "${AGENTFS_DIR}/nfs.log" 2>&1 &
  AGENTFS_PID=$!

  # Wait for NFS server to start
  sleep 2

  if ! kill -0 $AGENTFS_PID 2>/dev/null; then
    print_error "AgentFS NFS server failed to start"
    print_error "Check logs: ${AGENTFS_DIR}/nfs.log"
    exit 1
  fi

  print_message "AgentFS NFS server started (PID: ${AGENTFS_PID})"
}

# Cleanup function
cleanup() {
  print_message "Cleaning up..."

  # Kill AgentFS NFS server
  if [ ! -z "${AGENTFS_PID:-}" ]; then
    kill $AGENTFS_PID 2>/dev/null || true
    print_message "Stopped AgentFS NFS server"
  fi

  # Kill Arrakis REST server
  if [ ! -z "${ARRAKIS_PID:-}" ]; then
    sudo kill $ARRAKIS_PID 2>/dev/null || true
    print_message "Stopped Arrakis REST server"
  fi

  # Unmount rootfs if still mounted
  if mountpoint -q "${ROOTFS_MOUNT}" 2>/dev/null; then
    sudo umount "${ROOTFS_MOUNT}" 2>/dev/null || true
  fi

  echo ""
  print_message "Session complete!"
  print_info "View filesystem changes with: cd ${ARRAKIS_DIR} && agentfs diff ${AGENT_ID}"
  print_info "View operation log with: cd ${ARRAKIS_DIR} && agentfs log ${AGENT_ID}"
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Display banner
display_banner() {
  echo ""
  echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║                                                        ║${NC}"
  echo -e "${BLUE}║          ${GREEN}Arrakis + AgentFS Integration${BLUE}              ║${NC}"
  echo -e "${BLUE}║                                                        ║${NC}"
  echo -e "${BLUE}║  Persistent, Auditable VM Filesystem Tracking         ║${NC}"
  echo -e "${BLUE}║                                                        ║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
  echo ""
  print_info "Agent ID: ${AGENT_ID}"
  print_info "NFS Server: ${NFS_BIND_IP}:${NFS_PORT}"
  print_info "Database: ${AGENTFS_DIR}/${AGENT_ID}.db"
  echo ""
}

# Create NFS-aware config
create_nfs_config() {
  print_message "Creating NFS-aware configuration..."

  # This is a placeholder - in practice, you'd need to modify how Arrakis
  # creates VMs to use NFS root instead of the disk image
  # This would require either:
  # 1. Patching Arrakis to support NFS root
  # 2. Creating a wrapper that intercepts VM creation
  # 3. Manually configuring cloud-hypervisor with NFS root params

  cat > "${ARRAKIS_DIR}/nfs-config.yaml" << EOF
# AgentFS NFS Configuration for Arrakis
nfs:
  enabled: true
  server: ${NFS_BIND_IP}
  port: ${NFS_PORT}
  agent_id: ${AGENT_ID}

# Note: To use this, you need to configure cloud-hypervisor with:
# --kernel vmlinux.bin
# --cmdline "root=/dev/nfs nfsroot=${NFS_BIND_IP}:/,nfsvers=3,tcp,nolock,port=${NFS_PORT},mountport=${NFS_PORT} rw ip=dhcp"
EOF

  print_info "NFS config written to: ${ARRAKIS_DIR}/nfs-config.yaml"
}

# Display usage instructions
display_instructions() {
  echo ""
  print_message "Setup Complete! AgentFS NFS server is running."
  echo ""
  print_warning "IMPORTANT: Manual Integration Required"
  echo ""
  print_info "To use AgentFS with Arrakis VMs, you need to configure cloud-hypervisor"
  print_info "to use NFS root instead of the disk image. Here's how:"
  echo ""
  print_info "Option 1: Modify Arrakis VM creation code to use NFS root"
  print_info "  - Edit cloud-hypervisor kernel cmdline to include:"
  print_info "    root=/dev/nfs nfsroot=${NFS_BIND_IP}:/,nfsvers=3,tcp,nolock,port=${NFS_PORT}"
  echo ""
  print_info "Option 2: Start Arrakis REST server and configure VMs manually"
  print_info "  - In another terminal: cd ${ARRAKIS_DIR} && sudo ./arrakis-restserver"
  print_info "  - Use cloud-hypervisor API to create VMs with NFS root"
  echo ""
  print_info "Option 3: Use the standard Arrakis workflow (without AgentFS)"
  print_info "  - Press Ctrl+C to stop this script"
  print_info "  - Run: cd ${ARRAKIS_DIR} && sudo ./arrakis-restserver"
  echo ""
  print_message "AgentFS Features Available:"
  print_info "  • View changes: agentfs diff ${AGENT_ID}"
  print_info "  • View logs: agentfs log ${AGENT_ID}"
  print_info "  • Export filesystem: agentfs export ${AGENT_ID} /output/path"
  echo ""
}

# Main execution
main() {
  display_banner
  check_prerequisites
  initialize_agentfs
  start_agentfs_nfs
  create_nfs_config
  display_instructions

  print_message "Keeping AgentFS NFS server running..."
  print_info "Press Ctrl+C to stop"
  echo ""

  # Keep script running
  while true; do
    sleep 5
    # Check if NFS server is still running
    if ! kill -0 $AGENTFS_PID 2>/dev/null; then
      print_error "AgentFS NFS server died unexpectedly"
      exit 1
    fi
  done
}

# Run main
main
