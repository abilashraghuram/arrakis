"""
Basic Arrakis Test (without callbacks)

Use this to test basic VM functionality while the server
is being updated with callback support.
"""

import sys

# Use the local py_arrakis module
sys.path.insert(0, ".")
from py_arrakis import SandboxManager

# Initialize the sandbox manager with the Arrakis server URL
SERVER_URL = "http://35.212.185.249:7000"
manager = SandboxManager(SERVER_URL)

print("=" * 60)
print("Arrakis Basic Test (No Callbacks)")
print("=" * 60)

# Check server health
try:
    health = manager.health_check()
    print(f"Server status: {health.get('status')}")
except Exception as e:
    print(f"Server not reachable: {e}")
    sys.exit(1)

# List existing VMs
print("\nExisting sandboxes:")
sandboxes = manager.list_all()
for s in sandboxes:
    print(f"  - {s.name}: {s.status}")

# Start a new sandbox
print("\nStarting sandbox 'basic-test'...")
sandbox = manager.start_sandbox("basic-test")
print(f"Sandbox started: {sandbox.name} ({sandbox.status})")
print(f"Sandbox IP: {sandbox.ip}")

# Run a basic command
print("\nRunning basic Python command...")
result = sandbox.run_cmd("python3 -c 'a = 10; b = 25; print(f\"a = {a}, b = {b}, sum = {a + b}\")'")
print(f"Output: {result.get('output', '').strip()}")

# Run another command
print("\nChecking Python version...")
result = sandbox.run_cmd("python3 --version")
print(f"Output: {result.get('output', '').strip()}")

# List files
print("\nListing /tmp directory...")
result = sandbox.run_cmd("ls -la /tmp")
print(f"Output:\n{result.get('output', '')}")

# Clean up
print("\n" + "=" * 60)
print("Cleaning up...")
sandbox.destroy()
print("Sandbox destroyed!")

print("\nBasic test completed successfully!")
print("\nNote: Callback tests require the updated server with WebSocket support.")

