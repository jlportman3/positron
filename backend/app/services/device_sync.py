"""
Device synchronization service.

Handles pulling data from GAM devices via JSON-RPC and storing it in the database.
"""
import logging
import re
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import Device, Endpoint, Subscriber, Bandwidth, Port
from app.rpc.client import GamRpcClient, GamRpcError, create_client_for_device

logger = logging.getLogger(__name__)


class DeviceSyncService:
    """Service for synchronizing data from GAM devices."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_device(self, device: Device) -> dict:
        """Sync all data from a device.

        Args:
            device: Device model instance

        Returns:
            Dict with sync results for each data type
        """
        results = {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "endpoints": {"success": False, "count": 0, "error": None},
            "subscribers": {"success": False, "count": 0, "error": None},
            "bandwidths": {"success": False, "count": 0, "error": None},
            "ports": {"success": False, "count": 0, "error": None},
        }

        client = await create_client_for_device(device)

        try:
            # Sync endpoints
            try:
                count = await self.sync_endpoints(device, client)
                results["endpoints"] = {"success": True, "count": count, "error": None}
                device.last_endpoint_brief_pulled = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error syncing endpoints for {device.serial_number}: {e}")
                results["endpoints"]["error"] = str(e)

            # Sync subscribers
            try:
                count = await self.sync_subscribers(device, client)
                results["subscribers"] = {"success": True, "count": count, "error": None}
                device.last_subscriber_pulled = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error syncing subscribers for {device.serial_number}: {e}")
                results["subscribers"]["error"] = str(e)

            # Sync bandwidth profiles
            try:
                count = await self.sync_bandwidths(device, client)
                results["bandwidths"] = {"success": True, "count": count, "error": None}
                device.last_bandwidth_pulled = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error syncing bandwidths for {device.serial_number}: {e}")
                results["bandwidths"]["error"] = str(e)

            # Sync port status
            try:
                count = await self.sync_ports(device, client)
                results["ports"] = {"success": True, "count": count, "error": None}
                device.last_port_pulled = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error syncing ports for {device.serial_number}: {e}")
                results["ports"]["error"] = str(e)

            # Sync uptime
            try:
                await self.sync_uptime(device, client)
            except Exception as e:
                logger.error(f"Error syncing uptime for {device.serial_number}: {e}")

            # Update device online status - only mark online if at least one operation succeeded
            any_success = (
                results["endpoints"]["success"] or
                results["subscribers"]["success"] or
                results["bandwidths"]["success"] or
                results["ports"]["success"]
            )

            if any_success:
                device.is_online = True
                device.last_seen = datetime.utcnow()
            else:
                # All operations failed - device is not reachable
                device.is_online = False
                logger.warning(f"Device {device.serial_number} marked offline - all sync operations failed")

                # Cascade offline status to endpoints and subscribers
                endpoint_result = await self.db.execute(
                    select(Endpoint).where(Endpoint.device_id == device.id)
                )
                for endpoint in endpoint_result.scalars():
                    if endpoint.alive:
                        endpoint.alive = False

                subscriber_result = await self.db.execute(
                    select(Subscriber).where(Subscriber.device_id == device.id)
                )
                for subscriber in subscriber_result.scalars():
                    if subscriber.alive:
                        subscriber.alive = False

            await self.db.commit()

        except Exception as e:
            logger.error(f"Error connecting to device {device.serial_number}: {e}")
            device.is_online = False

            # Cascade offline status to endpoints and subscribers
            endpoint_result = await self.db.execute(
                select(Endpoint).where(Endpoint.device_id == device.id)
            )
            for endpoint in endpoint_result.scalars():
                if endpoint.alive:
                    endpoint.alive = False

            subscriber_result = await self.db.execute(
                select(Subscriber).where(Subscriber.device_id == device.id)
            )
            for subscriber in subscriber_result.scalars():
                if subscriber.alive:
                    subscriber.alive = False

            await self.db.commit()
            raise

        finally:
            await client.close()

        return results

    async def sync_endpoints(self, device: Device, client: GamRpcClient) -> int:
        """Sync endpoints from a device.

        Args:
            device: Device model instance
            client: JSON-RPC client

        Returns:
            Number of endpoints synced
        """
        # Get endpoints from device
        rpc_endpoints = await client.get_endpoints_brief()

        if not rpc_endpoints:
            # No endpoints, but that's OK - just mark any existing ones as offline
            result = await self.db.execute(
                select(Endpoint).where(
                    and_(Endpoint.device_id == device.id, Endpoint.alive == True)
                )
            )
            for endpoint in result.scalars():
                endpoint.alive = False
            return 0

        # Track MACs we've seen
        seen_macs = set()

        for ep_data in rpc_endpoints:
            # Handle both direct format and key/val format
            if isinstance(ep_data, dict) and "key" in ep_data:
                mac = ep_data["key"]
                data = ep_data.get("val", {})
            elif isinstance(ep_data, dict) and "mac" in ep_data:
                mac = ep_data["mac"]
                data = ep_data
            else:
                continue

            seen_macs.add(mac.lower())

            # Extract fields from data (handle both PascalCase and camelCase)
            def get(key, default=None):
                # Try various case formats
                for k in [key, key[0].lower() + key[1:], key.lower()]:
                    if k in data:
                        return data[k]
                return default

            # Find or create endpoint
            result = await self.db.execute(
                select(Endpoint).where(Endpoint.mac_address == mac)
            )
            endpoint = result.scalar_one_or_none()

            # Determine if alive based on state
            state = get("State", "")
            is_alive = state not in ["disconnected", "offline", ""]

            if endpoint:
                # Update existing endpoint
                endpoint.device_id = device.id
                endpoint.alive = is_alive
                endpoint.conf_endpoint_id = get("ConfEndpointId")
                endpoint.conf_endpoint_name = get("ConfEndpointName")
                endpoint.conf_port_if_index = get("ConfPortIfIndex")
                endpoint.conf_auto_port = get("ConfAutoPort", False)
                endpoint.detected_port_if_index = get("DetectedPortIfIndex")
                endpoint.conf_user_id = get("ConfUserId")
                endpoint.conf_user_name = get("ConfUserName")
                endpoint.conf_user_uid = get("ConfUserUid")
                endpoint.conf_bw_profile_id = get("ConfBwProfileId")
                endpoint.conf_bw_profile_name = get("ConfBwProfileName")
                endpoint.conf_bw_profile_uid = get("ConfBwProfileUid")
                endpoint.state = state
                endpoint.model_type = get("ModelType")
                endpoint.model_string = get("ModelString")
                endpoint.fw_mismatch = get("FwMismatch", False)
            else:
                # Create new endpoint
                endpoint = Endpoint(
                    device_id=device.id,
                    mac_address=mac,
                    alive=is_alive,
                    conf_endpoint_id=get("ConfEndpointId"),
                    conf_endpoint_name=get("ConfEndpointName"),
                    conf_port_if_index=get("ConfPortIfIndex"),
                    conf_auto_port=get("ConfAutoPort", False),
                    detected_port_if_index=get("DetectedPortIfIndex"),
                    conf_user_id=get("ConfUserId"),
                    conf_user_name=get("ConfUserName"),
                    conf_user_uid=get("ConfUserUid"),
                    conf_bw_profile_id=get("ConfBwProfileId"),
                    conf_bw_profile_name=get("ConfBwProfileName"),
                    conf_bw_profile_uid=get("ConfBwProfileUid"),
                    state=state,
                    model_type=get("ModelType"),
                    model_string=get("ModelString"),
                    fw_mismatch=get("FwMismatch", False),
                )
                self.db.add(endpoint)

        # Mark endpoints we didn't see as offline
        result = await self.db.execute(
            select(Endpoint).where(Endpoint.device_id == device.id)
        )
        for endpoint in result.scalars():
            if endpoint.mac_address.lower() not in seen_macs:
                endpoint.alive = False

        return len(seen_macs)

    async def sync_subscribers(self, device: Device, client: GamRpcClient) -> int:
        """Sync subscribers from a device.

        Field mapping from JSON-RPC response:
        - Id → json_id
        - Uid → uid
        - Name → name
        - Description → description
        - EndpointId → endpoint_json_id
        - EndpointName → endpoint_name
        - EndpointMacAddress → endpoint_mac_address
        - BwProfileId → bw_profile_id
        - BwProfileName → bw_profile_name
        - BwProfileUid → bw_profile_uid
        - VlanId + OuterTagVlanId + RemappedVlanId → port1_vlan_id (formatted)
        - VlanIsTagged → vlan_is_tagged
        - Port2VlanId → port2_vlan_id
        - Port2VlanIsTagged → vlan_is_tagged2
        - RemappedVlanId → remapped_vlan_id
        - TrunkMode → trunk_mode
        - PortIfIndex → port_if_index
        - DoubleTags → double_tags
        - NNIIfIndex → nni_if_index
        - PoeModeCtrl → poe_mode_ctrl

        Args:
            device: Device model instance
            client: JSON-RPC client

        Returns:
            Number of subscribers synced
        """
        # Get subscribers from device
        rpc_subs = await client.get_subscribers()

        if not rpc_subs:
            return 0

        # Track names we've seen
        seen_names = set()

        def get_int(data: dict, key: str, default: int = None):
            """Get integer value from dict, handling various formats."""
            val = data.get(key)
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        def get_str(data: dict, key: str, default: str = None):
            """Get string value from dict."""
            val = data.get(key)
            if val is None:
                return default
            return str(val) if val else default

        def get_bool(data: dict, key: str, default: bool = False):
            """Get boolean value from dict."""
            val = data.get(key)
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ('true', '1', 'yes')
            return bool(val)

        def format_vlan(vlan_id, outer_tag_vlan_id, remapped_vlan_id):
            """Format VLAN ID string."""
            if remapped_vlan_id and remapped_vlan_id > 0 and outer_tag_vlan_id and outer_tag_vlan_id > 0:
                return f"{outer_tag_vlan_id}/{vlan_id}/({remapped_vlan_id})"
            elif outer_tag_vlan_id and outer_tag_vlan_id > 0:
                return f"{outer_tag_vlan_id}/{vlan_id}"
            elif remapped_vlan_id and remapped_vlan_id > 0:
                return f"{vlan_id}/({remapped_vlan_id})"
            elif vlan_id:
                return str(vlan_id)
            return None

        for sub_data in rpc_subs:
            # Handle both direct format and key/val format
            if isinstance(sub_data, dict) and "key" in sub_data:
                data = sub_data.get("val", {})
            elif isinstance(sub_data, dict):
                data = sub_data
            else:
                continue

            # Get the actual name from the data, not the key
            name = data.get("Name", data.get("name", ""))
            if not name:
                continue

            # Ensure name is a string
            name = str(name)
            seen_names.add(name)

            # Extract all fields from JSON-RPC response
            json_id = get_int(data, "Id")
            uid = get_int(data, "Uid")
            description = get_str(data, "Description")
            endpoint_json_id = get_int(data, "EndpointId")
            endpoint_name = get_str(data, "EndpointName")
            endpoint_mac = get_str(data, "EndpointMacAddress")
            bw_profile_id = get_int(data, "BwProfileId")
            bw_profile_name = get_str(data, "BwProfileName")
            bw_profile_uid = get_int(data, "BwProfileUid")

            # VLAN configuration
            vlan_id = get_int(data, "VlanId", 0)
            outer_tag_vlan_id = get_int(data, "OuterTagVlanId", 0)
            remapped_vlan_id = get_int(data, "RemappedVlanId", 0)
            port1_vlan_id = format_vlan(vlan_id, outer_tag_vlan_id, remapped_vlan_id)

            vlan_is_tagged = get_bool(data, "VlanIsTagged")
            port2_vlan_id = get_int(data, "Port2VlanId")
            vlan_is_tagged2 = get_bool(data, "Port2VlanIsTagged")

            # Port configuration
            trunk_mode = get_bool(data, "TrunkMode")
            port_if_index = get_str(data, "PortIfIndex")
            double_tags = get_bool(data, "DoubleTags")
            nni_if_index = get_str(data, "NNIIfIndex")
            poe_mode_ctrl = get_str(data, "PoeModeCtrl")

            # Look up endpoint by MAC address to get endpoint_id
            endpoint_id = None
            if endpoint_mac:
                ep_result = await self.db.execute(
                    select(Endpoint).where(Endpoint.mac_address == endpoint_mac)
                )
                linked_endpoint = ep_result.scalar_one_or_none()
                if linked_endpoint:
                    endpoint_id = linked_endpoint.id

            # Find existing subscriber by json_id (device-side ID) first, then by name
            subscriber = None
            if json_id is not None:
                result = await self.db.execute(
                    select(Subscriber).where(
                        and_(Subscriber.device_id == device.id, Subscriber.json_id == json_id)
                    )
                )
                subscriber = result.scalar_one_or_none()
            if not subscriber:
                result = await self.db.execute(
                    select(Subscriber).where(
                        and_(Subscriber.device_id == device.id, Subscriber.name == name)
                    )
                )
                subscriber = result.scalar_one_or_none()

            if subscriber:
                # Update existing subscriber
                subscriber.endpoint_id = endpoint_id
                subscriber.json_id = json_id
                subscriber.uid = uid
                subscriber.description = description
                subscriber.endpoint_json_id = endpoint_json_id
                subscriber.endpoint_name = endpoint_name
                subscriber.endpoint_mac_address = endpoint_mac
                subscriber.bw_profile_id = bw_profile_id
                subscriber.bw_profile_name = bw_profile_name
                subscriber.bw_profile_uid = bw_profile_uid
                subscriber.port1_vlan_id = port1_vlan_id
                subscriber.vlan_is_tagged = vlan_is_tagged
                subscriber.port2_vlan_id = port2_vlan_id
                subscriber.vlan_is_tagged2 = vlan_is_tagged2
                subscriber.remapped_vlan_id = remapped_vlan_id
                subscriber.trunk_mode = trunk_mode
                subscriber.port_if_index = port_if_index
                subscriber.double_tags = double_tags
                subscriber.nni_if_index = nni_if_index
                subscriber.poe_mode_ctrl = poe_mode_ctrl
                subscriber.alive = True  # Device is online, so subscriber is alive
            else:
                # Create new subscriber
                subscriber = Subscriber(
                    device_id=device.id,
                    endpoint_id=endpoint_id,
                    name=name,
                    json_id=json_id,
                    uid=uid,
                    description=description,
                    endpoint_json_id=endpoint_json_id,
                    endpoint_name=endpoint_name,
                    endpoint_mac_address=endpoint_mac,
                    bw_profile_id=bw_profile_id,
                    bw_profile_name=bw_profile_name,
                    bw_profile_uid=bw_profile_uid,
                    port1_vlan_id=port1_vlan_id,
                    vlan_is_tagged=vlan_is_tagged,
                    port2_vlan_id=port2_vlan_id,
                    vlan_is_tagged2=vlan_is_tagged2,
                    remapped_vlan_id=remapped_vlan_id,
                    trunk_mode=trunk_mode,
                    port_if_index=port_if_index,
                    double_tags=double_tags,
                    nni_if_index=nni_if_index,
                    poe_mode_ctrl=poe_mode_ctrl,
                    alive=True,  # Device is online, so subscriber is alive
                )
                self.db.add(subscriber)

        return len(seen_names)

    async def sync_bandwidths(self, device: Device, client: GamRpcClient) -> int:
        """Sync bandwidth profiles from a device.

        Args:
            device: Device model instance
            client: JSON-RPC client

        Returns:
            Number of bandwidth profiles synced
        """
        # Get bandwidth profiles from device
        rpc_profiles = await client.get_bandwidth_profiles()

        if not rpc_profiles:
            return 0

        # Track names we've seen
        seen_names = set()

        for profile_data in rpc_profiles:
            # Handle key/val format
            if isinstance(profile_data, dict) and "key" in profile_data:
                data = profile_data.get("val", {})
            else:
                data = profile_data

            name = data.get("Name", data.get("name", ""))
            if not name:
                continue

            seen_names.add(name)

            uid = data.get("Uid", data.get("uid", data.get("Id", data.get("id"))))
            ds_bw = data.get("DsBw", data.get("dsBw", 0))
            us_bw = data.get("UsBw", data.get("usBw", 0))
            description = data.get("Description", data.get("description", ""))

            # Find or create bandwidth profile
            result = await self.db.execute(
                select(Bandwidth).where(
                    and_(Bandwidth.device_id == device.id, Bandwidth.name == name)
                )
            )
            bandwidth = result.scalar_one_or_none()

            if bandwidth:
                # Update existing profile
                bandwidth.uid = uid
                bandwidth.ds_bw = ds_bw
                bandwidth.us_bw = us_bw
                bandwidth.description = description
                bandwidth.sync = True
            else:
                # Create new profile
                bandwidth = Bandwidth(
                    device_id=device.id,
                    name=name,
                    uid=uid,
                    ds_bw=ds_bw,
                    us_bw=us_bw,
                    description=description,
                    sync=True,
                )
                self.db.add(bandwidth)

        # Mark profiles we didn't see as deleted
        result = await self.db.execute(
            select(Bandwidth).where(
                and_(Bandwidth.device_id == device.id, Bandwidth.deleted == False)
            )
        )
        for bandwidth in result.scalars():
            if bandwidth.name not in seen_names:
                bandwidth.deleted = True

        return len(seen_names)

    async def sync_ports(self, device: Device, client: GamRpcClient) -> int:
        """Sync port status from a device.

        Args:
            device: Device model instance
            client: JSON-RPC client

        Returns:
            Number of ports synced
        """
        # Get port status from device
        rpc_ports = await client.get_port_status()

        if not rpc_ports:
            return 0

        # Track keys we've seen
        seen_keys = set()
        position = 0

        for port_data in rpc_ports:
            # Handle key/val format
            if isinstance(port_data, dict) and "key" in port_data:
                key = port_data["key"]
                data = port_data.get("val", {})
            else:
                key = port_data.get("Key", port_data.get("key", ""))
                data = port_data

            if not key:
                continue

            seen_keys.add(key)
            position += 1

            # Find or create port
            result = await self.db.execute(
                select(Port).where(
                    and_(Port.device_id == device.id, Port.key == key)
                )
            )
            port = result.scalar_one_or_none()

            link = data.get("Link", data.get("link", False))
            fdx = data.get("Fdx", data.get("fdx", False))
            fiber = data.get("Fiber", data.get("fiber", False))
            speed = data.get("Speed", data.get("speed", ""))
            sfp_type = data.get("SFPType", data.get("sfpType", ""))
            sfp_vendor_name = data.get("SFPVendorName", data.get("sfpVendorName", ""))
            sfp_vendor_pn = data.get("SFPVendorPN", data.get("sfpVendorPN", ""))
            sfp_vendor_rev = data.get("SFPVendorRev", data.get("sfpVendorRev", ""))
            sfp_vendor_sn = data.get("SFPVendorSN", data.get("sfpVendorSN", ""))
            present = data.get("Present", data.get("present", False))
            loss_of_signal = data.get("LossOfSignal", data.get("lossOfSignal", False))
            tx_fault = data.get("TxFault", data.get("txFault", False))

            if port:
                # Update existing port
                port.link = link
                port.fdx = fdx
                port.fiber = fiber
                port.speed = speed
                port.sfp_type = sfp_type
                port.sfp_vendor_name = sfp_vendor_name
                port.sfp_vendor_pn = sfp_vendor_pn
                port.sfp_vendor_rev = sfp_vendor_rev
                port.sfp_vendor_sn = sfp_vendor_sn
                port.present = present
                port.loss_of_signal = loss_of_signal
                port.tx_fault = tx_fault
                port.position = position
            else:
                # Create new port
                port = Port(
                    device_id=device.id,
                    key=key,
                    position=position,
                    link=link,
                    fdx=fdx,
                    fiber=fiber,
                    speed=speed,
                    sfp_type=sfp_type,
                    sfp_vendor_name=sfp_vendor_name,
                    sfp_vendor_pn=sfp_vendor_pn,
                    sfp_vendor_rev=sfp_vendor_rev,
                    sfp_vendor_sn=sfp_vendor_sn,
                    present=present,
                    loss_of_signal=loss_of_signal,
                    tx_fault=tx_fault,
                )
                self.db.add(port)

        return len(seen_keys)

    @staticmethod
    def _parse_uptime(result) -> int:
        """Parse uptime RPC result to seconds.

        Handles formats like:
        - {"SystemUptime": "3d 13:32:27"}
        - {"Uptime": 12345}
        - int directly
        """
        if isinstance(result, (int, float)):
            return int(result)
        if isinstance(result, dict):
            val = result.get("SystemUptime") or result.get("Uptime") or result.get("uptime", 0)
        elif isinstance(result, list) and result:
            val = result[0] if not isinstance(result[0], dict) else (
                result[0].get("SystemUptime") or result[0].get("Uptime", 0)
            )
        else:
            return 0
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            # Parse "3d 13:32:27" format
            total = 0
            m = re.match(r'(?:(\d+)d\s*)?(\d+):(\d+):(\d+)', val)
            if m:
                total += int(m.group(1) or 0) * 86400
                total += int(m.group(2)) * 3600
                total += int(m.group(3)) * 60
                total += int(m.group(4))
                return total
        return 0

    async def sync_uptime(self, device: Device, client: GamRpcClient) -> Optional[int]:
        """Sync uptime from a device.

        Args:
            device: Device model instance
            client: JSON-RPC client

        Returns:
            Uptime in seconds, or None if failed
        """
        try:
            result = await client.get_uptime()
            logger.info(f"Uptime RPC result for {device.serial_number}: {result}")
            if result is not None:
                uptime = self._parse_uptime(result)
                device.uptime = uptime
                device.last_uptime_pulled = datetime.utcnow()
                return uptime
        except Exception as e:
            logger.error(f"Error getting uptime for {device.serial_number}: {e}")
        return None
