"""
Test Arrakis with RPC Callbacks

This script demonstrates how to:
1. Start a sandbox
2. Enable RPC callbacks from the VM
3. Register callback handlers that run on the host
4. Execute code in the VM that triggers callbacks
"""

import sys
import time
import json

# Use the local py_arrakis module with callback support
sys.path.insert(0, ".")
from py_arrakis import SandboxManager

# Initialize the sandbox manager with the Arrakis server URL
SERVER_URL = "http://35.212.130.118:7000"
manager = SandboxManager(SERVER_URL)

print("=" * 60)
print("Arrakis RPC Callback Test")
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
print("\nStarting sandbox 'callback-test'...")
sandbox = manager.start_sandbox("callback-test")
print(f"Sandbox started: {sandbox.name} ({sandbox.status})")
print(f"Sandbox IP: {sandbox.ip}")

# Enable callbacks - this connects the WebSocket
print("\nEnabling RPC callbacks...")
sandbox.enable_callbacks()
print("Callbacks enabled!")

# Register callback handlers
# These functions run on the HOST when the VM calls them

@sandbox.on_callback("get_host_time")
def handle_get_time(params):
    """Return the current time on the host."""
    return {"timestamp": time.time(), "formatted": time.strftime("%Y-%m-%d %H:%M:%S")}

@sandbox.on_callback("process_data")
def handle_process_data(params):
    """Process some data on the host and return results."""
    data = params.get("data", []) if params else []
    return {
        "sum": sum(data),
        "count": len(data),
        "average": sum(data) / len(data) if data else 0
    }

@sandbox.on_callback("read_host_file")
def handle_read_file(params):
    """Read a file from the host (example - be careful with security!)."""
    # This is just an example - in production, validate/restrict paths!
    filename = params.get("filename") if params else None
    if not filename:
        raise ValueError("filename is required")
    
    # Only allow reading certain safe files for this demo
    allowed = ["/etc/hostname", "/etc/os-release"]
    if filename not in allowed:
        raise ValueError(f"Access denied: {filename}")
    
    try:
        with open(filename, "r") as f:
            return {"content": f.read()}
    except FileNotFoundError:
        return {"error": f"File not found: {filename}"}

print("\nRegistered callback handlers:")
print("  - get_host_time: Returns host timestamp")
print("  - process_data: Processes a list of numbers")
print("  - read_host_file: Reads allowed files from host")

# Upload a Python script that will make callbacks
callback_script = '''
#!/usr/bin/env python3
"""Script that runs in the VM and makes callbacks to the host via HTTP."""

import json
import urllib.request
import urllib.error

# Gateway IP is the host (set via kernel cmdline, default to bridge IP)
GATEWAY_IP = "10.20.1.1"
VM_NAME = "callback-test"

def callback(method, params=None):
    """Make an RPC callback to the host via HTTP."""
    url = f"http://{GATEWAY_IP}:7000/v1/internal/callback"
    
    request_data = {
        "vmName": VM_NAME,
        "method": method,
    }
    if params is not None:
        request_data["params"] = params
    
    data = json.dumps(request_data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            
            if response_data.get("error"):
                raise RuntimeError(response_data["error"])
            
            return response_data.get("result", {})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection failed: {e.reason}")

# Test 1: Get host time
print("Test 1: Getting host time...")
result = callback("get_host_time")
print(f"  Host time: {result}")

# Test 2: Process data on host
print("\\nTest 2: Processing data on host...")
result = callback("process_data", {"data": [1, 2, 3, 4, 5, 10, 20, 30]})
print(f"  Result: sum={result['sum']}, count={result['count']}, avg={result['average']}")

# Test 3: Read host file
print("\\nTest 3: Reading host file...")
result = callback("read_host_file", {"filename": "/etc/hostname"})
print(f"  Host hostname: {result.get('content', result.get('error', 'unknown'))}")

print("\\nAll callback tests completed!")
'''

print("\nUploading callback test script to VM...")
sandbox.upload_files([{
    "path": "/tmp/test_callbacks.py",
    "content": callback_script
}])
print("Script uploaded!")

# Run the callback test script in the VM
print("\n" + "=" * 60)
print("Running callback tests in VM...")
print("=" * 60)

result = sandbox.run_cmd("python3 /tmp/test_callbacks.py")
print("\nVM Output:")
print(result.get("output", ""))
if result.get("error"):
    print(f"Error: {result.get('error')}")

# Also run a simple command to verify basic functionality
print("\n" + "=" * 60)
print("Running basic command test...")
print("=" * 60)
result = sandbox.run_cmd("python3 -c 'a = 10; b = 25; print(f\"a = {a}, b = {b}, sum = {a + b}\")'")
print(result.get("output", ""))

# Clean up
print("\n" + "=" * 60)
print("Cleaning up...")
print("=" * 60)
try:
    sandbox.destroy()
    print("Sandbox destroyed!")
except Exception as e:
    # VM may already be destroyed by WebSocket disconnect
    print(f"Note: {e}")
    print("(VM may have been auto-destroyed when WebSocket disconnected)")

print("\nTest completed successfully!")
