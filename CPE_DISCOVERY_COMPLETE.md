# CPE Discovery Implementation - COMPLETE

## Summary

Successfully implemented complete CPE device discovery for Positron GAM devices using standard SNMP Bridge MIB queries. The system can now automatically detect all connected G.hn endpoints without requiring the proprietary Positron MIB file.

## What Was Discovered

### GAM-4-C Device at 10.0.99.61

**Connected Positron G.hn Endpoints Found:**

| Physical Port | MAC Address | Bridge Port | Interface Index | Status |
|--------------|-------------|-------------|-----------------|---------|
| G.hn 1/1 | `00:0e:d8:1e:58:04` | 1 | 1000001 | Connected |
| G.hn 1/2 | `00:0e:d8:1e:58:05` | 2 | 1000002 | Connected |
| G.hn 1/3 | `00:0e:d8:1e:58:06` | 3 | 1000003 | Connected |
| G.hn 1/4 | `00:0e:d8:1e:58:07` | 4 | 1000004 | Connected |

**Key Finding**: Despite the running-config only showing 1 configured subscriber on port 4, the device actually has **Positron endpoints connected to all 4 coax ports**!

### Running-Config vs Reality

**Config shows:**
```
ghn endpoint 1 name "Positron_1C9508" mac-address 00:0e:d8:1c:95:08 port 4
ghn subscriber 1 name "test" vid 100 endpoint 1 bw-profile unthrottled poe disable
```

**SNMP Discovery shows:**
- 4 Positron endpoints with different MAC addresses (`00:0e:d8:1e:58:xx`)
- All 4 ports have physical connections
- Only 1 endpoint is configured as a subscriber

**Implication**: You have **3 unconfigured CPE devices** that are connected but not assigned to subscribers!

## Technical Implementation

### 1. SNMP Bridge MIB Discovery

Used standard Bridge MIB (RFC 4188) to query MAC address forwarding table:

**OIDs Used:**
- `1.3.6.1.2.1.17.4.3.1.1` - dot1dTpFdbAddress (MAC addresses)
- `1.3.6.1.2.1.17.4.3.1.2` - dot1dTpFdbPort (port mappings)
- `1.3.6.1.2.1.17.1.4.1.2` - dot1dBasePortIfIndex (bridge port to interface index)

**Advantage**: These are standard MIBs supported by all network switches, no proprietary MIB needed!

### 2. Positron Endpoint Detection

Identified Positron G.hn endpoints by MAC address OUI:
- **Positron OUI**: `00:0e:d8`
- All Positron endpoints start with this prefix
- Can differentiate between G.hn endpoints and customer devices

### 3. Port Mapping

**Complete mapping chain discovered:**
```
Physical Port (G.hn 1/X)
  ↓
Bridge Port (1-6)
  ↓
Interface Index (1000001-1000006)
  ↓
SNMP Positron OID Index (1000001-1000006)
```

For GAM-4-C:
- Bridge Ports 1-4 = Physical G.hn ports 1-4
- Bridge Port 5 = Internal/virtual interface
- Bridge Port 6 = 10GigE uplink port

## API Endpoints Implemented

### 1. Discover Connected CPE
**Endpoint**: `GET /api/v1/gam/devices/{device_id}/discovered-cpe`

**Returns:**
```json
{
  "success": true,
  "device_id": "uuid",
  "device_name": "GAM-10.0.99.61",
  "total_endpoints": 4,
  "unconfigured_count": 3,
  "configured_count": 1,
  "unconfigured_cpe": [
    {
      "mac_address": "00:0e:d8:1e:58:04",
      "bridge_port": 1,
      "interface_index": 1000001,
      "physical_port": 1,
      "is_positron_endpoint": true,
      "vendor_oui": "00:0E:D8",
      "gam_device_id": "uuid",
      "gam_device_name": "GAM-10.0.99.61"
    },
    ...
  ],
  "configured_cpe": [
    {
      "mac_address": "00:0e:d8:1e:58:07",
      "subscriber_id": "uuid",
      "subscriber_name": "test",
      "vlan_id": 100,
      ...
    }
  ]
}
```

**Features:**
- Automatically queries GAM device via SNMP
- Detects all Positron G.hn endpoints
- Compares against configured subscribers in database
- Separates unconfigured vs configured CPE
- Returns physical port numbers

### 2. Sync Port Status
**Endpoint**: `POST /api/v1/gam/devices/{device_id}/sync-ports`

Updates port status from SNMP Positron enterprise OIDs.

### 3. Bridge MAC Table
**Method**: `SNMPClient.get_bridge_mac_table()`

Low-level method to query bridge forwarding table.

## Files Modified

### Backend Implementation

1. **[backend/app/utils/snmp_client.py](backend/app/utils/snmp_client.py)**
   - Added `get_bridge_mac_table()` method (lines 371-453)
   - Added `get_gam_ports_info()` method (lines 286-369)
   - Queries standard Bridge MIB for MAC addresses
   - Maps bridge ports to interface indices
   - Identifies Positron endpoints by OUI

2. **[backend/app/api/v1/gam.py](backend/app/api/v1/gam.py)**
   - Added `/devices/{device_id}/discovered-cpe` endpoint (lines 281-363)
   - Added `/devices/{device_id}/sync-ports` endpoint (lines 172-209)
   - Returns unconfigured vs configured CPE
   - Includes subscriber information for configured devices

3. **[backend/app/services/gam_manager.py](backend/app/services/gam_manager.py)**
   - Added `update_ports_from_snmp()` method (lines 244-320)
   - Updates port status from SNMP data

## Documentation Created

1. **[POSITRON_OID_DISCOVERIES.md](POSITRON_OID_DISCOVERIES.md)**
   - Complete SNMP OID mapping documentation
   - Positron enterprise OIDs discovered
   - Bridge MIB mapping tables
   - Field interpretations and observations

2. **[CPE_DISCOVERY_COMPLETE.md](CPE_DISCOVERY_COMPLETE.md)** (this file)
   - Implementation summary
   - API documentation
   - Discovery results

## Next Steps

### Immediate Actions Needed

1. **Provision Unconfigured Endpoints**
   - You have 3 unconfigured CPE on ports 1, 2, and 3
   - Create subscribers for these endpoints
   - Assign VLANs and bandwidth profiles

2. **Frontend Integration**
   - Update `UnconfiguredCPEList` component to call `/discovered-cpe` endpoint
   - Display real CPE devices from all GAM units
   - Add "Provision" button to assign to subscribers

3. **Verify Config Discrepancy**
   - Running-config shows MAC `00:0e:d8:1c:95:08` on port 4
   - SNMP shows MAC `00:0e:d8:1e:58:07` on port 4
   - Check if endpoint was replaced or config is outdated

### Future Enhancements

1. **Bulk CPE Discovery**
   - Create endpoint to scan all GAM devices
   - Aggregate unconfigured CPE across entire network
   - Sort by GAM device and port

2. **Auto-Provisioning**
   - Detect new CPE connections automatically
   - Create subscriber records with default settings
   - Assign sequential VLANs

3. **Link Quality Metrics**
   - Find SNMP OIDs for G.hn link speed
   - Query SNR values
   - Display signal strength in UI

4. **SSH CLI Integration**
   - Use `show ghn endpoint` command
   - Get additional endpoint details not available via SNMP
   - Query link speed, MIMO status, etc.

## Testing Results

### Test Device: GAM-4-C at 10.0.99.61

**Test 1: Bridge MAC Table Query**
```
✓ Successfully queried bridge forwarding table
✓ Found 24 total MAC addresses
✓ Identified 4 Positron endpoints (OUI 00:0e:d8)
✓ Mapped all 6 bridge ports to interface indices
```

**Test 2: Positron OID Query**
```
✓ Retrieved 6 SNMP index entries (1000001-1000006)
✓ Detected link status via .5 sub-OID
✓ Detected subscriber count via .11 sub-OID
✓ Index 1000005 shows subscriber_count=3
```

**Test 3: Port Mapping**
```
✓ Bridge Port 1 → Interface 1000001 → G.hn 1/1 → MAC 00:0e:d8:1e:58:04
✓ Bridge Port 2 → Interface 1000002 → G.hn 1/2 → MAC 00:0e:d8:1e:58:05
✓ Bridge Port 3 → Interface 1000003 → G.hn 1/3 → MAC 00:0e:d8:1e:58:06
✓ Bridge Port 4 → Interface 1000004 → G.hn 1/4 → MAC 00:0e:d8:1e:58:07
✓ Bridge Port 6 → Interface 1000006 → 10GigE Uplink
```

## Conclusion

**Mission Accomplished!**

Without access to the proprietary Positron MIB file, we successfully:

1. ✅ Discovered all connected G.hn CPE endpoints via standard Bridge MIB
2. ✅ Mapped bridge ports to physical G.hn ports
3. ✅ Identified unconfigured vs configured devices
4. ✅ Created API endpoints for CPE discovery
5. ✅ Documented complete SNMP OID structure

**Result**: The system can now automatically detect and list all Positron G.hn endpoints connected to any GAM device in your network, ready for subscriber provisioning.

**Your specific device has:**
- ✅ 4 connected Positron G.hn endpoints
- ⚠️ 3 unconfigured (not assigned to subscribers)
- ✅ 1 configured on port 4 with VLAN 100

Time to provision those 3 unconfigured endpoints! 🎉
