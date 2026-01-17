# Arrakis NFS-Only Setup on GCP

## Overview

This guide walks you through setting up Arrakis in NFS-only mode on Google Cloud Platform. All VMs will boot with their root filesystem mounted over NFS from AgentFS, enabling complete filesystem tracking and auditability.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and configured locally

## Step 1: Create GCP VM with Nested Virtualization

```bash
# Set your variables
VM_NAME="arrakis-vm"
PROJECT_ID="your-project-id"
SERVICE_ACCOUNT="your-service-account@project.iam.gserviceaccount.com"
ZONE="us-west1-b"

# Create VM instance with nested virtualization enabled
gcloud compute instances create ${VM_NAME} \
  --project=${PROJECT_ID} \
  --zone=${ZONE} \
  --machine-type=n1-standard-4 \
  --network-interface=network-tier=STANDARD,stack-type=IPV4_ONLY,subnet=default \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account=${SERVICE_ACCOUNT} \
  --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append \
  --create-disk=auto-delete=yes,boot=yes,device-name=${VM_NAME}-disk,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20250128,mode=rw,size=50,type=pd-standard \
  --no-shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --enable-nested-virtualization

# Add network tags and create firewall rule
NETWORK_TAG=allow-arrakis-ports
FIREWALL_RULE=allow-arrakis-ports-rule

gcloud compute instances add-tags ${VM_NAME} \
  --tags=${NETWORK_TAG} \
  --zone=${ZONE}

gcloud compute firewall-rules create ${FIREWALL_RULE} \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:3000-5000,tcp:7000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=${NETWORK_TAG} \
  --description="Allow TCP ingress for Arrakis REST API and services"
```

## Step 2: SSH into the VM

```bash
gcloud compute ssh ${VM_NAME} --zone=${ZONE}
```

## Step 3: Install System Dependencies

```bash
# Update package lists
sudo apt-get update

# Install essential build tools and dependencies
sudo apt-get install -y \
  build-essential \
  pkg-config \
  libunwind-dev \
  libatomic1 \
  make \
  curl \
  git \
  bridge-utils \
  iptables \
  nfs-common \
  jq

# Install OpenJDK (required for OpenAPI generator)
sudo apt-get install -y openjdk-17-jdk

# Verify Java installation
java -version
```

## Step 4: Install Go

```bash
cd ~
wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz

# Add Go to PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
source ~/.bashrc

# Clean up
rm go1.21.6.linux-amd64.tar.gz

# Verify
go version
```

## Step 5: Install Node.js and npm

```bash
# Install nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js
nvm install 18
nvm use 18

# Verify
node --version
npm --version
```

## Step 6: Install Rust and AgentFS

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Verify Rust
rustc --version

# Clone and build AgentFS
cd ~
git clone https://github.com/abilashraghuram/agentfs.git
cd agentfs/cli

# Build AgentFS (this may take several minutes)
cargo build --release

# Install AgentFS globally
sudo cp target/release/agentfs /usr/local/bin/

# Verify
agentfs --version
```

## Step 7: Clone Arrakis Repository

```bash
cd ~
git clone https://github.com/abilashraghuram/arrakis.git arrakis-repo
cd arrakis-repo
```

## Step 8: Build Arrakis NFS-Only Binaries

```bash
cd ~/arrakis-repo

# Generate API client code
npx --yes @openapitools/openapi-generator-cli generate \
    -i api/server-api.yaml \
    -g go \
    -o out/gen/serverapi \
    --package-name serverapi \
    --git-user-id abshkbh \
    --git-repo-id arrakis/out/gen/serverapi \
    --additional-properties=withGoMod=false \
    --global-property models,supportingFiles,apis,apiTests=false

npx --yes @openapitools/openapi-generator-cli generate \
    -i api/chv-api.yaml \
    -g go \
    -o out/gen/chvapi \
    --package-name chvapi \
    --git-user-id abshkbh \
    --git-repo-id arrakis/out/gen/chvapi \
    --additional-properties=withGoMod=false \
    --global-property models,supportingFiles,apis,apiTests=false

# Update Go dependencies
go mod tidy

# Build Arrakis binaries
CGO_ENABLED=0 go build -o out/arrakis-restserver ./cmd/restserver
CGO_ENABLED=0 go build -o out/arrakis-client ./cmd/client

# Verify builds
ls -lh out/arrakis-*
```

## Step 9: Download Arrakis Prebuilt Components

```bash
cd ~
curl -sSL "https://raw.githubusercontent.com/abilashraghuram/arrakis/main/setup/setup.sh" | bash

# This downloads:
# - Cloud Hypervisor binary
# - Linux kernel with NFS support
# - Initramfs
# - Guest rootfs image
```

## Step 10: Setup Runtime Directory

```bash
# Create runtime directory
mkdir -p ~/arrakis-runtime
cd ~/arrakis-runtime

# Copy built binaries
cp ~/arrakis-repo/out/arrakis-restserver .
cp ~/arrakis-repo/out/arrakis-client .

# Copy config
cp ~/arrakis-repo/config.yaml .

# Copy resources from prebuilt
cp -r ~/arrakis-prebuilt/resources .
cp -r ~/arrakis-prebuilt/out .

# Verify structure
ls -la
```

## Step 11: Configure for NFS-Only Mode

Edit the configuration file:

```bash
cd ~/arrakis-runtime
nano config.yaml
```

Ensure it looks like this (note: no `rootfs` field):

```yaml
hostservices:
  restserver:
    host: "0.0.0.0"
    port: "7000"
    state_dir: "./vm-state"
    bridge_name: "br0"
    bridge_ip: "10.20.1.1/24"
    bridge_subnet: "10.20.1.0/24"
    chv_bin: "./resources/bin/cloud-hypervisor"
    kernel: "./resources/bin/vmlinux.bin"
    initramfs: "./out/initramfs.cpio.gz"
    port_forwards:
      - port: "5901"
        description: "gui"
      - port: "5736-5740"
        description: "code"
    stateful_size_in_mb: "2048"
    guest_mem_percentage: "30"
    # NFS configuration - REQUIRED
    nfs_server: "127.0.0.1"
    nfs_port: 11111
    nfs_path: "/"
  client:
    server_host: "127.0.0.1"
    server_port: "7000"
guestservices:
  codeserver:
    port: "4030"
  cmdserver:
    port: "4031"
```

## Step 12: Setup Network Bridge

```bash
# Create bridge
sudo ip link add name br0 type bridge
sudo ip addr add 10.20.1.1/24 dev br0
sudo ip link set br0 up

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Setup NAT for VM internet access
sudo iptables -t nat -A POSTROUTING -s 10.20.1.0/24 -j MASQUERADE

# Verify
ip link show br0
ip addr show br0
```

## Step 13: Start the NFS-Only System

### Option A: Using the Launcher Script (Recommended)

```bash
cd ~/arrakis-runtime

# Copy launcher script
cp ~/arrakis-repo/setup/arrakis-agentfs-launcher.sh .

# Start everything
bash ./arrakis-agentfs-launcher.sh my-agent-id
```

This will:
- Start AgentFS NFS server on port 11111
- Start Arrakis REST server on port 7000
- Monitor both services
- Show usage instructions

### Option B: Manual Start (More Control)

```bash
cd ~/arrakis-runtime

# Terminal 1: Start AgentFS NFS server
agentfs nfs my-agent-id --port 11111 &

# Wait for NFS to start
sleep 2

# Verify NFS is running
netstat -ln | grep 11111

# Start Arrakis REST server (runs in foreground)
sudo ./arrakis-restserver --config config.yaml
```

## Step 14: Test Your Setup

Open a **new SSH session** and run these tests:

```bash
# Check services
netstat -ln | grep -E "7000|11111"

# Test REST API health
curl http://localhost:7000/v1/health

# Create a VM (NFS root automatically used)
curl -X POST http://localhost:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "test-vm-1"
  }'

# Should return:
# {
#   "vmName": "test-vm-1",
#   "status": "running",
#   "ip": "10.20.1.2",
#   "tapDeviceName": "tap0",
#   "portForwards": [...]
# }

# List VMs
curl http://localhost:7000/v1/vms | jq .

# Execute command in VM
curl -X POST http://localhost:7000/v1/vms/test-vm-1/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "cmd": "ls -la /",
    "blocking": true
  }'

# Check AgentFS is tracking filesystem operations
agentfs log my-agent-id | tail -20
agentfs diff my-agent-id

# Destroy test VM
curl -X DELETE http://localhost:7000/v1/vms/test-vm-1
```

## Step 15: Access from External IP (Optional)

```bash
# Get your VM's external IP
curl ifconfig.me

# From your local machine, access the REST API
curl http://<EXTERNAL-IP>:7000/v1/health
```

## Understanding NFS-Only Mode

### How It Works

1. **AgentFS NFS Server**: Serves the root filesystem over NFSv3
2. **VM Boot**: All VMs boot with `root=/dev/nfs` kernel parameter
3. **Filesystem Tracking**: Every file operation goes through NFS to AgentFS
4. **SQLite Storage**: All operations stored in `.agentfs/<agent-id>.db`

### What's Different

**Old Mode (No Longer Supported):**
- VMs booted from local disk image
- `rootfs` parameter in API
- No filesystem tracking

**New NFS-Only Mode:**
- All VMs boot with NFS root
- No `rootfs` parameter needed
- Automatic filesystem tracking via AgentFS
- Complete audit trail

### Disk Configuration

```
VM Disks:
  /dev/vda: Stateful disk (local, for /var, /tmp, etc.)

Root Filesystem:
  /: NFS mount from AgentFS (127.0.0.1:11111)
```

### Kernel Command Line

Every VM boots with:
```
console=ttyS0 
root=/dev/nfs 
nfsroot=127.0.0.1:/,nfsvers=3,tcp,nolock,port=11111 
ip=dhcp 
rw 
gateway_ip="10.20.1.1" 
guest_ip="10.20.1.2" 
vm_name="test-vm"
```

## AgentFS Commands

```bash
# View filesystem changes
agentfs diff my-agent-id

# View operation log
agentfs log my-agent-id

# List files
agentfs ls my-agent-id /path

# Read file content
agentfs cat my-agent-id /etc/hostname

# Export filesystem to directory
agentfs export my-agent-id /output/path
```

## Troubleshooting

### NFS Server Won't Start

```bash
# Check if port is in use
netstat -ln | grep 11111

# Check AgentFS logs
tail -f ~/.agentfs-nfs.log

# Kill existing process
pkill -f "agentfs nfs"

# Restart
agentfs nfs my-agent-id --port 11111 &
```

### VM Boot Fails

```bash
# Check VM logs
tail -f vm-state/*/log

# Common issues:
# 1. NFS server not running
# 2. Bridge not configured
# 3. Kernel missing NFS support

# Verify NFS is accessible
netstat -ln | grep 11111

# Verify bridge exists
ip link show br0
```

### REST Server Fails

```bash
# Check logs
tail -f .arrakis-rest.log

# Common issues:
# 1. Missing NFS config in config.yaml
# 2. NFS server not running
# 3. Port 7000 already in use

# Check NFS config
grep -A 3 "nfs_server" config.yaml

# Kill existing REST server
sudo pkill -f arrakis-restserver
```

### Permission Errors

```bash
# AgentFS NFS runs as current user
# Check file ownership in VM

# If needed, adjust AgentFS permissions
# (implementation depends on your requirements)
```

### Bridge Setup Failed

```bash
# Remove existing bridge
sudo ip link del br0

# Recreate
sudo ip link add name br0 type bridge
sudo ip addr add 10.20.1.1/24 dev br0
sudo ip link set br0 up

# Re-enable forwarding
sudo sysctl -w net.ipv4.ip_forward=1
```

## Stopping the System

```bash
# If using launcher script: Press Ctrl+C

# If manual:
sudo pkill -f arrakis-restserver
pkill -f "agentfs nfs"
```

## Restarting the System

```bash
cd ~/arrakis-runtime

# Using launcher
bash ./arrakis-agentfs-launcher.sh my-agent-id

# Or manually
agentfs nfs my-agent-id --port 11111 &
sleep 2
sudo ./arrakis-restserver --config config.yaml
```

## Persistent Setup (Run on Boot)

To make services start automatically on boot:

```bash
# Create systemd service for NFS
sudo tee /etc/systemd/system/agentfs-nfs.service << EOF
[Unit]
Description=AgentFS NFS Server
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/agentfs nfs my-agent-id --port 11111
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for REST server
sudo tee /etc/systemd/system/arrakis-rest.service << EOF
[Unit]
Description=Arrakis REST Server
After=network.target agentfs-nfs.service
Requires=agentfs-nfs.service

[Service]
Type=simple
User=root
WorkingDirectory=$HOME/arrakis-runtime
ExecStart=$HOME/arrakis-runtime/arrakis-restserver --config config.yaml
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable agentfs-nfs arrakis-rest
sudo systemctl start agentfs-nfs arrakis-rest

# Check status
sudo systemctl status agentfs-nfs
sudo systemctl status arrakis-rest
```

## Next Steps

- Read [NFS-ROOT-QUICKSTART.md](../NFS-ROOT-QUICKSTART.md) for usage examples
- See [IMPLEMENTATION-SUMMARY.md](../IMPLEMENTATION-SUMMARY.md) for technical details
- Check [NFS-ROOT-USAGE.md](../docs/NFS-ROOT-USAGE.md) for comprehensive documentation

## Summary

You now have:
- ✅ Arrakis running in NFS-only mode
- ✅ AgentFS tracking all VM filesystem operations
- ✅ REST API for VM management
- ✅ Complete audit trail in SQLite

All VMs automatically boot with NFS root. No configuration needed per-VM! 🚀