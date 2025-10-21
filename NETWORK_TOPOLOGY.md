# Positron GAM Network Topology - Detailed Block Diagram

## Overview
This document provides a detailed block diagram and explanation of how customer equipment connects through the Positron GAM (G.hn Access Multiplexer) system to deliver Gigabit Internet services over existing copper or coaxial infrastructure.

---

## Complete Network Topology Block Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          ISP / SERVICE PROVIDER NETWORK                             │
│                                                                                     │
│  ┌──────────────────────┐         ┌─────────────────────┐                         │
│  │  Core Router/Switch  │◄────────┤   OLT (Optional)    │                         │
│  │   (10G/100G Core)    │         │  PON Aggregation    │                         │
│  └──────────┬───────────┘         └──────────┬──────────┘                         │
│             │                                 │                                     │
│             │ 10Gbps Fiber                   │ 10Gbps Fiber (XGS-PON/GEPON)       │
│             │ (Active Ethernet)              │ (Optional PON)                      │
└─────────────┼─────────────────────────────────┼─────────────────────────────────────┘
              │                                 │
              │                                 │
              │                                 ▼
              │                        ┌─────────────────┐
              │                        │  ONU/ONT Device │
              │                        │  (Optional for  │
              │                        │  PON Deployment)│
              │                        └────────┬────────┘
              │                                 │ 10Gbps Ethernet
              └─────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────────────┐
│                    MDU WIRING CLOSET / DISTRIBUTION POINT                           │
│                                       │                                             │
│  ╔════════════════════════════════════▼═══════════════════════════════════════════╗│
│  ║              POSITRON GAM (G.hn Access Multiplexer)                            ║│
│  ║                      GAM-12-C / GAM-24-C / GAM-12-M / GAM-24-M                 ║│
│  ╠════════════════════════════════════════════════════════════════════════════════╣│
│  ║                                                                                ║│
│  ║  ┌──────────────────────────────────────────────────────────────────────┐    ║│
│  ║  │                      UPLINK INTERFACES                               │    ║│
│  ║  │  ┌───────────────┐         ┌───────────────┐                        │    ║│
│  ║  │  │  SFP+ Port 1  │         │  SFP+ Port 2  │                        │    ║│
│  ║  │  │   10 Gbps     │         │   10 Gbps     │                        │    ║│
│  ║  │  │  (Primary)    │         │  (Redundant)  │                        │    ║│
│  ║  │  └───────────────┘         └───────────────┘                        │    ║│
│  ║  │                                                                      │    ║│
│  ║  │  Supports: Active Ethernet, GEPON, 10GEPON, XGS-PON, NG-PON2       │    ║│
│  ║  └──────────────────────────────────────────────────────────────────────┘    ║│
│  ║                                                                                ║│
│  ║  ┌──────────────────────────────────────────────────────────────────────┐    ║│
│  ║  │                 NON-BLOCKING CE 2.0 CARRIER ETHERNET CORE            │    ║│
│  ║  │                                                                      │    ║│
│  ║  │  • VLAN Management (Support 4094 VLANs, Q-in-Q)                    │    ║│
│  ║  │  • QoS & Traffic Shaping (Per-Subscriber Bandwidth Profiles)       │    ║│
│  ║  │  • AES-128 Encryption (G.hn Link Layer)                            │    ║│
│  ║  │  • ITU-T G.988 OMCI Management                                     │    ║│
│  ║  │  • Port Isolation & Subscriber Traffic Isolation                   │    ║│
│  ║  │  • Dynamic Bandwidth Allocation (up to 1.7 Gbps per port)          │    ║│
│  ║  └──────────────────────────────────────────────────────────────────────┘    ║│
│  ║                                                                                ║│
│  ║  ┌──────────────────────────────────────────────────────────────────────┐    ║│
│  ║  │               SUBSCRIBER PORTS (G.hn Wave 2)                         │    ║│
│  ║  │                                                                      │    ║│
│  ║  │  PORT TYPES:                                                         │    ║│
│  ║  │  • COAX PORTS (GAM-12-C / GAM-24-C): Point-to-Multipoint           │    ║│
│  ║  │    - Frequency: 2-200 MHz                                           │    ║│
│  ║  │    - Up to 16 subscribers per port via coax splitters              │    ║│
│  ║  │    - Max 384 subscribers (24-port × 16)                             │    ║│
│  ║  │                                                                      │    ║│
│  ║  │  • COPPER PORTS (GAM-12-M / GAM-24-M): Point-to-Point              │    ║│
│  ║  │    - SISO: Single twisted pair (1 subscriber per port)              │    ║│
│  ║  │    - MIMO: Dual twisted pair (1 subscriber per port)                │    ║│
│  ║  │    - Supports CAT-3, CAT-5/5e, UTP                                  │    ║│
│  ║  │    - Extended reach vs traditional Ethernet                         │    ║│
│  ║  └──────────────────────────────────────────────────────────────────────┘    ║│
│  ║                                                                                ║│
│  ║  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐    ║│
│  ║  │Port 1│Port 2│Port 3│Port 4│Port 5│Port 6│ ...  │      │      │Port24│    ║│
│  ║  └──┬───┴───┬──┴───┬──┴───┬──┴───┬──┴───┬──┴──────┴──────┴──────┴───┬──┘    ║│
│  ╚═════╪═══════╪══════╪══════╪══════╪══════╪══════════════════════════╪═════════╝│
│        │       │      │      │      │      │                          │          │
│   Coax │  Coax│ Coax │ Coax │Copper│Copper│                     Copper│          │
│   Cable│ Cable│Cable │Cable │Pair  │Pair  │                       Pair│          │
└────────┼───────┼──────┼──────┼──────┼──────┼──────────────────────────┼──────────┘
         │       │      │      │      │      │                          │
         │       │      │      │      │      │                          │
┌────────┼───────┼──────┼──────┼──────┼──────┼──────────────────────────┼──────────┐
│ EXISTING BUILDING INFRASTRUCTURE (In-Wall Cabling)                                │
│        │       │      │      │      │      │                          │           │
│  ┌─────▼───────▼──────▼──────▼──┐  │      │                          │           │
│  │  Coaxial Cable Infrastructure │  │      │                          │           │
│  │  (CATV Splitters - Passive)   │  │      │                          │           │
│  │                                │  │      │                          │           │
│  │    ┌──────────┐                │  │      │                          │           │
│  │    │ 1:4 or   │                │  │      │                          │           │
│  │    │ 1:8 or   │                │  │      │                          │           │
│  │    │ 1:16     │                │  │      │                          │           │
│  │    │ Splitter │                │  │      │                          │           │
│  │    └─┬─┬─┬─┬──┘                │  │      │                          │           │
│  │      │ │ │ │                   │  │      │                          │           │
│  └──────┼─┼─┼─┼───────────────────┘  │      │                          │           │
│         │ │ │ │                      │      │                          │           │
│    Coax │ │ │ │                 Copper     Copper                 Copper          │
│    Cable│ │ │ │                 Twisted    Twisted                Twisted         │
│         │ │ │ │                 Pair       Pair                   Pair            │
└─────────┼─┼─┼─┼──────────────────┼──────────┼──────────────────────┼──────────────┘
          │ │ │ │                  │          │                      │
          │ │ │ │                  │          │                      │
┌─────────┼─┼─┼─┼──────────────────┼──────────┼──────────────────────┼──────────────┐
│  SUBSCRIBER PREMISES (Apartment/Unit)                                             │
│         │ │ │ │                  │          │                      │              │
│  ┌──────▼─▼─▼─▼──────┐    ┌──────▼──────┐ ┌▼──────────┐    ┌──────▼──────┐      │
│  │                   │    │             │ │           │    │             │      │
│  │ ╔═══════════════╗ │    │ ╔═════════╗ │ │ ╔═══════╗ │    │ ╔═════════╗ │      │
│  │ ║  G1001-C CPE  ║ │    │ ║G1001-M  ║ │ │ ║G1001-M║ │    │ ║G1001-M+ ║ │      │
│  │ ║  (Coax to     ║ │    │ ║CPE      ║ │ │ ║CPE    ║ │    │ ║CPE      ║ │      │
│  │ ║   Ethernet)   ║ │    │ ║(Copper  ║ │ │ ║(Copper║ │    │ ║(Copper  ║ │      │
│  │ ╚═══════╤═══════╝ │    │ ╚════╤════╝ │ │ ╚═══╤═══╝ │    │ ╚════╤════╝ │      │
│  │         │         │    │      │      │ │     │     │    │      │      │      │
│  │  ┌──────▼──────┐  │    │ ┌────▼────┐ │ │ ┌───▼───┐ │    │ ┌────▼────┐ │      │
│  │  │ GigE Port 1 │  │    │ │GigE Port│ │ │ │GigE   │ │    │ │GigE Port│ │      │
│  │  │ GigE Port 2 │  │    │ │(RJ-45)  │ │ │ │Port   │ │    │ │+ PoE Out│ │      │
│  │  └──────┬──────┘  │    │ └────┬────┘ │ │ └───┬───┘ │    │ └────┬────┘ │      │
│  └─────────┼─────────┘    └──────┼──────┘ └─────┼─────┘    └──────┼──────┘      │
│            │                     │              │                 │              │
│       GigE │                GigE │         GigE │            GigE │              │
│      Patch │               Patch │        Patch │           Patch │              │
│            │                     │              │                 │              │
│  ┌─────────▼─────────┐    ┌──────▼──────┐ ┌────▼─────┐    ┌──────▼──────┐      │
│  │  ╔═══════════════╗│    │╔═══════════╗│ │╔════════╗│    │╔═══════════╗│      │
│  │  ║  CUSTOMER     ║│    │║  CUSTOMER ║│ │║CUSTOMER║│    │║  CUSTOMER ║│      │
│  │  ║  ROUTER       ║│    │║  ROUTER   ║│ │║ROUTER  ║│    │║  ROUTER   ║│      │
│  │  ║  (WiFi/AP)    ║│    │║  (WiFi/AP)║│ │║(WiFi)  ║│    │║  (WiFi/AP)║│      │
│  │  ╚═══════╤═══════╝│    │╚═════╤═════╝│ │╚════╤═══╝│    │╚═════╤═════╝│      │
│  └──────────┼─────────┘    └──────┼──────┘ └─────┼────┘    └──────┼──────┘      │
│             │                     │              │                │              │
│         WiFi│                 WiFi│          WiFi│            WiFi│              │
│      ───────┴──────       ────────┴─────   ──────┴────     ───────┴─────        │
│     /               \    /              \  /          \   /             \        │
│    │  User Devices  │  │  User Devices │ │User       │  │ User Devices │       │
│    │  (Laptop, PC,  │  │  (Laptop, PC, │ │Devices    │  │ (Laptop, PC, │       │
│    │   Phone, IoT)  │  │   Phone, IoT) │ │(Phone)    │  │  Phone, IoT) │       │
│     \               /    \              /  \          /   \             /        │
│      ───────────────      ──────────────    ──────────     ─────────────         │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Breakdown

### 1. UPSTREAM: ISP/Service Provider Network

#### Core Network Components:
- **Core Router/Switch**:
  - Aggregates traffic from multiple GAM deployments
  - Typically 10G, 40G, or 100G interfaces
  - Handles routing, firewalling, and CGNAT (if applicable)
  - Connects to upstream ISP transit or internet exchange

- **OLT (Optical Line Terminal)** - *Optional for PON Deployments*:
  - Used when deploying GAM over PON infrastructure
  - Supports XGS-PON, 10G-EPON, GPON, or NG-PON2
  - Aggregates multiple ONUs/ONTs
  - Provides centralized management and provisioning

#### Uplink Types:
1. **Active Ethernet** (Direct Fiber):
   - 10Gbps fiber directly to GAM SFP+ port
   - Most common for small-medium deployments
   - Lower complexity, easier troubleshooting

2. **PON Deployment** (via ONU/ONT):
   - OLT → Fiber → ONU/ONT → Ethernet → GAM
   - Better for large deployments sharing fiber infrastructure
   - Requires external ONU/ONT device or PON SFP ONT module

---

### 2. DISTRIBUTION: Positron GAM (G.hn Access Multiplexer)

**Location**: Installed in MDU wiring closet, basement, or distribution point

#### A. Uplink Interfaces (2× 10Gbps SFP+ Ports)

**SFP+ Port Specifications**:
- Speed: 10 Gbps per port
- Media Support:
  - Single-mode fiber (SMF)
  - Multi-mode fiber (MMF)
  - Direct Attach Copper (DAC) for short distances
  - PON SFP ONT modules (XGS-PON, GEPON, etc.)

**Redundancy Options**:
- **Primary/Backup**: SFP+ Port 1 active, Port 2 standby
- **Link Aggregation** (LAG): Both ports active, combined 20Gbps
- **Split Traffic**: Different VLANs on different ports

#### B. Non-Blocking CE 2.0 Carrier Ethernet Core

**Key Functions**:

1. **VLAN Management**:
   - Supports up to 4094 VLANs (VLAN IDs 1-4095)
   - Reserved VLANs: 1, 2, 4095 (internal use)
   - Default management VLAN: 4093
   - Default unprovisioned service VLAN: 4094
   - **Single VLAN Mode**: All subscribers on same VLAN (data VLAN)
     - Port isolation prevents subscriber-to-subscriber traffic
   - **Per-Subscriber VLAN**: Each subscriber gets unique VLAN
     - Better for managed services, easier accounting
   - **Q-in-Q (802.1ad)**: Double VLAN tagging support
     - Service Provider VLAN + Customer VLAN

2. **Bandwidth Profiles**:
   - Per-subscriber bandwidth allocation
   - CIR (Committed Information Rate)
   - PIR (Peak Information Rate)
   - EIR (Excess Information Rate)
   - Dynamic bandwidth allocation up to 1.7 Gbps per port

3. **QoS & Traffic Shaping**:
   - 802.1p CoS (Class of Service) marking
   - DSCP (Differentiated Services Code Point)
   - Priority queuing
   - Rate limiting per subscriber

4. **Security Features**:
   - **AES-128 Encryption**: All G.hn links encrypted at Layer 2
   - **Port Isolation**: Traffic between ports blocked by default
   - **Subscriber Isolation**: On coax (P2MP), subscribers on same port isolated
   - **MAC Address Filtering**: Optional per-subscriber MAC learning

5. **Management**:
   - **ITU-T G.988 OMCI**: Standards-based provisioning
   - **SNMP v2c/v3**: Monitoring and management
   - **SSH/HTTPS**: Secure CLI and web interface
   - **Syslog**: Centralized logging
   - **RADIUS/TACACS+**: Authentication (optional)

#### C. Subscriber Ports (12 or 24 ports)

**GAM Model Variants**:

1. **GAM-12-C / GAM-24-C** (Coaxial):
   - 12 or 24 coaxial F-connector ports
   - **Point-to-Multipoint (P2MP)** topology
   - Frequency Range: 2-200 MHz (G.hn Wave 2)
   - **Up to 16 subscribers per port** via passive coax splitters
   - Maximum capacity: 384 subscribers (24 ports × 16)
   - Typical splitter ratios: 1:4, 1:8, 1:16
   - Uses existing CATV coax infrastructure
   - Greater reach than structured cabling

2. **GAM-12-M / GAM-24-M** (Copper Twisted Pair):
   - 12 or 24 RJ-45 ports
   - **Point-to-Point (P2P)** topology
   - **One subscriber per port**
   - **SISO Mode** (Single Input Single Output):
     - Uses 1 twisted pair (2 wires)
     - Lower bandwidth, extended reach
   - **MIMO Mode** (Multiple Input Multiple Output):
     - Uses 2 twisted pairs (4 wires)
     - Higher bandwidth, better performance
   - Cable Support: CAT-3, CAT-5/5e, UTP
   - Extended reach vs traditional Ethernet

**G.hn Wave 2 Specifications**:
- ITU-T G.9960/G.9961 standards
- Bandwidth per port: Up to 1.7 Gbps (dynamically allocated)
- Typical service: 1 Gbps down / 1 Gbps up (near symmetrical)
- Encryption: AES-128 at G.hn layer
- Auto-negotiation with CPE endpoints
- Distance:
  - Coax: 500+ meters
  - Copper: 200-500 meters (depending on wire quality)

---

### 3. IN-BUILDING INFRASTRUCTURE: Existing Cabling

#### Coaxial Cable Infrastructure (for GAM-C models)

**Topology**: Point-to-Multipoint via Passive Splitters

```
GAM Port 1 ──── Coax Cable ──── [1:8 Splitter] ──┬── Apartment 101
                                                  ├── Apartment 102
                                                  ├── Apartment 103
                                                  ├── Apartment 104
                                                  ├── Apartment 105
                                                  ├── Apartment 106
                                                  ├── Apartment 107
                                                  └── Apartment 108
```

**Key Characteristics**:
- **Passive Splitters**: Standard CATV splitters (no power required)
  - 1:4 splitter: 6 dB loss per leg
  - 1:8 splitter: 9 dB loss per leg
  - 1:16 splitter: 12 dB loss per leg
- **Frequency Spectrum**: 2-200 MHz (below CATV/DOCSIS)
- **Subscriber Isolation**: GAM manages per-subscriber encryption and traffic isolation
- **Existing Infrastructure**: Leverages installed coax from cable TV

**Advantages**:
- High density (up to 16 subscribers per port)
- Uses existing infrastructure (no new cabling)
- Lower per-subscriber cost
- Passive splitters (no active equipment needed)

#### Copper Twisted Pair Infrastructure (for GAM-M models)

**Topology**: Point-to-Point (Dedicated pair per subscriber)

```
GAM Port 1 ──── Twisted Pair ──── Apartment 101
GAM Port 2 ──── Twisted Pair ──── Apartment 102
GAM Port 3 ──── Twisted Pair ──── Apartment 103
```

**Key Characteristics**:
- **Dedicated Connection**: Each subscriber has isolated physical connection
- **SISO or MIMO**: Single or dual pair operation
- **Cable Types**: CAT-3 (phone), CAT-5/5e, UTP
- **Distance**: Superior to traditional Ethernet over same cable
- **No Splitters**: Direct connection from GAM to CPE

**Advantages**:
- Higher per-subscriber bandwidth potential
- Better isolation (physical separation)
- Lower latency
- Easier troubleshooting (dedicated path)

---

### 4. SUBSCRIBER PREMISES: CPE (Customer Premises Equipment)

#### Positron G100x Series CPE Devices

**G1001-C** (Coax to Ethernet Bridge):
- **Input**: F-connector (Coaxial)
- **Output**: 2× Gigabit Ethernet RJ-45 ports
- **Power**: AC wall adapter (included)
- **Use Case**: MDUs with coaxial infrastructure
- **Features**:
  - G.hn Wave 2 (ITU-T G.9960/G.9961)
  - Managed by GAM via OMCI (G.988)
  - AES-128 encryption
  - Auto-provisioning
  - LED status indicators (Power, Link, Data)

**G1001-M** (Copper to Ethernet Bridge):
- **Input**: RJ-45 (Twisted Pair - SISO or MIMO)
- **Output**: 1× Gigabit Ethernet RJ-45 port
- **Power**: AC wall adapter (included)
- **Use Case**: Buildings with telephone/structured cabling
- **Features**: Same as G1001-C

**G1002-M+** (Copper to Ethernet Bridge with PoE):
- **Input**: RJ-45 (Twisted Pair)
- **Output**: 1× Gigabit Ethernet RJ-45 port with PoE+ Out (802.3at)
- **PoE Output**: Up to 25.5W (for powering WiFi APs)
- **Power**: AC wall adapter (included)
- **Use Case**: Powering customer WiFi AP or VoIP phone
- **Features**: Same as G1001-M plus PoE injection

**CPE Management**:
- **Provisioning**: Automatic via OMCI from GAM
- **Configuration**: VLAN assignment, bandwidth profile, QoS
- **Monitoring**: Link quality, throughput, errors
- **Authentication**: MAC address registration
- **Firmware**: Remote upgrades from GAM

#### CPE Connection Modes

1. **Transparent Bridge Mode** (Most Common):
   - CPE acts as Layer 2 bridge
   - Customer router gets public IP via DHCP
   - Customer router handles NAT, firewall, WiFi
   - Simplest for customer

2. **Router Mode** (Less Common):
   - CPE acts as router with built-in NAT
   - Customer devices connect directly to CPE
   - Limited CPE routing features

3. **VLAN Tagged Mode**:
   - CPE passes VLAN tags to customer router
   - Customer router must support 802.1Q
   - Used for multi-service deployments (Internet + IPTV + VoIP)

---

### 5. CUSTOMER NETWORK: Router and User Devices

#### Customer Router

**Typical Setup**:
- **Input**: Gigabit Ethernet from CPE
- **WAN Configuration**: DHCP client (receives IP from ISP)
- **LAN**: Private network (192.168.x.x or 10.x.x.x)
- **NAT**: Network Address Translation for multiple devices
- **Firewall**: Stateful packet inspection, port forwarding
- **WiFi**: 802.11ac/ax (WiFi 5/6) access point
- **Additional Features**:
  - Guest network (isolated VLAN)
  - Parental controls
  - QoS prioritization
  - VPN client/server
  - DDNS (Dynamic DNS)

**Common Customer Router Types**:
- ISP-provided router (if ISP offers managed service)
- Retail router (Netgear, TP-Link, Asus, Ubiquiti)
- Mesh WiFi system (Google WiFi, Eero, Orbi)
- Enterprise AP (UniFi, Ruckus, Aruba)

#### User Devices

Connected via WiFi or Ethernet:
- Laptops, desktops (work from home)
- Smartphones, tablets
- Smart TVs, streaming devices
- IoT devices (smart home, security cameras)
- Gaming consoles
- VoIP phones

---

## Network Flow Example: Subscriber to Internet

### Downstream (Internet → Customer)

```
ISP Core Router
    ↓ (10Gbps Fiber)
GAM Uplink (SFP+ Port 1)
    ↓ (VLAN 100, Subscriber A)
GAM Internal Switching Fabric
    ↓ (Bandwidth Profile: 1000 Mbps / 1000 Mbps)
GAM Port 5 (G.hn over Coax)
    ↓ (AES-128 Encrypted, 2-200 MHz)
Passive Coax Splitter (1:8)
    ↓ (Subscriber A's coax leg)
G1001-C CPE (Apartment 302)
    ↓ (GigE Port 1)
Customer Router (WAN Port)
    ↓ (NAT, Firewall, WiFi)
User Laptop (WiFi)
```

### Upstream (Customer → Internet)

```
User Laptop (WiFi)
    ↓
Customer Router (WiFi → WAN)
    ↓ (GigE)
G1001-C CPE (Ethernet → Coax)
    ↓ (G.hn Modulation, AES-128)
Passive Coax Splitter
    ↓
GAM Port 5 (Coax)
    ↓ (VLAN 100 Tagged)
GAM Internal Switching Fabric
    ↓ (Policing: Max 1000 Mbps)
GAM Uplink (SFP+ Port 1)
    ↓ (10Gbps Fiber)
ISP Core Router
    ↓
Internet
```

---

## VLAN Architecture Examples

### Scenario 1: Single VLAN Per Subscriber (Most Common)

```
VLAN Allocation:
- Management VLAN: 4093 (GAM Management)
- Subscriber A (Apt 101): VLAN 100
- Subscriber B (Apt 102): VLAN 101
- Subscriber C (Apt 103): VLAN 102
- ...
- Subscriber Z (Apt 150): VLAN 199

Uplink: All VLANs trunked to ISP core router (802.1Q tagged)
ISP Router: Per-VLAN IP subnets, routing, firewall, CGNAT
```

### Scenario 2: Shared Data VLAN with Port Isolation

```
VLAN Allocation:
- Management VLAN: 4093 (GAM Management)
- Data VLAN: 100 (All Subscribers)

Port Isolation: GAM isolates traffic between ports and between
                subscribers on the same coax port

Uplink: VLAN 100 tagged to ISP core router
ISP Router: Single large subnet (10.x.x.x/16), CGNAT, firewall
```

### Scenario 3: Multi-Service (Internet + IPTV + VoIP)

```
VLAN Allocation per Subscriber:
- Management VLAN: 4093 (GAM Management)
- Internet VLAN: 100-199 (Unique per subscriber)
- IPTV VLAN: 200 (Shared multicast VLAN)
- VoIP VLAN: 201 (Shared VoIP services)

CPE Configuration: Q-in-Q tagging
- Subscriber VLAN (outer): 100
- Service VLANs (inner): 200 (IPTV), 201 (VoIP)

Customer Router: Must support VLAN tagging (802.1Q)
- WAN VLAN 100: Internet (DHCP)
- IPTV VLAN 200: Set-top box (IGMP proxy)
- VoIP VLAN 201: VoIP ATA/phone (SIP)
```

---

## Bandwidth Management Example

### Subscriber Profile Configuration

**Subscriber A** (1 Gbps / 1 Gbps Plan):
```
GAM Configuration:
  Port: 5 (Coax)
  VLAN: 100
  CPE MAC: AA:BB:CC:DD:EE:01
  Bandwidth Profile:
    - CIR (Committed Rate): 500 Mbps down / 500 Mbps up
    - PIR (Peak Rate): 1000 Mbps down / 1000 Mbps up
    - Burst Size: 10 MB
  QoS: Best Effort (no prioritization)
```

**Subscriber B** (500 Mbps / 500 Mbps Plan):
```
GAM Configuration:
  Port: 5 (Coax, same as Subscriber A)
  VLAN: 101
  CPE MAC: AA:BB:CC:DD:EE:02
  Bandwidth Profile:
    - CIR: 250 Mbps down / 250 Mbps up
    - PIR: 500 Mbps down / 500 Mbps up
    - Burst Size: 5 MB
  QoS: Best Effort
```

**Port 5 Total Allocation**:
- Maximum aggregate bandwidth: 1.7 Gbps (G.hn Wave 2 limit)
- Subscriber A: Up to 1000 Mbps
- Subscriber B: Up to 500 Mbps
- If both use full PIR: 1500 Mbps (within 1700 Mbps limit)

**Dynamic Allocation**:
- If Subscriber A idle: Subscriber B can burst above 500 Mbps
- If Subscriber B idle: Subscriber A gets full 1 Gbps
- If both active: PIR limits enforced

---

## Physical Installation Notes

### GAM Installation Location
- **Indoor Environment**: Temperature controlled preferred
- **Mounting**: 19" rack-mountable or wall-mount bracket
- **Power**: AC 110-220V or DC 12V (outdoor models with RPF)
- **Ventilation**: Adequate airflow for cooling
- **Fiber Access**: Proximity to fiber demarc or ONU/ONT
- **Cabling Access**: Connection to building's coax/copper infrastructure

### Coax Splitter Guidelines
- **Quality Matters**: Use high-quality CATV splitters (5-1000 MHz rated)
- **Avoid Over-Splitting**: Max 1:16 split (signal degradation increases)
- **Minimize Splitters**: Fewer cascaded splitters = better performance
- **Document Topology**: Map which apartments connect to which splitter legs

### Cable Quality
- **Coax**: RG-6 or RG-11 (avoid RG-59 if possible)
- **Twisted Pair**: CAT-5e minimum (CAT-6 preferred)
- **Length**: Stay within G.hn distance limits
  - Coax: 500 meters typical
  - Copper: 200-500 meters (varies by wire gauge and quality)

### CPE Placement
- **Signal Strength**: Install near subscriber's main router location
- **Avoid Interference**: Keep away from motors, microwaves, fluorescent lights
- **Accessibility**: Easy for subscriber to power cycle if needed
- **Professional Install Recommended**: Ensures optimal placement and configuration

---

## Troubleshooting Quick Reference

### Common Issues and Diagnosis

**Issue: Subscriber has no connection**
1. Check GAM: Is subscriber port up? (SNMP/CLI)
2. Check CPE: Are LEDs showing link? (Power, Link, Data)
3. Check Cable: Coax/copper physically connected?
4. Check VLAN: Correct VLAN provisioned on GAM and uplink?
5. Check Bandwidth: Profile applied correctly?

**Issue: Slow speeds**
1. Check G.hn Link Quality: SNR (Signal-to-Noise Ratio) on GAM
2. Check Coax Splitter: Too many splits? (Try 1:4 instead of 1:16)
3. Check Cable Quality: Old/damaged coax or twisted pair?
4. Check Bandwidth Profile: Is subscriber hitting CIR/PIR limits?
5. Check Port Utilization: Is total port bandwidth saturated?

**Issue: Intermittent connection**
1. Check Environmental: Temperature, electrical interference?
2. Check Cable: Loose connections, damaged shielding?
3. Check Splitter: Corroded connectors, failing splitter?
4. Check CPE: Power supply stable? Overheating?
5. Check GAM Logs: Errors, link flaps?

---

## Management and Monitoring

### GAM Management Access

**Access Methods**:
1. **Web GUI**: HTTPS (default port 443)
   - Initial setup wizard
   - Subscriber provisioning
   - Monitoring dashboards
   - Firmware upgrades

2. **SSH CLI**: Port 22
   - Advanced configuration
   - Scripting and automation
   - Detailed diagnostics

3. **SNMP**: v2c or v3
   - Integration with NMS (Nagios, PRTG, LibreNMS)
   - Automated monitoring
   - Alerting and graphing

4. **OMCI (G.988)**: ITU-T standard
   - CPE management from GAM
   - Automatic provisioning
   - Remote firmware upgrades

**Default Credentials**: (MUST change on first login)
- Username: admin
- Password: admin
- Management VLAN: 4093

### Monitoring Metrics (SNMP OIDs)

**Per Subscriber Port**:
- Link Status (Up/Down)
- G.hn PHY Rate (Negotiated speed)
- SNR (Signal-to-Noise Ratio) - dB
- Attenuation (Signal loss) - dB
- Packet Rate (PPS)
- Throughput (Mbps)
- Error Counters (CRC, FEC)
- Bandwidth Utilization (%)

**Per CPE Endpoint**:
- MAC Address
- Firmware Version
- Online Time (Uptime)
- Rx/Tx Power Levels
- Temperature (if supported)

**Uplink Ports (SFP+)**:
- Link Status
- Optical Power Levels (Tx/Rx)
- Throughput (Gbps)
- Error Counters
- VLAN Traffic per VLAN

**System-Wide**:
- CPU Utilization (%)
- Memory Usage (%)
- Temperature (°C)
- Power Supply Status
- Fan Status
- Firmware Version

### Integration with Positron GAM Management System

**This Open-Source Project Provides**:
- Centralized management of multiple GAM devices
- Subscriber provisioning and lifecycle management
- Integration with billing systems (Sonar, Splynx)
- Monitoring and alerting
- Reporting and analytics
- API for automation

---

## Security Considerations

### G.hn Link Security
- **AES-128 Encryption**: All traffic encrypted at G.hn layer
- **Per-Subscriber Keys**: Each CPE has unique encryption key
- **Key Management**: Automatic key exchange and rotation

### Network Security
- **VLAN Isolation**: Subscribers cannot see each other's traffic
- **Port Isolation**: Prevents lateral movement
- **MAC Filtering**: Optional per-subscriber MAC authentication
- **Management Access**: Restrict to trusted management VLAN
- **HTTPS/SSH**: Encrypted management protocols
- **RADIUS/TACACS+**: Centralized authentication (optional)

### Physical Security
- **GAM Location**: Locked wiring closet or server room
- **Fiber Access**: Secured fiber demarc point
- **CPE Tampering**: Subscriber cannot bypass CPE (encrypted link)

---

## Scalability and Capacity Planning

### Single GAM Capacity

**GAM-24-C (Coax)**:
- Maximum subscribers: 384 (24 ports × 16 per port)
- Aggregate bandwidth: 20 Gbps (2× 10G SFP+ uplinks)
- Typical deployment: 100-200 active subscribers

**GAM-24-M (Copper)**:
- Maximum subscribers: 24 (1 per port)
- Aggregate bandwidth: 20 Gbps
- Typical deployment: 24 subscribers (full capacity)

### Multi-GAM Deployments

**Stacking/Chaining**:
- Connect multiple GAMs to same uplink switch
- Separate management VLANs for each GAM
- Redundant uplinks for failover

**Large MDU Example** (500 units):
- Deploy 2× GAM-24-C (coax)
- Total capacity: 768 subscribers (oversubscribed)
- Actual take rate: 50% = 250 subscribers
- Redundant 10G uplinks from each GAM

---

## Conclusion

The Positron GAM architecture provides a highly efficient and cost-effective solution for delivering Gigabit services to MDU subscribers by leveraging existing coaxial or copper infrastructure. The system's key strengths include:

1. **Infrastructure Reuse**: No need for costly fiber-to-unit deployments
2. **High Density**: Up to 16 subscribers per port (coax)
3. **Near-Gigabit Performance**: 1.7 Gbps per port with G.hn Wave 2
4. **Carrier-Grade**: Non-blocking switching, VLAN management, QoS
5. **Security**: AES-128 encryption, isolation between subscribers
6. **Scalability**: Multiple GAMs, 20 Gbps uplink capacity
7. **Standards-Based**: ITU-T G.hn, Carrier Ethernet 2.0, OMCI

This block diagram and documentation provide the foundation for understanding, deploying, and managing Positron GAM networks in MDU environments.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-10
**Positron GAM Management System Project**
https://github.com/your-repo/positron-gam-management
