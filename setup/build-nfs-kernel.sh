#!/bin/bash
set -e

# Build Linux kernel with NFS root support for Arrakis + AgentFS
# This kernel can boot from NFS and is compatible with cloud-hypervisor

KERNEL_VERSION="6.1.102"
KERNEL_DIR="linux-${KERNEL_VERSION}"
KERNEL_URL="https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KERNEL_VERSION}.tar.xz"
OUTPUT_DIR="$(pwd)/kernel-output"

echo "============================================================"
echo "Building Linux Kernel with NFS Root Support"
echo "Version: ${KERNEL_VERSION}"
echo "============================================================"

# Check dependencies
echo "Checking build dependencies..."
if ! command -v gcc &> /dev/null; then
    echo "Error: gcc not found. Install with: sudo apt-get install build-essential"
    exit 1
fi

if ! command -v make &> /dev/null; then
    echo "Error: make not found. Install with: sudo apt-get install make"
    exit 1
fi

if ! command -v flex &> /dev/null || ! command -v bison &> /dev/null; then
    echo "Installing flex and bison..."
    sudo apt-get update
    sudo apt-get install -y flex bison libelf-dev libssl-dev bc
fi

# Download kernel if not present
if [ ! -d "${KERNEL_DIR}" ]; then
    if [ ! -f "linux-${KERNEL_VERSION}.tar.xz" ]; then
        echo "Downloading Linux kernel ${KERNEL_VERSION}..."
        wget "${KERNEL_URL}"
    fi

    echo "Extracting kernel..."
    tar xf "linux-${KERNEL_VERSION}.tar.xz"
fi

cd "${KERNEL_DIR}"

# Start with minimal defconfig
echo "Creating kernel configuration..."
make defconfig

# Enable essential features for cloud-hypervisor
./scripts/config --enable CONFIG_HYPERVISOR_GUEST
./scripts/config --enable CONFIG_KVM_GUEST
./scripts/config --enable CONFIG_PARAVIRT
./scripts/config --enable CONFIG_PARAVIRT_SPINLOCKS

# Enable virtio drivers (required for cloud-hypervisor)
./scripts/config --enable CONFIG_VIRTIO
./scripts/config --enable CONFIG_VIRTIO_PCI
./scripts/config --enable CONFIG_VIRTIO_MMIO
./scripts/config --enable CONFIG_VIRTIO_MMIO_CMDLINE_DEVICES
./scripts/config --enable CONFIG_VIRTIO_BLK
./scripts/config --enable CONFIG_VIRTIO_NET
./scripts/config --enable CONFIG_VIRTIO_CONSOLE

# Enable networking
./scripts/config --enable CONFIG_NET
./scripts/config --enable CONFIG_INET
./scripts/config --enable CONFIG_PACKET

# Enable NFS client support (THE KEY PART!)
./scripts/config --enable CONFIG_NETWORK_FILESYSTEMS
./scripts/config --enable CONFIG_NFS_FS
./scripts/config --enable CONFIG_NFS_V3
./scripts/config --enable CONFIG_NFS_V3_ACL
./scripts/config --enable CONFIG_ROOT_NFS
./scripts/config --enable CONFIG_LOCKD
./scripts/config --enable CONFIG_LOCKD_V4
./scripts/config --enable CONFIG_SUNRPC

# Enable IP autoconfiguration (needed for ip= kernel parameter)
./scripts/config --enable CONFIG_IP_PNP
./scripts/config --enable CONFIG_IP_PNP_DHCP
./scripts/config --enable CONFIG_IP_PNP_BOOTP

# Disable features we don't need to speed up build
./scripts/config --disable CONFIG_MODULES
./scripts/config --disable CONFIG_SOUND
./scripts/config --disable CONFIG_USB
./scripts/config --disable CONFIG_WIRELESS
./scripts/config --disable CONFIG_WLAN
./scripts/config --disable CONFIG_BLK_DEV_INTEGRITY

# Disable certificate/keyring stuff that requires OpenSSL
./scripts/config --disable CONFIG_SYSTEM_TRUSTED_KEYRING
./scripts/config --disable CONFIG_SECONDARY_TRUSTED_KEYRING
./scripts/config --disable CONFIG_SYSTEM_REVOCATION_KEYS
./scripts/config --disable CONFIG_MODULE_SIG
./scripts/config --disable CONFIG_INTEGRITY
./scripts/config --disable CONFIG_IMA
./scripts/config --disable CONFIG_EVM
./scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ""
./scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ""

# Enable serial console
./scripts/config --enable CONFIG_SERIAL_8250
./scripts/config --enable CONFIG_SERIAL_8250_CONSOLE

# Enable /dev/pts
./scripts/config --enable CONFIG_UNIX98_PTYS
./scripts/config --enable CONFIG_DEVPTS_MULTIPLE_INSTANCES

# Enable tmpfs
./scripts/config --enable CONFIG_TMPFS

# Update config
make olddefconfig

# Verify NFS root is enabled
if ! grep -q "CONFIG_ROOT_NFS=y" .config; then
    echo "Error: CONFIG_ROOT_NFS not enabled!"
    exit 1
fi

echo "Configuration complete. Key NFS settings:"
grep "CONFIG_NFS" .config | grep -v "^#"
echo ""

# Build kernel
echo "Building kernel (this will take 10-30 minutes)..."
echo "Using $(nproc) CPU cores"
make -j$(nproc) bzImage

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Copy kernel
echo "Copying kernel to ${OUTPUT_DIR}/vmlinux-nfs"
cp arch/x86/boot/bzImage "${OUTPUT_DIR}/vmlinux-nfs"

cd ..

echo ""
echo "============================================================"
echo "Kernel build complete!"
echo "============================================================"
echo "Kernel location: ${OUTPUT_DIR}/vmlinux-nfs"
echo "Size: $(du -h ${OUTPUT_DIR}/vmlinux-nfs | cut -f1)"
echo ""
echo "To use with Arrakis:"
echo "  cp ${OUTPUT_DIR}/vmlinux-nfs ~/arrakis-repo/setup/arrakis-prebuilt/resources/bin/vmlinux-nfs.bin"
echo ""
echo "Then modify create-nfs-vm.sh to use vmlinux-nfs.bin instead of vmlinux.bin"
echo "============================================================"
