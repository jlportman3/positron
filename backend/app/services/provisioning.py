"""Subscriber provisioning service"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from ..models.subscriber import Subscriber, SubscriberStatus
from ..models.gam import GAMPort, PortStatus
from ..models.bandwidth import BandwidthPlan
from ..services.gam_manager import PortManager
from ..config import settings

logger = logging.getLogger(__name__)


class ProvisioningEngine:
    """Core provisioning logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.port_manager = PortManager(db)

    async def provision_subscriber(
        self,
        subscriber_id: UUID,
        gam_port_id: UUID,
        bandwidth_plan_id: UUID,
        vlan_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Provision subscriber service"""
        try:
            # Get subscriber
            subscriber_result = await self.db.execute(
                select(Subscriber).where(Subscriber.id == subscriber_id)
            )
            subscriber = subscriber_result.scalar_one_or_none()

            if not subscriber:
                return {'success': False, 'error': 'Subscriber not found'}

            # Get port
            port_result = await self.db.execute(
                select(GAMPort).where(GAMPort.id == gam_port_id)
            )
            port = port_result.scalar_one_or_none()

            if not port:
                return {'success': False, 'error': 'Port not found'}

            # Check port availability
            if not port.is_available:
                return {'success': False, 'error': 'Port is not available'}

            # Get bandwidth plan
            plan_result = await self.db.execute(
                select(BandwidthPlan).where(BandwidthPlan.id == bandwidth_plan_id)
            )
            plan = plan_result.scalar_one_or_none()

            if not plan:
                return {'success': False, 'error': 'Bandwidth plan not found'}

            # Assign VLAN if not provided
            if not vlan_id:
                vlan_id = await self._assign_vlan(subscriber_id)

            # Configure port
            success = await self.port_manager.configure_port(
                gam_port_id,
                vlan_id,
                plan.downstream_mbps,
                plan.upstream_mbps,
                mimo_enabled=port.port_type.value == 'mimo'
            )

            if not success:
                return {'success': False, 'error': 'Port configuration failed'}

            # Update subscriber
            subscriber.gam_port_id = gam_port_id
            subscriber.gam_device_id = port.gam_device_id
            subscriber.vlan_id = vlan_id
            subscriber.bandwidth_plan_id = bandwidth_plan_id
            subscriber.status = SubscriberStatus.ACTIVE

            await self.db.commit()

            logger.info(f"Provisioned subscriber {subscriber.name} on port {port.port_number}")

            return {
                'success': True,
                'subscriber_id': str(subscriber_id),
                'port_id': str(gam_port_id),
                'vlan_id': vlan_id,
                'bandwidth_plan': {
                    'downstream': plan.downstream_mbps,
                    'upstream': plan.upstream_mbps
                }
            }

        except Exception as e:
            logger.error(f"Provisioning error: {e}")
            await self.db.rollback()
            return {'success': False, 'error': str(e)}

    async def deprovision_subscriber(self, subscriber_id: UUID) -> Dict[str, Any]:
        """Deprovision subscriber service"""
        try:
            # Get subscriber
            result = await self.db.execute(
                select(Subscriber).where(Subscriber.id == subscriber_id)
            )
            subscriber = result.scalar_one_or_none()

            if not subscriber:
                return {'success': False, 'error': 'Subscriber not found'}

            if not subscriber.gam_port_id:
                return {'success': False, 'error': 'Subscriber not provisioned'}

            # Disable port
            port_result = await self.db.execute(
                select(GAMPort).where(GAMPort.id == subscriber.gam_port_id)
            )
            port = port_result.scalar_one_or_none()

            if port:
                # For copper ports, disable the port
                # For coax ports, just mark subscriber as inactive
                if port.port_type.value in ['mimo', 'siso']:
                    port.status = PortStatus.DISABLED

            # Update subscriber
            subscriber.status = SubscriberStatus.SUSPENDED
            subscriber.gam_port_id = None

            await self.db.commit()

            logger.info(f"Deprovisioned subscriber {subscriber.name}")

            return {
                'success': True,
                'subscriber_id': str(subscriber_id)
            }

        except Exception as e:
            logger.error(f"Deprovisioning error: {e}")
            await self.db.rollback()
            return {'success': False, 'error': str(e)}

    async def update_subscriber_bandwidth(
        self,
        subscriber_id: UUID,
        bandwidth_plan_id: UUID
    ) -> Dict[str, Any]:
        """Update subscriber bandwidth plan"""
        try:
            # Get subscriber
            result = await self.db.execute(
                select(Subscriber).where(Subscriber.id == subscriber_id)
            )
            subscriber = result.scalar_one_or_none()

            if not subscriber:
                return {'success': False, 'error': 'Subscriber not found'}

            if not subscriber.gam_port_id:
                return {'success': False, 'error': 'Subscriber not provisioned'}

            # Get new bandwidth plan
            plan_result = await self.db.execute(
                select(BandwidthPlan).where(BandwidthPlan.id == bandwidth_plan_id)
            )
            plan = plan_result.scalar_one_or_none()

            if not plan:
                return {'success': False, 'error': 'Bandwidth plan not found'}

            # Reconfigure port with new bandwidth
            success = await self.port_manager.configure_port(
                subscriber.gam_port_id,
                subscriber.vlan_id,
                plan.downstream_mbps,
                plan.upstream_mbps
            )

            if not success:
                return {'success': False, 'error': 'Port reconfiguration failed'}

            # Update subscriber
            subscriber.bandwidth_plan_id = bandwidth_plan_id
            await self.db.commit()

            logger.info(f"Updated bandwidth for subscriber {subscriber.name}")

            return {
                'success': True,
                'subscriber_id': str(subscriber_id),
                'new_plan': {
                    'downstream': plan.downstream_mbps,
                    'upstream': plan.upstream_mbps
                }
            }

        except Exception as e:
            logger.error(f"Bandwidth update error: {e}")
            await self.db.rollback()
            return {'success': False, 'error': str(e)}

    async def _assign_vlan(self, subscriber_id: UUID) -> int:
        """Assign VLAN ID to subscriber"""
        # Simple implementation: find next available VLAN
        # In production, implement proper VLAN pool management

        result = await self.db.execute(
            select(Subscriber.vlan_id).where(Subscriber.vlan_id.isnot(None))
        )
        used_vlans = set(row[0] for row in result.all())

        # Find first available VLAN in range
        for vlan_id in range(settings.default_subscriber_vlan_start, settings.default_subscriber_vlan_end):
            if vlan_id not in used_vlans:
                return vlan_id

        # Fallback to random VLAN if all are used
        import random
        return random.randint(settings.default_subscriber_vlan_start, settings.default_subscriber_vlan_end)

    async def validate_provisioning(
        self,
        gam_port_id: UUID,
        bandwidth_plan_id: UUID
    ) -> Dict[str, Any]:
        """Validate provisioning request"""
        errors = []

        # Check port exists and is available
        port_result = await self.db.execute(
            select(GAMPort).where(GAMPort.id == gam_port_id)
        )
        port = port_result.scalar_one_or_none()

        if not port:
            errors.append("Port not found")
        elif not port.is_available:
            errors.append("Port is not available")
        elif not port.enabled:
            errors.append("Port is disabled")

        # Check bandwidth plan exists
        plan_result = await self.db.execute(
            select(BandwidthPlan).where(BandwidthPlan.id == bandwidth_plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            errors.append("Bandwidth plan not found")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
