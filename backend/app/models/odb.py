from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid


class ODBSplitter(Base):
    """Optical Distribution Box / Fiber Splitters"""
    __tablename__ = "odb_splitters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    splitter_type = Column(String(50), nullable=True)  # e.g., "1x8", "1x16", "1x32"
    port_count = Column(Integer, nullable=False, default=8)

    # Location information
    location = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Zone assignment
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True)

    # Parent GAM device this splitter connects to
    gam_device_id = Column(UUID(as_uuid=True), ForeignKey("gam_devices.id"), nullable=True)
    gam_port_id = Column(UUID(as_uuid=True), ForeignKey("gam_ports.id"), nullable=True)

    # Notes and documentation
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    gam_device = relationship("GAMDevice", backref="splitters")
    gam_port = relationship("GAMPort", backref="splitters")
    subscribers = relationship("Subscriber", back_populates="odb_splitter")

    def __repr__(self):
        return f"<ODBSplitter(name='{self.name}', type='{self.splitter_type}')>"

    @property
    def available_ports(self):
        """Get count of available ports"""
        active_subscribers = len([s for s in self.subscribers if s.status == "active"])
        return self.port_count - active_subscribers
