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
