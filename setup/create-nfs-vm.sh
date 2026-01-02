#!/usr/bin/env bash
set -e

# Script to manually create and start a cloud-hypervisor VM with AgentFS NFS root
# This is a helper script to demonstrate NFS root integration with Arrakis

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_message() {
  echo -e "${GREEN}[NFS-VM]${NC} $1"
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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARRAKIS_DIR="${SCRIPT_DIR}/arrakis-prebuilt"
CHV_BIN="${ARRAKIS_DIR}/resources/bin/cloud-hypervisor"
KERNEL="${ARRAKIS_DIR}/resources/bin/vmlinux.bin"
NFS_SERVER="${1:-127.0.0.1}"
NFS_PORT="${2:-11111}"
VM_NAME="${3:-nfs-test-vm}"
TAP_DEV="tap-${VM_NAME}"
HOST_IP="172.20.0.1"
GUEST_IP="172.20.0.2"
VCPUS="2"
MEMORY="512M"
API_SOCKET="/tmp/${VM_NAME}.sock"

# Display usage
usage() {
  echo "Usage: $0 [NFS_SERVER] [NFS_PORT] [VM_NAME]"
  echo ""
  echo "Arguments:"
  echo "  NFS_SERVER  - NFS server IP (default: 127.0.0.1)"
  echo "  NFS_PORT    - NFS server port (default: 11111)"
  echo "  VM_NAME     - Name for the VM (default: nfs-test-vm)"
  echo ""
  echo "Example:"
  echo "  $0 127.0.0.1 11111 my-agent"
  echo ""
  echo "Prerequisites:"
  echo "  - AgentFS NFS server must be running (use arrakis-agentfs-launcher.sh)"
  echo "  - Cloud-hypervisor binary at: ${CHV_BIN}"
  echo "  - Kernel binary at: ${KERNEL}"
  exit 1
}

# Check prerequisites
check_prerequisites() {
  print_message "Checking prerequisites..."

  if [ ! -f "${CHV_BIN}" ]; then
    print_error "cloud-hypervisor not found at: ${CHV_BIN}"
    print_error "Run setup.sh first to download required binaries"
    exit 1
  fi

  if [ ! -f "${KERNEL}" ]; then
    print_error "Kernel not found at: ${KERNEL}"
    print_error "Run setup.sh first to download required images"
    exit 1
  fi

  # Check if NFS server is reachable
  if ! timeout 2 bash -c "cat < /dev/null > /dev/tcp/${NFS_SERVER}/${NFS_PORT}" 2>/dev/null; then
    print_warning "Cannot connect to NFS server at ${NFS_SERVER}:${NFS_PORT}"
    print_warning "Make sure AgentFS NFS server is running"
    print_warning "Start it with: bash arrakis-agentfs-launcher.sh <agent-id>"
    exit 1
  fi

  print_message "Prerequisites satisfied"
}

# Setup TAP device
setup_networking() {
  print_message "Setting up networking..."

  # Remove existing TAP device if present
  sudo ip link del "${TAP_DEV}" 2>/dev/null || true

  # Create TAP device
  sudo ip tuntap add dev "${TAP_DEV}" mode tap
  sudo ip addr add "${HOST_IP}/24" dev "${TAP_DEV}"
  sudo ip link set dev "${TAP_DEV}" up

  print_message "TAP device ${TAP_DEV} created (${HOST_IP})"
  print_info "Guest will use IP: ${GUEST_IP}"
}

# Cleanup function
cleanup() {
  print_message "Cleaning up..."

  # Remove API socket
  rm -f "${API_SOCKET}"

  # Remove TAP device
  sudo ip link del "${TAP_DEV}" 2>/dev/null || true

  print_message "Cleanup complete"
}

trap cleanup EXIT INT TERM

# Start cloud-hypervisor VM
start_vm() {
  print_message "Starting cloud-hypervisor VM: ${VM_NAME}"

  # Build kernel command line for NFS root
  KERNEL_CMDLINE="console=ttyS0 reboot=k panic=1 pci=off"
  KERNEL_CMDLINE="${KERNEL_CMDLINE} ip=${GUEST_IP}::${HOST_IP}:255.255.255.0::eth0:off"
  KERNEL_CMDLINE="${KERNEL_CMDLINE} root=/dev/nfs"
  KERNEL_CMDLINE="${KERNEL_CMDLINE} nfsroot=${NFS_SERVER}:/,nfsvers=3,tcp,nolock,port=${NFS_PORT},mountport=${NFS_PORT}"
  KERNEL_CMDLINE="${KERNEL_CMDLINE} rw init=/sbin/init"

  print_info "Kernel: ${KERNEL}"
  print_info "CPUs: ${VCPUS}, Memory: ${MEMORY}"
  print_info "NFS Root: ${NFS_SERVER}:/ (port ${NFS_PORT})"
  print_info "Console: Serial (ttyS0)"

  # Remove old API socket
  rm -f "${API_SOCKET}"

  # Start cloud-hypervisor
  print_message "Booting VM (this may take a few seconds)..."
  echo ""

  sudo "${CHV_BIN}" \
    --api-socket "${API_SOCKET}" \
    --cpus "boot=${VCPUS}" \
    --memory "size=${MEMORY}" \
    --kernel "${KERNEL}" \
    --cmdline "${KERNEL_CMDLINE}" \
    --net "tap=${TAP_DEV},mac=52:54:00:12:34:56,ip=${GUEST_IP},mask=255.255.255.0" \
    --console tty \
    --serial tty

  # Note: cloud-hypervisor will block here until VM shuts down
}

# Display banner
display_banner() {
  echo ""
  echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║                                                        ║${NC}"
  echo -e "${BLUE}║        ${GREEN}Cloud Hypervisor + AgentFS NFS Root${BLUE}          ║${NC}"
  echo -e "${BLUE}║                                                        ║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
  echo ""
  print_info "VM Name: ${VM_NAME}"
  print_info "NFS Server: ${NFS_SERVER}:${NFS_PORT}"
  print_info "Network: ${HOST_IP} (host) <-> ${GUEST_IP} (guest)"
  echo ""
}

# Main execution
main() {
  if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    usage
  fi

  display_banner
  check_prerequisites
  setup_networking
  start_vm
}

main "$@"
