"""SNMP client for GAM device communication"""
from pysnmp.hlapi import *
import logging
from typing import Optional, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)


class SNMPClient:
    """SNMP client for GAM device communication"""

    # Common OIDs for GAM devices
    OID_SYSTEM_DESC = '1.3.6.1.2.1.1.1.0'
    OID_SYSTEM_UPTIME = '1.3.6.1.2.1.1.3.0'
    OID_SYSTEM_NAME = '1.3.6.1.2.1.1.5.0'
    OID_IF_NUMBER = '1.3.6.1.2.1.2.1.0'
    OID_IF_DESC = '1.3.6.1.2.1.2.2.1.2'
    OID_IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8'
    OID_IF_ADMIN_STATUS = '1.3.6.1.2.1.2.2.1.7'

    def __init__(
        self,
        ip_address: str,
        community: Optional[str] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None
    ):
        self.ip_address = ip_address
        self.community = community or settings.default_snmp_community
        self.timeout = timeout or settings.snmp_timeout
        self.retries = retries or settings.snmp_retries

    async def get(self, oid: str) -> Optional[str]:
        """Get single SNMP value"""
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.ip_address, 161), timeout=self.timeout, retries=self.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )

            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

            if errorIndication:
                logger.error(f"SNMP error: {errorIndication}")
                return None
            elif errorStatus:
                logger.error(f"SNMP error: {errorStatus.prettyPrint()}")
                return None
            else:
                for varBind in varBinds:
                    return str(varBind[1])

        except Exception as e:
            logger.error(f"SNMP get error for {self.ip_address}: {e}")
            return None

    async def get_bulk(self, oid: str, max_repetitions: int = 10) -> Dict[str, Any]:
        """Get multiple SNMP values using GETBULK"""
        results = {}
        try:
            iterator = bulkCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.ip_address, 161), timeout=self.timeout, retries=self.retries),
                ContextData(),
                0, max_repetitions,
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False
            )

            for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                if errorIndication:
                    logger.error(f"SNMP error: {errorIndication}")
                    break
                elif errorStatus:
                    logger.error(f"SNMP error: {errorStatus.prettyPrint()}")
                    break
                else:
                    for varBind in varBinds:
                        oid_str = str(varBind[0])
                        value = str(varBind[1])
                        results[oid_str] = value

        except Exception as e:
            logger.error(f"SNMP get_bulk error for {self.ip_address}: {e}")

        return results

    async def set(self, oid: str, value: Any, value_type: str = 'i') -> bool:
        """Set SNMP value"""
        try:
            # Map value types: i=Integer, s=String, a=IpAddress, etc.
            if value_type == 'i':
                value_obj = Integer(value)
            elif value_type == 's':
                value_obj = OctetString(value)
            else:
                value_obj = OctetString(value)

            iterator = setCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.ip_address, 161), timeout=self.timeout, retries=self.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid), value_obj)
            )

            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

            if errorIndication:
                logger.error(f"SNMP set error: {errorIndication}")
                return False
            elif errorStatus:
                logger.error(f"SNMP set error: {errorStatus.prettyPrint()}")
                return False
            else:
                return True

        except Exception as e:
            logger.error(f"SNMP set error for {self.ip_address}: {e}")
            return False

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'description': await self.get(self.OID_SYSTEM_DESC),
            'uptime': await self.get(self.OID_SYSTEM_UPTIME),
            'name': await self.get(self.OID_SYSTEM_NAME)
        }

    async def get_interface_count(self) -> int:
        """Get number of interfaces"""
        count = await self.get(self.OID_IF_NUMBER)
        return int(count) if count else 0

    async def get_interface_status(self, interface_index: int) -> Dict[str, Any]:
        """Get interface status"""
        desc_oid = f"{self.OID_IF_DESC}.{interface_index}"
        oper_oid = f"{self.OID_IF_OPER_STATUS}.{interface_index}"
        admin_oid = f"{self.OID_IF_ADMIN_STATUS}.{interface_index}"

        return {
            'description': await self.get(desc_oid),
            'operational_status': await self.get(oper_oid),
            'admin_status': await self.get(admin_oid)
        }

    async def test_connection(self) -> bool:
        """Test SNMP connectivity"""
        result = await self.get(self.OID_SYSTEM_DESC)
        return result is not None

    async def get_all_ports_status(self) -> Dict[int, Dict[str, Any]]:
        """
        Get status of all ports on the GAM device
        Returns a dict with port_number as key and port info as value
        """
        ports_info = {}

        try:
            # Get interface count first
            interface_count = await self.get_interface_count()
            logger.info(f"Device {self.ip_address} has {interface_count} interfaces")

            # Query each interface
            for if_index in range(1, interface_count + 1):
                port_info = await self.get_interface_status(if_index)

                # Add interface index
                port_info['interface_index'] = if_index

                # Determine port number (typically interface index maps to port number for GAM devices)
                port_info['port_number'] = if_index

                ports_info[if_index] = port_info

            return ports_info

        except Exception as e:
            logger.error(f"Error getting ports status for {self.ip_address}: {e}")
            return {}

    async def discover_gam_device(self) -> Optional[Dict[str, Any]]:
        """
        Discover GAM device information via SNMP
        Returns device info including model, firmware, serial, MAC, etc.
        """
        try:
            # Get basic system info
            system_info = await self.get_system_info()
            if not system_info or not system_info.get('description'):
                logger.error(f"Unable to get system description from {self.ip_address}")
                return None

            # Extract model from system description
            # Expected format: "Positron GAM-12-M ..." or similar
            sys_desc = system_info.get('description', '')
            model = self._extract_model_from_description(sys_desc)

            # Get interface count to validate model
            interface_count = await self.get_interface_count()

            # Get MAC address (from first interface)
            # OID 1.3.6.1.2.1.2.2.1.6.1 is ifPhysAddress for interface 1
            mac_address = await self.get('1.3.6.1.2.1.2.2.1.6.1')
            if mac_address:
                # Convert MAC from hex string to readable format
                mac_address = self._format_mac_address(mac_address)

            # Get firmware version (may be in sysDescr or a custom OID)
            firmware = self._extract_firmware_from_description(sys_desc)

            # Get serial number (if available via standard OID)
            # OID 1.3.6.1.2.1.47.1.1.1.1.11.1 is entPhysicalSerialNum
            serial_number = await self.get('1.3.6.1.2.1.47.1.1.1.1.11.1')

            device_info = {
                'ip_address': self.ip_address,
                'model': model,
                'firmware_version': firmware,
                'serial_number': serial_number,
                'mac_address': mac_address,
                'system_description': sys_desc,
                'system_name': system_info.get('name'),
                'uptime': system_info.get('uptime'),
                'interface_count': interface_count,
                'discovered': True
            }

            logger.info(f"Successfully discovered GAM device at {self.ip_address}: {model}")
            return device_info

        except Exception as e:
            logger.error(f"Error discovering GAM device at {self.ip_address}: {e}")
            return None

    def _extract_model_from_description(self, sys_desc: str) -> Optional[str]:
        """Extract GAM model from system description"""
        import re
        # Look for GAM-XX-X pattern (e.g., GAM-12-M, GAM-24-C)
        match = re.search(r'GAM-(\d+)-([MC])', sys_desc, re.IGNORECASE)
        if match:
            port_count = match.group(1)
            media_type = match.group(2).upper()
            return f"GAM-{port_count}-{media_type}"

        # If not found, try to infer from description
        if 'positron' in sys_desc.lower() and 'gam' in sys_desc.lower():
            return "GAM-Unknown"

        return None

    def _extract_firmware_from_description(self, sys_desc: str) -> Optional[str]:
        """Extract firmware version from system description"""
        import re
        # Look for version patterns like "v1.2.3" or "version 1.2.3"
        match = re.search(r'v?(\d+\.\d+\.\d+)', sys_desc, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _format_mac_address(self, mac_raw: str) -> Optional[str]:
        """Format MAC address to standard notation"""
        try:
            # Remove any non-hex characters
            import re
            hex_only = re.sub(r'[^0-9a-fA-F]', '', str(mac_raw))

            # If it's already formatted, return as-is
            if ':' in str(mac_raw):
                return str(mac_raw)

            # Format as XX:XX:XX:XX:XX:XX
            if len(hex_only) >= 12:
                return ':'.join(hex_only[i:i+2] for i in range(0, 12, 2))

            return None
        except Exception as e:
            logger.warning(f"Failed to format MAC address {mac_raw}: {e}")
            return None

    async def get_gam_ports_info(self) -> Optional[Dict[int, Dict[str, Any]]]:
        """
        Query Positron GAM-specific port information using discovered enterprise OIDs

        Based on SNMP walk discoveries:
        - Positron Enterprise OID: 1.3.6.1.4.1.20095
        - Port table: 1.3.6.1.4.1.20095.2001.11.1.2.1.1.{sub_oid}.{index}
        - Indices observed: 1000001-1000006 (6 entries for a 4-port GAM-4-C)

        Returns dict with port_number as key and port info dict as value
        """
        try:
            ports_info = {}

            # Positron GAM port table base OID
            base_oid = '1.3.6.1.4.1.20095.2001.11.1.2.1.1'

            # Query all port indices (discovered: 1000001-1000006)
            # We'll query indices 1000001 through 1000020 to be safe
            for idx in range(1000001, 1000021):
                port_data = {}

                # Sub-OIDs discovered (1-11):
                # .2 = 2 (constant)
                # .3 = varies (6 for most, 8 and 5 for others - possibly port number?)
                # .4 = 0 (mostly)
                # .5 = 0 or 1 (link status? 1 = connected?)
                # .6 = 0 (unknown)
                # .7 = 2014 or 2048 (bandwidth/speed?)
                # .8 = 2 (status?)
                # .9 = 0 (unknown)
                # .10 = 2 (unknown)
                # .11 = 0, 1, or 3 (varies - possibly active subscribers on coax port?)

                # Try to get key values
                sub_oid_3 = await self.get(f'{base_oid}.3.{idx}')  # Possible port number
                sub_oid_5 = await self.get(f'{base_oid}.5.{idx}')  # Possible link status
                sub_oid_7 = await self.get(f'{base_oid}.7.{idx}')  # Possible speed/bandwidth
                sub_oid_11 = await self.get(f'{base_oid}.11.{idx}')  # Possible subscriber count

                # If we got valid data, this index exists
                if sub_oid_3 is not None:
                    # Map to actual port number
                    # Based on patterns: indices with .3=8 or .3=5 seem to be active ports
                    # .3=6 might be unused/disabled ports
                    port_number = int(sub_oid_3) if sub_oid_3 else 0

                    # Determine link status
                    link_status = 'up' if (sub_oid_5 and int(sub_oid_5) == 1) else 'down'

                    # Get speed (convert from unknown units)
                    speed_value = int(sub_oid_7) if sub_oid_7 else 0

                    # Get subscriber count (for coax ports)
                    subscriber_count = int(sub_oid_11) if sub_oid_11 else 0

                    port_data = {
                        'positron_index': idx,
                        'port_indicator': port_number,
                        'link_status': link_status,
                        'speed_indicator': speed_value,
                        'subscriber_count': subscriber_count,
                        'raw_data': {
                            'oid_3': int(sub_oid_3) if sub_oid_3 else None,
                            'oid_5': int(sub_oid_5) if sub_oid_5 else None,
                            'oid_7': int(sub_oid_7) if sub_oid_7 else None,
                            'oid_11': int(sub_oid_11) if sub_oid_11 else None,
                        }
                    }

                    # Only add if we have meaningful data
                    if port_number > 0:
                        ports_info[idx] = port_data
                        logger.debug(f"Port index {idx}: {port_data}")
                else:
                    # No more ports, break
                    break

            logger.info(f"Retrieved {len(ports_info)} Positron port entries from {self.ip_address}")
            return ports_info if ports_info else None

        except Exception as e:
            logger.error(f"Error getting GAM ports info from {self.ip_address}: {e}")
            return None

    async def get_bridge_mac_table(self) -> Optional[Dict[str, Any]]:
        """
        Query bridge forwarding table to get all learned MAC addresses and their ports

        Uses standard Bridge MIB:
        - 1.3.6.1.2.1.17.4.3.1.1 = dot1dTpFdbAddress (MAC addresses)
        - 1.3.6.1.2.1.17.4.3.1.2 = dot1dTpFdbPort (bridge port for each MAC)
        - 1.3.6.1.2.1.17.1.4.1.2 = dot1dBasePortIfIndex (bridge port to interface index)

        Returns dict with port mappings and MAC addresses
        """
        try:
            mac_table = {}
            port_mapping = {}

            # First, get bridge port to interface index mapping
            logger.debug(f"Getting bridge port to interface index mapping for {self.ip_address}")
            for bridge_port in range(1, 20):
                oid = f'1.3.6.1.2.1.17.1.4.1.2.{bridge_port}'
                if_index = await self.get(oid)
                if if_index:
                    port_mapping[bridge_port] = int(if_index)
                else:
                    break

            logger.debug(f"Bridge port mapping: {port_mapping}")

            # Now get MAC addresses and their bridge ports
            logger.debug(f"Getting MAC address table for {self.ip_address}")

            # Walk the dot1dTpFdbPort OID to get all MACs and their ports
            from pysnmp.hlapi import (
                SnmpEngine, CommunityData, UdpTransportTarget,
                ContextData, ObjectType, ObjectIdentity, nextCmd
            )

            mac_to_port = {}
            for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=0),
                UdpTransportTarget((self.ip_address, 161), timeout=2, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity('1.3.6.1.2.1.17.4.3.1.2')),
                lexicographicMode=False,
                maxRows=100
            ):
                if errorIndication or errorStatus:
                    break

                for varBind in varBinds:
                    oid = varBind[0].prettyPrint()
                    bridge_port = int(varBind[1])

                    # Extract MAC from OID (last 6 octets)
                    oid_parts = oid.split('.')
                    if len(oid_parts) >= 6:
                        mac_octets = oid_parts[-6:]
                        mac_address = ':'.join([f'{int(x):02x}' for x in mac_octets])

                        # Determine if this is a Positron endpoint (OUI 00:0e:d8)
                        is_positron = mac_address.startswith('00:0e:d8')

                        if_index = port_mapping.get(bridge_port)

                        mac_to_port[mac_address] = {
                            'mac_address': mac_address,
                            'bridge_port': bridge_port,
                            'interface_index': if_index,
                            'is_positron_endpoint': is_positron,
                            'vendor_oui': mac_address[:8].upper()
                        }

            logger.info(f"Retrieved {len(mac_to_port)} MAC addresses from {self.ip_address}")

            return {
                'port_mapping': port_mapping,
                'mac_addresses': mac_to_port,
                'total_macs': len(mac_to_port)
            }

        except Exception as e:
            logger.error(f"Error getting bridge MAC table from {self.ip_address}: {e}")
            return None
