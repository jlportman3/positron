"""
Device schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class DeviceAnnouncement(BaseModel):
    """Device announcement payload from GAM devices.

    This matches the JSON body sent by devices to PUT /device/announcement/request
    """
    # Core identification
    SerialNumber: str = Field(..., alias="SerialNumber")
    MACAddress: Optional[str] = Field(None, alias="MACAddress")
    Name: Optional[str] = Field(None, alias="Name")
    Vendor: Optional[str] = Field(None, alias="Vendor")
    ProductClass: Optional[str] = Field(None, alias="ProductClass")
    HardwareVersion: Optional[str] = Field(None, alias="HardwareVersion")
    Compatible: Optional[str] = Field(None, alias="Compatible")
    UNIPorts: Optional[str] = Field(None, alias="UNIPorts")
    CLEICode: Optional[str] = Field(None, alias="CLEICode")

    # Network
    IPAddress: Optional[str] = Field(None, alias="IPAddress")
    FQDN: Optional[str] = Field(None, alias="FQDN")
    Proto: str = Field("https", alias="Proto")
    Port: str = Field("443", alias="Port")

    # Software
    SoftwareVersion: Optional[str] = Field(None, alias="SoftwareVersion")
    SoftwareRevision: Optional[str] = Field(None, alias="SoftwareRevision")
    SoftwareBuildDate: Optional[str] = Field(None, alias="SoftwareBuildDate")
    Firmware: Optional[str] = Field(None, alias="Firmware")
    FirmwareEncryptionKeyID: Optional[str] = Field(None, alias="FirmwareEncryptionKeyID")
    SoftwareUpgradeStatus: Optional[str] = Field(None, alias="SoftwareUpgradeStatus")

    # Swap partition
    SwapSoftwareVersion: Optional[str] = Field(None, alias="SwapSoftwareVersion")
    SwapSoftwareRevision: Optional[str] = Field(None, alias="SwapSoftwareRevision")
    SwapSoftwareBuildDate: Optional[str] = Field(None, alias="SwapSoftwareBuildDate")

    # Announcement settings
    AnnouncementPeriod: Optional[str] = Field(None, alias="AnnouncementPeriod")
    AnnouncementURL: Optional[str] = Field(None, alias="AnnouncementURL")

    # Credentials (16 levels)
    UserName: Optional[str] = Field(None, alias="UserName")
    Password: Optional[str] = Field(None, alias="Password")
    UserNameLevel0: Optional[str] = Field(None, alias="UserNameLevel0")
    PasswordLevel0: Optional[str] = Field(None, alias="PasswordLevel0")
    UserNameLevel1: Optional[str] = Field(None, alias="UserNameLevel1")
    PasswordLevel1: Optional[str] = Field(None, alias="PasswordLevel1")
    UserNameLevel2: Optional[str] = Field(None, alias="UserNameLevel2")
    PasswordLevel2: Optional[str] = Field(None, alias="PasswordLevel2")
    UserNameLevel3: Optional[str] = Field(None, alias="UserNameLevel3")
    PasswordLevel3: Optional[str] = Field(None, alias="PasswordLevel3")
    UserNameLevel4: Optional[str] = Field(None, alias="UserNameLevel4")
    PasswordLevel4: Optional[str] = Field(None, alias="PasswordLevel4")
    UserNameLevel5: Optional[str] = Field(None, alias="UserNameLevel5")
    PasswordLevel5: Optional[str] = Field(None, alias="PasswordLevel5")
    UserNameLevel6: Optional[str] = Field(None, alias="UserNameLevel6")
    PasswordLevel6: Optional[str] = Field(None, alias="PasswordLevel6")
    UserNameLevel7: Optional[str] = Field(None, alias="UserNameLevel7")
    PasswordLevel7: Optional[str] = Field(None, alias="PasswordLevel7")
    UserNameLevel8: Optional[str] = Field(None, alias="UserNameLevel8")
    PasswordLevel8: Optional[str] = Field(None, alias="PasswordLevel8")
    UserNameLevel9: Optional[str] = Field(None, alias="UserNameLevel9")
    PasswordLevel9: Optional[str] = Field(None, alias="PasswordLevel9")
    UserNameLevel10: Optional[str] = Field(None, alias="UserNameLevel10")
    PasswordLevel10: Optional[str] = Field(None, alias="PasswordLevel10")
    UserNameLevel11: Optional[str] = Field(None, alias="UserNameLevel11")
    PasswordLevel11: Optional[str] = Field(None, alias="PasswordLevel11")
    UserNameLevel12: Optional[str] = Field(None, alias="UserNameLevel12")
    PasswordLevel12: Optional[str] = Field(None, alias="PasswordLevel12")
    UserNameLevel13: Optional[str] = Field(None, alias="UserNameLevel13")
    PasswordLevel13: Optional[str] = Field(None, alias="PasswordLevel13")
    UserNameLevel14: Optional[str] = Field(None, alias="UserNameLevel14")
    PasswordLevel14: Optional[str] = Field(None, alias="PasswordLevel14")
    UserNameLevel15: Optional[str] = Field(None, alias="UserNameLevel15")
    PasswordLevel15: Optional[str] = Field(None, alias="PasswordLevel15")

    # SSH Tunnel
    RemotePortTunnel: int = Field(0, alias="RemotePortTunnel")
    RemotePortTunnelIndex: int = Field(0, alias="RemotePortTunnelIndex")

    # Status
    Virtual: bool = Field(False, alias="Virtual")
    Uptime: Optional[int] = Field(None, alias="Uptime")

    # Location
    Location: Optional[str] = Field(None, alias="Location")
    Contact: Optional[str] = Field(None, alias="Contact")

    class Config:
        populate_by_name = True


class DeviceCreate(BaseModel):
    """Manual device creation request."""
    serial_number: str
    name: Optional[str] = None
    ip_address: str
    proto: str = "https"
    port: str = "443"
    user_name: Optional[str] = None
    password: Optional[str] = None
    group_id: Optional[UUID] = None


class DeviceUpdate(BaseModel):
    """Device update request."""
    name: Optional[str] = None
    ip_address: Optional[str] = None
    proto: Optional[str] = None
    port: Optional[str] = None
    user_name: Optional[str] = None
    password: Optional[str] = None
    rpc_username: Optional[str] = None
    rpc_password: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None
    group_id: Optional[UUID] = None
    read_only: Optional[bool] = None


class DeviceBrief(BaseModel):
    """Brief device info for lists."""
    id: UUID
    serial_number: str
    name: Optional[str] = None
    ip_address: Optional[str] = None
    is_online: bool
    read_only: bool = False
    product_class: Optional[str] = None
    software_version: Optional[str] = None
    endpoint_count: int = 0
    subscriber_count: int = 0
    alarm_count: int = 0
    uptime: Optional[int] = None
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """Full device response."""
    id: UUID
    serial_number: str
    mac_address: Optional[str] = None
    name: Optional[str] = None
    vendor: Optional[str] = None
    product_class: Optional[str] = None
    hardware_version: Optional[str] = None
    compatible: Optional[str] = None
    uni_ports: Optional[str] = None
    clei_code: Optional[str] = None

    # Network
    ip_address: Optional[str] = None
    fqdn: Optional[str] = None
    proto: str
    port: str

    # RPC credentials
    rpc_username: Optional[str] = None

    # Software
    software_version: Optional[str] = None
    software_revision: Optional[str] = None
    software_build_date: Optional[str] = None
    firmware: Optional[str] = None
    swap_software_version: Optional[str] = None
    swap_software_revision: Optional[str] = None
    swap_software_build_date: Optional[str] = None

    # Status
    is_virtual: bool
    is_online: bool
    read_only: bool = False
    uptime: Optional[int] = None

    # Location
    location: Optional[str] = None
    contact: Optional[str] = None

    # Group
    group_id: Optional[UUID] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_announcement: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    # Counts
    endpoint_count: int = 0
    subscriber_count: int = 0
    alarm_count: int = 0

    # Health monitoring
    health_score: int = 100
    health_status: str = "healthy"
    last_health_check: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeviceList(BaseModel):
    """Paginated device list."""
    items: List[DeviceBrief]
    total: int
    page: int
    page_size: int
    online_count: int = 0
    offline_count: int = 0
