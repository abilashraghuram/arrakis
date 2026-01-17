#!/usr/bin/env python3
"""
Arrakis RPC Callback Demo

This script demonstrates how Python code running inside a MicroVM can invoke
functions defined on your local machine via the HTTP callback mechanism.

The pattern:
1. Define functions locally that you want to expose to the VM
2. Register them with a callback server
3. Run Python code in the VM that calls these functions via HTTP
4. The VM code gets back the results as if calling local functions

Usage:
    1. Start ngrok: ngrok http 8080
    2. Update NGROK_URL below with your ngrok URL
    3. Run: python test_callback_rpc.py

Requirements:
    pip install requests
"""

import json
import threading
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Dict

# =============================================================================
# Configuration - UPDATE THESE
# =============================================================================
ARRAKIS_SERVER_URL = "http://35.212.221.66:7000"  # Your Arrakis devbox
NGROK_URL = "https://7202f9750f8f.ngrok-free.app"  # Update with your ngrok URL
CALLBACK_PORT = 8080

# =============================================================================
# Local Functions - These run on YOUR machine, callable from the VM
# =============================================================================

def get_weather(city: str) -> dict:
    """Get weather for a city (simulated)."""
    weather_data = {
        "San Francisco": {"temp": 65, "condition": "Foggy", "humidity": 80},
        "New York": {"temp": 45, "condition": "Cloudy", "humidity": 60},
        "Miami": {"temp": 82, "condition": "Sunny", "humidity": 75},
    }
    return weather_data.get(city, {"temp": 70, "condition": "Unknown", "humidity": 50})


def calculate_factorial(n: int) -> int:
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def search_database(query: str, limit: int = 5) -> list:
    """Search a mock database (simulated)."""
    mock_data = [
        {"id": 1, "name": "Alice", "role": "Engineer"},
        {"id": 2, "name": "Bob", "role": "Designer"},
        {"id": 3, "name": "Charlie", "role": "Manager"},
        {"id": 4, "name": "Diana", "role": "Engineer"},
        {"id": 5, "name": "Eve", "role": "Analyst"},
    ]
    results = [item for item in mock_data if query.lower() in item["name"].lower() or query.lower() in item["role"].lower()]
    return results[:limit]


def execute_privileged_operation(operation: str, params: dict) -> dict:
    """
    Execute an operation that requires local machine access.
    This simulates operations that can't run in a sandbox.
    """
    if operation == "read_config":
        # Simulated config reading
        return {"database_url": "postgres://localhost:5432/mydb", "api_key": "sk-xxx-redacted"}
    elif operation == "check_license":
        return {"valid": True, "expires": "2025-12-31", "tier": "enterprise"}
    elif operation == "get_credentials":
        return {"username": "service_account", "token": "Bearer xxx-redacted"}
    else:
        return {"error": f"Unknown operation: {operation}"}


# =============================================================================
# Function Registry - Maps method names to local functions
# =============================================================================

FUNCTION_REGISTRY: Dict[str, Callable] = {
    "get_weather": get_weather,
    "calculate_factorial": calculate_factorial,
    "search_database": search_database,
    "execute_privileged_operation": execute_privileged_operation,
}


# =============================================================================
# Callback Server - Receives calls from VM and invokes local functions
# =============================================================================

class RPCCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that routes callbacks to local functions."""

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body)
            method = request.get('method', '')
            params = request.get('params', {})
            vm_name = request.get('vmName', 'unknown')

            print(f"\n📥 RPC Call from VM '{vm_name}':")
            print(f"   Method: {method}")
            print(f"   Params: {params}")

            # Look up and invoke the local function
            if method in FUNCTION_REGISTRY:
                func = FUNCTION_REGISTRY[method]

                # Call the function with params
                if isinstance(params, dict):
                    result = func(**params)
                elif isinstance(params, list):
                    result = func(*params)
                else:
                    result = func(params) if params else func()

                print(f"   ✅ Result: {result}")
                response = {"result": result}
            else:
                error_msg = f"Unknown method: {method}. Available: {list(FUNCTION_REGISTRY.keys())}"
                print(f"   ❌ {error_msg}")
                response = {"error": error_msg}

            response_body = json.dumps(response).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response_body))
            self.end_headers()
            self.wfile.write(response_body)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            response = {"error": str(e)}
            response_body = json.dumps(response).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response_body))
            self.end_headers()
            self.wfile.write(response_body)

    def log_message(self, format, *args):
        pass  # Suppress default logging


def start_callback_server():
    server = HTTPServer(("0.0.0.0", CALLBACK_PORT), RPCCallbackHandler)
    print(f"🚀 RPC Callback server started on port {CALLBACK_PORT}")
    server.serve_forever()


# =============================================================================
# Python code that will run INSIDE the MicroVM
# =============================================================================

VM_PYTHON_CODE = '''
import json
import urllib.request
import urllib.error

# Configuration - the VM calls back to the Arrakis restserver
CALLBACK_URL = "http://10.20.1.1:7000/v1/internal/callback"
VM_NAME = "rpc-test-sandbox"

def call_host_function(method: str, **kwargs):
    """
    Call a function on the host machine via HTTP callback.
    This is the magic - code in the VM can invoke functions on your local machine!
    """
    payload = {
        "vmName": VM_NAME,
        "method": method,
        "params": kwargs
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        CALLBACK_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if "error" in result:
                raise Exception(result["error"])
            return result.get("result")
    except urllib.error.URLError as e:
        raise Exception(f"Callback failed: {e}")

# =============================================================================
# Now let's use these host functions from inside the VM!
# =============================================================================

print("=" * 60)
print("Running Python code INSIDE the MicroVM")
print("Calling functions on the HOST machine via callbacks")
print("=" * 60)

# Test 1: Get weather
print("\\n📍 Test 1: Getting weather for San Francisco...")
weather = call_host_function("get_weather", city="San Francisco")
print(f"   Weather: {weather}")

# Test 2: Calculate factorial
print("\\n🔢 Test 2: Calculating factorial of 10...")
factorial_result = call_host_function("calculate_factorial", n=10)
print(f"   10! = {factorial_result}")

# Test 3: Search database
print("\\n🔍 Test 3: Searching database for 'Engineer'...")
search_results = call_host_function("search_database", query="Engineer", limit=3)
print(f"   Found: {search_results}")

# Test 4: Privileged operation (can't do this in sandbox!)
print("\\n🔐 Test 4: Reading config from host (privileged operation)...")
config = call_host_function("execute_privileged_operation", operation="read_config", params={})
print(f"   Config: {config}")

print("\\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
'''


# =============================================================================
# Main Test Runner
# =============================================================================

def main():
    print("=" * 60)
    print("Arrakis RPC Callback Demo")
    print("=" * 60)
    print(f"\nThis demo shows how code in a MicroVM can call")
    print(f"functions defined on your local machine.\n")

    # Start callback server
    print("📡 Starting RPC callback server...")
    server_thread = threading.Thread(target=start_callback_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    print(f"   Callback URL: {NGROK_URL}")
    print(f"   Arrakis Server: {ARRAKIS_SERVER_URL}")

    # Start VM with callback URL
    print("\n🖥️  Starting MicroVM sandbox...")

    start_request = {
        "vmName": "rpc-test-sandbox",
        "callbackUrl": NGROK_URL
    }

    try:
        resp = requests.post(
            f"{ARRAKIS_SERVER_URL}/v1/vms",
            json=start_request,
            timeout=120
        )
        resp.raise_for_status()
        vm_info = resp.json()
        print(f"   ✅ Sandbox started: {vm_info.get('vmName')}")
        print(f"   IP: {vm_info.get('ip')}")
    except Exception as e:
        print(f"   ❌ Failed to start sandbox: {e}")
        return

    vm_name = vm_info.get('vmName')

    try:
        print("\n⏳ Waiting for VM to be ready...")
        time.sleep(5)

        # Run Python code inside the VM
        print("\n🐍 Executing Python code inside the MicroVM...")
        print("-" * 60)

        # Create a command that runs our Python code
        # We use python3 -c to execute the code string
        escaped_code = VM_PYTHON_CODE.replace("'", "'\"'\"'")  # Escape single quotes for shell
        cmd = f"python3 -c '{escaped_code}'"

        result = requests.post(
            f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}/cmd",
            json={"cmd": cmd},
            timeout=60
        )

        response = result.json()
        if response.get('error'):
            print(f"❌ Error: {response['error']}")
        else:
            print("\n📤 Output from VM:")
            print("-" * 60)
            print(response.get('output', ''))

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        try:
            requests.delete(f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}")
            print("   ✅ Sandbox destroyed")
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
