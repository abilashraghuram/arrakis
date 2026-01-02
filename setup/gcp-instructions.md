# Setup Instructions on GCP

## Setting Up a GCE VM with Nested Virtualization Support

- To create a Google Compute Engine (GCE) virtual machine with nested virtualization enabled, run the following command make sure to replace the $VM_NAME and $PROJECT with your own values.

    ```bash
    VM_NAME=<your-vm-name>
    PROJECT_ID=<your-project-id>
    SERVICE_ACCOUNT=<your-service-account>
    ZONE=<your-zone>

    gcloud compute instances create ${VM_NAME} --project=${PROJECT_ID} --zone=${ZONE} --machine-type=n1-standard-1 --network-interface=network-tier=STANDARD,stack-type=IPV4_ONLY,subnet=default --maintenance-policy=MIGRATE --provisioning-model=STANDARD --service-account=${SERVICE_ACCOUNT} --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=maverick-gcp-dev-vm3,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20250128,mode=rw,size=20,type=pd-standard --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --labels=goog-ec-src=vm_add-gcloud --reservation-affinity=any --enable-nested-virtualization

    NETWORK_TAG=allow-ingress-ports
    FIREWALL_RULE=allow-ingress-ports-rule
    gcloud compute instances add-tags ${VM_NAME} --tags=${NETWORK_TAG} --zone=${ZONE}
    gcloud compute firewall-rules create ${FIREWALL_RULE} \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:3000-5000,tcp:7000 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=${NETWORK_TAG} \
    --description="Allow TCP ingress on ports 3000-5000 and 7000 for VMs with the ${NETWORK_TAG} tag"
    ```

## Instructions to run on the GCE VM

- SSH into the VM.

    ```bash    
    # Install dependencies (includes AgentFS)
    cd $HOME
    curl -sSL "https://raw.githubusercontent.com/abshkbh/arrakis/main/setup/install-deps.sh" | bash
    
    # Reload shell to get updated PATH
    source ~/.bashrc
    
    # Install Arrakis
    curl -sSL "https://raw.githubusercontent.com/abshkbh/arrakis/main/setup/setup.sh" | bash
    ```

- Verify the installation

    ```bash
    cd $HOME/arrakis-prebuilt
    ls
    ```

- **Run Arrakis with AgentFS:**

    AgentFS provides persistent, auditable filesystem tracking for your Arrakis VMs. All filesystem operations are stored in SQLite with full change history.

- Start the AgentFS-enabled launcher:

    ```bash
    cd $HOME/arrakis-prebuilt
    bash ../setup/arrakis-agentfs-launcher.sh my-agent-id
    ```

    This will:
    - Initialize AgentFS database from the Arrakis rootfs
    - Start an NFS server serving the filesystem
    - Keep running to maintain the NFS server

### AgentFS Features

Once your VMs are using AgentFS (requires manual configuration), you can:

- **View filesystem changes:**

    ```bash
    cd $HOME/arrakis-prebuilt
    agentfs diff my-agent-id
    ```

- **View operation logs:**

    ```bash
    agentfs log my-agent-id
    ```

- **Export filesystem to directory:**

    ```bash
    agentfs export my-agent-id /path/to/output
    ```

- **List all files:**

    ```bash
    agentfs ls my-agent-id /
    ```

- **Read specific files:**

    ```bash
    agentfs cat my-agent-id /etc/hostname
    ```

### Important Notes

- AgentFS is REQUIRED for this setup - there is no standard Arrakis mode
- The setup requires manual configuration to make Arrakis VMs boot with NFS root
- AgentFS tracks all filesystem operations transparently via NFS protocol
- VMs have no awareness they're writing to SQLite - they just see a normal filesystem
- Perfect for auditing AI agent behavior, debugging, and version control of VM states
- See `arrakis-agentfs-launcher.sh` for integration details
- See `AGENTFS-INTEGRATION.md` for complete documentation
