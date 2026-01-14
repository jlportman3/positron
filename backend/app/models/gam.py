from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid
import enum


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class PortType(str, enum.Enum):
    MIMO = "mimo"
    SISO = "siso"
    COAX = "coax"


class PortStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    DISABLED = "disabled"
    ERROR = "error"


class GAMDevice(Base):
    __tablename__ = "gam_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=False, unique=True)  # Support IPv6
    mac_address = Column(String(17), nullable=True)
    model = Column(String(50), nullable=False)  # GAM-12-M, GAM-24-M, GAM-12-C, GAM-24-C
    firmware_version = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE, nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Geographic coordinates for mapping
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True)
    
    # Connection settings
    snmp_community = Column(String(100), nullable=False, default="public")
    ssh_credentials = Column(JSONB, nullable=True)  # Store encrypted credentials (legacy)
    ssh_username = Column(String(100), nullable=True)  # SSH username for CLI access
    ssh_password = Column(String(255), nullable=True)  # SSH password (should be encrypted in production)
    ssh_port = Column(Integer, nullable=False, default=22)  # SSH port
    management_vlan = Column(Integer, nullable=False, default=4093)
    
    # Device info
    serial_number = Column(String(100), nullable=True)
    uptime = Column(Integer, nullable=True)  # Seconds
    cpu_usage = Column(Integer, nullable=True)  # Percentage
    memory_usage = Column(Integer, nullable=True)  # Percentage
    temperature = Column(Integer, nullable=True)  # Celsius
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    ports = relationship("GAMPort", back_populates="device", cascade="all, delete-orphan")
    subscribers = relationship("Subscriber", back_populates="gam_device")

    def __repr__(self):
        return f"<GAMDevice(name='{self.name}', ip='{self.ip_address}', status='{self.status}')>"

    @property
    def port_count(self):
        """Get total number of ports based on model"""
        import re
        # Extract number from model string (e.g., GAM-4-C -> 4, GAM-12-M -> 12)
        match = re.search(r'GAM-(\d+)-', self.model, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Fallback for older logic
        if "24" in self.model:
            return 24
        elif "12" in self.model:
            return 12
        elif "4" in self.model:
            return 4
        return 0

    @property
    def active_subscribers(self):
        """Get count of active subscribers"""
        return len([s for s in self.subscribers if s.status == "active"])

    @property
    def is_coax_model(self):
        """Check if this is a coax model"""
        return "C" in self.model

    @property
    def is_copper_model(self):
        """Check if this is a copper model"""
        return "M" in self.model


class GAMPort(Base):
    __tablename__ = "gam_ports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gam_device_id = Column(UUID(as_uuid=True), ForeignKey("gam_devices.id"), nullable=False)
    port_number = Column(Integer, nullable=False)
    port_type = Column(Enum(PortType), nullable=False)
    status = Column(Enum(PortStatus), default=PortStatus.DOWN, nullable=False)
    name = Column(String(100), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Port configuration
    mimo_enabled = Column(Boolean, default=False, nullable=False)  # For copper ports
    vectorboost_level = Column(Integer, default=0, nullable=False)  # 0-4
    power_mask_config = Column(JSONB, nullable=True)  # Power mask notches
    
    # Port statistics
    link_speed_down = Column(Integer, nullable=True)  # Mbps
    link_speed_up = Column(Integer, nullable=True)  # Mbps
    snr_downstream = Column(Integer, nullable=True)  # dB
    snr_upstream = Column(Integer, nullable=True)  # dB
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    device = relationship("GAMDevice", back_populates="ports")
    subscribers = relationship("Subscriber", back_populates="gam_port")

    def __repr__(self):
        return f"<GAMPort(device='{self.device.name}', port={self.port_number}, status='{self.status}')>"

    @property
    def is_available(self):
        """Check if port is available for new subscriber"""
        if not self.enabled or self.status == PortStatus.ERROR:
            return False
        
        # For coax ports, can have multiple subscribers (up to 16)
        if self.port_type == PortType.COAX:
            active_subscribers = len([s for s in self.subscribers if s.status == "active"])
            return active_subscribers < 16
        
        # For copper ports (MIMO/SISO), only one subscriber per port
        return len([s for s in self.subscribers if s.status == "active"]) == 0

    @property
    def subscriber_count(self):
        """Get count of active subscribers on this port"""
        return len([s for s in self.subscribers if s.status == "active"])
