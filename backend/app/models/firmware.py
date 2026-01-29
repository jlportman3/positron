"""
Firmware model for storing firmware files.

Firmware files come as a folder containing:
- .mfip (firmware image)
- .xml (manifest with version/revision/technology)
- .mfip.sha256 (checksum)
- .mfip.sha256.sign and .mfip.sign (signatures)

The device downloads firmware from the server via HTTP URL.
Virtuoso protocol: firmware.control.imageUpload.set with {DoUpload, Url, ImageType, NoSwap}
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Firmware(Base):
    """
    Firmware file storage.

    Matches Virtuoso's Firmware entity structure.
    Baseline = one default firmware per technology + port_qty combination.
    """
    __tablename__ = "firmware"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Version info (from firmware.xml manifest)
    version = Column(String(50), nullable=False)        # e.g., "1.8.1"
    revision = Column(String(50), default="")            # e.g., "r5"
    technology = Column(String(20), default="")           # "mimo" or "coax"
    port_qty = Column(String(20), default="")             # e.g., "12-24", "4-8"

    # File info
    folder_name = Column(String(255), nullable=False, unique=True)  # e.g., "GAM_1_8_1_mimo_12-24_r5"
    filename = Column(String(255), nullable=False)        # Primary .mfip filename
    original_name = Column(String(255), nullable=False)   # Original upload filename
    file_size = Column(Integer, nullable=False)
    checksum = Column(String(64))                         # SHA256 hash of .mfip

    # Device compatibility
    model_type = Column(String(50))  # "mimo" or "coax" (derived from technology)
    image_type = Column(String(20), default="firmware")   # "firmware" or "bootloader"

    # Metadata
    description = Column(Text)
    release_notes = Column(Text)
    is_default = Column(Boolean, default=False)  # Baseline firmware for this technology+port_qty

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100))

    def __repr__(self):
        return f"<Firmware {self.folder_name} v{self.version}>"
