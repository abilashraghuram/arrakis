#!/usr/bin/env python3
"""
Test script demonstrating HTTP callbacks from Arrakis MicroVM to an external callback server.

This test:
1. Starts a simple HTTP callback server
2. Creates a MicroVM with callbackUrl pointing to our server
3. Executes code in the VM that triggers CALLBACK commands
4. Demonstrates the callback being received and responded to

Usage:
    python test_arrakis_callback.py

Requirements:
    pip install py-arrakis
"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from py_arrakis import SandboxManager

# Configuration
ARRAKIS_SERVER_URL = "http://35.212.221.66:7000"
CALLBACK_SERVER_HOST = "0.0.0.0"
CALLBACK_SERVER_PORT = 8080

# Store received callbacks for verification
received_callbacks = []


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving callbacks from MicroVMs."""

    def do_POST(self):
        """Handle POST requests (callbacks from VM)."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body)
            print(f"\n📥 Received callback from VM:")
            print(f"   VM Name: {request.get('vmName')}")
            print(f"   Method: {request.get('method')}")
            print(f"   Params: {request.get('params')}")

            # Store for verification
            received_callbacks.append(request)

            # Process the callback based on method
            result = self.process_callback(request)

            # Send response
            response = {"result": result}
            response_body = json.dumps(response).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response_body))
            self.end_headers()
            self.wfile.write(response_body)

            print(f"   ✅ Responded with: {result}")

        except Exception as e:
            print(f"   ❌ Error processing callback: {e}")
            error_response = {"error": str(e)}
            response_body = json.dumps(error_response).encode('utf-8')

            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response_body))
            self.end_headers()
            self.wfile.write(response_body)

    def process_callback(self, request):
        """Process callback and return result based on method."""
        method = request.get('method', '')
        params = request.get('params', {})

        # Simulate different tool implementations
        if method == 'get_appliance_info':
            return {
                "appliances": [
                    {"name": "branch-01", "status": "online", "cpu": 45},
                    {"name": "branch-02", "status": "online", "cpu": 72},
                    {"name": "branch-03", "status": "offline", "cpu": 0},
                ]
            }
        elif method == 'get_system_status':
            return {
                "status": "healthy",
                "uptime": "5 days",
                "version": "1.2.3"
            }
        elif method == 'add_numbers':
            a = params.get('a', 0) if isinstance(params, dict) else 0
            b = params.get('b', 0) if isinstance(params, dict) else 0
            return {"sum": a + b}
        elif method == 'echo':
            return {"echo": params}
        else:
            return {"message": f"Unknown method: {method}"}

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


def start_callback_server():
    """Start the HTTP callback server in a background thread."""
    server = HTTPServer((CALLBACK_SERVER_HOST, CALLBACK_SERVER_PORT), CallbackHandler)
    print(f"🚀 Callback server started on {CALLBACK_SERVER_HOST}:{CALLBACK_SERVER_PORT}")
    server.serve_forever()


def get_callback_url():
    """
    Get the callback URL that the VM should use.

    Note: In a real deployment, this would be the external IP/hostname
    that the VM can reach. For local testing, you may need to use
    your machine's IP address that's reachable from the VM network.
    """
    # Using ngrok to expose local callback server to the internet
    # The VM on the remote devbox can reach this URL
    return "https://e46e12e1d790.ngrok.app"


def main():
    print("=" * 60)
    print("Arrakis HTTP Callback Test")
    print("=" * 60)

    # Start callback server in background
    print("\n📡 Starting callback server...")
    server_thread = threading.Thread(target=start_callback_server, daemon=True)
    server_thread.start()
    time.sleep(1)  # Wait for server to start

    callback_url = get_callback_url()
    print(f"   Callback URL: {callback_url}")

    # Initialize Arrakis sandbox manager
    print(f"\n🔧 Connecting to Arrakis at {ARRAKIS_SERVER_URL}...")
    manager = SandboxManager(ARRAKIS_SERVER_URL)

    # Start VM with callback URL
    # Note: This requires the modified Arrakis that supports callbackUrl parameter
    print("\n🖥️  Starting sandbox with callback URL...")

    # The py-arrakis SDK needs to be updated to support callbackUrl,
    # or you can make a direct HTTP request:
    import requests

    start_request = {
        "vmName": "callback-test-sandbox",
        "callbackUrl": callback_url
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
        print("\n⚠️  Note: Make sure Arrakis is running with the HTTP callback patches applied.")
        return

    vm_name = vm_info.get('vmName')

    try:
        # Wait for VM to be ready
        print("\n⏳ Waiting for VM to be ready...")
        time.sleep(5)

        # Test 1: Simple callback
        print("\n" + "=" * 60)
        print("Test 1: Simple echo callback")
        print("=" * 60)

        # Execute a command that triggers a CALLBACK
        # The vsockserver inside the VM listens on VSOCK port 4032
        # CID 2 is the host in virtio-vsock
        callback_cmd = '''
echo "CALLBACK echo {\\"message\\": \\"Hello from VM\\"}" | socat - VSOCK-CONNECT:2:4032 2>/dev/null || echo "Callback failed - socat/vsock not available"
'''
        result = requests.post(
            f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}/cmd",
            json={"cmd": callback_cmd}
        )
        print(f"   Command result: {result.json()}")

        # Test 2: Callback with tool simulation
        print("\n" + "=" * 60)
        print("Test 2: Simulated MCP tool callback")
        print("=" * 60)

        callback_cmd = '''
echo "CALLBACK get_appliance_info {}" | socat - VSOCK-CONNECT:2:4032 2>/dev/null || echo "Callback failed - socat/vsock not available"
'''
        result = requests.post(
            f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}/cmd",
            json={"cmd": callback_cmd}
        )
        print(f"   Command result: {result.json()}")

        # Test 3: Callback with parameters
        print("\n" + "=" * 60)
        print("Test 3: Callback with parameters")
        print("=" * 60)

        callback_cmd = '''
echo "CALLBACK add_numbers {\\"a\\": 10, \\"b\\": 25}" | socat - VSOCK-CONNECT:2:4032 2>/dev/null || echo "Callback failed - socat/vsock not available"
'''
        result = requests.post(
            f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}/cmd",
            json={"cmd": callback_cmd}
        )
        print(f"   Command result: {result.json()}")

        # Wait a moment for callbacks to be processed
        time.sleep(2)

        # Summary
        print("\n" + "=" * 60)
        print("Callback Summary")
        print("=" * 60)
        print(f"Total callbacks received: {len(received_callbacks)}")
        for i, cb in enumerate(received_callbacks, 1):
            print(f"  {i}. Method: {cb.get('method')}, VM: {cb.get('vmName')}")

    finally:
        # Cleanup: Destroy the VM
        print("\n🧹 Cleaning up...")
        try:
            resp = requests.delete(f"{ARRAKIS_SERVER_URL}/v1/vms/{vm_name}")
            print(f"   ✅ Sandbox destroyed")
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
