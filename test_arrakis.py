from py_arrakis import SandboxManager

# Initialize the sandbox manager with the Arrakis server URL
manager = SandboxManager("http://35.212.185.249:7000")

# List all VMs
sandboxes = manager.list_all()

# Start a new VM
sandbox = manager.start_sandbox("my-sandbox")

# Run a command in the VM
result = sandbox.run_cmd("python3 -c 'a = 10; b = 25; print(f\"a = {a}, b = {b}, sum = {a + b}\")'")
print(result["output"])

# Destroy the VM when done
sandbox.destroy()
