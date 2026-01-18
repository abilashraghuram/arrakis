# Versa Networks Benchmark: Production-Ready Proof

## Background

**Customer**: Versa Networks (Sridhar Iyer)
**Status**: Final M1 milestone to prove production-readiness
**Deadline**: TBD (4-week timeline proposed)

## What Sridhar Wants

### The Challenge

Versa Networks has a **6-month, hand-coded XML-driven FSM** for network troubleshooting (see `agent.branch-disconnect.xml` in project root). This XML defines:

- **~50 states** (intents) for "branch down" troubleshooting
- **Complex conditional branching** based on tool results (Yes/No/Timeout/Error)
- **Multi-path decision trees** (e.g., if branch reachable → check admin dir → check connect; if unreachable → check overlay route → check controller → etc.)
- **Human-in-the-loop elicitation** mid-workflow when data is missing

Example flow from XML:
```
branch_reachability → [Yes/No]
  ├─ Yes → check_admin_dir → [Yes/No]
  │         ├─ Yes → connect_from_vd → [connected/timeout/bad_key]
  │         └─ No → "Admin not configured - contact support"
  └─ No → check_overlay_route → [Yes/No]
            ├─ Yes → check_controller_connectivity → ...
            └─ No → "NextHop unreachable - contact support"
```

**Pre-LLM reality**: This single XML took **6 months to build** by hand.

### Sridhar's Requirements

Prove that cintegrity SDK can:

1. **Replace manual rule engines** - LLM-generated workflows replicate XML FSM logic
2. **Handle complex branching** - Multi-path troubleshooting with conditional logic (not just linear flows)
3. **Support conditional elicitation** - Ask for missing data **mid-workflow** only when needed (not just upfront)
4. **Maintain correctness** - Audit trail proves data flow and execution path accuracy
5. **Scale to production** - Handle real-world complexity (20-30+ troubleshooting steps)

### What He Doesn't Want

- 404 error handling alone (already shown)
- Simple failure modes (already shown)
- Upfront parameter collection only (that's basic)
- Toy examples with 2-3 steps

### The Real Test

> "Prove to me that the workflows generated will be correct and **rich enough to support elicitation**."

Translation: Can LLM-generated workflows handle the same complexity as the 6-month hand-coded XML FSM?

---

## How This Relates to Our SDK

### Current State

cintegrity is an **MCP gateway for workflow execution with provenance tracking**:

```python
# External agent (Claude, LangChain, etc.) generates workflow code
workflow_code = """
from cintegrity.mcp_tools.versa import check_branch_reachability

async def workflow():
    branch = await elicit(message="Branch name?", response_type=str)
    result = await check_branch_reachability(branch=branch, org="Production")
    return {"reachable": result["status"] == "up"}
"""

# SDK executes workflow and tracks provenance
result = execute_workflow(workflow_code)

# Returns: {"reachable": "Yes"} + full audit trail with data flow graph
```

**What we do well**:
- ✅ Execute Python workflows with tool calls
- ✅ Track per-argument provenance (which outputs flow to which inputs)
- ✅ Support conditional elicitation via `await elicit()`
- ✅ Generate complete audit trails with data flow graphs
- ✅ Handle tool errors and missing data (404s)

**What we haven't proven**:
- ❓ Can handle **complex multi-step** workflows (50-state FSM equivalent)
- ❓ Can execute workflows **rich enough** for production troubleshooting
- ❓ Can scale beyond toy examples

### The Gap

**Versa's XML FSM** = 50 interconnected states with complex branching
**Our current demos** = Simple 2-3 step linear workflows

**The question**: Can agents generate workflows complex enough to replace the XML FSM?

**Our answer**: Maybe not in one shot, but yes through **multi-turn orchestration**.

---

## Proposed Solution: Multi-Turn Agent Orchestration

### Core Insight

**We don't need to build an agent framework.** Our SDK executes workflows; agents orchestrate them.

Instead of generating one massive 50-state workflow, the agent:
1. Executes **simple, focused workflows** one at a time
2. Makes **decisions between executions** based on results
3. Calls `execute_workflow()` multiple times in sequence

**This keeps us in our lane**: Workflow execution SDK with provenance tracking, not an agent orchestration platform.

### Execution Pattern

```
Turn 1: Agent decides first step
───────────────────────────────
Agent generates and executes:
  → Check branch reachability
Result: {"reachable": "Yes"}

Turn 2: Agent sees "Yes", decides next step
───────────────────────────────
Agent generates and executes:
  → Check admin directory configuration
Result: {"configured": "Yes"}

Turn 3: Agent sees "Yes", decides next step
───────────────────────────────
Agent generates and executes:
  → Request device connect from VD
Result: {"status": "connected"}

Turn 4: Agent concludes
───────────────────────────────
Agent: "Branch dc-east-001 is connected successfully. No issues found."
```

**Key insight**: The agent is the FSM decision-maker, our SDK just executes each step with full provenance.

### Why This Works

**For Versa's 50-state FSM**:
- 50 states become ~10-15 focused workflows (many states are just branching logic)
- Agent orchestrates which workflow to execute next based on results
- Each workflow is simple enough for reliable generation
- Full audit trail preserved across all executions
- Conditional elicitation works in each workflow independently

**For our SDK**:
- No scope creep - we stay a workflow execution engine
- No "skills framework" needed - just example workflow patterns
- Agent handles complexity, we handle provenance
- Proven pattern from research (multi-turn CodeAct, LangGraph orchestration)

---

## Implementation Approach

### Phase 1: Example Workflow Library (Week 1)

Create **10 example workflows** for common Versa troubleshooting steps:

```python
# docs/examples/versa_troubleshooting/check_reachability.py

"""
Check branch reachability from Versa Director.

Example workflow that pings a branch appliance to determine if it's reachable.
"""

WORKFLOW_CODE = '''
from cintegrity.mcp_tools.versa import check_branch_reachability

async def workflow():
    """Check if branch appliance is reachable from Versa Director."""
    branch = await elicit(
        message="Branch appliance name?",
        response_type=str
    )
    org = await elicit(
        message="Organization name?",
        response_type=str
    )

    result = await check_branch_reachability(branch=branch, org=org)

    return {
        "reachable": "Yes" if result["status"] == "up" else "No",
        "latency_ms": result.get("latency_ms"),
        "error": result.get("error")
    }
'''
```

**Example workflows to create** (based on XML FSM):
1. `check_reachability.py` - Ping branch from VD
2. `check_admin_dir.py` - Verify admin user configuration
3. `check_connect_from_vd.py` - Request device connect
4. `check_overlay_route.py` - Get VD NextHop SouthBound IP and ping
5. `check_controller_connectivity.py` - Ping controller from VD
6. `check_vd_southbound_reachability.py` - Ping SB IP with routing-instance
7. `compare_wan_ip.py` - Compare WAN IP on branch vs controller
8. `check_branch_tvi_status.py` - Check tunnel-type entries on controller
9. `check_vxlan_reachability.py` - Ping VxLAN Remote-IP from controller
10. `check_ipsec_status.py` - Check IKE/IPSec history for errors

These are **not** part of the SDK - just documented patterns agents can reference.

### Phase 2: Mock Versa Tools (Week 1-2)

Create **67 mock Versa MCP tools** with realistic data:

```python
# tests/mocks/versa_tools.py

MOCK_APPLIANCES = [
    {"name": "dc-east-001", "ip": "10.1.1.1", "org": "Production", "status": "up"},
    {"name": "dc-west-002", "ip": "10.1.2.1", "org": "Production", "status": "up"},
    {"name": "branch-north-01", "ip": "10.2.1.1", "org": "Staging", "status": "down"},
    # ... 69 total appliances
]

def mock_check_branch_reachability(branch: str, org: str) -> dict:
    """Mock: Ping branch from Versa Director."""
    appliance = next((a for a in MOCK_APPLIANCES if a["name"] == branch), None)
    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found", status_code=404)

    if appliance["status"] == "up":
        return {"status": "up", "latency_ms": random.randint(10, 50)}
    else:
        return {"status": "down", "error": "Connection timeout"}

# ... Mock all 67 Versa tools
```

### Phase 3: Multi-Turn Orchestration Tests (Week 2-3)

Test that agents can orchestrate complex troubleshooting through multiple workflow executions:

```python
# tests/integration/test_multi_turn_troubleshooting.py

async def test_branch_down_troubleshooting_reachable_path():
    """Test multi-turn orchestration for reachable branch."""

    # Turn 1: Check reachability
    result1 = await execute_workflow(CHECK_REACHABILITY_CODE)
    assert result1["reachable"] == "Yes"

    # Turn 2: Agent decides to check admin dir (based on result1)
    result2 = await execute_workflow(CHECK_ADMIN_DIR_CODE)
    assert result2["configured"] == "Yes"

    # Turn 3: Agent decides to check connect (based on result2)
    result3 = await execute_workflow(CHECK_CONNECT_CODE)
    assert result3["status"] == "connected"

    # Verify provenance tracked for each turn
    assert len(result1["_audit"]["calls"]) >= 1
    assert len(result2["_audit"]["calls"]) >= 1
    assert len(result3["_audit"]["calls"]) >= 1


async def test_branch_down_troubleshooting_unreachable_path():
    """Test multi-turn orchestration for unreachable branch."""

    # Turn 1: Check reachability
    result1 = await execute_workflow(CHECK_REACHABILITY_CODE)
    assert result1["reachable"] == "No"

    # Turn 2: Agent decides to check overlay route (different path)
    result2 = await execute_workflow(CHECK_OVERLAY_ROUTE_CODE)
    assert result2["reachable"] == "Yes"

    # Turn 3: Agent continues down unreachable branch path
    result3 = await execute_workflow(CHECK_CONTROLLER_CONNECTIVITY_CODE)
    assert result3["reachable"] == "Yes"

    # Turn 4: Continue troubleshooting
    result4 = await execute_workflow(CHECK_VD_SOUTHBOUND_CODE)
    # ... etc
```

### Phase 4: Enhanced Error Handling (Week 3)

Improve error messages to help agents refine workflows:

```python
# src/cintegrity/gateway/tools/execute_workflow.py

except WorkflowError as e:
    # Return actionable error feedback
    return {
        "error": str(e),
        "error_type": type(e).__name__,
        "code": planner_code,
        "line_number": getattr(e, 'line_number', None),
        "available_tools": list(manager.tool_names()),  # Help fix imports
        "suggestion": generate_fix_suggestion(e)  # "Did you mean...?"
    }
```

This enables CodeAct-style multi-turn refinement where agent sees error and retries with corrected code.

### Phase 5: Benchmark & Demo (Week 4)

**Benchmark metrics**:
- Success rate: % of troubleshooting flows that reach correct conclusion
- Path accuracy: % of correct decision points taken
- Elicitation quality: Does it ask for missing params only when needed?
- Provenance completeness: 100% of data flows tracked
- Execution time: <60 seconds for 10-step troubleshooting flow

**Demo format for Sridhar**:
1. Video showing multi-turn troubleshooting in action
2. Interactive test environment (Claude Desktop or VSCode)
3. Benchmark report comparing XML FSM vs LLM orchestration
4. Architecture documentation

---

## Testing Infrastructure & Benchmark Design

This section details how we'll build a **realistic testing environment** that convinces Sridhar our SDK can handle production complexity.

### Test Bench Architecture

```
tests/versa_benchmark/
├── mocks/
│   ├── __init__.py
│   ├── data.py              # Mock network topology (69 appliances, 5 orgs, etc.)
│   ├── tools.py             # All 67 mock Versa tool implementations
│   └── scenarios.py         # Pre-configured test scenarios
├── workflows/
│   ├── __init__.py
│   ├── check_reachability.py
│   ├── check_admin_dir.py
│   ├── ... (10 workflow patterns)
│   └── supervisor.py        # Optional: pre-coded supervisor workflow
├── integration/
│   ├── __init__.py
│   ├── test_reachable_path.py
│   ├── test_unreachable_path.py
│   ├── test_timeout_scenarios.py
│   ├── test_elicitation.py
│   └── test_end_to_end.py
└── benchmark/
    ├── __init__.py
    ├── runner.py            # Benchmark test runner
    ├── metrics.py           # Metrics collection
    └── report.py            # Generate benchmark report
```

### Mock Data: Realistic Network Topology

**Design principle**: Create a network topology complex enough to exercise all troubleshooting paths from the XML FSM.

```python
# tests/versa_benchmark/mocks/data.py

from dataclasses import dataclass
from typing import Literal

@dataclass
class Appliance:
    """Mock branch appliance."""
    name: str
    ip: str
    organization: str
    status: Literal["up", "down", "degraded"]
    admin_configured: bool
    wan_ip: str
    transport_domain: str
    controller: str | None
    vpn_profile: str | None
    tvi_status: Literal["up", "down", "no_entry"] | None
    vxlan_remote_ip: str | None
    ipsec_errors: list[str]

@dataclass
class Organization:
    """Mock organization."""
    name: str
    id: str
    provider_org: str
    control_vr: str

@dataclass
class Controller:
    """Mock controller appliance."""
    name: str
    ip: str
    southbound_ip: str
    organization: str
    status: Literal["up", "down"]

# Realistic mock data covering all test scenarios
MOCK_APPLIANCES = [
    # Scenario 1: Healthy branch (reachable path)
    Appliance(
        name="dc-east-001",
        ip="10.1.1.1",
        organization="Production",
        status="up",
        admin_configured=True,
        wan_ip="203.0.113.10",
        transport_domain="prod-transport",
        controller="controller-east",
        vpn_profile="Production-PostStaging",
        tvi_status="up",
        vxlan_remote_ip="10.100.1.1",
        ipsec_errors=[]
    ),

    # Scenario 2: Branch reachable but admin not configured
    Appliance(
        name="dc-west-002",
        ip="10.1.2.1",
        organization="Production",
        status="up",
        admin_configured=False,  # Will fail admin dir check
        wan_ip="203.0.113.20",
        transport_domain="prod-transport",
        controller="controller-west",
        vpn_profile="Production-PostStaging",
        tvi_status="up",
        vxlan_remote_ip="10.100.2.1",
        ipsec_errors=[]
    ),

    # Scenario 3: Branch unreachable (needs overlay route check)
    Appliance(
        name="branch-north-01",
        ip="10.2.1.1",
        organization="Staging",
        status="down",  # Not reachable
        admin_configured=True,
        wan_ip="203.0.113.30",
        transport_domain="staging-transport",
        controller="controller-north",
        vpn_profile="Staging-PostStaging",
        tvi_status="down",
        vxlan_remote_ip="10.100.3.1",
        ipsec_errors=[]
    ),

    # Scenario 4: WAN IP mismatch
    Appliance(
        name="branch-south-02",
        ip="10.2.2.1",
        organization="Staging",
        status="down",
        admin_configured=True,
        wan_ip="203.0.113.40",  # Mismatched with controller
        transport_domain="staging-transport",
        controller="controller-south",
        vpn_profile="Staging-PostStaging",
        tvi_status="up",
        vxlan_remote_ip="10.100.4.1",
        ipsec_errors=[]
    ),

    # Scenario 5: IPSec errors
    Appliance(
        name="branch-remote-03",
        ip="10.3.1.1",
        organization="Remote",
        status="up",
        admin_configured=True,
        wan_ip="203.0.113.50",
        transport_domain="remote-transport",
        controller="controller-remote",
        vpn_profile="Remote-PostStaging",
        tvi_status="up",
        vxlan_remote_ip="10.100.5.1",
        ipsec_errors=["IKE SA timeout", "Phase 2 negotiation failed"]
    ),

    # ... Add 64 more appliances for realistic scale
]

MOCK_ORGANIZATIONS = [
    Organization(
        name="Production",
        id="prod-001",
        provider_org="Provider-Org",
        control_vr="Provider-Org-Control-VR"
    ),
    Organization(
        name="Staging",
        id="stage-001",
        provider_org="Provider-Org",
        control_vr="Provider-Org-Control-VR"
    ),
    # ... 3 more orgs
]

MOCK_CONTROLLERS = [
    Controller(
        name="controller-east",
        ip="10.50.1.1",
        southbound_ip="10.51.1.1",
        organization="Production",
        status="up"
    ),
    # ... Controllers for each region
]

# Network topology: which branches connect to which controllers
NETWORK_TOPOLOGY = {
    "dc-east-001": {
        "controller": "controller-east",
        "wan_ip_on_controller": "203.0.113.10",  # Should match appliance.wan_ip
        "nexthop_southbound": "10.51.1.254",
        "vxlan_local_ip": "10.100.1.254",
    },
    "branch-south-02": {
        "controller": "controller-south",
        "wan_ip_on_controller": "203.0.113.99",  # MISMATCH - will fail wan_ip check
        "nexthop_southbound": "10.51.2.254",
        "vxlan_local_ip": "10.100.4.254",
    },
    # ... Topology for all appliances
}
```

### Mock Tool Implementations: All 67 Versa Tools

**Design principle**: Each mock tool implements realistic logic based on the XML FSM behavior, including proper error conditions.

```python
# tests/versa_benchmark/mocks/tools.py

from cintegrity.gateway.errors import ToolExecutionError
from .data import MOCK_APPLIANCES, NETWORK_TOPOLOGY, MOCK_CONTROLLERS
import random

def mock_check_branch_reachability(branch: str, org: str) -> dict:
    """
    Mock: Ping branch appliance from Versa Director.

    XML logic: ping <Branch ip>
    Success: branch.status == "up"
    Failure: branch.status == "down"
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch and a.organization == org), None)

    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found in organization {org}", status_code=404)

    if appliance.status == "up":
        return {
            "status": "up",
            "reachable": True,
            "latency_ms": random.randint(10, 50),
            "ip": appliance.ip
        }
    else:
        return {
            "status": "down",
            "reachable": False,
            "error": "Connection timeout - host unreachable",
            "ip": appliance.ip
        }


def mock_check_admin_dir(branch: str, org: str) -> dict:
    """
    Mock: Check for Admin homedir and ssh_keydir configuration on VD.

    XML logic: show configuration aaa authentication users user admin
    Success: homedir = '/var/versa/vnms/ncs/homes/admin' and ssh_keydir correct
    Failure: configuration not matching
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch and a.organization == org), None)

    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found", status_code=404)

    if appliance.admin_configured:
        return {
            "configured": True,
            "homedir": "/var/versa/vnms/ncs/homes/admin",
            "ssh_keydir": "/var/versa/vnms/ncs/homes/admin/.ssh"
        }
    else:
        return {
            "configured": False,
            "error": "Admin user directory not properly configured",
            "current_homedir": "/home/admin",  # Wrong path
            "current_ssh_keydir": None
        }


def mock_connect_from_vd(branch: str, org: str, override_southbound_locked: bool = False) -> dict:
    """
    Mock: Request devices device {appliance} connect from Versa Director.

    XML logic: request devices device {appliance} connect
    Results:
    - Success: result is true, info shows "Connected to {appliance}"
    - Timeout: connection to CPE timed out
    - Bad key: device as southbound-locked, then BAD Private Key if override
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)

    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found", status_code=404)

    # Simulate different failure modes based on appliance properties
    if appliance.name == "branch-bad-key-01":
        if override_southbound_locked:
            return {
                "status": "error",
                "error_type": "bad_private_key",
                "info": "BAD Private Key - cannot authenticate"
            }
        else:
            return {
                "status": "error",
                "error_type": "southbound_locked",
                "info": "Device is southbound-locked"
            }

    if appliance.status == "up" and appliance.admin_configured:
        return {
            "status": "connected",
            "info": f"(Administrator) Connected to {branch} - {appliance.ip}:2022"
        }
    else:
        return {
            "status": "timeout",
            "error_type": "timeout",
            "info": f"Connection to CPE {appliance.ip} timed out"
        }


def mock_check_overlay_route(branch: str, org: str) -> dict:
    """
    Mock: Get VD NextHop SouthBound IP and ping it.

    XML logic:
    1. ip route show match <branch-ip>
    2. ping VD NextHop on Southbound
    Success: ping succeeds
    Failure: ping fails
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)
    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found", status_code=404)

    topology = NETWORK_TOPOLOGY.get(branch)
    if not topology:
        return {
            "reachable": False,
            "error": "No route to branch found in routing table"
        }

    nexthop = topology["nexthop_southbound"]

    # Simulate: branches starting with "branch-no-route" have no southbound route
    if branch.startswith("branch-no-route"):
        return {
            "reachable": False,
            "nexthop": nexthop,
            "error": "NextHop on SouthBound is not reachable"
        }

    return {
        "reachable": True,
        "nexthop": nexthop,
        "latency_ms": random.randint(5, 20)
    }


def mock_check_controller_connectivity(branch: str, org: str) -> dict:
    """
    Mock: Get Controller IP and ping it from VD.

    XML logic: ping Controller from VD
    Success: controller.status == "up"
    Failure: controller.status == "down"
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)
    if not appliance or not appliance.controller:
        raise ToolExecutionError(f"No controller found for branch {branch}", status_code=404)

    controller = next((c for c in MOCK_CONTROLLERS if c.name == appliance.controller), None)
    if not controller:
        return {
            "reachable": False,
            "error": "Controller not found in network"
        }

    if controller.status == "up":
        return {
            "reachable": True,
            "controller_ip": controller.ip,
            "latency_ms": random.randint(5, 15)
        }
    else:
        return {
            "reachable": False,
            "controller_ip": controller.ip,
            "error": "Unable to connect to Controller"
        }


def mock_check_vd_southbound_reachability(branch: str, org: str) -> dict:
    """
    Mock: Ping Controller Southbound IP with routing-instance provider-org-Control-VR.

    XML logic: ping {controller-southbound-ip} routing-instance {provider-org-Control-VR}
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)
    if not appliance or not appliance.controller:
        raise ToolExecutionError(f"No controller found for branch {branch}", status_code=404)

    controller = next((c for c in MOCK_CONTROLLERS if c.name == appliance.controller), None)
    if not controller:
        return {"reachable": False, "error": "Controller not found"}

    # Simulate: some controllers have unreachable southbound
    if controller.name == "controller-bad-southbound":
        return {
            "reachable": False,
            "southbound_ip": controller.southbound_ip,
            "error": "Director Southbound is not reachable from Provider-Org Control VR"
        }

    return {
        "reachable": True,
        "southbound_ip": controller.southbound_ip,
        "latency_ms": random.randint(3, 12)
    }


def mock_compare_wan_ip(branch: str, org: str) -> dict:
    """
    Mock: Compare WAN IP configured on branch vs WAN IP on controller.

    XML logic: Complex algorithm comparing transport-addresses from branch
    and wan-interfaces from controller.

    Success: WAN IPs match
    Failure: Configuration mismatch
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)
    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found", status_code=404)

    topology = NETWORK_TOPOLOGY.get(branch)
    if not topology:
        return {"match": False, "error": "No topology information found"}

    branch_wan_ip = appliance.wan_ip
    controller_wan_ip = topology["wan_ip_on_controller"]

    if branch_wan_ip == controller_wan_ip:
        return {
            "match": True,
            "branch_wan_ip": branch_wan_ip,
            "controller_wan_ip": controller_wan_ip,
            "transport_domain": appliance.transport_domain
        }
    else:
        return {
            "match": False,
            "branch_wan_ip": branch_wan_ip,
            "controller_wan_ip": controller_wan_ip,
            "error": "WAN IP mismatch between branch and controller configuration"
        }


def mock_check_branch_tvi_status(branch: str, org: str) -> dict:
    """
    Mock: Check for tunnel-type entries and their if-oper-status on Controller.

    XML logic: show devices device {controller} live-status interfaces dynamic-tunnels
    Results:
    - No entry: "no entry is found for any tunnel-type"
    - Secure down: if-oper-status of secure tunnel-type is down
    - Up: secure tunnel-type is up
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)
    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found", status_code=404)

    if appliance.tvi_status == "no_entry":
        return {
            "status": "no_entry",
            "error": "No entry for clear-text and secure TVI"
        }
    elif appliance.tvi_status == "down":
        return {
            "status": "down",
            "tunnel_type": "secure",
            "if_oper_status": "down",
            "error": "Secure tunnel interface is down"
        }
    else:
        return {
            "status": "up",
            "tunnel_type": "secure",
            "if_oper_status": "up",
            "cleartext_status": "up"
        }


def mock_check_vxlan_reachability(branch: str, org: str) -> dict:
    """
    Mock: Ping VxLAN Remote-IP from Controller.

    XML logic:
    1. Get VxLAN Remote-Ip, Local-Ip, and vrf from dynamic-tunnels
    2. Execute ping from Controller: ping hostname=remote-ip routing-instance=vrf source=local-ip
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)
    if not appliance or not appliance.vxlan_remote_ip:
        raise ToolExecutionError(f"No VxLAN config found for {branch}", status_code=404)

    topology = NETWORK_TOPOLOGY.get(branch)

    # Simulate: branches with "vxlan-unreachable" in name fail this check
    if "vxlan-unreachable" in branch:
        return {
            "reachable": False,
            "remote_ip": appliance.vxlan_remote_ip,
            "local_ip": topology["vxlan_local_ip"] if topology else None,
            "error": "VxLAN remote IP is not reachable from Control VR"
        }

    return {
        "reachable": True,
        "remote_ip": appliance.vxlan_remote_ip,
        "local_ip": topology["vxlan_local_ip"] if topology else None,
        "latency_ms": random.randint(2, 8)
    }


def mock_check_ipsec_status(branch: str, org: str) -> dict:
    """
    Mock: Check IPSec IKE history for errors.

    XML logic:
    1. Get VxLAN remote-ip, local-ip
    2. Check IKE history for errors
    3. Check IPSec history for errors
    """
    appliance = next((a for a in MOCK_APPLIANCES if a.name == branch), None)
    if not appliance:
        raise ToolExecutionError(f"Appliance {branch} not found", status_code=404)

    if appliance.ipsec_errors:
        return {
            "status": "error",
            "errors": appliance.ipsec_errors,
            "vpn_profile": appliance.vpn_profile,
            "error_summary": " | ".join(appliance.ipsec_errors)
        }

    return {
        "status": "ok",
        "vpn_profile": appliance.vpn_profile,
        "ike_status": "established",
        "ipsec_status": "up"
    }


# ... Implement remaining 57 tools following same pattern:
# - mock_check_netconf()
# - mock_check_sla_loss()
# - mock_check_ngfw_enabled()
# - mock_check_wan_reachability()
# - ... etc

# Register all mock tools
ALL_MOCK_TOOLS = {
    "check_branch_reachability": mock_check_branch_reachability,
    "check_admin_dir": mock_check_admin_dir,
    "connect_from_vd": mock_connect_from_vd,
    "check_overlay_route": mock_check_overlay_route,
    "check_controller_connectivity": mock_check_controller_connectivity,
    "check_vd_southbound_reachability": mock_check_vd_southbound_reachability,
    "compare_wan_ip": mock_compare_wan_ip,
    "check_branch_tvi_status": mock_check_branch_tvi_status,
    "check_vxlan_reachability": mock_check_vxlan_reachability,
    "check_ipsec_status": mock_check_ipsec_status,
    # ... 57 more tools
}
```

### Test Scenarios: Pre-Configured Network States

**Design principle**: Create specific test scenarios that exercise every path in the XML FSM.

```python
# tests/versa_benchmark/mocks/scenarios.py

from enum import Enum
from dataclasses import dataclass

class ScenarioType(Enum):
    """Predefined troubleshooting scenarios."""
    HEALTHY_BRANCH = "healthy_branch"
    ADMIN_NOT_CONFIGURED = "admin_not_configured"
    CONNECT_TIMEOUT = "connect_timeout"
    BAD_PRIVATE_KEY = "bad_private_key"
    BRANCH_UNREACHABLE = "branch_unreachable"
    NEXTHOP_UNREACHABLE = "nexthop_unreachable"
    CONTROLLER_UNREACHABLE = "controller_unreachable"
    WAN_IP_MISMATCH = "wan_ip_mismatch"
    TVI_STATUS_DOWN = "tvi_down"
    TVI_NO_ENTRY = "tvi_no_entry"
    VXLAN_UNREACHABLE = "vxlan_unreachable"
    IPSEC_ERRORS = "ipsec_errors"
    NGFW_BLOCKING = "ngfw_blocking"
    SLA_LOSS = "sla_loss"

@dataclass
class TestScenario:
    """A complete test scenario with expected flow."""
    name: str
    type: ScenarioType
    branch: str
    organization: str
    expected_path: list[str]  # Expected sequence of workflow calls
    expected_outcome: str
    description: str

# Define all test scenarios
TEST_SCENARIOS = [
    TestScenario(
        name="Scenario 1: Healthy Branch (Happy Path)",
        type=ScenarioType.HEALTHY_BRANCH,
        branch="dc-east-001",
        organization="Production",
        expected_path=[
            "check_reachability",  # → Yes
            "check_admin_dir",     # → Yes
            "connect_from_vd",     # → connected
        ],
        expected_outcome="Branch connected successfully",
        description="Branch is reachable, admin configured, connects successfully"
    ),

    TestScenario(
        name="Scenario 2: Admin Not Configured",
        type=ScenarioType.ADMIN_NOT_CONFIGURED,
        branch="dc-west-002",
        organization="Production",
        expected_path=[
            "check_reachability",  # → Yes
            "check_admin_dir",     # → No
        ],
        expected_outcome="Admin user not configured properly - contact support",
        description="Branch reachable but admin directory not configured"
    ),

    TestScenario(
        name="Scenario 3: Branch Unreachable → WAN IP Mismatch",
        type=ScenarioType.WAN_IP_MISMATCH,
        branch="branch-south-02",
        organization="Staging",
        expected_path=[
            "check_reachability",              # → No
            "check_overlay_route",             # → Yes
            "check_controller_connectivity",   # → Yes
            "check_vd_southbound_reachability", # → Yes
            "compare_wan_ip",                  # → No (mismatch)
        ],
        expected_outcome="WAN IP mismatch - reconfigure branch",
        description="Branch unreachable due to WAN IP configuration mismatch"
    ),

    TestScenario(
        name="Scenario 4: IPSec Errors",
        type=ScenarioType.IPSEC_ERRORS,
        branch="branch-remote-03",
        organization="Remote",
        expected_path=[
            "check_reachability",              # → Yes (eventually)
            "check_admin_dir",                 # → Yes
            "connect_from_vd",                 # → timeout
            # ... continues down IPSec troubleshooting path
            "check_ipsec_status",              # → errors found
        ],
        expected_outcome="IPSec errors detected - IKE SA timeout, Phase 2 failed",
        description="Branch has IPSec configuration or connection issues"
    ),

    # Add all 14 scenarios covering every major path in XML FSM
]

def get_scenario(scenario_type: ScenarioType) -> TestScenario:
    """Get a test scenario by type."""
    return next(s for s in TEST_SCENARIOS if s.type == scenario_type)
```

### Integration Tests: Realistic End-to-End Flows

```python
# tests/versa_benchmark/integration/test_end_to_end.py

import pytest
from ..mocks.scenarios import TEST_SCENARIOS, ScenarioType
from ..workflows import (
    CHECK_REACHABILITY_CODE,
    CHECK_ADMIN_DIR_CODE,
    CHECK_CONNECT_CODE,
    CHECK_OVERLAY_ROUTE_CODE,
    # ... import all workflow patterns
)

@pytest.mark.asyncio
class TestEndToEndTroubleshooting:
    """Test complete troubleshooting flows matching XML FSM behavior."""

    async def test_scenario_healthy_branch(self):
        """Scenario 1: Healthy branch - reachable path."""
        scenario = get_scenario(ScenarioType.HEALTHY_BRANCH)

        # Turn 1: Check reachability
        result1 = await execute_workflow(
            CHECK_REACHABILITY_CODE,
            elicit_responses={"Branch appliance name?": scenario.branch, "Organization name?": scenario.organization}
        )
        assert result1["reachable"] == "Yes"
        assert len(result1["_audit"]["calls"]) >= 1

        # Turn 2: Check admin dir (agent decides based on result1)
        result2 = await execute_workflow(
            CHECK_ADMIN_DIR_CODE,
            elicit_responses={"Branch appliance name?": scenario.branch, "Organization name?": scenario.organization}
        )
        assert result2["configured"] == True

        # Turn 3: Connect from VD (agent decides based on result2)
        result3 = await execute_workflow(
            CHECK_CONNECT_CODE,
            elicit_responses={"Branch appliance name?": scenario.branch}
        )
        assert result3["status"] == "connected"
        assert scenario.expected_outcome.lower() in result3["info"].lower()

        # Verify complete audit trail
        assert "check_branch_reachability" in str(result1["_audit"]["calls"])
        assert "check_admin_dir" in str(result2["_audit"]["calls"])
        assert "connect_from_vd" in str(result3["_audit"]["calls"])

    async def test_scenario_wan_ip_mismatch(self):
        """Scenario 3: Branch unreachable → WAN IP mismatch path."""
        scenario = get_scenario(ScenarioType.WAN_IP_MISMATCH)

        # Execute full troubleshooting path
        results = []

        # Turn 1: Reachability → No
        result1 = await execute_workflow(CHECK_REACHABILITY_CODE, elicit_responses={...})
        results.append(("check_reachability", result1))
        assert result1["reachable"] == "No"

        # Turn 2: Overlay route → Yes
        result2 = await execute_workflow(CHECK_OVERLAY_ROUTE_CODE, elicit_responses={...})
        results.append(("check_overlay_route", result2))
        assert result2["reachable"] == True

        # Turn 3: Controller connectivity → Yes
        result3 = await execute_workflow(CHECK_CONTROLLER_CONNECTIVITY_CODE, elicit_responses={...})
        results.append(("check_controller_connectivity", result3))
        assert result3["reachable"] == True

        # Turn 4: VD southbound → Yes
        result4 = await execute_workflow(CHECK_VD_SOUTHBOUND_CODE, elicit_responses={...})
        results.append(("check_vd_southbound_reachability", result4))
        assert result4["reachable"] == True

        # Turn 5: Compare WAN IP → No (mismatch)
        result5 = await execute_workflow(COMPARE_WAN_IP_CODE, elicit_responses={...})
        results.append(("compare_wan_ip", result5))
        assert result5["match"] == False
        assert "mismatch" in result5.get("error", "").lower()

        # Verify expected path
        actual_path = [name for name, _ in results]
        assert actual_path == scenario.expected_path

        # Verify final outcome
        assert scenario.expected_outcome.lower() in result5.get("error", "").lower()

    # ... Implement tests for all 14 scenarios
```

### Benchmark Runner & Metrics Collection

```python
# tests/versa_benchmark/benchmark/runner.py

from dataclasses import dataclass
from datetime import datetime
import time
from ..mocks.scenarios import TEST_SCENARIOS

@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    scenario_name: str
    success: bool
    path_correct: bool
    execution_time_ms: float
    num_turns: int
    num_tool_calls: int
    num_elicitations: int
    provenance_complete: bool
    error: str | None

class BenchmarkRunner:
    """Run all test scenarios and collect metrics."""

    async def run_all_scenarios(self) -> list[BenchmarkResult]:
        """Execute all test scenarios."""
        results = []

        for scenario in TEST_SCENARIOS:
            start_time = time.time()

            try:
                result = await self._run_scenario(scenario)
                execution_time = (time.time() - start_time) * 1000

                results.append(BenchmarkResult(
                    scenario_name=scenario.name,
                    success=result["success"],
                    path_correct=result["path"] == scenario.expected_path,
                    execution_time_ms=execution_time,
                    num_turns=result["num_turns"],
                    num_tool_calls=result["num_tool_calls"],
                    num_elicitations=result["num_elicitations"],
                    provenance_complete=self._verify_provenance(result),
                    error=None
                ))
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                results.append(BenchmarkResult(
                    scenario_name=scenario.name,
                    success=False,
                    path_correct=False,
                    execution_time_ms=execution_time,
                    num_turns=0,
                    num_tool_calls=0,
                    num_elicitations=0,
                    provenance_complete=False,
                    error=str(e)
                ))

        return results

    def generate_report(self, results: list[BenchmarkResult]) -> dict:
        """Generate benchmark report with metrics."""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        path_correct = sum(1 for r in results if r.path_correct)
        avg_execution_time = sum(r.execution_time_ms for r in results) / total
        provenance_complete = sum(1 for r in results if r.provenance_complete)

        return {
            "summary": {
                "total_scenarios": total,
                "successful": successful,
                "success_rate": f"{(successful / total) * 100:.1f}%",
                "path_accuracy": f"{(path_correct / total) * 100:.1f}%",
                "avg_execution_time_ms": f"{avg_execution_time:.0f}",
                "provenance_completeness": f"{(provenance_complete / total) * 100:.1f}%",
            },
            "detailed_results": [
                {
                    "scenario": r.scenario_name,
                    "success": r.success,
                    "path_correct": r.path_correct,
                    "execution_time_ms": f"{r.execution_time_ms:.0f}",
                    "turns": r.num_turns,
                    "tool_calls": r.num_tool_calls,
                    "elicitations": r.num_elicitations,
                    "error": r.error
                }
                for r in results
            ],
            "target_metrics": {
                "success_rate": ">80%",
                "path_accuracy": ">90%",
                "avg_execution_time": "<60000ms",
                "provenance_completeness": "100%"
            }
        }
```

### What Makes This Convincing for Sridhar

1. **Realistic Scale**: 69 appliances, 5 orgs, full network topology - not toy data
2. **All Failure Modes**: Every path from XML FSM is testable
3. **Quantitative Metrics**: Success rate, path accuracy, execution time - objective measures
4. **Provenance Proof**: Every test verifies complete audit trail with data flow
5. **Reproducible**: Sridhar can run tests himself, add new scenarios
6. **Visual Report**: Benchmark generates comparison chart: XML FSM vs LLM orchestration

---

## What We're NOT Building

**We are NOT building**:
- ❌ Agent orchestration framework (no skills infrastructure, no execute_skill builtin)
- ❌ Hierarchical agent system (no supervisor/worker architecture)
- ❌ LLM-driven decision engine (agents make decisions, we execute)
- ❌ Workflow composition framework (no nested workflow primitives)

**We ARE enhancing**:
- ✅ Error handling for better agent refinement
- ✅ Documentation of workflow patterns
- ✅ Testing multi-turn orchestration flows
- ✅ Provenance tracking (already works, just needs testing at scale)

**Identity preserved**: MCP gateway for workflow execution with provenance tracking.

---

## Success Criteria

**For Sridhar**: Proof that LLM-orchestrated workflows can replace the 6-month XML FSM
- ✅ Handles complex multi-step troubleshooting (10+ steps)
- ✅ Conditional branching based on results
- ✅ Conditional elicitation mid-workflow
- ✅ Complete audit trail with data flow graphs
- ✅ Scales to production complexity

**For cintegrity**: Validation of production-readiness
- ✅ Proven at enterprise scale (Versa's real use case)
- ✅ Multi-turn orchestration pattern validated
- ✅ Provenance tracking works for complex flows
- ✅ Reference implementation for other customers

---

## Open Questions

1. **Timeline**: When does Sridhar need to see this? (4-week timeline proposed)
2. **Demo format**: Live demo or pre-recorded video?
3. **XML coverage**: Target subset (branch reachability flow) or full FSM?
4. **Cross-turn provenance**: Should we link multiple workflow executions in a single audit trail, or keep them separate?

---

## Next Steps

1. **Clarify open questions** with Sridhar and team
2. **Create example workflow library** (10 patterns)
3. **Set up mock Versa tools** (67 tools)
4. **Write multi-turn orchestration tests**
5. **Run benchmark and collect metrics**
6. **Prepare demo materials for Sridhar**

---

## Related Files

- `agent.branch-disconnect.xml` - Versa's 50-state XML FSM (in project root)
- `debug_graph.pdf` - Visual representation of FSM complexity (in project root)
- `.claude/plans/idempotent-shimmying-piglet.md` - Detailed research and design
- Research reports in `.claude/plans/` - CodeAct, Skills, Long-running agents, MCP patterns
