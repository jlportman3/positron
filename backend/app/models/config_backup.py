"""
Configuration backup model for storing device config snapshots.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ConfigBackup(Base):
    """Device configuration backup snapshot."""

    __tablename__ = "config_backups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    config_content = Column(Text, nullable=False)
    config_type = Column(String(50), default="runningConfig")  # runningConfig or startupConfig
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

    def __repr__(self):
        return f"<ConfigBackup device={self.device_id} v{self.version_number}>"
