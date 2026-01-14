# Positron GAM SNMP OID Discoveries

This document captures the reverse-engineered SNMP OID mappings for Positron GAM devices, discovered through SNMP walks on a real GAM-4-C device (10.0.99.61).

## Device Information

- **Model**: GAM-4-CX-AC (4-port Coax G.hn Access Multiplexer)
- **Firmware**: GAM-4/8-C_v1.5.4
- **Test Date**: 2025-10-21

## Enterprise OID

- **Positron Enterprise Number**: 20095
- **Base OID**: 1.3.6.1.4.1.20095

## Port Information Table

**Base OID**: `1.3.6.1.4.1.20095.2001.11.1.2.1.1`

### Table Structure

The port table uses the format: `{base_oid}.{sub_oid}.{index}`

**Indices Found**: 1000001 through 1000006 (6 entries for a 4-port device)

### Sub-OID Mappings (Best Guess Without MIB)

| Sub-OID | Field Name | Values Observed | Interpretation |
|---------|------------|-----------------|----------------|
| .2 | Unknown | 2 (constant) | Port table identifier? |
| .3 | Port Indicator | 6, 5, 8 | Port number or type? (6=disabled, 5/8=active?) |
| .4 | Unknown | 0 (constant) | Reserved/unused |
| .5 | **Link Status** | 0, 1 | **0 = down, 1 = up/connected** |
| .6 | Unknown | 0 (constant) | Reserved/unused |
| .7 | Speed Indicator | 2014, 2048 | Bandwidth profile? (2014=standard, 2048=enhanced?) |
| .8 | Unknown | 2 (constant) | Administrative status? |
| .9 | Unknown | 0 (constant) | Reserved/unused |
| .10 | Unknown | 2 (constant) | Unknown |
| .11 | **Subscriber Count** | 0, 1, 3 | **Number of active CPE on coax port** |

### Example Data from GAM-4-C

```
Index 1000001: port_indicator=6, link=down, speed=2014, subscribers=0
Index 1000002: port_indicator=6, link=down, speed=2014, subscribers=0
Index 1000003: port_indicator=6, link=down, speed=2014, subscribers=0
Index 1000004: port_indicator=6, link=down, speed=2014, subscribers=0
Index 1000005: port_indicator=8, link=UP,   speed=2048, subscribers=3  <- ACTIVE PORT
Index 1000006: port_indicator=5, link=down, speed=2048, subscribers=1
```

## Key Findings

1. **Ports with Activity**: Indices 1000005 and 1000006 show actual port usage
   - Index 1000005 has link UP with 3 active subscribers (CPE devices)
   - Index 1000006 has 1 subscriber configured but link currently down

2. **Port Mapping Challenge**: 4-port device shows 6 SNMP indices
   - Likely represents: 4 physical ports + 2 management/virtual interfaces
   - OR: Table includes disabled/future ports

3. **Subscriber Count on Coax**: Sub-OID .11 appears to track multiple CPE per port
   - Matches GAM-C coax capability (up to 16 subscribers per port)
   - Confirmed: Port 1000005 shows 3 active subscribers

## Standard MIB-2 Interface Table

The device also responds to standard interface queries:

- **Interface Count**: Reports 4100+ interfaces (likely VLAN interfaces)
- **Interface Descriptions**: `1.3.6.1.2.1.2.2.1.2.{index}` returns "VLAN {index}"
- **Interface Types**: Type 135 (l2vlan) for VLAN interfaces
- **Operational Status**: `1.3.6.1.2.1.2.2.1.8.{index}` (1=up, 2=down)

### Physical Port Interfaces

Did NOT find standard Ethernet/GigabitEthernet interface descriptions. The device appears to represent all interfaces as VLANs.

## Bridge Port to SNMP Index Mapping (CRITICAL FINDING!)

**Bridge MIB Mapping Discovered** via `1.3.6.1.2.1.17.1.4.1.2` (dot1dBasePortIfIndex):

| Bridge Port | SNMP Index | Physical Interface | Connected MACs |
|-------------|------------|-------------------|----------------|
| 1 | 1000001 | G.hn 1/1 (Port 1) | `00:0e:d8:1e:58:04` |
| 2 | 1000002 | G.hn 1/2 (Port 2) | `00:0e:d8:1e:58:05` |
| 3 | 1000003 | G.hn 1/3 (Port 3) | `00:0e:d8:1e:58:06` |
| 4 | 1000004 | G.hn 1/4 (Port 4) | `00:0e:d8:1e:58:07`, `18:fd:74:17:35:9f` |
| 5 | 1000005 | Internal/Virtual? | Multiple Positron MACs |
| 6 | 1000006 | 10GigE Uplink | All network traffic |

**NOTE**: The config shows `ghn endpoint 1` with MAC `00:0e:d8:1c:95:08` on port 4, but bridge table shows different MACs. This suggests:
1. The config endpoint MAC might be outdated or represents a different endpoint
2. Current active MACs are `00:0e:d8:1e:58:xx` (Positron endpoints on all 4 ports)
3. Additional client device `18:fd:74:17:35:9f` is behind endpoint on port 4

### MAC Address Discovery via Bridge MIB

**OID**: `1.3.6.1.2.1.17.4.3.1.1` (dot1dTpFdbAddress) and `.2` (dot1dTpFdbPort)

This standard bridge MIB provides MAC-to-port mappings for all learned MAC addresses.

**Positron Endpoint MACs Found** (vendor OUI `00:0e:d8`):
- `00:0e:d8:1e:58:04` on Bridge Port 1 (G.hn 1/1)
- `00:0e:d8:1e:58:05` on Bridge Port 2 (G.hn 1/2)
- `00:0e:d8:1e:58:06` on Bridge Port 3 (G.hn 1/3)
- `00:0e:d8:1e:58:07` on Bridge Port 4 (G.hn 1/4)

**Client Device MACs**: Multiple non-Positron MACs on Bridge Port 6 (uplink)

## Missing Information (Need MIB File)

Without the official Positron MIB file, we cannot definitively determine:

1. ✅ ~~**MAC addresses of connected CPE**~~ - **SOLVED**: Use Bridge MIB `1.3.6.1.2.1.17.4.3.1.x`
2. ✅ ~~**Port numbering mapping**~~ - **SOLVED**: Bridge Port to Interface Index mapping discovered
3. **Link speed/SNR values** - Where actual G.hn link speeds and signal quality are stored
4. **G.hn specific parameters** - MIMO status, VectorBoost settings, power masks
5. **Per-endpoint statistics** - Traffic counters, error rates per CPE

## Recommendations

1. **Contact Positron Support**: Request official MIB file for proper OID documentation
2. **Physical Testing**: Connect/disconnect CPE and observe OID value changes to confirm mappings
3. **Compare Models**: Test on GAM-12-M or GAM-24-C to see if patterns hold
4. **Alternative Discovery**: Check if device supports NETCONF, REST API, or CLI for better data access

## Implementation Status

### Implemented
- ✅ SNMP client with `get_gam_ports_info()` method
- ✅ API endpoint `/api/v1/gam/devices/{id}/sync-ports` for port synchronization
- ✅ Basic port status detection (up/down based on .5 sub-OID)
- ✅ Subscriber count tracking (from .11 sub-OID)

### TODO
- ⏳ Map SNMP indices to physical port numbers
- ⏳ Discover CPE MAC addresses
- ⏳ Extract G.hn link speeds and SNR values
- ⏳ Create unconfigured CPE detection endpoint
- ⏳ Implement frontend sync button on device detail page

## Usage Example

```python
from app.utils.snmp_client import SNMPClient

snmp = SNMPClient('10.0.99.61', 'public')
port_info = await snmp.get_gam_ports_info()

# Returns:
# {
#   1000005: {
#     'positron_index': 1000005,
#     'port_indicator': 8,
#     'link_status': 'up',
#     'speed_indicator': 2048,
#     'subscriber_count': 3,
#     'raw_data': {'oid_3': 8, 'oid_5': 1, 'oid_7': 2048, 'oid_11': 3}
#   },
#   ...
# }
```
