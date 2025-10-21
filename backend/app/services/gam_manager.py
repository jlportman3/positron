"""GAM device manager service"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from ..models.gam import GAMDevice, GAMPort, DeviceStatus, PortStatus, PortType
from ..utils.snmp_client import SNMPClient
from ..utils.ssh_client import SSHClient
from ..config import settings

logger = logging.getLogger(__name__)


class GAMManager:
    """Manager for GAM devices"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_device(
        self,
        name: str,
        ip_address: str,
        model: str,
        snmp_community: Optional[str] = None,
        ssh_credentials: Optional[Dict] = None,
        location: Optional[str] = None,
        management_vlan: Optional[int] = None
    ) -> GAMDevice:
        """Create new GAM device"""
        device = GAMDevice(
            name=name,
            ip_address=ip_address,
            model=model,
            snmp_community=snmp_community or settings.default_snmp_community,
            ssh_credentials=ssh_credentials,
            location=location,
            management_vlan=management_vlan or settings.default_management_vlan,
            status=DeviceStatus.OFFLINE
        )

        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)

        # Initialize ports for the device
        await self._initialize_ports(device)

        logger.info(f"Created GAM device: {name} ({ip_address})")
        return device

    async def get_device(self, device_id: UUID) -> Optional[GAMDevice]:
        """Get device by ID"""
        result = await self.db.execute(
            select(GAMDevice).where(GAMDevice.id == device_id)
        )
        return result.scalar_one_or_none()

    async def get_device_by_ip(self, ip_address: str) -> Optional[GAMDevice]:
        """Get device by IP address"""
        result = await self.db.execute(
            select(GAMDevice).where(GAMDevice.ip_address == ip_address)
        )
        return result.scalar_one_or_none()

    async def list_devices(
        self,
        status: Optional[DeviceStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[GAMDevice]:
        """List all devices with optional filtering"""
        query = select(GAMDevice)

        if status:
            query = query.where(GAMDevice.status == status)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_device(
        self,
        device_id: UUID,
        **kwargs
    ) -> Optional[GAMDevice]:
        """Update device properties"""
        device = await self.get_device(device_id)
        if not device:
            return None

        for key, value in kwargs.items():
            if hasattr(device, key) and value is not None:
                setattr(device, key, value)

        await self.db.commit()
        await self.db.refresh(device)
        logger.info(f"Updated device {device.name}")
        return device

    async def delete_device(self, device_id: UUID) -> bool:
        """Delete device"""
        device = await self.get_device(device_id)
        if not device:
            return False

        await self.db.delete(device)
        await self.db.commit()
        logger.info(f"Deleted device {device.name}")
        return True

    async def _initialize_ports(self, device: GAMDevice):
        """Initialize ports for a device"""
        port_count = device.port_count
        port_type = PortType.COAX if device.is_coax_model else PortType.MIMO

        for port_num in range(1, port_count + 1):
            port = GAMPort(
                gam_device_id=device.id,
                port_number=port_num,
                port_type=port_type,
                status=PortStatus.DOWN,
                enabled=True,
                name=f"Port {port_num}"
            )
            self.db.add(port)

        await self.db.commit()
        logger.info(f"Initialized {port_count} ports for device {device.name}")

    async def get_port(self, port_id: UUID) -> Optional[GAMPort]:
        """Get port by ID"""
        result = await self.db.execute(
            select(GAMPort).where(GAMPort.id == port_id)
        )
        return result.scalar_one_or_none()

    async def get_device_ports(self, device_id: UUID) -> List[GAMPort]:
        """Get all ports for a device"""
        result = await self.db.execute(
            select(GAMPort).where(GAMPort.gam_device_id == device_id)
        )
        return list(result.scalars().all())

    async def update_port(
        self,
        port_id: UUID,
        **kwargs
    ) -> Optional[GAMPort]:
        """Update port properties"""
        port = await self.get_port(port_id)
        if not port:
            return None

        for key, value in kwargs.items():
            if hasattr(port, key) and value is not None:
                setattr(port, key, value)

        await self.db.commit()
        await self.db.refresh(port)
        logger.info(f"Updated port {port.port_number} on device {port.device.name}")
        return port

    async def test_device_connectivity(self, device_id: UUID) -> Dict[str, Any]:
        """Test device connectivity via SNMP and SSH"""
        device = await self.get_device(device_id)
        if not device:
            return {'success': False, 'error': 'Device not found'}

        results = {
            'device_id': str(device_id),
            'device_name': device.name,
            'snmp_test': False,
            'ssh_test': False,
            'errors': []
        }

        # Test SNMP
        try:
            snmp_client = SNMPClient(device.ip_address, device.snmp_community)
            results['snmp_test'] = await snmp_client.test_connection()
        except Exception as e:
            results['errors'].append(f"SNMP test failed: {str(e)}")

        # Test SSH
        if device.ssh_credentials:
            try:
                ssh_client = SSHClient(
                    device.ip_address,
                    device.ssh_credentials.get('username'),
                    password=device.ssh_credentials.get('password'),
                    private_key=device.ssh_credentials.get('private_key')
                )
                results['ssh_test'] = await ssh_client.test_connection()
            except Exception as e:
                results['errors'].append(f"SSH test failed: {str(e)}")

        results['success'] = results['snmp_test'] and results['ssh_test']
        return results

    async def update_device_status(self, device_id: UUID) -> Dict[str, Any]:
        """Update device status from SNMP"""
        device = await self.get_device(device_id)
        if not device:
            return {'success': False, 'error': 'Device not found'}

        try:
            snmp_client = SNMPClient(device.ip_address, device.snmp_community)
            system_info = await snmp_client.get_system_info()

            if system_info.get('uptime'):
                # Device is online
                device.status = DeviceStatus.ONLINE
                device.uptime = int(system_info.get('uptime', 0))
                device.last_seen = func.now()

                await self.db.commit()
                logger.info(f"Updated status for device {device.name}: ONLINE")
                return {
                    'success': True,
                    'status': 'online',
                    'system_info': system_info
                }
            else:
                device.status = DeviceStatus.OFFLINE
                await self.db.commit()
                return {'success': False, 'status': 'offline'}

        except Exception as e:
            logger.error(f"Error updating device status: {e}")
            device.status = DeviceStatus.ERROR
            await self.db.commit()
            return {'success': False, 'error': str(e)}

    async def discover_devices(self, network_range: str) -> List[Dict[str, Any]]:
        """Discover GAM devices on network (basic implementation)"""
        # This is a simplified version - a real implementation would scan the network
        logger.info(f"Device discovery started for range: {network_range}")

        discovered = []
        # TODO: Implement actual network scanning
        # For now, this is a placeholder that would be extended with:
        # - Network scanning (nmap, scapy, etc.)
        # - SNMP polling to identify GAM devices
        # - MAC address verification

        return discovered


class PortManager:
    """Manager for GAM ports"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def configure_port(
        self,
        port_id: UUID,
        vlan_id: int,
        bandwidth_down: int,
        bandwidth_up: int,
        mimo_enabled: bool = False
    ) -> bool:
        """Configure port via SSH"""
        result = await self.db.execute(
            select(GAMPort).where(GAMPort.id == port_id)
        )
        port = result.scalar_one_or_none()

        if not port:
            logger.error(f"Port {port_id} not found")
            return False

        device = port.device

        if not device.ssh_credentials:
            logger.error(f"No SSH credentials for device {device.name}")
            return False

        try:
            ssh_client = SSHClient(
                device.ip_address,
                device.ssh_credentials.get('username'),
                password=device.ssh_credentials.get('password'),
                private_key=device.ssh_credentials.get('private_key')
            )

            await ssh_client.connect()
            success = await ssh_client.configure_port(
                port.port_number,
                vlan_id,
                bandwidth_down,
                bandwidth_up,
                mimo_enabled
            )
            await ssh_client.disconnect()

            if success:
                port.status = PortStatus.UP
                port.mimo_enabled = mimo_enabled
                await self.db.commit()
                logger.info(f"Configured port {port.port_number} on device {device.name}")

            return success

        except Exception as e:
            logger.error(f"Error configuring port: {e}")
            return False
