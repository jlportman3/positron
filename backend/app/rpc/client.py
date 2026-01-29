"""
JSON-RPC client for GAM device communication.

Implements JSON-RPC 2.0 protocol over HTTP/HTTPS for communicating with
Positron GAM devices.
"""
import ssl
import logging
from typing import Any, Optional
import httpx

logger = logging.getLogger(__name__)


class GamRpcError(Exception):
    """Exception raised for GAM RPC errors."""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"RPC Error {code}: {message}")


class GamRpcClient:
    """JSON-RPC client for GAM devices."""

    def __init__(
        self,
        host: str,
        port: int = 80,
        proto: str = "http",
        username: str = "admin",
        password: str = "",
        timeout: float = 45.0,
    ):
        """Initialize GAM RPC client.

        Args:
            host: Device IP address or hostname
            port: HTTP port (default 80)
            proto: Protocol (http or https)
            username: HTTP Basic Auth username
            password: HTTP Basic Auth password
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.proto = proto
        self.username = username
        self.password = password
        self.timeout = timeout
        self._request_id = 0
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def url(self) -> str:
        """Get the JSON-RPC endpoint URL."""
        return f"{self.proto}://{self.host}:{self.port}/json_rpc"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            # For HTTPS, accept self-signed certificates
            verify = True
            if self.proto == "https":
                verify = False  # GAM devices use self-signed certs

            self._client = httpx.AsyncClient(
                auth=(self.username, self.password),
                timeout=self.timeout,
                verify=verify,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def call(self, method: str, params: list = None) -> Any:
        """Make a JSON-RPC call to the device.

        Args:
            method: JSON-RPC method name
            params: Method parameters (default empty list)

        Returns:
            The 'result' field from the JSON-RPC response

        Raises:
            GamRpcError: If the device returns an error
            httpx.HTTPError: If connection fails
        """
        if params is None:
            params = []

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._request_id,
        }

        logger.debug(f"RPC call to {self.host}: {method}")
        print(f"RPC PAYLOAD: {request}")  # Debug: print actual payload

        client = await self._get_client()
        response = await client.post(
            self.url,
            json=request,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        data = response.json()

        # Check for error (GAM returns "error": null on success)
        error = data.get("error")
        if error is not None:
            raise GamRpcError(
                code=error.get("code", -1),
                message=error.get("message", "Unknown error"),
            )

        return data.get("result")

    # Endpoint methods
    async def get_endpoints_brief(self) -> list:
        """Get all endpoints with basic info."""
        return await self.call("ghnAgent.status.endpointByMac.brief.get")

    async def get_endpoint_detailed(self, mac: str = None) -> Any:
        """Get detailed endpoint information."""
        params = [mac] if mac else []
        return await self.call("ghnAgent.status.endpointByMac.detailed.get", params)

    async def get_endpoint_link(self, conf_endpoint_id: int, position: int) -> Any:
        """Get endpoint Ethernet port link status.

        Args:
            conf_endpoint_id: The endpoint's configured ID on the device.
            position: Port position (1 or 2).

        Returns:
            Dict with Valid, State, Link, Fdx, Speed fields.
        """
        return await self.call("ghnAgent.status.endpoint.link.get", [conf_endpoint_id, position])

    async def reset_endpoint_poe(self, conf_endpoint_id: int) -> Any:
        """Reset PoE power for an endpoint.

        Matches Java EndpointPoeSetParams structure.

        Args:
            conf_endpoint_id: The endpoint's configured ID on the device
        """
        params = {"CyclePower": True}
        return await self.call("ghnAgent.control.endpoint.poe.set", [conf_endpoint_id, params])

    async def reboot_endpoint(self, conf_endpoint_id: int, start_fw_upgrade: bool = False) -> Any:
        """Reboot an endpoint.

        Matches Java EndpointRebootSetParams structure.

        Args:
            conf_endpoint_id: The endpoint's configured ID on the device
            start_fw_upgrade: Whether to start firmware upgrade after reboot
        """
        params = {"Reboot": True, "StartFwUpgrade": start_fw_upgrade}
        return await self.call("ghnAgent.control.endpoint.system.set", [conf_endpoint_id, params])

    async def get_endpoint_config(self) -> list:
        """Get configured endpoints from device."""
        return await self.call("ghnAgent.config.endpoint.get")

    def _port_string_to_index(self, port_if_index: str) -> int:
        """Convert a port string like 'G.hn 1/4' to its numeric index (4).

        The IfIndex enum maps port strings to numbers:
        - G.hn 1/1 -> 1, G.hn 1/2 -> 2, ..., G.hn 1/24 -> 24
        - 10G 1/1 -> 25, 10G 1/2 -> 26
        - Gi 1/1 -> 27
        """
        if port_if_index.startswith("G.hn 1/"):
            try:
                return int(port_if_index.split("/")[1])
            except (IndexError, ValueError):
                pass
        elif port_if_index.startswith("10G 1/"):
            try:
                return 24 + int(port_if_index.split("/")[1])
            except (IndexError, ValueError):
                pass
        elif port_if_index == "Gi 1/1":
            return 27
        elif port_if_index == "NONE":
            return 0

        raise ValueError(f"Unknown port format: {port_if_index}")

    async def add_endpoint(
        self,
        mac_address: str,
        port_if_index: str,
        name: str = "",
        description: str = "",
        auto_port: bool = False,
    ) -> Any:
        """Add/configure an endpoint on the device.

        This assigns a detected endpoint (by MAC) to a specific G.hn port,
        taking it out of quarantine and making it available for subscriber creation.

        Args:
            mac_address: The endpoint's MAC address (e.g., "00:0E:D8:1D:7B:2A")
            port_if_index: The G.hn port to assign as string (e.g., "G.hn 1/1", "G.hn 1/4")
            name: Endpoint name/label
            description: Endpoint description
            auto_port: Whether to auto-detect port

        Returns:
            Response from device (contains new conf_endpoint_id)
        """
        # NOTE: PortIfIndex must be a STRING like "G.hn 1/4", not a numeric index.
        # The device firmware expects the string representation.
        params = {
            "MacAddress": mac_address,
            "Name": name,
            "Description": description,
            "PortIfIndex": port_if_index,  # String format: "G.hn 1/4", "NONE", etc.
            "AutoPort": auto_port,
            "AllowMgmtVlan": False,
        }
        # First param is 0 (for new endpoint), second is the params object
        return await self.call("ghnAgent.config.endpoint.add", [0, params])

    async def edit_endpoint(
        self,
        conf_endpoint_id: int,
        port_if_index: str = None,
        name: str = None,
        description: str = None,
        auto_port: bool = None,
    ) -> Any:
        """Edit an existing configured endpoint.

        Args:
            conf_endpoint_id: The endpoint's configured ID
            port_if_index: New G.hn port assignment as string (e.g., "G.hn 1/4")
            name: New endpoint name
            description: New description
            auto_port: New auto-port setting
        """
        params = {}
        if port_if_index is not None:
            params["PortIfIndex"] = port_if_index  # String format
        if name is not None:
            params["Name"] = name
        if description is not None:
            params["Description"] = description
        if auto_port is not None:
            params["AutoPort"] = auto_port
        return await self.call("ghnAgent.config.endpoint.set", [conf_endpoint_id, params])

    async def delete_endpoint(self, conf_endpoint_id: int) -> Any:
        """Delete a configured endpoint from the device.

        Args:
            conf_endpoint_id: The endpoint's configured ID
        """
        return await self.call("ghnAgent.config.endpoint.del", [conf_endpoint_id])

    # Subscriber methods
    async def get_subscribers(self) -> list:
        """Get all subscribers."""
        return await self.call("ghnAgent.config.user.get")

    async def add_subscriber(
        self,
        name: str,
        description: str = "",
        endpoint_id: int = 0,
        bw_profile_uid: int = 0,
        vlan_id: int = 0,
        vlan_is_tagged: bool = False,
        remapped_vlan_id: int = 0,
        port2_vlan_id: int = 0,
        trunk_mode: bool = False,
        port_if_index: str = "NONE",
        double_tags: bool = False,
        nni_if_index: str = "NONE",
        outer_tag_vlan_id: int = 0,
        poe_mode_ctrl: str = "",
    ) -> Any:
        """Add a new subscriber.

        Args:
            name: Subscriber name
            description: Subscriber description
            endpoint_id: Device's internal endpoint ID (conf_endpoint_id)
            bw_profile_uid: Device's internal bandwidth profile UID (use BwProfileId)
            vlan_id: Primary VLAN ID
            vlan_is_tagged: Whether VLAN is tagged
            remapped_vlan_id: Remapped VLAN ID
            port2_vlan_id: Secondary VLAN ID
            trunk_mode: Enable trunk mode
            port_if_index: Port interface as string ("NONE", "G.hn 1/1", etc.)
            double_tags: Enable QinQ double tagging
            nni_if_index: Uplink port as string ("NONE", "Gi 1/1", "10G 1/1", etc.)
            outer_tag_vlan_id: Outer tag VLAN ID for QinQ
            poe_mode_ctrl: PoE mode control (e.g., "enable", "disable", "")
        """
        params = {
            "Name": name,
            "Description": description,
            "EndpointId": endpoint_id,
            "BwProfileId": bw_profile_uid,  # Device uses BwProfileId, not BwProfileUid
            "VlanId": vlan_id,
            "VlanIsTagged": vlan_is_tagged,
            "RemappedVlanId": remapped_vlan_id,
            "Port2VlanId": port2_vlan_id,
            "TrunkMode": trunk_mode,
            "PortIfIndex": port_if_index,  # Must be string: "NONE", "G.hn 1/1", etc.
            "DoubleTags": double_tags,
            "NNIIfIndex": nni_if_index,  # Must be string: "NONE", "Gi 1/1", etc.
            "OuterTagVlanId": outer_tag_vlan_id,
        }
        # PoeModeCtrl only valid values are "enable" or "disable" - don't send if empty
        if poe_mode_ctrl in ("enable", "disable"):
            params["PoeModeCtrl"] = poe_mode_ctrl
        # First param is always 0 for add (new subscriber)
        return await self.call("ghnAgent.config.user.add", [0, params])

    async def edit_subscriber(
        self,
        json_id: int,
        name: str,
        description: str = "",
        endpoint_id: int = 0,
        bw_profile_uid: int = 0,
        vlan_id: int = 0,
        vlan_is_tagged: bool = False,
        remapped_vlan_id: int = 0,
        port2_vlan_id: int = 0,
        port2_vlan_is_tagged: bool = False,
        trunk_mode: bool = False,
        port_if_index: str = "NONE",
        double_tags: bool = False,
        nni_if_index: str = "NONE",
        outer_tag_vlan_id: int = 0,
        poe_mode_ctrl: str = "",
    ) -> Any:
        """Edit an existing subscriber.

        Matches Java SubscriberEditParamsContainer structure.

        Args:
            json_id: The subscriber's JSON ID on the device
            (other params same as add_subscriber)
            port2_vlan_is_tagged: Whether secondary VLAN is tagged (edit only)
        """
        params = {
            "Name": name,
            "Description": description,
            "EndpointId": endpoint_id,
            "BwProfileId": bw_profile_uid,
            "VlanId": vlan_id,
            "VlanIsTagged": vlan_is_tagged,
            "RemappedVlanId": remapped_vlan_id,
            "Port2VlanId": port2_vlan_id,
            "Port2VlanIsTagged": port2_vlan_is_tagged,
            "TrunkMode": trunk_mode,
            "PortIfIndex": port_if_index,  # Must be string: "NONE", "G.hn 1/1", etc.
            "DoubleTags": double_tags,
            "NNIIfIndex": nni_if_index,  # Must be string: "NONE", "Gi 1/1", etc.
            "OuterTagVlanId": outer_tag_vlan_id,
        }
        # PoeModeCtrl only valid values are "enable" or "disable" - don't send if empty
        if poe_mode_ctrl in ("enable", "disable"):
            params["PoeModeCtrl"] = poe_mode_ctrl
        # First param is the subscriber's JSON ID
        return await self.call("ghnAgent.config.user.set", [json_id, params])

    async def delete_subscriber(self, json_id: int) -> Any:
        """Delete a subscriber.

        Args:
            json_id: The subscriber's JSON ID on the device
        """
        return await self.call("ghnAgent.config.user.del", [json_id])

    # Bandwidth profile methods
    async def get_bandwidth_profiles(self) -> list:
        """Get all bandwidth profiles."""
        return await self.call("ghnAgent.config.bwProfile.get")

    async def add_bandwidth_profile(
        self,
        name: str,
        description: str = "",
        ds_bw: int = 0,
        us_bw: int = 0,
    ) -> Any:
        """Add a new bandwidth profile.

        Matches Java BandwidthAddParams structure.

        Args:
            name: Profile name
            description: Profile description
            ds_bw: Downstream bandwidth in Mbps
            us_bw: Upstream bandwidth in Mbps
        """
        params = {
            "Name": name,
            "Description": description,
            "DsBw": str(ds_bw),  # Sent as string for add
            "UsBw": str(us_bw),  # Sent as string for add
        }
        # First param is always 0 for add
        return await self.call("ghnAgent.config.bwProfile.add", [0, params])

    async def edit_bandwidth_profile(
        self,
        name: str,
        description: str = "",
        ds_bw: int = 0,
        us_bw: int = 0,
    ) -> Any:
        """Edit an existing bandwidth profile.

        Args:
            name: Profile name (used as identifier)
            description: Profile description
            ds_bw: Downstream bandwidth in Mbps
            us_bw: Upstream bandwidth in Mbps
        """
        params = {
            "Name": name,
            "Description": description,
            "DsBw": ds_bw,
            "UsBw": us_bw,
        }
        # First param is the profile NAME (not UID)
        return await self.call("ghnAgent.config.bwProfileByName.set", [name, params])

    async def delete_bandwidth_profile(self, name: str) -> Any:
        """Delete a bandwidth profile by name.

        Args:
            name: The bandwidth profile name
        """
        return await self.call("ghnAgent.config.bwProfileByName.del", [name])

    # Port methods
    async def get_port_status(self) -> list:
        """Get port status information."""
        return await self.call("port.status.get")

    async def get_port_config(self) -> list:
        """Get port configuration."""
        return await self.call("port.config.get")

    async def get_ghn_port_config(self) -> list:
        """Get G.hn port configuration."""
        return await self.call("ghnAgent.config.port.get")

    # System methods
    async def get_uptime(self) -> Any:
        """Get system uptime."""
        return await self.call("systemUtility.status.systemUptime.get")

    async def get_ghn_global_config(self) -> Any:
        """Get global G.hn configuration."""
        return await self.call("ghnAgent.config.global.get")

    # Configuration management
    async def save_config(self) -> Any:
        """Save running config to startup config.

        Matches Java GamConfigCopySetParams structure.
        """
        params = {
            "Copy": True,
            "SourceConfigType": "runningConfig",
            "DestinationConfigType": "startupConfig",
        }
        return await self.call("icfg.control.copy.set", [params])

    async def download_config(self, source_type: str = "runningConfig") -> str:
        """Download device configuration.

        Args:
            source_type: Configuration type - 'runningConfig' or 'startupConfig'

        Returns:
            Configuration content as string
        """
        params = {
            "SourceConfigType": source_type,
            "SourceConfigFile": "flash:default-config",
        }
        return await self.call("icfg.control.download.get", [params])

    async def upload_config(self, config_content: str) -> Any:
        """Upload configuration to device.

        Args:
            config_content: Configuration content to upload
        """
        return await self.call("icfg.control.upload.set", [config_content])

    # Firmware management
    async def firmware_upload(
        self,
        firmware_url: str,
        no_swap: bool = True,
    ) -> Any:
        """Initiate firmware download on device.

        Matches Java FirmwareUploadParams structure.
        The device downloads the firmware from the provided URL.

        Args:
            firmware_url: URL where device can download firmware file
            no_swap: If True, don't auto-swap after download (default True)
        """
        params = {
            "DoUpload": True,
            "ImageType": "firmware",
            "Url": firmware_url,
            "NoSwap": no_swap,
        }
        return await self.call("firmware.control.imageUpload.set", [params])

    async def firmware_swap(self) -> Any:
        """Swap to alternate firmware partition.

        Matches Java FirmwareSwapParams structure.
        Device will reboot to the other firmware partition.
        """
        params = {"SwapFirmware": True}
        return await self.call("firmware.control.global.set", [params])

    async def firmware_config_copy(self) -> Any:
        """Copy config to alternate partition before firmware swap.

        Matches Java FirmwareConfigCopyParams structure.
        Ensures config is preserved when swapping partitions.
        """
        params = {"ConfigCopy": True}
        return await self.call("firmware.control.configCopy.set", [params])

    # NTP/Timezone methods
    async def get_timezone(self) -> Any:
        """Get device timezone configuration."""
        return await self.call("daylightSaving.config.global.get")

    async def set_timezone(
        self,
        offset_minutes: int,
        summer_time_mode: str = "disable",
        acronym: str = "",
    ) -> Any:
        """Set device timezone configuration.

        Args:
            offset_minutes: Timezone offset in minutes from UTC (e.g., -360 for UTC-6)
            summer_time_mode: "enable" or "disable"
            acronym: Timezone acronym (e.g., "CST")
        """
        params = {
            "TimeZoneOffset": offset_minutes,
            "SummerTimeMode": summer_time_mode,
            "TimeZoneAcronym": acronym,
        }
        return await self.call("daylightSaving.config.global.set", [params])

    async def get_ntp_servers(self) -> list:
        """Get NTP server configuration."""
        return await self.call("ntp.config.servers.get")

    async def set_ntp_servers(self, servers: list) -> Any:
        """Set NTP server configuration.

        Args:
            servers: List of NTP server addresses (strings)
        """
        # Device expects [{key: 1, val: "address"}, ...] format
        server_list = [
            {"key": i + 1, "val": addr}
            for i, addr in enumerate(servers)
        ]
        return await self.call("ntp.config.servers.set", [server_list])

    async def set_ntp_mode(self, enabled: bool = True) -> Any:
        """Enable or disable NTP.

        Args:
            enabled: True to enable NTP, False to disable
        """
        params = {"Enabled": enabled}
        return await self.call("ntp.config.global.set", [params])

    # Port configuration methods
    async def set_port_config(
        self,
        port_index: int,
        enabled: bool = None,
        speed: str = None,
        duplex: str = None,
        auto_negotiation: bool = None,
        mtu: int = None,
        description: str = None,
    ) -> Any:
        """Set port configuration.

        Args:
            port_index: Port index number
            enabled: Enable/disable port
            speed: Port speed (10/100/1000)
            duplex: Duplex mode (full/half/auto)
            auto_negotiation: Enable auto-negotiation
            mtu: MTU size
            description: Port description
        """
        params = {}
        if enabled is not None:
            params["Enabled"] = enabled
        if speed is not None:
            params["Speed"] = speed
        if duplex is not None:
            params["Duplex"] = duplex
        if auto_negotiation is not None:
            params["AutoNegotiation"] = auto_negotiation
        if mtu is not None:
            params["MTU"] = mtu
        if description is not None:
            params["Description"] = description
        return await self.call("port.config.set", [port_index, params])

    # Discovery agent methods (for device announcement configuration)
    async def get_discovery_config(self) -> Any:
        """Get discovery agent configuration."""
        return await self.call("discoveryAgent.config.target.get")

    async def set_discovery_target(
        self,
        url: str,
        username: str = "device",
        password: str = "device",
        period: int = 60,
    ) -> Any:
        """Set discovery/announcement target URL.

        This configures where the device sends its announcements.

        Args:
            url: Server URL (e.g., "https://alamo-gam.example.com:8000")
            username: HTTP Basic Auth username for announcements
            password: HTTP Basic Auth password for announcements
            period: Announcement period in seconds
        """
        params = {
            "Url": url,
            "Username": username,
            "Password": password,
            "Period": period,
        }
        return await self.call("discoveryAgent.config.target.set", [params])

    async def get_discovery_global(self) -> Any:
        """Get discovery agent global settings."""
        return await self.call("discoveryAgent.config.global.get")

    async def set_discovery_global(
        self,
        enabled: bool = True,
        use_ssl: bool = True,
    ) -> Any:
        """Set discovery agent global settings.

        Args:
            enabled: Enable/disable discovery agent
            use_ssl: Use SSL for announcements
        """
        params = {
            "Enabled": enabled,
            "UseSsl": use_ssl,
        }
        return await self.call("discoveryAgent.config.global.set", [params])

    async def set_discovery_tunnel_port(self, port: int) -> Any:
        """Set SSH reverse tunnel port for discovery.

        Args:
            port: SSH tunnel port to use
        """
        params = {"Port": port}
        return await self.call("discoveryAgent.config.rpt.set", [params])

    # Diagnostics methods
    async def get_signal_measurement(self, port_if_index: str = None) -> Any:
        """Get signal/spectrum measurement data.

        Args:
            port_if_index: Optional port to measure (e.g., "G.hn 1/1")
        """
        params = []
        if port_if_index:
            params = [{"PortIfIndex": port_if_index}]
        return await self.call("ghnAgent.diagnostics.signalMeasurement.get", params)

    # G.hn port-specific methods
    async def set_ghn_port_config(
        self,
        port_if_index: str,
        enabled: bool = None,
        power_back_off: int = None,
        force_master: bool = None,
    ) -> Any:
        """Set G.hn port configuration.

        Args:
            port_if_index: Port interface (e.g., "G.hn 1/1")
            enabled: Enable/disable G.hn port
            power_back_off: Power back-off level
            force_master: Force this port as domain master
        """
        params = {}
        if enabled is not None:
            params["Enabled"] = enabled
        if power_back_off is not None:
            params["PowerBackOff"] = power_back_off
        if force_master is not None:
            params["ForceMaster"] = force_master
        return await self.call("ghnAgent.config.port.set", [port_if_index, params])


async def create_client_for_device(device) -> GamRpcClient:
    """Create a GamRpcClient for a device model instance.

    Args:
        device: Device model instance with connection details

    Returns:
        Configured GamRpcClient instance

    Note:
        GAM devices use HTTP Basic Auth. The user_name/password fields from
        the announcement are the actual HTTP credentials (obfuscated tokens
        that the device's web server accepts directly).
        Per-device rpc_username/rpc_password override if set.
    """
    username = device.rpc_username or device.user_name or "admin"
    password = device.rpc_password or device.password or ""

    return GamRpcClient(
        host=device.ip_address,
        port=int(device.port or 80),
        proto=device.proto or "http",
        username=username,
        password=password,
    )
