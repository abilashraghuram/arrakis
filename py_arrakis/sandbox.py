"""
Arrakis Sandbox Management with RPC Callback Support
"""

import json
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin

import requests

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False


class CallbackHandler:
    """Handles RPC callbacks from the VM to the client."""
    
    def __init__(self, sandbox: "Sandbox"):
        self.sandbox = sandbox
        self.handlers: Dict[str, Callable] = {}
        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.connected = False
        self.should_stop = False
        
    def register(self, method: str, handler: Callable) -> None:
        """
        Register a callback handler for a specific method.
        
        Args:
            method: The method name that the VM will call.
            handler: A function that takes params (dict) and returns a result.
        """
        self.handlers[method] = handler
        
    def unregister(self, method: str) -> None:
        """Unregister a callback handler."""
        self.handlers.pop(method, None)
        
    def _on_message(self, ws, message: str) -> None:
        """Handle incoming callback request from the server."""
        try:
            request = json.loads(message)
            callback_id = request.get("id")
            method = request.get("method")
            params = request.get("params")
            
            # Find and execute the handler
            handler = self.handlers.get(method)
            if handler is None:
                # Send error response
                response = {
                    "id": callback_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            else:
                try:
                    result = handler(params)
                    response = {
                        "id": callback_id,
                        "result": result
                    }
                except Exception as e:
                    response = {
                        "id": callback_id,
                        "error": {
                            "code": -32000,
                            "message": str(e)
                        }
                    }
            
            # Send response back
            ws.send(json.dumps(response))
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse callback message: {e}")
        except Exception as e:
            print(f"Error handling callback: {e}")
            
    def _on_error(self, ws, error) -> None:
        """Handle WebSocket errors."""
        print(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Handle WebSocket close."""
        self.connected = False
        if not self.should_stop:
            print(f"WebSocket closed: {close_status_code} - {close_msg}")
        
    def _on_open(self, ws) -> None:
        """Handle WebSocket open."""
        self.connected = True
        print(f"WebSocket connected for sandbox: {self.sandbox.name}")
        
    def connect(self) -> None:
        """
        Connect to the WebSocket endpoint for receiving callbacks.
        This runs in a background thread.
        """
        if not HAS_WEBSOCKET:
            raise ImportError(
                "websocket-client is required for callbacks. "
                "Install with: pip install websocket-client"
            )
            
        if self.connected:
            return
            
        # Build WebSocket URL
        base_url = self.sandbox.manager.base_url
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/v1/vms/{self.sandbox.name}/ws"
        
        self.should_stop = False
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        # Run WebSocket in background thread
        self.ws_thread = threading.Thread(
            target=self.ws.run_forever,
            daemon=True
        )
        self.ws_thread.start()
        
        # Wait for connection
        timeout = 5.0
        start = time.time()
        while not self.connected and (time.time() - start) < timeout:
            time.sleep(0.1)
            
        if not self.connected:
            raise ConnectionError("Failed to connect WebSocket for callbacks")
            
    def disconnect(self) -> None:
        """Disconnect the WebSocket."""
        self.should_stop = True
        if self.ws:
            self.ws.close()
            self.ws = None
        self.connected = False


class Sandbox:
    """Represents a running sandbox (MicroVM)."""
    
    def __init__(self, manager: "SandboxManager", name: str, data: Dict[str, Any]):
        self.manager = manager
        self.name = name
        self.data = data
        self._callback_handler: Optional[CallbackHandler] = None
        
    @property
    def status(self) -> str:
        """Get the sandbox status."""
        return self.data.get("status", "UNKNOWN")
    
    @property
    def ip(self) -> Optional[str]:
        """Get the sandbox IP address."""
        return self.data.get("ip")
    
    @property
    def port_forwards(self) -> List[Dict[str, str]]:
        """Get the port forwards for this sandbox."""
        return self.data.get("portForwards", [])
    
    @property
    def callbacks(self) -> CallbackHandler:
        """
        Get the callback handler for this sandbox.
        Creates one if it doesn't exist.
        """
        if self._callback_handler is None:
            self._callback_handler = CallbackHandler(self)
        return self._callback_handler
    
    def run_cmd(self, cmd: str, blocking: bool = True) -> Dict[str, Any]:
        """
        Execute a command in the sandbox.
        
        Args:
            cmd: The command to execute.
            blocking: Whether to wait for the command to complete.
            
        Returns:
            Dict with 'output' and optionally 'error' keys.
        """
        url = f"{self.manager.base_url}/v1/vms/{self.name}/cmd"
        payload = {
            "cmd": cmd,
            "blocking": blocking
        }
        
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()
    
    def upload_files(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Upload files to the sandbox.
        
        Args:
            files: List of dicts with 'path' and 'content' keys.
            
        Returns:
            Response dict.
        """
        url = f"{self.manager.base_url}/v1/vms/{self.name}/files"
        payload = {"files": files}
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def download_files(self, paths: List[str]) -> Dict[str, Any]:
        """
        Download files from the sandbox.
        
        Args:
            paths: List of file paths to download.
            
        Returns:
            Dict with 'files' list containing path, content, and error.
        """
        url = f"{self.manager.base_url}/v1/vms/{self.name}/files"
        params = {"paths": ",".join(paths)}
        
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def snapshot(self, snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a snapshot of the sandbox.
        
        Args:
            snapshot_id: Optional custom snapshot ID.
            
        Returns:
            Dict with 'snapshotId'.
        """
        url = f"{self.manager.base_url}/v1/vms/{self.name}/snapshots"
        payload = {}
        if snapshot_id:
            payload["snapshotId"] = snapshot_id
            
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    
    def pause(self) -> Dict[str, Any]:
        """Pause the sandbox."""
        url = f"{self.manager.base_url}/v1/vms/{self.name}"
        payload = {"status": "paused"}
        
        response = requests.patch(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def resume(self) -> Dict[str, Any]:
        """Resume a paused sandbox."""
        url = f"{self.manager.base_url}/v1/vms/{self.name}"
        payload = {"status": "resume"}
        
        response = requests.patch(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def stop(self) -> Dict[str, Any]:
        """Stop the sandbox."""
        url = f"{self.manager.base_url}/v1/vms/{self.name}"
        payload = {"status": "stopped"}
        
        response = requests.patch(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def destroy(self) -> Dict[str, Any]:
        """Destroy the sandbox."""
        # Disconnect callbacks first
        if self._callback_handler:
            self._callback_handler.disconnect()
            
        url = f"{self.manager.base_url}/v1/vms/{self.name}"
        
        response = requests.delete(url, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def refresh(self) -> None:
        """Refresh the sandbox data from the server."""
        url = f"{self.manager.base_url}/v1/vms/{self.name}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        self.data = response.json()
        
    def enable_callbacks(self) -> "Sandbox":
        """
        Enable RPC callbacks from this sandbox.
        Connects to the WebSocket endpoint.
        
        Returns:
            self for chaining.
        """
        self.callbacks.connect()
        return self
    
    def on_callback(self, method: str) -> Callable:
        """
        Decorator to register a callback handler.
        
        Usage:
            @sandbox.on_callback("get_time")
            def handle_get_time(params):
                return {"time": time.time()}
        """
        def decorator(func: Callable) -> Callable:
            self.callbacks.register(method, func)
            return func
        return decorator
    
    def register_callback(self, method: str, handler: Callable) -> "Sandbox":
        """
        Register a callback handler.
        
        Args:
            method: The method name.
            handler: The handler function.
            
        Returns:
            self for chaining.
        """
        self.callbacks.register(method, handler)
        return self


class SandboxManager:
    """Manages Arrakis sandboxes (MicroVMs)."""
    
    def __init__(self, base_url: str):
        """
        Initialize the sandbox manager.
        
        Args:
            base_url: The Arrakis server URL (e.g., "http://localhost:7000")
        """
        self.base_url = base_url.rstrip("/")
        
    def health_check(self) -> Dict[str, Any]:
        """Check if the server is healthy."""
        url = f"{self.base_url}/v1/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def list_all(self) -> List[Sandbox]:
        """
        List all sandboxes.
        
        Returns:
            List of Sandbox objects.
        """
        url = f"{self.base_url}/v1/vms"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        sandboxes = []
        for vm_data in data.get("vms", []):
            name = vm_data.get("vmName")
            if name:
                sandboxes.append(Sandbox(self, name, vm_data))
                
        return sandboxes
    
    def get_sandbox(self, name: str) -> Optional[Sandbox]:
        """
        Get a specific sandbox by name.
        
        Args:
            name: The sandbox name.
            
        Returns:
            Sandbox object or None if not found.
        """
        url = f"{self.base_url}/v1/vms/{name}"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        
        data = response.json()
        return Sandbox(self, name, data)
    
    def start_sandbox(
        self,
        name: str,
        snapshot_id: Optional[str] = None,
        kernel: Optional[str] = None,
        rootfs: Optional[str] = None,
        initramfs: Optional[str] = None,
        entry_point: Optional[str] = None
    ) -> Sandbox:
        """
        Start a new sandbox or restore from a snapshot.
        
        Args:
            name: The sandbox name.
            snapshot_id: Optional snapshot ID to restore from.
            kernel: Optional custom kernel path.
            rootfs: Optional custom rootfs path.
            initramfs: Optional custom initramfs path.
            entry_point: Optional entry point command.
            
        Returns:
            Sandbox object.
        """
        url = f"{self.base_url}/v1/vms"
        payload = {"vmName": name}
        
        if snapshot_id:
            payload["snapshotId"] = snapshot_id
        if kernel:
            payload["kernel"] = kernel
        if rootfs:
            payload["rootfs"] = rootfs
        if initramfs:
            payload["initramfs"] = initramfs
        if entry_point:
            payload["entryPoint"] = entry_point
            
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        
        data = response.json()
        return Sandbox(self, name, data)
    
    def destroy_sandbox(self, name: str) -> Dict[str, Any]:
        """
        Destroy a sandbox by name.
        
        Args:
            name: The sandbox name.
            
        Returns:
            Response dict.
        """
        url = f"{self.base_url}/v1/vms/{name}"
        
        response = requests.delete(url, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def destroy_all(self) -> Dict[str, Any]:
        """
        Destroy all sandboxes.
        
        Returns:
            Response dict.
        """
        url = f"{self.base_url}/v1/vms"
        
        response = requests.delete(url, timeout=120)
        response.raise_for_status()
        return response.json()

