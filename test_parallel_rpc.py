#!/usr/bin/env python3
"""
Arrakis Parallel RPC Callback Demo

This script demonstrates multiple MicroVMs running concurrently, each executing
Python code that makes RPC callbacks to functions on your local machine.

Features:
- Spawns N MicroVMs in parallel
- Each VM runs different tasks via callbacks
- Shows concurrent callback handling from multiple VMs
- Demonstrates vmName-based routing working correctly

Usage:
    1. Start ngrok: ngrok http 8080
    2. Update NGROK_URL below with your ngrok URL
    3. Run: python test_parallel_rpc.py

Requirements:
    pip install requests
"""

import json
import threading
import time
import requests
import concurrent.futures
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Dict, List
from dataclasses import dataclass

# =============================================================================
# Configuration - UPDATE THESE
# =============================================================================
ARRAKIS_SERVER_URL = "http://35.212.221.66:7000"  # Your Arrakis devbox
NGROK_URL = "https://7202f9750f8f.ngrok-free.app"  # Update with your ngrok URL
CALLBACK_PORT = 8080
NUM_VMS = 3  # Number of parallel VMs to spawn (limited by devbox memory ~3.6GB, each VM needs ~1GB)

# =============================================================================
# Local Functions - These run on YOUR machine, callable from VMs
# =============================================================================

def get_weather(city: str) -> dict:
    """Get weather for a city (simulated)."""
    weather_data = {
        "San Francisco": {"temp": 65, "condition": "Foggy", "humidity": 80},
        "New York": {"temp": 45, "condition": "Cloudy", "humidity": 60},
        "Miami": {"temp": 82, "condition": "Sunny", "humidity": 75},
        "Seattle": {"temp": 55, "condition": "Rainy", "humidity": 90},
        "Denver": {"temp": 40, "condition": "Snowy", "humidity": 30},
    }
    return weather_data.get(city, {"temp": 70, "condition": "Unknown", "humidity": 50})


def calculate_fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def process_data(data: list, operation: str) -> dict:
    """Process a list of numbers with various operations."""
    if not data:
        return {"error": "Empty data"}

    if operation == "sum":
        return {"result": sum(data), "operation": "sum"}
    elif operation == "average":
        return {"result": sum(data) / len(data), "operation": "average"}
    elif operation == "max":
        return {"result": max(data), "operation": "max"}
    elif operation == "min":
        return {"result": min(data), "operation": "min"}
    elif operation == "sorted":
        return {"result": sorted(data), "operation": "sorted"}
    else:
        return {"error": f"Unknown operation: {operation}"}


def fetch_user_data(user_id: int) -> dict:
    """Fetch user data from mock database."""
    users = {
        1: {"name": "Alice", "email": "alice@example.com", "role": "Admin"},
        2: {"name": "Bob", "email": "bob@example.com", "role": "Developer"},
        3: {"name": "Charlie", "email": "charlie@example.com", "role": "Designer"},
        4: {"name": "Diana", "email": "diana@example.com", "role": "Manager"},
        5: {"name": "Eve", "email": "eve@example.com", "role": "Analyst"},
    }
    return users.get(user_id, {"error": f"User {user_id} not found"})


def run_computation(task_type: str, complexity: int) -> dict:
    """Simulate running a computation task."""
    # Simulate some work
    result = 0
    for i in range(complexity * 1000):
        result += i

    return {
        "task_type": task_type,
        "complexity": complexity,
        "result": result,
        "status": "completed"
    }


# =============================================================================
# Function Registry
# =============================================================================

FUNCTION_REGISTRY: Dict[str, Callable] = {
    "get_weather": get_weather,
    "calculate_fibonacci": calculate_fibonacci,
    "process_data": process_data,
    "fetch_user_data": fetch_user_data,
    "run_computation": run_computation,
}

# Track callbacks per VM for statistics
callback_stats: Dict[str, int] = {}
callback_lock = threading.Lock()


# =============================================================================
# Callback Server
# =============================================================================

class ParallelRPCHandler(BaseHTTPRequestHandler):
    """HTTP handler that routes callbacks from multiple VMs to local functions."""

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body)
            method = request.get('method', '')
            params = request.get('params', {})
            vm_name = request.get('vmName', 'unknown')

            # Track stats
            with callback_lock:
                callback_stats[vm_name] = callback_stats.get(vm_name, 0) + 1

            print(f"  📥 [{vm_name}] → {method}({params})")

            # Invoke the function
            if method in FUNCTION_REGISTRY:
                func = FUNCTION_REGISTRY[method]
                if isinstance(params, dict):
                    result = func(**params)
                elif isinstance(params, list):
                    result = func(*params)
                else:
                    result = func(params) if params else func()

                response = {"result": result}
            else:
                response = {"error": f"Unknown method: {method}"}

            response_body = json.dumps(response).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response_body))
            self.end_headers()
            self.wfile.write(response_body)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            response = {"error": str(e)}
            response_body = json.dumps(response).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response_body))
            self.end_headers()
            self.wfile.write(response_body)

    def log_message(self, format, *args):
        pass


def start_callback_server():
    server = HTTPServer(("0.0.0.0", CALLBACK_PORT), ParallelRPCHandler)
    print(f"🚀 Parallel RPC server started on port {CALLBACK_PORT}")
    server.serve_forever()


# =============================================================================
# Python code templates for each VM (different tasks per VM)
# =============================================================================

def get_vm_code(vm_name: str, vm_index: int) -> str:
    """Generate unique Python code for each VM based on its index."""

    base_code = f'''
import json
import urllib.request
import urllib.error

CALLBACK_URL = "http://10.20.1.1:7000/v1/internal/callback"
VM_NAME = "{vm_name}"

def call_host(method: str, **kwargs):
    payload = {{"vmName": VM_NAME, "method": method, "params": kwargs}}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(CALLBACK_URL, data=data, headers={{"Content-Type": "application/json"}})
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        if "error" in result:
            raise Exception(result["error"])
        return result.get("result")

print(f"[{{VM_NAME}}] Starting tasks...")
'''

    # Different tasks for each VM
    if vm_index % 3 == 0:
        # VM does weather lookups
        task_code = '''
cities = ["San Francisco", "New York", "Miami", "Seattle", "Denver"]
print(f"[{VM_NAME}] Task: Weather lookups for {len(cities)} cities")
for city in cities:
    weather = call_host("get_weather", city=city)
    print(f"  {city}: {weather['temp']}°F, {weather['condition']}")
print(f"[{VM_NAME}] Completed weather lookups!")
'''
    elif vm_index % 3 == 1:
        # VM does Fibonacci calculations
        task_code = '''
fib_numbers = [10, 20, 30, 40, 50]
print(f"[{VM_NAME}] Task: Fibonacci calculations")
for n in fib_numbers:
    result = call_host("calculate_fibonacci", n=n)
    print(f"  Fib({n}) = {result}")
print(f"[{VM_NAME}] Completed Fibonacci calculations!")
'''
    else:
        # VM does data processing
        task_code = '''
data = [42, 17, 89, 3, 56, 91, 23, 8, 67, 45]
operations = ["sum", "average", "max", "min", "sorted"]
print(f"[{VM_NAME}] Task: Data processing with {len(operations)} operations")
for op in operations:
    result = call_host("process_data", data=data, operation=op)
    print(f"  {op}: {result['result']}")
print(f"[{VM_NAME}] Completed data processing!")
'''

    # Add user lookups for all VMs
    user_code = f'''
# All VMs also fetch user data
user_ids = [{vm_index + 1}, {(vm_index + 2) % 5 + 1}]
print(f"[{{VM_NAME}}] Fetching user data...")
for uid in user_ids:
    user = call_host("fetch_user_data", user_id=uid)
    if "error" not in user:
        print(f"  User {{uid}}: {{user['name']}} ({{user['role']}})")

print(f"[{{VM_NAME}}] All tasks completed!")
'''

    return base_code + task_code + user_code


# =============================================================================
# VM Management
# =============================================================================

@dataclass
class VMResult:
    name: str
    success: bool
    output: str
    error: str = ""
    duration: float = 0.0


def start_vm(vm_name: str) -> dict:
    """Start a single VM with callback URL."""
    start_request = {
        "vmName": vm_name,
        "callbackUrl": NGROK_URL
    }
    resp = requests.post(
        f"{ARRAKIS_SERVER_URL}/v1/vms",
        json=start_request,
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()


def run_code_in_vm(vm_name: str, code: str) -> dict:
    """Execute Python code in a VM."""
    escaped_code = code.replace("'", "'\"'\"'")
    cmd = f"python3 -c '{escaped_code}'"

    resp = requests.post(
        f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}/cmd",
        json={"cmd": cmd},
        timeout=120
    )
    return resp.json()


def destroy_vm(vm_name: str):
    """Destroy a VM."""
    requests.delete(f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}", timeout=30)


def run_vm_task(vm_index: int) -> VMResult:
    """Complete lifecycle for one VM: start, run code, destroy."""
    vm_name = f"parallel-vm-{vm_index}"
    start_time = time.time()

    try:
        # Start VM
        print(f"  🚀 Starting {vm_name}...")
        vm_info = start_vm(vm_name)
        print(f"  ✅ {vm_name} started (IP: {vm_info.get('ip')})")

        # Wait for VM to be ready
        time.sleep(5)

        # Generate and run code
        code = get_vm_code(vm_name, vm_index)
        print(f"  🐍 Running code in {vm_name}...")
        result = run_code_in_vm(vm_name, code)

        duration = time.time() - start_time

        if result.get('error'):
            return VMResult(
                name=vm_name,
                success=False,
                output="",
                error=result['error'],
                duration=duration
            )
        else:
            return VMResult(
                name=vm_name,
                success=True,
                output=result.get('output', ''),
                duration=duration
            )

    except Exception as e:
        duration = time.time() - start_time
        return VMResult(
            name=vm_name,
            success=False,
            output="",
            error=str(e),
            duration=duration
        )
    finally:
        # Always try to cleanup
        try:
            destroy_vm(vm_name)
            print(f"  🧹 {vm_name} destroyed")
        except:
            pass


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Arrakis Parallel RPC Callback Demo")
    print("=" * 70)
    print(f"\nSpawning {NUM_VMS} MicroVMs in parallel, each running Python code")
    print(f"that makes callbacks to functions on your local machine.\n")

    # Start callback server
    print("📡 Starting callback server...")
    server_thread = threading.Thread(target=start_callback_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    print(f"   Callback URL: {NGROK_URL}")
    print(f"   Arrakis Server: {ARRAKIS_SERVER_URL}")
    print(f"   Number of VMs: {NUM_VMS}")

    print("\n" + "=" * 70)
    print("Starting VMs and executing tasks...")
    print("=" * 70 + "\n")

    start_time = time.time()
    results: List[VMResult] = []

    # Run VMs in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_VMS) as executor:
        futures = {executor.submit(run_vm_task, i): i for i in range(NUM_VMS)}

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    total_duration = time.time() - start_time

    # Print results
    print("\n" + "=" * 70)
    print("Results from all VMs")
    print("=" * 70)

    for result in sorted(results, key=lambda r: r.name):
        print(f"\n📦 {result.name} (Duration: {result.duration:.2f}s)")
        print("-" * 50)
        if result.success:
            print(result.output)
        else:
            print(f"❌ Error: {result.error}")

    # Print statistics
    print("\n" + "=" * 70)
    print("Callback Statistics")
    print("=" * 70)

    total_callbacks = sum(callback_stats.values())
    print(f"\n📊 Total callbacks received: {total_callbacks}")
    print(f"⏱️  Total execution time: {total_duration:.2f}s")
    print(f"\nCallbacks per VM:")
    for vm_name, count in sorted(callback_stats.items()):
        print(f"  {vm_name}: {count} callbacks")

    successful = sum(1 for r in results if r.success)
    print(f"\n✅ Successful VMs: {successful}/{NUM_VMS}")

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
