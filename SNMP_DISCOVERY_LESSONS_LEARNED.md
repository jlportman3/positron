# SNMP CPE Discovery - Lessons Learned

## Summary

After extensive SNMP exploration of the Positron GAM-4-C device, we discovered both the capabilities and limitations of using SNMP Bridge MIB for CPE discovery.

## What SNMP Bridge MIB CAN Tell Us

### ✅ Bridge Port Mapping
Successfully mapped bridge ports to interface indices:
- Bridge Port 1-4 → G.hn physical ports 1-4 (interface indices 1000001-1000004)
- Bridge Port 6 → 10GigE uplink (interface index 1000006)

### ✅ All Learned MAC Addresses
Retrieved complete MAC address forwarding table showing all devices the GAM has seen traffic from.

### ✅ Customer Device Detection
Found customer router `18:fd:74:17:35:9f` connected behind the CPE on port 4, confirming an active service.

## What SNMP Bridge MIB CANNOT Tell Us

### ❌ Distinguish GAM Port MACs from CPE MACs
**Problem**: Both the GAM device's own port MAC addresses (`00:0e:d8:1e:58:04-07`) and actual Positron CPE endpoint MACs use the same OUI (`00:0e:d8`).

**Result**: SNMP Bridge MIB shows 4 Positron MACs (one per port), but these are the GAM's interface MACs, not CPE devices.

**Reality**: Only 1 actual CPE is connected (on port 4), as confirmed by user.

### ❌ G.hn Link Status
Bridge MIB doesn't indicate whether a G.hn link is established on each port - it only shows Ethernet-level MAC forwarding.

### ❌ Endpoint Configuration Details
Cannot retrieve endpoint names, bandwidth profiles, or subscriber associations via standard SNMP.

## The Correct Approach: SSH CLI

### Running-Config Shows Truth

The device's running-config provides authoritative CPE information:

```
ghn endpoint 1 name "Positron_1C9508" mac-address 00:0e:d8:1c:95:08 port 4
ghn subscriber 1 name "test" vid 100 endpoint 1 bw-profile unthrottled poe disable
```

This shows:
- **Endpoint MAC**: `00:0e:d8:1c:95:08` (NOT the `00:0e:d8:1e:58:07` we saw in bridge table)
- **Physical Port**: 4
- **Subscriber Name**: "test"
- **VLAN**: 100

### Recommended CLI Commands for Discovery

**1. Show all configured endpoints:**
```bash
show ghn endpoint
```
Returns: endpoint ID, name, MAC address, port number

**2. Show endpoint status/statistics:**
```bash
show ghn endpoint status
```
Returns: link status, speeds, SNR

**3. Show subscribers:**
```bash
show ghn subscriber
```
Returns: subscriber config, VLAN, bandwidth profile

**4. Show port status:**
```bash
show ghn port
```
Returns: operational status per port

## Recommended Implementation Strategy

### Phase 1: SSH CLI Discovery (Accurate)

1. **SSH into GAM device**
2. **Run `show ghn endpoint`** to get all configured CPE
3. **Parse output** to extract:
   - Endpoint MAC addresses
   - Port numbers
   - Endpoint names
4. **Run `show ghn subscriber`** to get subscriber associations
5. **Compare against database** to find unconfigured endpoints

**Pros:**
- ✅ Accurate CPE detection
- ✅ Authoritative source (device config)
- ✅ Includes endpoint names and details
- ✅ Shows actual G.hn connections

**Cons:**
- ❌ Requires SSH access
- ❌ Need to parse CLI output
- ❌ Device-specific command syntax

### Phase 2: SNMP for Monitoring (Supplementary)

Use SNMP for:
- Device status monitoring (uptime, reachability)
- Interface statistics (traffic counters)
- Bridge table for customer device detection
- Positron enterprise OIDs for link quality (if we get the MIB)

**Pros:**
- ✅ Standard protocol
- ✅ Good for polling/monitoring
- ✅ Works without authentication

**Cons:**
- ❌ Cannot distinguish CPE MACs from port MACs
- ❌ Missing Positron-specific data without MIB

## Current Database Status

**Subscribers in Database**: 0 (none configured yet)

**GAM Device Configuration**: 1 endpoint configured (per running-config)

**Action Needed**:
1. Parse running-config or use CLI to import existing endpoint
2. Create subscriber record in database for "test" subscriber
3. Link to endpoint MAC `00:0e:d8:1c:95:08`, port 4, VLAN 100

## Updated API Endpoint Strategy

### Option A: CLI-based Discovery (Recommended)

```python
@router.get("/devices/{device_id}/discovered-cpe")
async def get_discovered_cpe_via_cli(device_id: UUID, db: AsyncSession):
    """
    Use SSH CLI to discover actual CPE endpoints.
    Parses 'show ghn endpoint' output.
    """
    device = await get_device(device_id)

    # SSH into device
    ssh_client = SSHClient(device.ip_address, device.ssh_credentials)

    # Run command
    output = await ssh_client.execute_command("show ghn endpoint")

    # Parse output
    endpoints = parse_ghn_endpoint_output(output)

    # Compare against database subscribers
    configured_subscribers = await get_subscribers_for_device(device_id)
    configured_macs = {s.endpoint_mac for s in configured_subscribers}

    # Separate configured vs unconfigured
    unconfigured = [ep for ep in endpoints if ep['mac'] not in configured_macs]
    configured = [ep for ep in endpoints if ep['mac'] in configured_macs]

    return {
        'unconfigured_cpe': unconfigured,
        'configured_cpe': configured
    }
```

### Option B: Hybrid Approach

1. **CLI** for CPE discovery (authoritative)
2. **SNMP Bridge MIB** for customer device detection (supplementary)
3. **SNMP Positron OIDs** for link quality metrics (when MIB available)

Combine data to show:
- CPE MAC and port (from CLI)
- Customer devices behind CPE (from Bridge MIB)
- Link speed and SNR (from Positron OIDs)

## Next Steps

1. **Implement SSH CLI integration**
   - Add SSH command execution to SSHClient
   - Create CLI output parsers for `show ghn endpoint/subscriber`
   - Update discovery endpoint to use CLI

2. **Import existing configuration**
   - Parse running-config or use CLI
   - Create subscriber in database for "test" endpoint
   - Associate with GAM device and port 4

3. **Test with multiple CPE**
   - Connect CPE to other ports
   - Verify discovery works correctly
   - Test unconfigured vs configured detection

4. **Request Positron MIB from vendor**
   - Contact Positron support
   - Request official MIB file
   - Document additional OIDs for link metrics

## Conclusion

**Key Learning**: Standard SNMP Bridge MIB is insufficient for Positron CPE discovery because it cannot distinguish between:
- GAM device's own port MAC addresses (00:0e:d8:XX:XX:XX)
- Actual CPE endpoint MAC addresses (also 00:0e:d8:XX:XX:XX)

**Solution**: Use SSH CLI commands (`show ghn endpoint`) as the authoritative source for CPE discovery, and use SNMP as a supplementary monitoring tool.

**Current Status**:
- ✅ SNMP bridge table mapping works
- ✅ Can detect customer devices behind CPE
- ✅ Port mapping established
- ❌ Cannot identify CPE endpoints via SNMP alone
- ⏳ Need SSH CLI implementation for accurate CPE discovery
