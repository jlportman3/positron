from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid
import enum


class SubscriberStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    service_address = Column(String(500), nullable=False)
    
    # GAM Assignment
    gam_device_id = Column(UUID(as_uuid=True), ForeignKey("gam_devices.id"), nullable=False)
    gam_port_id = Column(UUID(as_uuid=True), ForeignKey("gam_ports.id"), nullable=False)
    
    # Endpoint Configuration
    endpoint_mac = Column(String(17), nullable=False)  # G1000/G1001 MAC address
    endpoint_model = Column(String(50), nullable=True)  # G1000-M, G1001-C, etc.
    endpoint_firmware = Column(String(50), nullable=True)
    
    # VLAN Configuration
    vlan_id = Column(Integer, nullable=False)  # Primary VLAN (3-4093)
    remapped_vid = Column(Integer, nullable=True)  # Remapped VLAN ID
    endpoint_tagging = Column(Boolean, default=False, nullable=False)  # Tag at endpoint
    allowed_vlans = Column(JSONB, nullable=True)  # List of allowed VLANs for IPTV
    
    # Service Configuration
    bandwidth_plan_id = Column(UUID(as_uuid=True), ForeignKey("bandwidth_plans.id"), nullable=False)
    status = Column(Enum(SubscriberStatus), default=SubscriberStatus.PENDING, nullable=False)
    
    # External System Integration
    external_id = Column(String(100), nullable=True)  # Sonar/Splynx customer ID
    external_service_id = Column(String(100), nullable=True)  # Service ID in billing system
    external_system = Column(String(50), nullable=True)  # "sonar" or "splynx"
    
    # Service Statistics
    bytes_downloaded = Column(Integer, default=0, nullable=False)
    bytes_uploaded = Column(Integer, default=0, nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    connection_uptime = Column(Integer, default=0, nullable=False)  # Seconds
    
    # Provisioning
    provisioned_at = Column(DateTime(timezone=True), nullable=True)
    deprovisioned_at = Column(DateTime(timezone=True), nullable=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Notes and metadata
    notes = Column(String(1000), nullable=True)
    tags = Column(JSONB, nullable=True)  # Flexible tagging system
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    gam_device = relationship("GAMDevice", back_populates="subscribers")
    gam_port = relationship("GAMPort", back_populates="subscribers")
    bandwidth_plan = relationship("BandwidthPlan", back_populates="subscribers")

    def __repr__(self):
        return f"<Subscriber(name='{self.name}', status='{self.status}', vlan={self.vlan_id})>"

    @property
    def is_active(self):
        """Check if subscriber is active"""
        return self.status == SubscriberStatus.ACTIVE

    @property
    def is_provisioned(self):
        """Check if subscriber is provisioned"""
        return self.provisioned_at is not None and self.deprovisioned_at is None

    @property
    def bandwidth_down_mbps(self):
        """Get downstream bandwidth in Mbps"""
        return self.bandwidth_plan.downstream_mbps if self.bandwidth_plan else 0

    @property
    def bandwidth_up_mbps(self):
        """Get upstream bandwidth in Mbps"""
        return self.bandwidth_plan.upstream_mbps if self.bandwidth_plan else 0

    @property
    def total_data_gb(self):
        """Get total data usage in GB"""
        total_bytes = self.bytes_downloaded + self.bytes_uploaded
        return round(total_bytes / (1024 ** 3), 2)

    @property
    def port_type(self):
        """Get the port type this subscriber is connected to"""
        return self.gam_port.port_type if self.gam_port else None

    @property
    def device_name(self):
        """Get the GAM device name"""
        return self.gam_device.name if self.gam_device else None

    def can_provision(self):
        """Check if subscriber can be provisioned"""
        if self.status not in [SubscriberStatus.PENDING, SubscriberStatus.INACTIVE]:
            return False, "Subscriber status does not allow provisioning"
        
        if not self.gam_port or not self.gam_port.is_available:
            return False, "GAM port is not available"
        
        if not self.bandwidth_plan:
            return False, "No bandwidth plan assigned"
        
        return True, "Ready for provisioning"

    def get_vlan_config(self):
        """Get VLAN configuration for this subscriber"""
        config = {
            "primary_vlan": self.vlan_id,
            "endpoint_tagging": self.endpoint_tagging,
            "allowed_vlans": self.allowed_vlans or []
        }
        
        if self.remapped_vid:
            config["remapped_vlan"] = self.remapped_vid
            
        return config
