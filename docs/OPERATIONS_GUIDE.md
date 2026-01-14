# Positron GAM Operations Guide

## Table of Contents
1. [Connecting to the GAM](#connecting-to-the-gam)
2. [Initial Setup and Configuration](#initial-setup-and-configuration)
3. [Monitoring Operations](#monitoring-operations)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance Procedures](#maintenance-procedures)

---

## Connecting to the GAM

### Default Access Credentials

**Via Web/Ethernet (Management Port):**
- Connect Ethernet cable from laptop/PC to MGMT port on GAM
- Set PC Ethernet port to IP: `192.168.10.2`, Mask: `255.255.255.0`
- GAM Management IP: `192.168.10.1`
- Username: `admin`
- Password: *blank* (no password by default)
- Access via browser: `http://192.168.10.1`

**Via Serial/CRAFT Port:**
- Serial settings: 115200 8, N, 1
- Username: `admin`
- Password: *blank*
- A Cisco console cable will work

### Management Port Locations

**Indoor GAM:**
- Ethernet MGMT Port: Front panel (green RJ-45 port)
- Serial MGMT Port: Front panel (DB-9 or RJ-45 console port)

**Outdoor GAM:**
- Accessible inside weatherproof enclosure
- Ethernet and Serial ports clearly labeled

---

## Initial Setup and Configuration

### 1. Configure System Information

**Path:** `Configuration > System > Information`

```
System Name: [your-gam-name]  # Used in SNMP, web, CLI, and DHCP Option-82 Remote ID
System Contact: [contact-name]
System Location: [physical-location]
```

**Important:**
- Click "Save" to save to running config
- Click disk icon (upper right) to save to flash (persistent)

### 2. Configure Bandwidth Profiles

**Path:** `Configuration > G.hn > Bandwidth Profile > Add New Bandwidth Plan`

Bandwidth profiles are rate limiters applied per subscriber:
- Optional feature (subscribers can be "Unthrottled")
- **Add 6% to the rate for TCP overhead**

**Example Profiles:**
```
Profile Name: 100/100
Downstream: 106 Mbps (100 + 6%)
Upstream: 106 Mbps (100 + 6%)

Profile Name: 500/500
Downstream: 530 Mbps (500 + 6%)
Upstream: 530 Mbps (500 + 6%)

Profile Name: 1000/1000
Downstream: 1060 Mbps (1000 + 6%)
Upstream: 1060 Mbps (1000 + 6%)
```

### 3. Configure Endpoints

**Path:** `Configuration > G.hn > Endpoints > Add New Endpoint`

Endpoints are physical G.hn bridges (G1001/G1002) installed at subscriber locations.

**Steps:**
1. Click "Add New Endpoint"
2. Enter MAC address (or select from discovered table)
3. Enter mandatory Name field
4. Enter optional Description (friendly name)
5. Save configuration

### 4. Configure G.hn Ports

**Path:** `Configuration > G.hn > Ports`

**For Copper (Twisted Pair) Ports:**
- Default mode: MIMO (2-pair)
- If only 1 pair available: Change to SISO mode (1-pair)

**For Coax Ports:**
- Simply activate the port (already in P2MP mode)
- Supports up to 16 subscribers per port via passive splitters

**Port Isolation:**
- GAM supports port isolation
- Traffic between ports is isolated
- Traffic between subscribers on same coax port is also isolated

### 5. Configure Subscribers

**Path:** `Configuration > G.hn > Subscribers > Add New Subscriber`

A subscriber is the service configuration linking:
- VLAN
- Endpoint (CPE device)
- Bandwidth profile

**Configuration Steps:**

**Step 1 - Add New Subscriber:**
```
Subscriber Name: [unique-identifier]
VLAN: [vlan-id]  # See VLAN strategies below
```

**Step 2 - Configure Service:**
```
Double Tagging: No (unless using Q-in-Q)
Remapped VID: 0 (no VLAN remapping)
Endpoint Tagging: Unchecked (traffic untagged on subscriber side by default)
Trunk Mode: Unchecked
Allowed Tagged VLAN: [leave empty]
Bandwidth Plan: [select-profile-or-Unthrottled]
Port #2 VLAN: [if needed for multi-service]
Endpoint: [select-configured-endpoint]
Description: [friendly-description]
```

**VLAN Configuration Strategies:**

1. **Unique VLAN per Subscriber** (Recommended for managed services):
   - Assign each subscriber a unique VLAN (e.g., 100, 101, 102...)
   - Easier accounting and traffic management
   - Better isolation at Layer 2

2. **Shared VLAN with Port Isolation**:
   - All subscribers on same VLAN (e.g., VLAN 100)
   - GAM port isolation prevents inter-subscriber traffic
   - Simpler VLAN management
   - Requires upstream CGNAT or large subnet

**Traffic Tagging Options:**
- **Default:** Traffic untagged on subscriber side (most common)
- **Keep Tag:** Option to preserve VLAN tag (for subscriber routers supporting 802.1Q)
- **Allow Other VLANs:** Pass through additional VLANs (multi-service)

### 6. Configure Ethernet Uplink Ports

**Path:** `Configuration > Ports (Ethernet)`

**10G SFP+ Ports:**
- Default: "10G FDX" auto-negotiation
- Usually auto-detects 10G or 1G SFP modules
- **Troubleshooting:** If 1G copper SFP doesn't link, manually select speed:
  - Options: Auto, 10Gbps FDX, 1Gbps FDX, 100Mbps FDX

**Supported SFP Modules:**
- 10G SR/LR fiber
- 1G SX/LX fiber
- 1G copper RJ-45
- DAC (Direct Attach Copper) cables
- PON SFP ONT modules (XGS-PON, GEPON)

### 7. Configure VLAN Trunking (Uplink)

**Path:** `Configuration > VLANs > Configuration`

**Default Configuration:**
- Uplink ports: Trunk mode
- Allowed VLANs: 3-4094 (all VLANs)
- Reserved VLANs: 1, 2, 4095 (internal use)
- Default management VLAN: 4093
- Default unprovisioned VLAN: 4094

**To Untag a VLAN on Uplink:**
1. Set Port VLAN: [vlan-id]
2. Egress Tagging: "Untag Port VLAN"

**Common VLAN Assignments:**
```
VLAN 4093: GAM Management (inband)
VLAN 100-199: Subscriber data VLANs
VLAN 200: IPTV/Multicast (if using)
VLAN 201: VoIP services (if using)
```

### 8. Configure Inband Management

**Path:** `Configuration > System > IP > Add Interface`

**For Remote Management via Uplink:**

1. Create VLAN interface:
   ```
   VLAN: 4093 (or your management VLAN)
   Mode: Host
   ```

2. Configure IP (choose one):
   - **DHCP:** Enable DHCP client
   - **Static IP:**
     ```
     IPv4 Address: [management-ip]
     Mask Length: [cidr-prefix]
     ```

3. Add default route (if using static IP):
   ```
   Network: 0.0.0.0
   Mask Length: 0
   Gateway: [upstream-gateway]
   Next Hop VLAN: [management-vlan]
   ```

### 9. Configure NTP (Optional but Recommended)

**Path:** `Configuration > System > NTP`

```
Mode: Enabled
Server 1: [ntp-server-ip or pool.ntp.org]
Server 2: [backup-ntp-server] (optional)
```

**Path:** `Configuration > System > Time Zone`
- Select appropriate time zone
- Configure daylight saving if applicable

**Note:** Date/time not required for GAM to operate, but used for alarms and event logging.

### 10. Configure Security

**Path:** `Configuration > Security > Users`

**Change Default Password (Critical):**
1. Select "admin" user
2. Set new password
3. Save configuration

**Access Level Configuration:**
**Path:** `Configuration > Security > Privilege Levels`

Configure read/write access per menu section:
- Configuration: Read-only / Read-write
- Status/Statistics: Read-only / Read-write
- Diagnostics: Various privilege levels (5, 10, 15)

---

## Monitoring Operations

### 1. Monitor G.hn Service Overview

**Path:** `Monitor > G.hn > Overview`

This page shows all endpoints (discovered and configured).

**For Coax GAM:**
- Click green circle (●) to expand port and see all endpoints

**For Copper GAM:**
- All MACs displayed directly

**Status Indicators:**
- **Green (●):** Endpoint connected, G.hn link UP
- **Blue (●):** Endpoint configured but not connected
- **Yellow (⚠):** Endpoint firmware mismatch (needs upgrade)
- **Red (●):** Error condition

**Columns Displayed:**
- Port Name / Status
- MAC Address
- RFC 5517 Role (Domain Master / Isolated)
- Allowed VLAN
- Forbidden VLAN
- Number of Endpoints
- Endpoint Status
- Endpoint MAC Address
- Endpoint Name / Model
- Uplink Port
- Subscriber S-VLAN (Outer Tag)
- Subscriber C-VLAN (Inner Tag)
- Bandwidth Plan

### 2. Monitor Endpoint Details

**Click on Endpoint MAC Address** to view detailed status:

**System Section:**
```
Detected on Port: [port-number]
Uptime: [days, hours, minutes]
MAC: [mac-address]
Model: [G1001-C / G1001-M / G1002-C+ / G1002-M+ / etc.]
Serial: [serial-number]
FW Version: [firmware-version]
```

**Link Section (Critical Metrics):**
```
Downstream PHY Allocated Bandwidth (Mbps): [max-downstream]
Upstream PHY Allocated Bandwidth (Mbps): [max-upstream]
Downstream Max Usable Data Throughput (Mbps): [l2-capacity-down]
Upstream Max Usable Data Throughput (Mbps): [l2-capacity-up]
```

**Important:**
- Downstream and Upstream BW should be **symmetrical**
- Asymmetrical values indicate wiring issues (bad connector, defective splitter, etc.)

**Ethernet Port Section:**
```
Port #1: [Up/Down] [Speed/Duplex]
Port #2: [Up/Down] [Speed/Duplex]  # If available
PoE Enabled: [Yes/No]  # G1002-C+/M+/G2002-M+ only
PoE Power Source: [No, 802.3af (15W), 802.3at (30W)]
PoE Power Level: [Watts]
PoE PoE Overload: [802.3af / 802.3at]
```

### 3. Monitor System Information

**Path:** `Monitor > System > Information`

**Critical System Metrics:**
```
System:
- Contact: [system-contact]
- Name: [system-name]
- Location: [system-location]

Hardware:
- MAC Address: [gam-mac]
- FPGA Version: [version]
- Hardware Version: [asy-number]
- Serial Number: [serial]

Temperatures:
- CPU: [temp]°C, [temp]°F
- Intake #1: [temp]°C, [temp]°F
- Intake #2: [temp]°C, [temp]°F
- Exhaust #1: [temp]°C, [temp]°F
- Exhaust #2: [temp]°C, [temp]°F

Fans:
- Fan #1: [rpm] rpm
- Fan #2: [rpm] rpm
- Fan #3: [rpm] rpm
- Fan #4: [rpm] rpm

Time:
- System Date: [date]
- System Uptime: [uptime]

Software:
- Bootloader Version: [version]
- Software Version: [version]
- Software Date: [date]
- Code Revision: [revision]
```

**Normal Operating Ranges:**
- CPU Temperature: < 90°C (< 194°F)
- Intake/Exhaust: < 85°C (< 185°F)
- Fan speeds: 6000-8000 RPM typical

### 4. Monitor Active Alarms

**Path:** `Monitor > Alarms > Active`

**Alarm Severity Levels:**
- **Critical:** Service affecting
- **Major:** Significant issue
- **Minor:** Warning condition
- **Info:** Informational

**Common Alarms:**
- Ethernet Link Down (10G-1/10G-2)
- G.hn Port Link Down
- High Temperature
- Fan Failure
- Power Supply Issue

### 5. Monitor System Logs

**Path:** `Monitor > Alarms > Log`

View historical events and alarms.

**Configure Syslog Export (Optional):**
**Path:** `Configuration > System > Log`
- Enable remote syslog
- Configure syslog server IP
- Select severity levels to export

### 6. Monitor DHCP Snooping

**Path:** `Monitor > DHCP`

**Enable DHCP Snooping:**
**Path:** `Configuration > DHCP > Snooping`
- Enable snooping mode
- Set port modes (Trusted / Untrusted)

**Benefits:**
- Shows IP addresses assigned to subscribers
- Required for DHCP Option-82 authentication
- Helps troubleshoot subscriber connectivity

### 7. Monitor MAC Address Table

**Path:** `Monitor > MAC Table`

Shows all learned MAC addresses on the GAM:
- VLAN ID
- MAC Address
- Port Members (which ports have learned this MAC)
- Type (Static / Dynamic)

**Useful for:**
- Verifying subscriber device connectivity
- Identifying which port a device is connected to
- Troubleshooting Layer 2 issues

---

## Troubleshooting

### Basic Troubleshooting Workflow

#### 1. Check Endpoint Status

**Path:** `Monitor > G.hn > Overview`

**Issue:** Endpoint not showing green status

**Troubleshooting Steps:**

a. **Verify Physical Connection:**
   - Check coax/copper cable properly connected
   - Verify splitter/tap connections (for coax)
   - Check for damaged cables

b. **Check Port Configuration:**
   - **Path:** `Configuration > G.hn > Ports`
   - Verify port is enabled
   - For copper: Check SISO vs MIMO mode
   - For coax: Verify port activated

c. **Verify Endpoint Configuration:**
   - **Path:** `Configuration > G.hn > Endpoints`
   - Check endpoint MAC address matches physical device
   - Verify endpoint is assigned to correct port

d. **Check Subscriber Configuration:**
   - **Path:** `Configuration > G.hn > Subscribers`
   - Verify subscriber configured with correct:
     - Endpoint MAC
     - VLAN
     - Bandwidth profile

#### 2. Check G.hn Signal Quality (SNR and Noise)

**Path:** `Diagnostics > G.hn > SNR, PSD & Noise`

**Procedure:**

1. Select G.hn port
2. Select Endpoint MAC address
3. Select Direction:
   - **Downstream:** GAM to Endpoint
   - **Upstream:** Endpoint to GAM
4. Select Type:
   - **SNR Probe** (most important)
   - **Noise**
   - **PSD** (Power Spectral Density)
5. Click "Start" to begin measurement

**SNR (Signal-to-Noise Ratio) Analysis:**

**Good Signal Quality:**
```
SNR: 40 dB or higher
AGC RX: 18-60 dB (automatic gain control)
MAX SNR: Displayed in yellow on graph
```

**Poor Signal Quality:**
```
SNR: Below 40 dB
AGC RX: 62 dB (maxed out - indicates high attenuation)
Attenuation: 42 dB or more
```

**SNR Interpretation:**
- **45+ dB:** Excellent (Gigabit speeds achievable)
- **40-45 dB:** Good (Near-Gigabit speeds)
- **35-40 dB:** Fair (Reduced speeds, connection stable)
- **< 35 dB:** Poor (Connection issues likely)

**Noise Level Analysis:**

**Good Noise Levels:**
```
Noise: < -110 dB  (e.g., -115, -120, -125 dB)
Impact: No impact on G.hn link quality
```

**High Noise Levels:**
```
Noise: > -110 dB  (e.g., -105, -100, -95 dB)
Impact: Can degrade G.hn link quality
```

**Common Noise Sources:**
- AM/FM radio interference (coax)
- Fluorescent lights
- Motors and compressors
- Power line interference
- Poor grounding

**Troubleshooting High Attenuation / Low SNR:**

1. **Check Cable Quality:**
   - Coax: Use RG-6 or RG-11 (avoid RG-59 if possible)
   - Copper: Use CAT-5e or better

2. **Check Cable Length:**
   - Coax: Max ~500 meters typical
   - Copper SISO: Max ~200 meters
   - Copper MIMO: Max ~250-300 meters

3. **Check Splitter Quality (Coax):**
   - Use high-quality CATV splitters (5-1000 MHz rated)
   - Avoid over-splitting (max 1:16 recommended)
   - Check for corroded connectors
   - Replace defective splitters

4. **Check Connections:**
   - Tighten all F-connectors (coax)
   - Check RJ-45 crimps (copper)
   - Look for damaged ports

5. **Reduce Splits (Coax):**
   - Try 1:4 splitter instead of 1:8 or 1:16
   - Each split adds 6-12 dB loss

#### 3. Endpoint Firmware Issues

**Issue:** Warning icon (⚠) shown for endpoint

**Cause:** Endpoint firmware version doesn't match GAM firmware

**Solution: Enable Automatic Firmware Upgrade**

**For Copper GAM:**
**Path:** `Configuration > G.hn > Global Configuration`
```
Endpoint Automatic Firmware Upgrade: Enable
```

**For Coax GAM:**
**Path:** `Configuration > G.hn > Global Configuration`
```
Endpoint Automatic Firmware Upgrade: Enable
```

**Upgrade Process:**
- Takes approximately 2 minutes per endpoint
- Endpoint will reboot a couple of times
- Green status will return when complete
- GAM can upgrade multiple endpoints simultaneously

**Manual Firmware Upgrade:**
**Path:** `Monitor > G.hn > Overview`
1. Click on Endpoint MAC
2. Click "Update Endpoint" button
3. Confirm upgrade

#### 4. Asymmetric Bandwidth

**Symptom:** Download and upload speeds very different

**Check Endpoint Link Status:**
**Path:** `Monitor > G.hn > Overview` → Click Endpoint MAC

**Compare:**
```
Downstream PHY Allocated Bandwidth: [value] Mbps
Upstream PHY Allocated Bandwidth: [value] Mbps
```

**If values are significantly different:**
- Indicates wiring problem
- Check SNR in both directions
- Check for bad connectors
- Check for failing splitter
- Check for RF interference in one direction

#### 5. No Internet Connectivity

**Troubleshooting Checklist:**

a. **Verify Endpoint Link:**
   - Check green status in G.hn Overview
   - Verify SNR > 40 dB

b. **Verify VLAN Configuration:**
   - Check subscriber VLAN matches upstream router
   - Verify VLAN trunked on uplink port
   - Check VLAN not in forbidden list

c. **Check Bandwidth Profile:**
   - Verify not set to 0 Mbps
   - Try "Unthrottled" to rule out rate limiting

d. **Verify Uplink Status:**
   - **Path:** `Monitor > Ports (Ethernet)`
   - Check 10G-1 or 10G-2 port status
   - Verify link is UP
   - Check for errors

e. **Check DHCP (if applicable):**
   - **Path:** `Monitor > DHCP`
   - Verify subscriber receiving IP address
   - Check IP address in correct subnet

f. **Check MAC Table:**
   - **Path:** `Monitor > MAC Table`
   - Verify subscriber device MAC learned
   - Check MAC on correct VLAN

#### 6. Intermittent Connection

**Common Causes:**

a. **Environmental Issues:**
   - Check GAM temperature
   - Verify fan operation
   - Check for overheating

b. **Endpoint Power:**
   - Verify stable power at endpoint
   - Check power supply not overheating
   - Try different power outlet

c. **Cable Issues:**
   - Check for loose connections
   - Look for intermittent opens
   - Check for water ingress (outdoor cables)

d. **Splitter Issues (Coax):**
   - Replace suspect splitter
   - Check for corroded ports
   - Verify proper grounding

e. **RF Interference:**
   - Check noise levels during problem times
   - Look for intermittent noise sources
   - Check grounding

#### 7. Low Throughput / Slow Speeds

**Troubleshooting Steps:**

a. **Check SNR:**
   - Should be > 40 dB for Gigabit speeds
   - Lower SNR = lower speeds

b. **Check Bandwidth Allocation:**
   - Verify sufficient PHY bandwidth
   - Compare allocated vs usable throughput

c. **Check Port Saturation:**
   - **Path:** `Monitor > Performance Monitor`
   - Check if total port bandwidth saturated
   - Coax ports share 1.7 Gbps among all endpoints

d. **Check for Errors:**
   - **Path:** `Monitor > Ports (Ethernet)`
   - Look for CRC errors, collisions
   - Check for packet drops

e. **Verify Endpoint Model:**
   - G1001 vs G1002 vs G2002
   - Check GigE port status (should be 1000 FDX)

#### 8. IGMP / Multicast Issues

**For IPTV or multicast applications**

**Verify IGMP Snooping Configured:**
**Path:** `Configuration > IPMC > IGMP Snooping > Basic Configuration`

```
Snooping Enabled: ✓
Unregistered IPMCv4 Flooding Enabled: ☐ (unchecked - important!)
Leave Proxy Enabled: ☐
Proxy Enabled: ☐
```

**Check VLAN Configuration:**
**Path:** `Configuration > IPMC > IGMP Snooping > VLAN Configuration`

```
Enable snooping on video VLAN
Querier Election: ☐ (GAM should NOT be querier)
Compatibility: Forced IGMPv2 (most common)
```

**Monitor IGMP Status:**
**Path:** `Monitor > IPMC > IGMP Snooping > Status`

**Check:**
- Active Querier detected (must show router IP)
- Querier Status: Active
- Version: v2 or v3

**Monitor Multicast Groups:**
**Path:** `Monitor > IPMC > IGMP Snooping > Group Information`

Verify:
- Multicast groups showing up
- Correct ports listed as members

**Note:** If no active querier detected, video will disconnect after ~2 minutes.

---

## Maintenance Procedures

### 1. Configuration Backup

**Path:** `Maintenance > Configuration > Download`

**Steps:**
1. Select configuration file to save:
   - **running-config:** Current active configuration
   - **default-config:** Factory defaults
   - **startup-config:** Configuration loaded at boot
   - **startup-config-alternate:** Backup boot configuration

2. Click "Download Configuration"
3. File saved as text file in CLI format
4. Store safely for disaster recovery

**Best Practice:**
- Backup after any configuration changes
- Keep dated backups (e.g., `gam-config-2024-01-15.txt`)
- Store off-site or in configuration management system

### 2. Configuration Restore

**Path:** `Maintenance > Configuration > Upload`

**Steps:**
1. Click "Choose File"
2. Select previously downloaded configuration file
3. Click "Upload"
4. GAM will load configuration
5. May require reboot to activate

**Warning:** Uploading configuration will overwrite current settings!

### 3. Software Upgrade

**Obtain Firmware:**
1. Access Positron FTP server:
   ```
   ftp://ftp.positronaccess.com
   Username: positron
   Password: positron
   ```
2. Navigate to: `GAM/2-NEW-SW/`
3. Download `.mfi` file for your GAM model:
   - `GAM-12-C.mfi`
   - `GAM-24-C.mfi`
   - `GAM-12-M.mfi`
   - `GAM-24-M.mfi`
   - etc.

**Upgrade Procedure:**

1. **Save Current Configuration:**
   - **Path:** Click disk icon (save to flash)
   - **Path:** `Maintenance > Configuration > Download`

2. **Upload New Firmware:**
   - **Path:** `Maintenance > Software > Update From File`
   - Click "Choose File"
   - Select downloaded `.mfi` file
   - Click "Upload"

3. **Wait for Upload:**
   - Progress bar shows upload status
   - Do NOT power off during upgrade!

4. **Automatic Reboot:**
   - GAM will reboot automatically
   - Wait 2-5 minutes for system to come back online

5. **Verify New Version:**
   - Reconnect to GAM web interface
   - **Path:** `Monitor > System > Information`
   - Check "Software Version" field

**Upgrade Time:** Typically 5-10 minutes total

**Rollback:**
If issues occur after upgrade:
- **Path:** `Maintenance > Software > Activate Alternate Image`
- GAM maintains previous firmware version
- Can switch between current and alternate images

### 4. Factory Reset

**Path:** `Maintenance > Factory Defaults`

**WARNING:** This will erase ALL configuration!

**Steps:**
1. Backup configuration first!
2. Click "Factory Defaults"
3. Confirm action
4. GAM will reboot with factory settings
5. Default IP: 192.168.10.1
6. Default credentials: admin / (blank password)

**Use Cases:**
- GAM being redeployed to different site
- Forgot management IP address
- Configuration corruption
- Troubleshooting last resort

### 5. Reboot GAM

**Path:** `Maintenance > Restart Device`

**Steps:**
1. Save configuration first (click disk icon)
2. Click "Restart Device"
3. Confirm reboot
4. Wait 2-3 minutes for system to restart

**When to Reboot:**
- After configuration changes requiring restart
- Troubleshooting network connectivity issues
- After software upgrade (if not automatic)
- Scheduled maintenance window

### 6. Save Configuration to Flash

**Critical Step After Any Configuration Change!**

**Method 1: Click Disk Icon**
- Located in upper right corner of web interface
- Saves running-config to startup-config
- Configuration persists across reboots

**Method 2: Via Menu**
**Path:** `Maintenance > Configuration > Save startup-config`

**Important:**
- Changes are NOT automatically saved!
- Unsaved changes lost after reboot/power loss
- Always save after configuration changes

### 7. Check for Alarms Before Maintenance

**Path:** `Monitor > Alarms > Active`

**Before performing maintenance:**
1. Check for active alarms
2. Resolve critical issues first
3. Document existing issues
4. Clear false alarms

**After maintenance:**
1. Verify no new alarms
2. Check all services restored
3. Verify endpoint connections
4. Test subscriber connectivity

### 8. Endpoint Firmware Management

**Check Endpoint Versions:**
**Path:** `Monitor > G.hn > Overview`
- Look for warning icons (⚠)
- Click endpoint MAC to see firmware version

**Enable Auto-Upgrade:**
**Path:** `Configuration > G.hn > Global Configuration`
```
Endpoint Automatic Firmware Upgrade: Enable
```

**Monitor Upgrade Progress:**
- Endpoints will upgrade one at a time
- Each takes ~2 minutes
- Endpoint reboots when complete
- Status returns to green when done

**Best Practice:**
- Enable auto-upgrade during low-traffic hours
- Monitor endpoints during upgrade
- Keep endpoint firmware synchronized with GAM

### 9. Periodic Maintenance Checklist

**Weekly:**
- [ ] Check active alarms
- [ ] Monitor system temperatures
- [ ] Verify fan speeds
- [ ] Check uplink port status
- [ ] Review endpoint connections

**Monthly:**
- [ ] Backup configuration
- [ ] Review system logs
- [ ] Check for firmware updates
- [ ] Verify DHCP snooping table
- [ ] Clean log files if needed

**Quarterly:**
- [ ] Test configuration restore
- [ ] Review bandwidth utilization
- [ ] Update documentation
- [ ] Check physical connections
- [ ] Clean equipment/fans if needed

**Annually:**
- [ ] Full firmware upgrade
- [ ] Review security settings
- [ ] Update passwords
- [ ] Verify redundancy features
- [ ] Test failover scenarios

---

## Quick Reference - Common Tasks

### Add New Subscriber (Quick)
1. `Configuration > G.hn > Endpoints > Add New Endpoint` (if needed)
2. `Configuration > G.hn > Ports` - Verify port enabled
3. `Configuration > G.hn > Subscribers > Add New Subscriber`
4. Click disk icon to save

### Troubleshoot No Connection
1. `Monitor > G.hn > Overview` - Check endpoint status
2. `Diagnostics > G.hn > SNR, PSD & Noise` - Check signal quality
3. `Monitor > DHCP` - Verify IP assignment
4. `Monitor > MAC Table` - Verify MAC learned

### Change Bandwidth
1. `Configuration > G.hn > Subscribers` - Find subscriber
2. Edit Bandwidth Plan
3. Save configuration
4. Click disk icon

### View Subscriber Status
1. `Monitor > G.hn > Overview`
2. Click on endpoint MAC address
3. Review Link section for bandwidth
4. Check Ethernet port status

### Backup Configuration
1. `Maintenance > Configuration > Download`
2. Select "running-config"
3. Click "Download Configuration"

### Upgrade Firmware
1. Save configuration
2. Download .mfi file from Positron FTP
3. `Maintenance > Software > Update From File`
4. Upload and wait for reboot

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Based on:** Positron GAM Quick Start Guide (June 2022), Basic Troubleshooting Guide v1.1 (July 2024)
