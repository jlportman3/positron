"""
Subscriber Excel import API.

Accepts an Excel (.xlsx) file and creates subscriber records.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, require_privilege
from app.models import User, Device, Subscriber

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/import")
async def import_subscribers(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),
):
    """Import subscribers from an Excel file.

    Expected columns: device_serial, name, description, endpoint_mac_address,
    bw_profile_name, port1_vlan_id, vlan_is_tagged, port2_vlan_id,
    vlan_is_tagged2, poe_mode_ctrl
    """
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be .xlsx or .xls")

    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl not installed")

    contents = await file.read()

    import io
    wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True)
    ws = wb.active
    if not ws:
        raise HTTPException(status_code=400, detail="Empty workbook")

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="File must have a header row and at least one data row")

    # Parse header
    header = [str(c).strip().lower().replace(' ', '_') if c else '' for c in rows[0]]
    wb.close()

    # Build device cache by serial
    device_cache: dict[str, Device] = {}

    results = []
    created = 0

    for row_num, row in enumerate(rows[1:], start=2):
        row_data = dict(zip(header, row))

        serial = str(row_data.get('device_serial', '') or '').strip()
        name = str(row_data.get('name', '') or '').strip()

        if not serial:
            results.append({"row": row_num, "status": "error", "detail": "Missing device_serial"})
            continue
        if not name:
            results.append({"row": row_num, "status": "error", "detail": "Missing name"})
            continue

        # Lookup device
        if serial not in device_cache:
            res = await db.execute(select(Device).where(Device.serial_number == serial))
            dev = res.scalar_one_or_none()
            if dev:
                device_cache[serial] = dev
            else:
                results.append({"row": row_num, "status": "error", "detail": f"Device {serial} not found"})
                continue
        device = device_cache[serial]

        def _bool(val):
            if val is None:
                return False
            if isinstance(val, bool):
                return val
            return str(val).strip().lower() in ('true', '1', 'yes')

        def _int(val):
            if val is None:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        try:
            sub = Subscriber(
                device_id=device.id,
                name=name,
                description=str(row_data.get('description', '') or '').strip() or None,
                endpoint_mac_address=str(row_data.get('endpoint_mac_address', '') or '').strip() or None,
                bw_profile_name=str(row_data.get('bw_profile_name', '') or '').strip() or None,
                port1_vlan_id=str(row_data.get('port1_vlan_id', '') or '').strip() or None,
                vlan_is_tagged=_bool(row_data.get('vlan_is_tagged')),
                port2_vlan_id=_int(row_data.get('port2_vlan_id')),
                vlan_is_tagged2=_bool(row_data.get('vlan_is_tagged2')),
                poe_mode_ctrl=str(row_data.get('poe_mode_ctrl', '') or '').strip() or None,
            )
            db.add(sub)
            created += 1
            results.append({"row": row_num, "status": "created", "name": name})
        except Exception as e:
            results.append({"row": row_num, "status": "error", "detail": str(e)})

    if created > 0:
        await db.commit()

    return {
        "message": f"Imported {created}/{len(rows) - 1} subscribers",
        "created": created,
        "total_rows": len(rows) - 1,
        "results": results,
    }
