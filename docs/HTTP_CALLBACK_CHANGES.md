# HTTP Callback Changes for Arrakis

This document describes the changes made to Arrakis to support direct HTTP callbacks from MicroVMs to external services (e.g., MCP servers), bypassing the WebSocket-based callback system.

## Summary of Changes

| File | Change |
|------|--------|
| `api/server-api.yaml` | Added `callbackUrl` field to `StartVMRequest` schema |
| `pkg/server/server.go` | Updated `getKernelCmdLine()` to accept and include callback URL in kernel parameters |
| `pkg/server/server.go` | Updated `createVM()` signature to pass callback URL through |
| `pkg/server/server.go` | Updated `StartVM()` to extract callback URL from request |
| `cmd/vsockserver/main.go` | Added parsing of `callback_url` from kernel command line |
| `cmd/vsockserver/main.go` | Updated `handleCallback()` to POST directly to callback URL when configured |

**New Files:**
- `test_arrakis_callback.py` - Test script demonstrating HTTP callbacks
- `docs/HTTP_CALLBACK_CHANGES.md` - This documentation

## Overview

Previously, Arrakis used a WebSocket-based callback system where:
1. MicroVM sends CALLBACK command via vsock to Arrakis host
2. Arrakis host routes callback via WebSocket to connected client
3. Client responds via WebSocket
4. Response is returned to MicroVM

The new HTTP callback option allows:
1. MicroVM sends CALLBACK command via vsock
2. vsockserver makes direct HTTP POST to configured callback URL
3. External service responds with HTTP response
4. Response is returned to MicroVM

This simplifies integration with external services that prefer stateless HTTP over WebSocket connections.

## Files Modified

### 1. `api/server-api.yaml`

**Change:** Added `callbackUrl` field to `StartVMRequest` schema.

```yaml
StartVMRequest:
  type: object
  properties:
    # ... existing fields ...
    callbackUrl:
      type: string
      description: Optional URL for the VM to send HTTP callbacks to. If provided, the VM will call this URL directly instead of going through the Arrakis WebSocket callback system.
```

### 2. `pkg/server/server.go`

**Changes:**

#### a) Updated `getKernelCmdLine` function signature

```go
// Before
func getKernelCmdLine(gatewayIP string, guestIP string, vmName string) string

// After
func getKernelCmdLine(gatewayIP string, guestIP string, vmName string, callbackUrl string) string
```

The function now appends `callback_url` to the kernel command line if provided:
```
console=ttyS0 gateway_ip="10.20.1.1" guest_ip="10.20.1.2" vm_name="my-sandbox" callback_url="http://mcp-server:8080/callback"
```

#### b) Updated `createVM` function signature

```go
// Before
func (s *Server) createVM(ctx, vmName, kernelPath, initramfsPath, rootfsPath string, forRestore bool) (*vm, error)

// After
func (s *Server) createVM(ctx, vmName, kernelPath, initramfsPath, rootfsPath string, forRestore bool, callbackUrl string) (*vm, error)
```

#### c) Updated `StartVM` to pass callback URL

The `StartVM` function now extracts `callbackUrl` from the request and passes it to `createVM`.

### 3. `cmd/vsockserver/main.go`

**Changes:**

#### a) Added `callbackURL` global variable

```go
var (
    gatewayIP   string
    vmName      string
    callbackURL string // NEW: Optional direct callback URL
)
```

#### b) Updated `parseKernelCmdLine` to extract callback URL

```go
if strings.HasPrefix(part, "callback_url=") {
    callbackURL = strings.Trim(strings.TrimPrefix(part, "callback_url="), "\"")
}
```

#### c) Updated `handleCallback` to use callback URL when available

```go
func handleCallback(method string, paramsJSON string) (string, error) {
    var url string

    if callbackURL != "" {
        // Direct HTTP callback to external URL (e.g., MCP server)
        url = callbackURL
    } else {
        // Fallback to Arrakis host callback (original behavior)
        hostIP := gatewayIP
        if idx := strings.Index(hostIP, "/"); idx != -1 {
            hostIP = hostIP[:idx]
        }
        url = fmt.Sprintf("http://%s:7000/v1/internal/callback", hostIP)
    }
    
    // ... make HTTP request to url ...
}
```

## Architecture Comparison

### Before: WebSocket-based Callbacks

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   MicroVM    │     │   Arrakis Host   │     │   MCP Server     │
│              │     │                  │     │                  │
│  CALLBACK ───┼────►│ /v1/internal/    │     │                  │
│  (vsock)     │     │ callback         │     │                  │
│              │     │       │          │     │                  │
│              │     │       ▼          │     │                  │
│              │     │ SessionManager   │     │                  │
│              │     │       │          │     │                  │
│              │     │       │ WebSocket│     │                  │
│              │     │       └──────────┼────►│ WS Client        │
│              │     │                  │     │                  │
│  ◄───────────┼─────┼──────────────────┼─────┼─ Response        │
│              │     │                  │     │                  │
└──────────────┘     └──────────────────┘     └──────────────────┘
```

### After: Direct HTTP Callbacks (when callbackUrl is set)

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   MicroVM    │     │   Arrakis Host   │     │   MCP Server     │
│              │     │                  │     │                  │
│  CALLBACK ───┼─────┼──────────────────┼────►│ /callback        │
│  (HTTP POST) │     │   (bypassed)     │     │ endpoint         │
│              │     │                  │     │                  │
│  ◄───────────┼─────┼──────────────────┼─────┼─ HTTP Response   │
│              │     │                  │     │                  │
└──────────────┘     └──────────────────┘     └──────────────────┘
```

## Usage

### Starting a VM with HTTP Callbacks

```bash
curl -X POST http://arrakis-server:7000/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "vmName": "my-sandbox",
    "callbackUrl": "http://mcp-server:8080/callback"
  }'
```

### Callback Request Format

The MicroVM sends callbacks in this format:

```json
{
  "vmName": "my-sandbox",
  "method": "get_appliance_info",
  "params": {"org": "MyOrg"}
}
```

### Expected Response Format

Your callback endpoint should respond with:

```json
{
  "result": {
    "appliances": [...]
  }
}
```

Or on error:

```json
{
  "error": "Error message here"
}
```

### Triggering Callbacks from VM Code

Inside the MicroVM, code can trigger callbacks using the CALLBACK command:

```bash
# Via vsock (handled by vsockserver)
echo 'CALLBACK get_appliance_info {"org": "MyOrg"}' | nc -U /run/vsock.sock

# The vsockserver will POST to the configured callbackUrl
```

## Backward Compatibility

- If `callbackUrl` is NOT provided in StartVMRequest, the system behaves exactly as before (WebSocket-based callbacks through Arrakis host)
- If `callbackUrl` IS provided, callbacks go directly to that URL via HTTP
- The callback request/response format remains the same in both modes

## Network Requirements

When using HTTP callbacks, ensure:

1. The MicroVM can reach the callback URL (network routing must be configured)
2. The callback server is accessible from the Arrakis host network
3. Firewall rules allow HTTP traffic from VM network to callback server

## Testing

See `test_arrakis_callback.py` for a complete example that:

1. Starts a local HTTP callback server
2. Creates a MicroVM with `callbackUrl` pointing to the server
3. Executes code that triggers callbacks
4. Verifies callbacks are received and processed

```bash
# Run the test
python test_arrakis_callback.py
```

## Build Instructions

After making these changes, you need to regenerate the serverapi package from the updated OpenAPI spec:

```bash
# Navigate to the Arrakis directory
cd arrakis

# Regenerate the Go client from the OpenAPI spec
# (Assuming you're using oapi-codegen or similar)
oapi-codegen -generate types,client -package serverapi api/server-api.yaml > pkg/serverapi/serverapi.go

# Or if using openapi-generator:
openapi-generator generate -i api/server-api.yaml -g go -o pkg/serverapi --package-name serverapi

# Build to verify
go build ./...
```

**Note:** The `GetCallbackUrl()` method will be available on `StartVMRequest` after regenerating the serverapi package.

## Security Considerations

1. **URL Validation**: Consider validating callback URLs to prevent SSRF attacks
2. **Authentication**: Add authentication tokens to callback requests if needed
3. **Network Isolation**: Ensure VMs can only reach authorized callback endpoints
4. **TLS**: Use HTTPS for callback URLs in production environments