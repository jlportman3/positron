"""
Firmware management API.

Handles firmware file uploads, downloads, and device upgrade orchestration.
Firmware structure matches Virtuoso:
- Files stored in folders: {folder_name}/{folder_name}_positronfw.mfip
- Device downloads firmware via URL (server doesn't push)
- JSON-RPC: firmware.control.imageUpload.set, firmware.control.global.set
"""
import os
import re
import hashlib
import shutil
import xml.etree.ElementTree as ET
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import User, Firmware, Device
from app.core.config import settings
from app.rpc.client import create_client_for_device

router = APIRouter()

# Firmware storage directory
FIRMWARE_DIR = Path(settings.FIRMWARE_DIR if hasattr(settings, 'FIRMWARE_DIR') else "/app/firmware")
FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def parse_firmware_xml(xml_path: Path) -> dict:
    """Parse firmware.xml manifest to extract version metadata.

    Virtuoso manifest format:
    <firmware>
      <version>1.8.1</version>
      <revision>r5</revision>
      <technology>mimo</technology>
      <portQty>12-24</portQty>
    </firmware>
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        return {
            "version": root.findtext("version", ""),
            "revision": root.findtext("revision", ""),
            "technology": root.findtext("technology", ""),
            "port_qty": root.findtext("portQty", ""),
        }
    except Exception:
        return {}


def parse_folder_name(folder_name: str) -> dict:
    """Parse firmware folder name to extract metadata.

    Format: GAM_{version}_{technology}_{ports}_{revision}
    Example: GAM_1_8_1_mimo_12-24_r5
    """
    match = re.match(
        r'GAM_(\d+_\d+_\d+)_(\w+)_([\d-]+)_(\w+)',
        folder_name
    )
    if match:
        version_raw, technology, port_qty, revision = match.groups()
        return {
            "version": version_raw.replace("_", "."),
            "technology": technology,
            "port_qty": port_qty,
            "revision": revision,
        }
    return {}


def firmware_to_dict(fw: Firmware) -> dict:
    """Convert firmware model to API response dict."""
    return {
        "id": str(fw.id),
        "version": fw.version,
        "revision": fw.revision,
        "technology": fw.technology,
        "port_qty": fw.port_qty,
        "folder_name": fw.folder_name,
        "filename": fw.filename,
        "original_name": fw.original_name,
        "file_size": fw.file_size,
        "checksum": fw.checksum,
        "model_type": fw.model_type,
        "image_type": fw.image_type,
        "description": fw.description,
        "release_notes": fw.release_notes,
        "is_default": fw.is_default,
        "uploaded_at": fw.uploaded_at.isoformat() if fw.uploaded_at else None,
        "uploaded_by": fw.uploaded_by,
    }


@router.get("")
async def list_firmware(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    model_type: Optional[str] = None,
    technology: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all firmware files."""
    query = select(Firmware)

    if model_type:
        query = query.where(
            (Firmware.model_type == model_type) | (Firmware.model_type == None)
        )
    if technology:
        query = query.where(Firmware.technology == technology)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Firmware.uploaded_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [firmware_to_dict(fw) for fw in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("")
async def upload_firmware(
    files: List[UploadFile] = File(...),
    version: Optional[str] = Form(None),
    revision: Optional[str] = Form(None),
    technology: Optional[str] = Form(None),
    port_qty: Optional[str] = Form(None),
    model_type: Optional[str] = Form(None),
    image_type: str = Form("firmware"),
    description: Optional[str] = Form(None),
    release_notes: Optional[str] = Form(None),
    is_default: str = Form("false"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),
):
    """Upload firmware files.

    Accepts multiple files (.mfip, .xml, .sha256, .sign).
    If a firmware.xml manifest is included, metadata is auto-extracted.
    Files are stored in a folder: {folder_name}/{original_filenames}
    """
    is_default_bool = is_default.lower() in ("true", "1", "yes")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Find the .mfip file (primary firmware image)
    mfip_file = None
    xml_file = None
    all_files = []

    for f in files:
        all_files.append(f)
        if f.filename and f.filename.endswith('.mfip'):
            mfip_file = f
        elif f.filename and f.filename.endswith('.xml'):
            xml_file = f

    if not mfip_file:
        # If no .mfip, use first file as primary
        mfip_file = files[0]

    # Generate folder name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = mfip_file.filename.rsplit('.', 1)[0] if mfip_file.filename else "firmware"
    folder_name = f"{base_name}_{timestamp}"

    # Create folder
    folder_path = FIRMWARE_DIR / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)

    # Save all files
    saved_files = []
    try:
        for f in all_files:
            safe_name = f.filename.replace(" ", "_") if f.filename else "unknown"
            filepath = folder_path / safe_name
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            saved_files.append(filepath)
    except Exception as e:
        # Cleanup on failure
        shutil.rmtree(folder_path, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save files: {str(e)}")

    # Parse manifest if XML was uploaded
    manifest = {}
    xml_path = folder_path / (xml_file.filename if xml_file and xml_file.filename else "firmware.xml")
    if xml_path.exists():
        manifest = parse_firmware_xml(xml_path)

    # Try parsing folder name for metadata
    folder_meta = parse_folder_name(base_name)

    # Resolve metadata: form values > manifest > folder name parsing
    final_version = version or manifest.get("version") or folder_meta.get("version") or "unknown"
    final_revision = revision or manifest.get("revision") or folder_meta.get("revision") or ""
    final_technology = technology or manifest.get("technology") or folder_meta.get("technology") or ""
    final_port_qty = port_qty or manifest.get("port_qty") or folder_meta.get("port_qty") or ""
    final_model_type = model_type or final_technology

    # Get .mfip file info
    mfip_path = folder_path / (mfip_file.filename.replace(" ", "_") if mfip_file.filename else "unknown")
    file_size = mfip_path.stat().st_size if mfip_path.exists() else 0
    checksum = compute_sha256(mfip_path) if mfip_path.exists() else None

    # If baseline, unset other baselines for same technology+port_qty
    if is_default_bool:
        stmt = (
            update(Firmware)
            .where(
                (Firmware.technology == final_technology) &
                (Firmware.port_qty == final_port_qty) &
                (Firmware.is_default == True)
            )
            .values(is_default=False)
        )
        await db.execute(stmt)

    firmware = Firmware(
        version=final_version,
        revision=final_revision,
        technology=final_technology,
        port_qty=final_port_qty,
        folder_name=folder_name,
        filename=mfip_file.filename.replace(" ", "_") if mfip_file.filename else "unknown",
        original_name=mfip_file.filename or "unknown",
        file_size=file_size,
        checksum=checksum,
        model_type=final_model_type,
        image_type=image_type,
        description=description,
        release_notes=release_notes,
        is_default=is_default_bool,
        uploaded_by=user.username,
    )

    db.add(firmware)
    await db.commit()
    await db.refresh(firmware)

    return {
        "id": str(firmware.id),
        "folder_name": firmware.folder_name,
        "version": firmware.version,
        "revision": firmware.revision,
        "technology": firmware.technology,
        "checksum": firmware.checksum,
        "files": [f.filename for f in all_files],
        "message": "Firmware uploaded successfully",
    }


@router.get("/download/{folder_name}/{filename}")
async def download_firmware_file(
    folder_name: str,
    filename: str,
):
    """Download a firmware file from a folder.

    Used by GAM devices to pull firmware during upgrade.
    No auth required - devices need unauthenticated access.
    URL format: /firmware/download/{folder_name}/{filename}
    """
    filepath = FIRMWARE_DIR / folder_name / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Firmware file not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


# Keep legacy single-file download for backward compatibility
@router.get("/download/{filename}")
async def download_firmware_legacy(filename: str):
    """Legacy single-file download endpoint."""
    # Search in all folders
    for folder in FIRMWARE_DIR.iterdir():
        if folder.is_dir():
            filepath = folder / filename
            if filepath.exists():
                return FileResponse(path=filepath, filename=filename, media_type="application/octet-stream")

    # Check root firmware dir
    filepath = FIRMWARE_DIR / filename
    if filepath.exists():
        return FileResponse(path=filepath, filename=filename, media_type="application/octet-stream")

    raise HTTPException(status_code=404, detail="Firmware file not found")


@router.get("/{firmware_id}")
async def get_firmware(
    firmware_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get firmware details by ID."""
    result = await db.execute(select(Firmware).where(Firmware.id == firmware_id))
    firmware = result.scalar_one_or_none()

    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")

    return firmware_to_dict(firmware)


@router.delete("/{firmware_id}")
async def delete_firmware(
    firmware_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(10)),
):
    """Delete a firmware file and its folder."""
    result = await db.execute(select(Firmware).where(Firmware.id == firmware_id))
    firmware = result.scalar_one_or_none()

    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")

    # Delete folder from storage
    folder_path = FIRMWARE_DIR / firmware.folder_name
    if folder_path.exists() and folder_path.is_dir():
        shutil.rmtree(folder_path)

    # Also check for legacy single-file
    legacy_path = FIRMWARE_DIR / firmware.filename
    if legacy_path.exists():
        legacy_path.unlink()

    await db.delete(firmware)
    await db.commit()

    return {"message": "Firmware deleted successfully"}


@router.post("/{firmware_id}/set-default")
async def set_default_firmware(
    firmware_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(10)),
):
    """Set a firmware as baseline for its technology+port_qty."""
    result = await db.execute(select(Firmware).where(Firmware.id == firmware_id))
    firmware = result.scalar_one_or_none()

    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")

    # Unset other baselines for same technology+port_qty
    stmt = (
        update(Firmware)
        .where(
            (Firmware.technology == firmware.technology) &
            (Firmware.port_qty == firmware.port_qty) &
            (Firmware.is_default == True)
        )
        .values(is_default=False)
    )
    await db.execute(stmt)

    firmware.is_default = True
    await db.commit()

    return {"message": f"Firmware set as baseline for {firmware.technology} {firmware.port_qty}"}


@router.post("/deploy/{device_id}")
async def deploy_firmware_to_device(
    device_id: UUID,
    firmware_id: UUID = Query(...),
    auto_swap: bool = Query(False, description="Automatically swap to new firmware after download"),
    save_config: bool = Query(True, description="Save config before firmware upload"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),
):
    """Deploy firmware to a device.

    Virtuoso workflow:
    1. Save device config (optional)
    2. Construct firmware download URL
    3. Send imageUpload command - device pulls firmware from server
    4. Optionally auto-swap to new partition
    """
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    firmware_result = await db.execute(select(Firmware).where(Firmware.id == firmware_id))
    firmware = firmware_result.scalar_one_or_none()
    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")

    # Build firmware URL: {base_url}/firmware/download/{folder_name}/{filename}
    base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://localhost:8000"
    firmware_url = f"{base_url}/firmware/download/{firmware.folder_name}/{firmware.filename}"

    try:
        client = await create_client_for_device(device)

        # Step 1: Save config
        if save_config:
            await client.save_config()

        # Step 2: Send firmware upload command
        result = await client.firmware_upload(
            firmware_url=firmware_url,
            no_swap=not auto_swap,
        )

        await client.close()

        return {
            "message": "Firmware deployment initiated",
            "device_id": str(device_id),
            "firmware_id": str(firmware_id),
            "firmware_url": firmware_url,
            "auto_swap": auto_swap,
            "save_config": save_config,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy firmware: {str(e)}")


@router.post("/swap/{device_id}")
async def swap_firmware(
    device_id: UUID,
    save_config: bool = Query(True, description="Save config before swap"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),
):
    """Swap a device to its alternate firmware partition.

    Sends firmware.control.global.set {SwapFirmware: true} via JSON-RPC.
    Device will reboot to the other partition.
    """
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        client = await create_client_for_device(device)

        if save_config:
            await client.save_config()

        result = await client.firmware_swap()
        await client.close()

        return {
            "message": "Firmware swap initiated - device will reboot",
            "device_id": str(device_id),
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to swap firmware: {str(e)}")


class BulkDeviceRequest(BaseModel):
    device_ids: List[str]


@router.post("/bulk-download")
async def bulk_download_firmware(
    request: BulkDeviceRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),
):
    """Download baseline firmware to multiple devices (no swap).

    For each device, finds the baseline firmware matching its technology
    and sends the download command.
    """
    results = []
    for device_id_str in request.device_ids:
        try:
            device_id = UUID(device_id_str)
            device_result = await db.execute(select(Device).where(Device.id == device_id))
            device = device_result.scalar_one_or_none()
            if not device:
                results.append({"device_id": device_id_str, "status": "error", "detail": "Device not found"})
                continue

            # Find baseline firmware for this device's technology
            tech = device.technology or "mimo"
            fw_result = await db.execute(
                select(Firmware).where(
                    (Firmware.technology == tech) &
                    (Firmware.is_default == True)
                )
            )
            firmware = fw_result.scalar_one_or_none()
            if not firmware:
                results.append({"device_id": device_id_str, "status": "error", "detail": f"No baseline firmware for {tech}"})
                continue

            base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://localhost:8000"
            firmware_url = f"{base_url}/firmware/download/{firmware.folder_name}/{firmware.filename}"

            client = await create_client_for_device(device)
            await client.save_config()
            await client.firmware_upload(firmware_url=firmware_url, no_swap=True)
            await client.close()

            results.append({"device_id": device_id_str, "status": "success", "firmware": firmware.version})
        except Exception as e:
            results.append({"device_id": device_id_str, "status": "error", "detail": str(e)})

    return {"results": results}


@router.post("/bulk-download-activate")
async def bulk_download_activate(
    request: BulkDeviceRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),
):
    """Download baseline firmware and auto-swap on multiple devices."""
    results = []
    for device_id_str in request.device_ids:
        try:
            device_id = UUID(device_id_str)
            device_result = await db.execute(select(Device).where(Device.id == device_id))
            device = device_result.scalar_one_or_none()
            if not device:
                results.append({"device_id": device_id_str, "status": "error", "detail": "Device not found"})
                continue

            tech = device.technology or "mimo"
            fw_result = await db.execute(
                select(Firmware).where(
                    (Firmware.technology == tech) &
                    (Firmware.is_default == True)
                )
            )
            firmware = fw_result.scalar_one_or_none()
            if not firmware:
                results.append({"device_id": device_id_str, "status": "error", "detail": f"No baseline firmware for {tech}"})
                continue

            base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://localhost:8000"
            firmware_url = f"{base_url}/firmware/download/{firmware.folder_name}/{firmware.filename}"

            client = await create_client_for_device(device)
            await client.save_config()
            await client.firmware_upload(firmware_url=firmware_url, no_swap=False)
            await client.close()

            results.append({"device_id": device_id_str, "status": "success", "firmware": firmware.version})
        except Exception as e:
            results.append({"device_id": device_id_str, "status": "error", "detail": str(e)})

    return {"results": results}


@router.post("/bulk-activate-alternate")
async def bulk_activate_alternate(
    request: BulkDeviceRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),
):
    """Swap firmware partition on multiple devices (activate alternate)."""
    results = []
    for device_id_str in request.device_ids:
        try:
            device_id = UUID(device_id_str)
            device_result = await db.execute(select(Device).where(Device.id == device_id))
            device = device_result.scalar_one_or_none()
            if not device:
                results.append({"device_id": device_id_str, "status": "error", "detail": "Device not found"})
                continue

            client = await create_client_for_device(device)
            await client.save_config()
            await client.firmware_swap()
            await client.close()

            results.append({"device_id": device_id_str, "status": "success"})
        except Exception as e:
            results.append({"device_id": device_id_str, "status": "error", "detail": str(e)})

    return {"results": results}
