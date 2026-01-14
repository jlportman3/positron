# GAM Technical Knowledge Base

Detailed technical reference extracted from Positron GAM documentation

---

## JSON-RPC API Reference

### Available Methods

```
jsonRpc.status.introspection.generic.inventory.get
```

### Example API Calls

```json
{"method":"jsonRpc.status.introspection.generic.inventory.get", "params":[""],"id":"1"}

{"method":"jsonRpc.status.introspection.generic.inventory.get",  
"params":[""],"id":"1"}

```

## CLI Command Reference

### Show Commands

```
show         Display statistics count ers.
show  interface <port _type> <port_type_list> statistics [ { packets | bytes | errors | discards | f
show  interface <port _type> <port_type_list> veriph y
show  interface <port_type> < port_type_list> capabilities
show  interface <port_type> <port_type_list> status
show  interface vl an [ <vlan_list> ]
show  pppoe discovery statistics
show  pppoe forward  statistics
show aaa
show access -list
show access management
show access management [ statistics | < access_id_list > ]
show access-list [ interface [ <port_type> <por t_type_list> ] ] [ rate -limiter [ <1~16> ] ] [ ace 
show access-list ace -status [ static ] [ link -oam ] [ loop -protect ] [ dhcp ] [ ptp ] [ upnp ] [ 
show aggregation
show aggregation [ mode ]
show alarm
show alarm { active | log }
show all ghn endpoints  (discover)
show clock
```

### Configure Commands

```
% No ERPS groups configured.
0 GAM# configure terminal
<ipv4_netmask>  Select a subnet mask to configure.
<ipv4_ucast>  Select an IP Address to configure .
<ipv4_ucast>  Select an IP Address to configure.
<mac_ucast>  Select a MAC addre ss to configure.
<mac_ucast>  Select a MAC address to configure.
<vlan_id>  Select a VLAN id to configure.
<vlan_list>  Select a VLAN id to configure.
Configure NTP .
Configure Network Time Protocol .
Configure Network Time Protocol.
Configure a G.hn profile to define rate limiting  for upstream and downstream subscriber traffic.
Configure a terminal line.
Configure s a connection to a RADIUS  server.  The GAM supports up to five RADIUS servers. Servers a
Configure s a connection to a TACACS+ server. The GAM supports up to five TACACS+ servers. Servers a
Configure s the PPPOE  agent infor mation index base .
Configure s the PPPOE  agent information policy . When PPPoE forward  inform ation mode operation is
Configure s the PPPOE  information access no de ID.
Configure s the announcement URL of the do main controller . Announcements can be set to up to fo ur
```

### Ghn Commands

```
% Rebooting G.hn Endpoint 1 with MAC: 00:0f:df:11:05:54
00:0e:d8:13:08:1a  GAM# show ghn port 14 statistics
10          0          0          0   GAM# no ghn notch 1 GAM# ghn notch 1 startfreq 4.5 stopfreq 20
15 G.hn services  ................................ ................................ ................
2      VLAN0002                          G.hn 1/1 -24
4000   VLAN4000                          Gi 1/1 10G 1/1 -2 G.hn 1/13 -15,18
<ghn_endpoint> ] [ vid < ghn_vid> ] [ tagged | untagged ] [ { remapped -vid { none | <ghn_mapped_vid
<ghn_mac>  Endpoint MAC address.
<ghn_port2_vid > Set the G.hn VLAN ID for traffic on endpoint port 2 (G1001 -M or G1001 -C only).
<port_ type >  10GigabitEthernet  or G.hn .
<port_t ype>  10GigabitEtherne t or G.hn .
<port_t ype_list>  Port list in 1/ 1-5 for GigabitEthernet , 1/1 for G.hn .
<port_ty pe > 10GigabitEthernet or G.hn .
<port_type >  10GigabitEth ernet or G.hn .
<port_type >  10GigabitEthernet  or G.hn .
<port_type >  10GigabitEthernet or G.hn .
<port_type >  10GigabitEthernet or G.hn.
<port_type > Port type: Fast, Giga or G.hn ..
<port_type _list>  Port list in  1/1-2 for 10GigabitEthernet, 1/1 -24 for G.hn .
<port_type>  10GigabitEthernet  or G.hn
```

### Vlan Commands

```
% Invalid MVR IGMP VLAN 10.
% Invalid MVR MLD VLAN 10.
% Invalid PVLAN detected
'Mirroring' 'NTP' 'PTP' 'Ports' 'Priv ate_VLANs' 'QoS'
'UPnP' 'VCL' 'VLAN_Translation' 'VLANs' 'Voice_VL AN'
'ip-igmp -snooping' 'ip -igmp -snooping -port 'ip -igmp -snoopi ng-vlan' 'ipmc -profile'
'monitor' 'mstp'  'mvr' 'mvr -port' 'ntp' 'port' 'port -security' 'p tp' 'pvlan' 'qos' 'rmon' 'snmp'
'source -guard' 'ssh' 'upnp' 'user' 'vlan' 'voice -vlan' 'web -privilege -group -level'
10 VLAN management  ................................ ................................ ..............
10.2 PORT VLAN  ................................ ................................ ..................
10.2 Port VLAN
10.4 MULTICAST VLAN  REGISTRATION  ................................ ................................
10.5 PVLAN COMMANDS  ................................ ................................ .............
10.5 pvlan commands
100   VLAN0100
1000  VLAN1000
14    VLAN0014
15    VLAN0015
2      VLAN0002                          G.hn 1/1 -24
4000   VLAN4000                          Gi 1/1 10G 1/1 -2 G.hn 1/13 -15,18
```

### Network Commands

```
"hold time" multiplied with "timer" se conds ).
'Aggregation' 'Debug' 'Dhcp_Client'
'Green_Ethernet' 'IP2' 'IPMC_Snooping' 'LACP' 'LLDP'
'dhcp -snooping' 'dns' 'dot1x' 'eps 'e rps' 'evc' 'green -ethernet' 'http' 'icli'
'ip-igmp -snooping' 'ip -igmp -snooping -port 'ip -igmp -snoopi ng-vlan' 'ipmc -profile'
'ipmc -profile -range' 'ipv4' 'ipv6' 'ipv6 -mld-snooping' 'ipv6 -mld-snooping -port'
7.1 IPV4 ................................ ................................ .........................
7.1 IPv4
7.2 IPV6 ................................ ................................ .........................
7.2 IPv6
7.3 IPMC COMMANDS  ................................ ................................ ...............
7.3 ipmc commands
<0~15>  Send a message to multiple lines .
<0~16>  Send a message to multiple lines .
<2-1452>  2-1452 . Default : 56 (excluding MAC, IP and ICMP headers) .
<host_name > Identifies the RADIUS server . Specify a fully -qualified  host nam e or the server’s I
<ipv4_addr>  Gateway.
<ipv4_addr>  IPv4 a ddress.
<ipv4_addr>  Network.
<ipv4_mcast>  Valid IPv4 multicast address.
```

## Installation & Configuration

### Default IP Addresses

- 192.0.2.1
- 0.0.0.0

### VLANs Referenced

- VLAN 1
- VLAN 2
- VLAN 4093
- VLAN 4094

### Requirements

- ONT as required  that is compatible with the OLT ). These SFP+ ports can further
- The GAM devices require local 110-220Vac  power  and come  with a country -
- you need to use the “inner” pair.  When connecting a second pair (MIMO mode),
- the second  pair needs to be connected to the “outer” pair.
- be configured. This list is required for some application such as IPTV.   The
- allowed VLANs per end -point device can be configured. This list is required for
- be configured. This list is required for some application such as IPTV .  The
- per end -point device can be configured. This list is required for some application
- Name : This field is mandatory, and the name must be unique among all
- bandwidth plans. It must contain b etween 1 and 31 alphanumeric characters.
-  COAX : 10 to 800 Mbps . A service over 800M bps must be set to
- make sure the overall G.hn infrastructure is secure and delivers the required
- Positron Access Solutions  27 Document 180 -0186 -001 R0 3 Name : This field is mandatory, and the name must be unique among all
- endpoints . It must contain between 1 and 31 alphanumeric characters.
- Subscriber Name : This field is mandatory, and the  name must be unique among

## GAM Device Models

### Supported Models

| Model | Ports | Technology |
|-------|-------|------------|
| GAM-12-C | 12 | Coax |
| GAM-12-M | 12 | Copper |
| GAM-24-C | 24 | Coax |
| GAM-24-M | 24 | Copper |
| GAM-4-CRX | 4 | Coax |
| GAM-4-CX | 4 | Coax |
| GAM-4-MRX | 4 | Copper |
| GAM-4-MX | 4 | Copper |
| GAM-8-M | 8 | Copper |
| GAM-8-MRX | 8 | Copper |
| GAM-8-MX | 8 | Copper |

### Technologies

- SISO
- IGMP
- MIMO
- IPTV
- G.hn

### Distance Specifications

Common distances mentioned: 150, 2, 23, 24, 250, 30, 5, 500, 800

