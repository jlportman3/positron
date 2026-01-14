# GAM Knowledge Base for Development

**Auto-generated from Positron GAM Documentation**
**Last Updated:** 2025-10-21

This document contains essential knowledge extracted from GAM technical documentation to support development of the Positron GAM Management System.

---

## 1. Device Models & Specifications

### Supported GAM Models

| Model | Ports | Technology | Max Subscribers per Port | Notes |
|-------|-------|------------|-------------------------|-------|
| GAM-4-M/MX/MRX | 4 | Copper (Cat3/5) | 1 | SISO/MIMO capable |
| GAM-8-M/MX/MRX | 8 | Copper (Cat3/5) | 1 | SISO/MIMO capable |
| GAM-12-M | 12 | Copper (Cat3/5) | 1 | SISO/MIMO capable |
| GAM-24-M | 24 | Copper (Cat3/5) | 1 | SISO/MIMO capable |
| GAM-4-C/CX/CRX | 4 | Coax (RG59/RG6) | 16 | Multi-subscriber per port |
| GAM-12-C | 12 | Coax (RG59/RG6) | 16 | Multi-subscriber per port |
| GAM-24-C | 24 | Coax (RG59/RG6) | 16 | Multi-subscriber per port |

**Key Differences:**
- **M-series (Copper):** One subscriber per port, supports SISO/MIMO modes
- **C-series (Coax):** Up to 16 subscribers per port (using TDMA)
- **X/RX variants:** Extended features (exact differences TBD from docs)

### Distance Capabilities
- **Copper (Cat3 single pair):** Up to 150 meters / 500 feet
- **Copper (Cat3 2-pair MIMO):** Up to 250 meters / 800 feet
- **Coax:** Up to 800 meters (exact spec varies by model)

### Port Types
- **10G SFP+ Uplink Ports:** 1-2 ports depending on model (fiber/copper via SFP modules)
- **G.hn Downstream Ports:** 4, 8, 12, or 24 ports for subscriber connections

---

## 2. Default Configuration & Network Settings

### Default Credentials & Access
- **Default Management IP:** `192.168.1.1` (verify from docs)
- **Default Subnet Mask:** `255.255.255.0`
- **Default Gateway:** `0.0.0.0` (unconfigured)
- **SNMP Community:** `public` (default - CHANGE IN PRODUCTION)
- **Web Interface Port:** 80 (HTTP) / 443 (HTTPS)
- **SSH Port:** 22
- **JSON-RPC API Port:** 8080

### VLAN Configuration
- **Management VLAN:** Typically VLAN 4093 (configurable)
- **Subscriber VLAN Range:** 1-4094 (recommend 100-4000 for subscribers)
- **Default VLAN:** VLAN 1 (untagged)
- **Reserved VLANs:** 4093 (management), 4094 (internal use)

### Important VLAN Behaviors
- Each subscriber can be assigned a specific VLAN ID
- VLAN translation supported at endpoint level
- Priority tagging (802.1p) supported for QoS
- IGMP snooping enabled per-VLAN for IPTV multicast

---

## 3. Management Interfaces

### JSON-RPC API

**Base Endpoint:**
```
http://${USERNAME}:${PASSWORD}@${IP_ADDRESS}:${PORT}/json_rpc
```

**Authentication:** HTTP Basic Auth in URL or headers

**Example API Call:**
```json
{
  "method": "jsonRpc.status.introspection.generic.inventory.get",
  "params": [""],
  "id": "1"
}
```

**Key API Capabilities:**
- Device status and inventory retrieval
- Configuration management
- Subscriber provisioning
- Statistics collection
- Firmware management

### CLI Access (SSH)

**Connection:** SSH to management IP (default port 22)

**Common Command Categories:**
- `show` - Display status, statistics, configuration
- `configure terminal` - Enter configuration mode
- `ghn` - G.hn specific commands for endpoint management
- `vlan` - VLAN configuration
- `interface` - Port/interface configuration

**Key CLI Commands:**

```bash
# Discovery & Status
show all ghn endpoints           # Discover all connected G.hn endpoints
show interface ghn 1/1-24 status # Show status of G.hn ports
show vlan                        # Display VLAN configuration

# G.hn Port Statistics
show ghn port <port_number> statistics

# VLAN Configuration
configure terminal
  vlan <vlan_id>
  name <vlan_name>

# Endpoint Management
show interface ghn <port> status
show interface ghn <port> capabilities
```

### SNMP Management

**SNMP Version:** v2c supported (v3 capabilities TBD)
**Community String:** `public` (default)
**MIBs:** Proprietary Positron MIBs + standard interface MIBs

**Use Cases:**
- Monitoring link status
- Collecting port statistics (TX/RX rates, errors)
- Discovery of device inventory
- Trap-based alerting

---

## 4. Subscriber Provisioning

### Endpoint Configuration Requirements

Each subscriber requires:
1. **Endpoint MAC Address** (G.hn CPE device MAC)
2. **Port Assignment** (which physical port on GAM)
3. **VLAN ID** (subscriber's service VLAN)
4. **Bandwidth Profile** (upload/download speed limits)
5. **Subscriber Name** (1-31 alphanumeric characters, unique)

### Bandwidth Profiles

**Bandwidth Ranges:**
- **Coax (C-series):** 10 to 800 Mbps per subscriber
- **Copper (M-series):** Depends on distance and SISO/MIMO mode
  - SISO: Typically up to 500 Mbps
  - MIMO: Up to 1+ Gbps at short distances

**Profile Configuration:**
- Profiles define downstream and upstream rate limits
- Applied per-subscriber (per endpoint MAC)
- Configurable via CLI, Web UI, or JSON-RPC API

### Multi-Subscriber Support (Coax Only)

- **Coax ports support up to 16 subscribers per port**
- Each subscriber identified by unique endpoint MAC
- Bandwidth shared using TDMA (time-division)
- Each subscriber can have different VLAN and bandwidth profile

---

## 5. IPTV & Multicast Configuration

### IGMP Snooping

**Best Practices:**
- Enable IGMP snooping ONLY on IPTV VLAN
- GAM should NOT be IGMP querier (querier at video source)
- Set multicast priority tagging (PCP=5, CoS=2, DEI=0)

**Configuration Steps:**
1. Enable IGMP snooping globally
2. Enable snooping on specific IPTV VLAN
3. Set VLAN ID to specific IPTV VLAN
4. Enable Leave Proxy for faster channel changes
5. Configure priority tagging for QoS

### QAM TV Mixing (Coax Models)

- Coax models support mixing QAM TV with G.hn traffic
- QAM frequencies >200 MHz (RF spectrum)
- G.hn uses 2-100 MHz (managed by GAM)
- Use diplexers/splitters at subscriber premises

---

## 6. Key Technical Concepts

### G.hn Technology

**G.hn (ITU-T G.9960/G.9961):**
- Unified home networking standard
- Works over coax, phone lines (Cat3), and power lines
- Frequency range: 2-100 MHz (for coax/copper)
- Supports SISO (single pair) and MIMO (dual pair) modes

**Operating Modes:**
- **SISO:** Single twisted pair or coax, lower speeds, longer distances
- **MIMO:** Dual twisted pair, higher speeds, shorter distances

### Port Types in CLI

When using CLI commands, port types are referenced as:
- `10G 1/1` - 10 Gigabit Ethernet uplink port 1
- `Gi 1/1` - Gigabit Ethernet port 1
- `G.hn 1/1-24` - G.hn ports 1 through 24

---

## 7. Troubleshooting Reference

### Common Issues

**No Endpoint Discovery:**
1. Verify endpoint is powered and connected
2. Check physical layer (cable continuity)
3. Verify endpoint MAC is not already registered on another port
4. Check VLAN configuration matches endpoint

**Low Link Speeds:**
1. Check cable quality and distance
2. Verify SISO vs MIMO mode
3. Check for interference (notch filters may be needed)
4. Review SNR (Signal-to-Noise Ratio) statistics

**IPTV Issues:**
1. Verify IGMP snooping enabled on IPTV VLAN only
2. Ensure GAM is not configured as IGMP querier
3. Check multicast priority tagging (PCP=5)
4. Verify sufficient bandwidth allocation

### Key Statistics to Monitor

**Per-Port Metrics:**
- Link status (up/down)
- Link speed (Mbps actual negotiated rate)
- SNR values (signal quality)
- Packet counters (TX/RX packets, bytes)
- Error counters (CRC, discards, collisions)

**Per-Endpoint Metrics:**
- Endpoint MAC address
- Connection status
- Bandwidth utilization
- VLAN assignment
- Firmware version

---

## 8. Software Upgrade Procedures

### Firmware Upgrade Process

1. Download firmware from Positron FTP server (credentials required)
2. Upload to GAM via web interface or TFTP/FTP
3. Verify firmware file integrity
4. Schedule upgrade (immediate or scheduled)
5. Reboot required after upgrade
6. Verify new firmware version post-upgrade

**Supported Models for Upgrades:**
- GAM-4-M/C, GAM-8-M, GAM-12-M/C, GAM-24-M/C

**Upgrade Method Options:**
- Web UI upload
- FTP/TFTP server pull
- CLI-based upgrade commands

---

## 9. Security Considerations

### Default Security Settings

**CHANGE IMMEDIATELY IN PRODUCTION:**
- Default SNMP community: `public`
- Default admin credentials (vendor-specific, consult docs)
- Default management VLAN may be accessible

### Recommended Security Hardening

1. **Change default passwords** for all admin accounts
2. **Configure strong SNMP community strings** (or use SNMPv3)
3. **Isolate management VLAN** from subscriber traffic
4. **Enable SSH** and disable Telnet if available
5. **Restrict management access** by IP/subnet (ACLs)
6. **Use RADIUS/TACACS+** for centralized AAA if managing multiple GAMs
7. **Enable HTTPS** for web interface, disable HTTP

---

## 10. Integration Points for Management System

### Required Management System Capabilities

Based on documentation, the management system should support:

1. **Device Discovery & Onboarding**
   - SNMP-based discovery of GAM devices on network
   - Auto-detection of model, firmware version, port count
   - Bulk import of GAM devices from CSV/spreadsheet

2. **Configuration Management**
   - VLAN configuration and validation
   - Bandwidth profile creation and assignment
   - Backup and restore of device configurations
   - Template-based provisioning for new devices

3. **Subscriber Lifecycle**
   - Provision new subscribers (assign MAC, VLAN, bandwidth)
   - Modify existing subscriber settings
   - Suspend/resume service (bandwidth throttling or port disable)
   - De-provision and remove subscribers
   - Bulk operations for multiple subscribers

4. **Monitoring & Alerts**
   - Real-time port status monitoring
   - Link speed and quality metrics (SNR)
   - Bandwidth utilization tracking
   - Alerting on port down, high errors, threshold breaches
   - Historical trend data and graphing

5. **Billing System Integration**
   - Sync subscribers from Sonar/Splynx
   - Map external customer ID to GAM subscriber
   - Webhook handlers for customer create/update/delete events
   - Scheduled sync jobs for bulk updates
   - Service activation/suspension based on billing status

6. **Reporting**
   - Device inventory reports
   - Port utilization reports
   - Subscriber list with service details
   - Capacity planning (available ports per GAM)
   - Audit logs for all provisioning changes

---

## 11. Important OIDs & API Methods (For Reference)

### JSON-RPC API Methods Identified

```
jsonRpc.status.introspection.generic.inventory.get
```

*(Additional methods to be documented as discovered in testing)*

### SNMP OIDs

*(To be populated after MIB analysis or vendor documentation)*

Standard OIDs that should work:
- `1.3.6.1.2.1.1.1.0` - sysDescr (system description)
- `1.3.6.1.2.1.1.3.0` - sysUpTime
- `1.3.6.1.2.1.2.2.1.*` - ifTable (interface statistics)

---

## 12. Next Steps for Development

### Priority 1: Core Device Management
- [ ] Implement SNMP client for device discovery
- [ ] Implement SSH client for CLI command execution
- [ ] Implement JSON-RPC API client
- [ ] Build device model detection and port count mapping
- [ ] Create configuration backup/restore functionality

### Priority 2: Subscriber Provisioning
- [ ] Endpoint MAC validation and duplicate detection
- [ ] VLAN assignment logic with validation
- [ ] Bandwidth profile CRUD operations
- [ ] Bulk subscriber import from CSV
- [ ] Port availability checking (accounting for coax 16-subscriber limit)

### Priority 3: Billing Integration
- [ ] Sonar API integration (customer sync)
- [ ] Splynx API integration (customer sync)
- [ ] Webhook receivers for real-time updates
- [ ] Two-way sync logic (conflict resolution)
- [ ] Celery workers for scheduled sync jobs

### Priority 4: Monitoring & Alerting
- [ ] SNMP polling for port statistics
- [ ] Link status monitoring
- [ ] Alert threshold configuration
- [ ] Email/webhook notifications
- [ ] Historical metrics storage and graphing

---

## 13. References

### Documentation Sources
- **PAS - GAM CLI guide.pdf** (139 pages) - CLI command reference
- **PAS - GAM Json API.pdf** (66 pages) - JSON-RPC API documentation
- **PAS - GAM Installation and Activation Guide** (90 pages) - Setup procedures
- **PAS - GAM Quick Start Guide** (36 pages) - Overview and quick setup
- **PAS - GAM VLAN Configuration Guide** (8 pages) - VLAN best practices
- **PAS - GAM IGMP Snooping Guide** (10 pages) - IPTV multicast setup
- **PAS - GAM Basic Troubleshooting Guide** (9 pages) - Common issues

### Vendor Information
- **Vendor:** Positron Access Solutions
- **Website:** http://www.positronaccess.com/
- **Product Line:** GAM (G.hn Access Multiplexer)

---

## Appendix: Extracted Commands Summary

### Most Useful Show Commands
```bash
show all ghn endpoints                    # Discover all G.hn endpoints
show interface ghn 1/1-24 status         # G.hn port status
show interface ghn <port> statistics     # Port statistics
show vlan                                # VLAN configuration
show access management                   # Management access settings
show aggregation                         # Link aggregation status
show alarm active                        # Active alarms
show clock                              # System time
```

### Configuration Examples
```bash
# Enter configuration mode
configure terminal

# Create VLAN
vlan 100
  name "Subscribers"

# Configure G.hn endpoint (example structure, verify exact syntax)
ghn endpoint <mac_address>
  vlan 100
  bandwidth-profile <profile_name>

# IGMP snooping for IPTV
ip igmp snooping vlan 200
  enable
  leave-proxy enable
  priority 5
```

---

**END OF KNOWLEDGE BASE**
