from sqlalchemy import Column, String, DateTime, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid


class Zone(Base):
    """Geographic zones for organizing GAM devices"""
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code for map display

    # Geographic bounds for the zone (optional)
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    gam_devices = relationship("GAMDevice", backref="zone")
    odb_splitters = relationship("ODBSplitter", backref="zone")

    def __repr__(self):
        return f"<Zone(name='{self.name}')>"
